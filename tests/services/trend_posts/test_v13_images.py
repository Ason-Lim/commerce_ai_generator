"""2026-11-20 실제 초안 검증(v1.3) 반영 · 트렌드 글 대표 그림 (구매 = 쿠팡 사진, 보류 = AI 그림)."""

from __future__ import annotations

import pytest

import io

from app.services.trend_posts import cover, draft, frame, render, templates
from app.services.trend_posts.model import VALID_IMAGE, PostImage
from app.services.trends import blog_autosave as bas
from app.services.trends import surge as S

from .helpers import approved, item, report, search_result, service


@pytest.fixture(autouse=True)
def _frame04_format(monkeypatch):
    """이 파일은 프레임 0.4 사이트 글을 검사한다 — 2026-11-21 부터 새 글 기본은 보고서형(test_report.py)."""
    monkeypatch.setenv("TREND_POST_FORMAT", "frame04")


# ── 문장 (v1.3) ─────────────────────────────────────────────────────────
def test_answer_heads_are_whole_sentences():
    assert all(not h.endswith("하면.") for h in frame.ANSWER_HEAD["blog"])
    assert "한 줄로 정리하면." not in frame.ANSWER_HEAD["blog"]


def test_kimjang_criteria_differ_by_item():
    assert frame.kimjang_part("절임배추10kg") == "cabbage" and frame.kimjang_part("황석어젓갈") == "jeotgal"
    assert frame.kimjang_part("고춧가루") == ""
    cabbage, jeotgal = (
        frame.criteria("절임배추10kg", "blog", "kimjang"),
        frame.criteria("황석어젓갈", "blog", "kimjang"),
    )
    assert any("포기 수" in c for c in cabbage) and not any("포기" in c for c in jeotgal)
    assert any("전날" in c and "당일" in c for c in cabbage)
    assert not any("포기" in c for c in frame.criteria("고춧가루", "site", "kimjang"))


def test_cabbage_receiving_line_is_not_store_ahead():
    secs = templates.sections("05", "절임배추10kg", "kimjang", [], None, "blog")
    text = " ".join(x for _, lines in secs for x in lines)
    assert "미리 받아 두는 재료가 아니에요" in text and "미리 받으면 보관할 자리" not in text


def test_signals_line_names_what_moved():
    s = frame.signals_line(
        {"n": 2, "of": 3, "parts": {"블로그 글 증가": True, "식품 순위 상승": True, "구글 트렌드": False}}
    )
    assert s.startswith("함께 움직인 신호: 블로그 글 증가·식품 순위 상승") and "구글 트렌드" in s and "/" not in s
    assert "아직 없어요" in frame.signals_line({"parts": {"블로그 글 증가": False}})
    assert frame.signals_line({"n": 1, "of": 2}) is None  # 예전 리포트(parts 없음)는 줄을 빼기
    assert frame.clue_phrase({"할인·행사": 1}) == "할인·행사 이야기 1건"


def test_why_lines_use_real_particle_and_say_when_cause_unknown():
    lines = draft.why_lines(item("페레로로쉐", status="new", cause=None), "2026-11-19")
    assert "'페레로로쉐'는" in lines[0] and "은(는)" not in " ".join(lines)
    assert draft.NO_CAUSE["site"] in lines


def test_hold_gift_variant_and_hold_wording():
    ch = templates.hold("페레로로쉐", channel="site", cause="수능 선물 추천과 카페 디저트로 언급")
    assert "선물" in ch.question and "선물할 건지" in ch.answer[0] and ch.sections[0][0] == "선물용인지, 내가 먹을 건지"
    assert ch.id == "20" and "선물" in ch.note
    plain = templates.hold("천수무", channel="site")
    assert "무엇을 기준으로" not in plain.question and "필요한 양과 받을 날짜" not in " ".join(plain.answer)
    assert any(x.startswith("예시:") for x in plain.sections[0][1])
    assert not any("냉장·냉동 보관할 자리" in c for c in plain.criteria)
    assert frame.experience_line("x", "site", hold=True) != frame.experience_line("x", "site")
    assert "상품 정보" not in frame.experience_line("x", "blog", hold=True)


def test_site_hold_sets_question_answer_criteria(tmp_path):
    svc = service(tmp_path)
    post, _ = svc.create_from_surge(
        report(item("페레로로쉐", cause={"cause": "수능 선물로 언급", "kind": "선물", "public": True})),
        "페레로로쉐",
        find_products=lambda k: search_result(),
    )
    held = svc.update(post.id, {"conclusion": "hold"})
    assert "선물" in held.question and held.criteria[0].startswith("받는 분")
    back = svc.update(post.id, {"conclusion": "buy"})
    assert back.question == frame.question("페레로로쉐", "site", back.topic_kind)
    assert back.criteria == frame.criteria("페레로로쉐", "site", back.topic_kind)


# ── 블로그 초안 ─────────────────────────────────────────────────────────
def _kimjang_rep():
    def it(k):
        return {
            "keyword": k,
            "status": "new",
            "onset": "2026-11-05",
            "rank_trend": {},
            "blog": {"status": "ok", "posts": 3, "last7": 3, "clues": {"할인·행사": 1}},
            "google": {},
            "cross": {"n": 1, "of": 2, "parts": {"블로그 글 증가": True, "식품 순위 상승": False}},
            "cause": None,
        }

    return {"data_until": "2026-11-19", "items": [it("황석어젓갈"), it("절임배추10kg")]}


def test_blog_multi_keyword_no_repeat_and_cover_is_first_photo():
    links = {
        "황석어젓갈": [
            {
                "title": "[로켓프레시] 황석어젓 1kg",
                "url": "https://link.coupang.com/a/1",
                "image_url": "https://thumbnail6.coupangcdn.com/a.jpg",
            }
        ],
        "절임배추10kg": [{"title": "절임배추 10kg", "url": "https://link.coupang.com/a/2"}],
    }
    d = S.blog_draft(_kimjang_rep(), coupang=links, variant="coupang")
    body = d["body"]
    assert body.count("판매 페이지에서 볼 것") == 1  # 05 절의 같은 줄은 한 번만
    assert "제목 단서" not in body and "할인·행사 이야기 1건" in body
    assert "함께 확인된 신호" not in body and "함께 움직인 신호: 블로그 글 증가" in body
    assert body.count("왜 늘었는지는 아직 확인되지 않았어요") == 2
    assert "가격·재고는 판매처에서 확인해 주세요." not in body  # '구매 전에 알아 둘 것'과 중복
    assert "결론부터 말하면." not in body and "한 줄로 정리하면." not in body
    assert d["cover"] == {
        "kind": "seller",
        "url": "https://thumbnail6.coupangcdn.com/a.jpg",
        "caption": "쿠팡 상품 사진 · [로켓프레시] 황석어젓 1kg (판매처 이미지)",
    }


def test_blog_hold_cover_is_ai_and_no_product_info_claim():
    d = S.blog_draft(_kimjang_rep(), coupang={}, variant="coupang", hold=True)
    assert d["cover"] == {"kind": "ai"} and "상품 정보를" not in d["body"]
    assert S.blog_draft(_kimjang_rep(), variant="naver")["cover"] is None


# ── 대표 그림: 사이트 ───────────────────────────────────────────────────
def test_site_buy_cover_is_first_coupang_photo_and_hold_never_uses_product_photo(tmp_path):
    svc = service(tmp_path)
    post = approved(svc)
    hero = render.cover(post)
    assert hero["kind"] == "product" and "coupang" in hero["src"] and "판매처 이미지" in hero["caption"]
    html = render.post_page(post)
    assert "class=hero" in html and html.index("class=hero") < html.index("먼저 답부터")
    assert "lthumb" in render.index_page([post])
    held = post.model_copy(update={"conclusion": "hold"})
    assert render.cover(held) is None and "class=hero" not in render.post_page(held)
    with_ai = held.model_copy(update={"cover": PostImage(file=f"{post.id}.png")})
    hero = render.cover(with_ai)
    assert hero == {
        "src": render.image_url(f"{post.id}.png"),
        "kind": "ai",
        "caption": "AI로 만든 그림 · 실제 상품 사진이 아니에요",
    }
    assert "coupang" not in render.post_page(with_ai).split("class=hero")[1].split("</figure>")[0]


def test_image_name_rule():
    assert VALID_IMAGE.match("2026-11-19-페레로로쉐.png") and VALID_IMAGE.match("2026-11-19-천수무-2.png")
    for bad in ("../x.png", "2026-11-19-a.jpg", "a.png", "2026-11-19-a/../b.png"):
        assert not VALID_IMAGE.match(bad)


def test_cover_job_attaches_ai_image_only_to_hold_posts(tmp_path, monkeypatch):
    monkeypatch.setattr(cover, "image_dir", lambda: tmp_path / "imgs")
    src = tmp_path / "gen.png"
    src.write_bytes(b"\x89PNG")
    svc = service(tmp_path)
    post, _ = svc.create_from_surge(report(), "대방어", find_products=lambda k: search_result())
    svc.update(post.id, {"conclusion": "hold"})
    prompts = []

    def run(module, payload):
        prompts.append(payload["prompt"])
        return {"status": "done", "image_path": str(src)}

    assert cover.start(svc, post.id, run=run, background=False)
    got = svc.get(post.id)
    assert got.cover and got.cover.file == f"{post.id}.png" and (tmp_path / "imgs" / got.cover.file).is_file()
    assert "no logos" in prompts[0] and "No text" in prompts[0]
    # 구매 글로 바뀐 뒤 끝난 작업은 붙이지 않는다
    svc.update(post.id, {"conclusion": "buy"})
    p2 = svc.get(post.id).model_copy(update={"cover": None})
    svc.store.save(p2)
    assert cover.start(svc, post.id, run=run, background=False)
    assert svc.get(post.id).cover is None


def test_cover_failure_is_logged_not_raised(tmp_path):
    svc = service(tmp_path)
    post, _ = svc.create_from_surge(report(), "대방어")
    svc.update(post.id, {"conclusion": "hold"})
    cover.start(svc, post.id, run=lambda m, p: {"status": "error", "message": "키 없음"}, background=False)
    got = svc.get(post.id)
    assert got.cover is None and got.history[-1].action == "cover" and "키 없음" in got.history[-1].note


# ── 대표 그림: 블로그 임시저장 ──────────────────────────────────────────
TITLE = "[광고] 절임배추"
BODY = f"{S.COUPANG_DISCLOSURE}\n받은 수수료는 운영에 도움이 됩니다.\n\n먼저 답부터 말씀드릴게요.\n답\n\n본문"


def _draft(tmp_path):
    folder = tmp_path / "var" / "blog_drafts"
    folder.mkdir(parents=True)
    p = folder / "trend_2026-11-20_절임배추_쿠팡용.txt"
    p.write_text("x", encoding="utf-8")
    return p


def test_seller_cover_goes_in_as_seller_image(tmp_path):
    calls = []

    def worker(module, payload):
        calls.append((module, payload))
        return {"status": "done", "message": "임시저장 완료"}

    p = _draft(tmp_path)
    photo = tmp_path / "var" / "blog_images" / "x.jpg"

    def fetch(url, dest, name):
        assert url == "https://thumbnail6.coupangcdn.com/a.jpg" and dest == tmp_path / "var" / "blog_images"
        photo.parent.mkdir(parents=True, exist_ok=True)
        photo.write_bytes(b"jpg")
        return photo

    rec = bas.start(
        p,
        variant="coupang",
        title=TITLE,
        tags=["절임배추"],
        body=BODY,
        keywords=["절임배추"],
        with_image=False,
        worker=worker,
        background=False,
        fetch_image=fetch,
        cover={"kind": "seller", "url": "https://thumbnail6.coupangcdn.com/a.jpg", "caption": "쿠팡 상품 사진"},
    )
    assert [m for m, _ in calls] == ["naver_blog_mcp.post_worker"]  # AI 그림은 만들지 않음
    payload = calls[0][1]
    assert payload["publish"] is False and payload["images"] == [
        {"path": str(photo), "source": "seller", "caption": "쿠팡 상품 사진"}
    ]
    assert bas.IMAGE_MARK in payload["content"] and rec["status"] == "done" and rec["cover"] == "seller"


def test_ai_cover_for_hold_and_photo_failure_still_saves(tmp_path):
    calls = []

    def worker(module, payload):
        calls.append(module)
        if module.endswith("image_worker"):
            return {"status": "done", "image_path": "/tmp/a.png"}
        return {"status": "done", "message": "ok"}

    p = _draft(tmp_path)
    bas.start(
        p,
        variant="coupang",
        title="제목",
        tags=[],
        body="본문",
        keywords=["두쫀쿠"],
        with_image=False,
        worker=worker,
        background=False,
        cover={"kind": "ai"},
    )
    assert calls == ["naver_blog_mcp.image_worker", "naver_blog_mcp.post_worker"]
    calls.clear()
    rec = bas.start(
        p,
        variant="coupang",
        title=TITLE,
        tags=[],
        body=BODY,
        keywords=["x"],
        with_image=False,
        worker=worker,
        background=False,
        fetch_image=lambda u, d, n: None,
        cover={"kind": "seller", "url": "https://thumbnail6.coupangcdn.com/a.jpg"},
    )
    assert calls == ["naver_blog_mcp.post_worker"] and rec["status"] == "done" and "사진을 받지 못해" in rec["message"]


def test_download_seller_image_only_coupang_images(tmp_path):
    class Res(io.BytesIO):
        def __init__(self, data, kind):
            super().__init__(data)
            self.headers = {"Content-Type": kind}

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

    ok = bas.download_seller_image(
        "https://thumbnail6.coupangcdn.com/a.jpg",
        tmp_path,
        "trend_a",
        opener=lambda req, timeout: Res(b"jpgdata", "image/jpeg"),
    )
    assert ok == tmp_path / "trend_a.jpg" and ok.read_bytes() == b"jpgdata"
    assert (
        bas.download_seller_image(
            "https://evil.example/a.jpg", tmp_path, "b", opener=lambda req, timeout: Res(b"x", "image/jpeg")
        )
        is None
    )
    assert (
        bas.download_seller_image(
            "https://thumbnail6.coupangcdn.com/a.jpg",
            tmp_path,
            "c",
            opener=lambda req, timeout: Res(b"<html>", "text/html"),
        )
        is None
    )
