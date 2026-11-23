"""2026-11-23 (3-D ⑤, 설계 claude/improve_without_training_proposal_2026-11-22.md §6): 바꿔 쓸 말 표 kind·when.

- kind  typo · alias · broaden(고객 조건보다 넓은 말) / when  zero · few · both (비면 alias·both = 예전 동작)
- **broaden 으로 찾은 상품이 추천 후보 칸에 들어가면 실패** — 0건 다시 찾기에 쓰지 않고 '추가 후보' 칸에만, 안내 문구와 함께.
"""
from __future__ import annotations

import pytest

from app.services.chat.service import ChatService
from app.services.commerce import coupang_gaps as cg
from app.services.recipe_chat.service import RecipeChat
from tests.services.chat.test_evoo_retry_2026_11_22 import ByQuery, _cp

TABLE = """# 시험 표
from,to,kind,when,note
저온압착 참기름,참기름,broaden,few,조건 빠짐
저온압착 들기름,들기름,broaden,both,both 로 적어도 few 로 봄
브레타,부라타,typo,both,
올리브유,올리브오일,,,
현미유,쌀겨유,alias,zero,
포도씨유,포도씨오일,alias,few,
이상한,말,similar,both,
"""


@pytest.fixture
def table(tmp_path, monkeypatch):
    p = tmp_path / "query_synonyms.csv"
    p.write_text(TABLE, encoding="utf-8")
    monkeypatch.setattr(cg, "SYNONYMS", p)
    monkeypatch.setattr(cg, "_rows_cache", None)
    monkeypatch.setattr(cg, "similar_query", lambda q: None)       # 자모 고침은 이 시험 밖
    monkeypatch.setenv("COUPANG_MORE_ON_FEW", "on")
    return p


def test_rows_parse_defaults_and_broaden_is_few_only(table):
    rows = {r["from"]: r for r in cg.synonym_rows()}
    assert rows["올리브유"]["kind"] == "alias" and rows["올리브유"]["when"] == "both"   # 비면 예전 동작
    assert rows["저온압착 들기름"]["when"] == "few"                                   # broaden 은 늘 few
    assert "이상한" not in rows                                                      # 모르는 kind 는 뺌
    zero = dict(cg.synonyms(purpose="zero"))
    assert "저온압착 참기름" not in zero and "저온압착 들기름" not in zero and "포도씨유" not in zero
    assert zero["현미유"] == "쌀겨유" and zero["브레타"] == "부라타"
    few = dict(cg.synonyms(purpose="few"))
    assert few["저온압착 참기름"] == "참기름" and "현미유" not in few
    assert cg.retry_queries("저온압착 참기름") == []
    assert cg.retry_queries("저온압착 참기름", purpose="few") == ["참기름"]
    assert cg.is_broaden("저온압착 참기름", "참기름") and not cg.is_broaden("올리브유", "올리브오일")


def test_real_table_keeps_old_behavior():
    """실제 표: 지금 줄은 모두 alias/typo·both — 0건 다시 찾기·추가 후보 둘 다 예전과 같은 말."""
    cg._rows_cache = None
    rows = cg.synonym_rows()
    assert rows and all(r["kind"] in ("alias", "typo") and r["when"] == "both" for r in rows)
    old = [(r["from"], r["to"]) for r in rows]
    for a, _ in old:
        assert cg.retry_queries(a) == cg.retry_queries(a, old) == cg.retry_queries(a, purpose="few")


def _items(res):
    return {b["data"].get("title"): [i["title"] for i in b["data"]["items"]]
            for b in res["blocks"] if b["type"] == "product_list"}


def test_broaden_never_enters_recommendation_on_zero(table, sqlite_db):
    shop = ByQuery({"참기름": [_cp("오뚜기 참기름 320ml", 6900, 1), _cp("백설 참기름 500ml", 9900, 2)]})
    svc = ChatService(sqlite_db, shopping=shop, recipe_chat=RecipeChat(statement_factory=str))
    res = svc.handle(None, message="저온압착 참기름")
    assert "참기름" not in shop.calls                                 # 0건 다시 찾기에 넓힌 말을 쓰지 않음
    assert not any("오뚜기 참기름" in t for ts in _items(res).values() for t in ts)


def test_broaden_only_in_extra_slot_with_notice(table, sqlite_db):
    shop = ByQuery({
        "저온압착 참기름": [_cp("저온압착 참기름 국산 180ml", 15900, 1)],
        "참기름": [_cp("오뚜기 참기름 320ml", 6900, 2), _cp("백설 참기름 500ml", 9900, 3)],
    })
    svc = ChatService(sqlite_db, shopping=shop, recipe_chat=RecipeChat(statement_factory=str))
    res = svc.handle(None, message="저온압착 참기름")
    lists = _items(res)
    extra = {t: v for t, v in lists.items() if t and t.startswith("다른 검색어로 찾은 추가 후보")}
    main = [x for t, v in lists.items() if t not in extra for x in v]
    assert main == ["저온압착 참기름 국산 180ml"]                    # 추천 후보는 고객 조건 그대로
    assert extra and {"오뚜기 참기름 320ml", "백설 참기름 500ml"} <= set(next(iter(extra.values())))
    note = next(b["data"]["note"] for b in res["blocks"] if b["type"] == "product_list"
                and (b["data"].get("title") or "").startswith("다른 검색어로 찾은 추가 후보"))
    assert "찾으신 조건보다 넓은 말" in note and "'참기름'" in note


def test_alias_extra_slot_has_no_broaden_notice(table, sqlite_db):
    shop = ByQuery({"포도씨유": [_cp("포도씨유 900ml", 8900, 1)], "포도씨오일": [_cp("이탈리아 포도씨오일 1L", 12900, 2)]})
    svc = ChatService(sqlite_db, shopping=shop, recipe_chat=RecipeChat(statement_factory=str))
    res = svc.handle(None, message="포도씨유")
    notes = [b["data"].get("note") or "" for b in res["blocks"] if b["type"] == "product_list"]
    assert any("포도씨오일" in n for n in notes) and not any("넓은 말" in n for n in notes)
