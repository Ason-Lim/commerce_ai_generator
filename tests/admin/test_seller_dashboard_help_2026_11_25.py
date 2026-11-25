"""셀러 대시보드 · 사용법 도우미 (창 5, 2026-11-25).

대시보드: 판매 현황(기간·전 기간 대비)·주문 흐름·상품 상태·상품별 판매 — 셀러 격리, 받는 분 정보 안 씀, 금액은 추정이라고 밝힘.
도우미: help_kb.json 지식만으로 답(Claude·Ollama), 지식 밖 번호·약속 문장은 버리고 규칙 답, 개인정보는 보내기 전에 가림.
학습 자료: scripts/export_seller_help_dataset.py — JSONL + Ollama Modelfile.
"""

from __future__ import annotations

import json
import os
from datetime import datetime

import pytest
from cryptography.fernet import Fernet
from fastapi.testclient import TestClient

os.environ.setdefault("CORPMALL_KEY", Fernet.generate_key().decode())

from app.services.corpmall import store as corp  # noqa: E402
from app.services.seller import dashboard  # noqa: E402
from app.services.seller import help as H  # noqa: E402
from app.services.seller import products as prod  # noqa: E402
from app.services.seller import scm  # noqa: E402
from app.services.seller import store as sel  # noqa: E402

IP = "1.1.1.1"
KST = sel.KST
AT = datetime(2026, 11, 25, 15, 0, tzinfo=KST)


@pytest.fixture
def eng(tmp_path, monkeypatch):
    monkeypatch.setenv("CS_DIR", str(tmp_path / "cs"))
    monkeypatch.setenv("OPERATOR_NOTIFY", "off")
    corp.reset_limits()
    e = scm.engine()
    with e.begin() as c:
        for t in (scm.t_order, scm.t_batch, scm.t_supply, scm.t_supplier, scm.t_stock, prod.t_listing, prod.t_product,
                  sel.t_event, sel.t_key, sel.t_seller):  # fmt: skip
            c.execute(t.delete())
    return e


def _seller(eng, name="가농장"):
    s = sel.create_seller(eng, name=name, kind="consign", contact={"name": "김", "email": "k@a.kr"}, by="operator")
    sel.set_status(eng, s["seller_id"], "active", by="operator", reason="ok")
    return s, sel.issue_key(eng, s["seller_id"], by="operator")["code"]


def _orders(eng, k, lines):
    head = "판매처 주문번호,상품 번호,수량,받는 분,휴대폰,우편번호,주소,배송 메모,주문일\n"
    body = "".join(
        f"{no},{pid},{q},홍길동,010-1234-5678,04524,서울 중구 세종대로 110,,{od}\n" for no, pid, q, od in lines
    )
    got = scm.import_orders(eng, k, IP, head + body, entrust_ok=True)
    assert got["ok"] is True, got


def _shop(eng):
    s, k = _seller(eng)
    a = prod.save(eng, k, IP, {"name": "제주 감귤", "volume": "5kg", "price": "23900", "origin": "제주"})["product_id"]
    b = prod.save(eng, k, IP, {"name": "한라봉", "volume": "3kg", "price": "31000", "origin": "제주"})["product_id"]
    for pid in (a, b):
        prod.review(eng, pid, "approved", by="operator")
    _orders(eng, k, [("N1", a, 2, "2026-11-25"), ("N2", a, 1, "2026-11-23"), ("N2", b, 1, "2026-11-23"),
                     ("N3", b, 3, "2026-11-15"), ("N4", a, 1, "2026-10-01")])  # fmt: skip
    return s, k, a, b, None


# ── 대시보드 ──
def test_week_sales_compare_with_the_week_before(eng):
    s, k, a, b, _ = _shop(eng)
    d = dashboard.build(eng, s["seller_id"], period="week", at=AT)
    assert d["range"] == {"from": "2026-11-19", "to": "2026-11-25"}
    sl = d["sales"]
    assert (sl["orders"], sl["qty"], sl["amount"]) == (2, 4, 23900 * 3 + 31000)  # N1·N2 (11-23 두 줄은 한 주문)
    assert sl["prev"] == {"orders": 1, "qty": 3, "amount": 31000 * 3}  # 11-15
    assert sl["change"]["qty"] == 33 and "정산 금액 아님" in sl["amount_note"]
    rows = {r["product_id"]: r for r in d["by_product"]}
    assert rows[a]["qty"] == 3 and rows[a]["orders"] == 2 and rows[b]["prev_qty"] == 3
    assert d["by_product"][0]["product_id"] == a  # 많이 팔린 순
    assert len(d["series"]) == 14 and d["series"][-1] == {"day": "2026-11-25", "orders": 1, "qty": 2}


def test_day_and_month_and_empty_previous_period(eng):
    s, *_ = _shop(eng)
    day = dashboard.build(eng, s["seller_id"], period="day", at=AT)
    assert day["sales"]["qty"] == 2 and day["sales"]["change"]["qty"] is None  # 어제 판매 없음 → 비교 없음
    month = dashboard.build(eng, s["seller_id"], period="month", at=AT)
    assert month["sales"]["qty"] == 7 and month["sales"]["prev"]["qty"] == 1  # 10-01 은 그 전 30일
    with pytest.raises(sel.SellerError):
        dashboard.build(eng, s["seller_id"], period="year", at=AT)


def test_product_states_order_flow_and_no_clicks_made_up(eng):
    s, k, a, b, _ = _shop(eng)
    prod.save(eng, k, IP, {"name": "천혜향", "price": "29000", "origin": "제주"})  # 검수 대기
    prod.set_listing(eng, k, IP, b, False)
    scm.set_stock(eng, k, IP, a, stock="0", sold_out=False, restock_on=None)
    d = dashboard.build(eng, s["seller_id"], period="week", at=AT)
    assert d["products"] == {"on_sale": 0, "off": 1, "sold_out": 1, "pending": 1, "rejected": 0, "total": 3}
    assert d["orders_flow"]["new"] == 5 and d["orders_flow"]["delayed"] >= 1
    assert d["visits"] == {"clicks": None, "note": "방문·클릭 수는 아직 재지 않아요(준비 중)."}


def test_dashboard_is_isolated_and_has_no_recipient_data(eng):
    _s, k, *_ = _shop(eng)
    _s2, k2 = _seller(eng, "나농장")
    mine = dashboard.my_dashboard(eng, k, IP, at=AT)
    other = dashboard.my_dashboard(eng, k2, IP, at=AT)
    assert mine["sales"]["qty"] == 4 and other["sales"]["qty"] == 0 and other["by_product"] == []
    text = json.dumps(mine, ensure_ascii=False)
    assert "홍길동" not in text and "010-" not in text and "세종대로" not in text
    assert mine["alerts"]["new_orders"] == 5 and mine["asks"]["open"] == 0


def test_dashboard_api(eng):
    from app.main import app

    _s, k, *_ = _shop(eng)
    c = TestClient(app)
    j = c.post("/seller/api/dashboard", json={"key": k, "period": "month"}).json()
    assert j["ok"] and j["dashboard"]["period"] == "month"
    assert c.post("/seller/api/dashboard", json={"key": "nope-nope-nope", "period": "week"}).json()["ok"] is False
    page = c.get("/seller").text
    assert 'id="dash-h"' in page and 'id="help-h"' in page and "/seller/api/help" in page


# ── 사용법 도우미 ──
def test_kb_is_complete_and_points_to_real_sections():
    kb = H.kb()
    assert len(kb["entries"]) >= 30
    from pathlib import Path

    html = (Path(__file__).resolve().parents[2] / "app/services/seller/web/seller.html").read_text(encoding="utf-8")
    for e in kb["entries"]:
        assert e["answer"] and len(e["questions"]) >= 2
        assert f'id="{e["section"]}"' in html, e["id"]
    assert len({e["id"] for e in kb["entries"]}) == len(kb["entries"])


@pytest.mark.parametrize(
    "q, want",
    [
        ("상품 잠깐 내리려면 어떻게 해요?", "off"),
        ("품절 처리 어떻게 해요", "soldout"),
        ("스마트스토어 상품 그대로 가져올 수 있어요?", "channel"),
        ("송장 번호 어떻게 넣어요", "tracking"),
        ("엑셀로 상품 여러개 등록", "upload_csv"),
        ("방문자 수는 왜 안 나와요", "visits"),
    ],
)
def test_rule_search_finds_the_entry(q, want):
    assert H.search(q)[0][1]["id"] == want
    out = H.answer(q)
    assert out["by"] == "rule" and out["sources"][0]["id"] == want


def test_ai_answer_uses_only_given_entries():
    seen = []

    def ai(text):
        seen.append(json.loads(text))
        return {
            "answer": "‘내 상품’ 표에서 ‘판매 끄기’를 누르면 바로 내려가요. 검수는 필요 없어요.",
            "sources": ["off"],
            "sure": True,
        }

    out = H.answer("상품 내리는 방법 알려줘", ai=ai, ai_name="anthropic:claude-haiku-5-5")
    assert out["by"] == "anthropic:claude-haiku-5-5" and out["sources"][0]["id"] == "off" and not out["handoff"]
    assert {x["id"] for x in seen[0]["지식"]} >= {"off"} and len(seen[0]["지식"]) <= H.TOP_K


@pytest.mark.parametrize(
    "bad",
    [
        {"answer": "판매 끄기를 누르세요. 그리고 이용료는 면제해 드릴게요.", "sources": ["off"], "sure": True},  # 약속
        {"answer": "‘판매 끄기’를 누르세요. 그러면 바로 내려가요.", "sources": ["made_up"], "sure": True},  # 없는 항목
        {"answer": "짧", "sources": ["off"], "sure": True},
        "not a dict",
    ],
)
def test_bad_ai_answers_fall_back_to_the_rule_answer(bad):
    out = H.answer("상품 내리는 방법", ai=lambda t: bad, ai_name="x")
    assert out["by"] == "rule" and out["sources"][0]["id"] == "off"


def test_ai_failure_and_unsure_answers():
    def boom(_t):
        raise TimeoutError

    assert H.answer("상품 내리는 방법", ai=boom)["by"] == "rule"
    out = H.answer("상품 내리는 방법", ai=lambda t: {"answer": "안내 내용으로는 답하기 어려워요. 운영팀에 묻기로 남겨 주세요.",
                                                  "sources": [], "sure": False})  # fmt: skip
    assert out["handoff"] is True and out["by"] != "rule"


def test_safety_questions_never_go_to_ai():
    called = []
    out = H.answer("손님이 먹고 배탈이 났대요", ai=lambda t: called.append(t) or {})
    assert called == [] and out["handoff"] is True and "식품 안전" in out["answer"]


def test_unknown_question_offers_the_ops_team():
    out = H.answer("오늘 점심 뭐 먹지")
    assert out["handoff"] is True and "운영팀에 묻기" in out["answer"]


def test_ask_masks_personal_data_before_ai_and_logs_no_text(eng, monkeypatch):
    _s, k = _seller(eng)
    sent = []
    monkeypatch.setattr(H, "_client", lambda env=None: ((lambda t: sent.append(t) or {
        "answer": "‘주문 · 발주서 · 송장’에서 ‘송장 파일’을 올리고 ‘송장 넣기’를 누르세요.", "sources": ["tracking"], "sure": True}),
        "ollama:commerce-seller-help"))  # fmt: skip
    out = H.ask(eng, k, IP, "홍길동 010-1234-5678 송장 어떻게 넣어요")
    assert "010-1234-5678" not in sent[0] and out["masked"] and out["by"] == "ollama:commerce-seller-help"
    with eng.connect() as c:
        ev = c.execute(sel.t_event.select().where(sel.t_event.c.kind == "help")).mappings().all()
    assert len(ev) == 1 and "010" not in json.dumps(ev[0]["detail"]) and ev[0]["detail"]["by"] == "ai"


def test_provider_choice(monkeypatch):
    assert H._client({"SELLER_HELP_PROVIDER": "off", "ANTHROPIC_API_KEY": "a"}) == (None, None)
    assert H._client({}) == (None, None)  # Claude 키 없음 → 규칙 답
    fn, name = H._client({"ANTHROPIC_API_KEY": "a"})
    assert fn is not None and name == "anthropic:claude-haiku-5-5"
    fn, name = H._client({"SELLER_HELP_PROVIDER": "ollama", "OLLAMA_MODEL": "commerce-seller-help"})
    assert fn is not None and name == "ollama:commerce-seller-help"


def test_help_api(eng, monkeypatch):
    from app.main import app

    monkeypatch.setattr(H, "_client", lambda env=None: (None, None))
    _s, k = _seller(eng)
    j = TestClient(app).post("/seller/api/help", json={"key": k, "text": "상품 다시 판매하려면?"}).json()
    assert j["ok"] and j["by"] == "rule" and j["sources"][0]["id"] == "on"


# ── 학습 자료 ──
def test_export_dataset_for_ollama(tmp_path):
    import importlib.util
    from pathlib import Path

    p = Path(__file__).resolve().parents[2] / "scripts" / "export_seller_help_dataset.py"
    spec = importlib.util.spec_from_file_location("export_seller_help_dataset", p)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    m = mod.export(tmp_path, base="qwen2.5:7b")
    lines = (tmp_path / "seller_help_train.jsonl").read_text(encoding="utf-8").splitlines()
    assert m["examples"] == len(lines) and m["contains_customer_text"] is False
    first = json.loads(lines[0])
    assert [x["role"] for x in first["messages"]] == ["system", "user", "assistant"]
    mf = (tmp_path / "Modelfile").read_text(encoding="utf-8")
    assert mf.startswith("FROM qwen2.5:7b") and "판매 끄기" in mf and 'SYSTEM """' in mf
