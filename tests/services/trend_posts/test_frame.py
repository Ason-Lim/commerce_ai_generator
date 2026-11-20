"""프레임 0.4 (2026-11-20) — 쿠팡 사이트 글: 고지 → 질문과 조건부 답 → 선택 기준 → 구매 전 제약·결제 전 확인 → 근거 붙은 상품."""
from __future__ import annotations

from app.services.trend_posts import frame, policy, render
from app.services.trend_posts.model import Post

from .helpers import T0, report, search_result, service


def _made(tmp_path):
    svc = service(tmp_path)
    post, _ = svc.create_from_surge(report(), "대방어", find_products=lambda k: search_result())
    return svc, post


def test_draft_fills_frame_fields_and_product_facts(tmp_path):
    svc, post = _made(tmp_path)
    assert post.experience == "data" and post.question == frame.question("대방어", "site")
    assert frame.keyword_type("대방어") == "seasonal" and any("로켓배송" in a for a in post.answer)
    assert post.criteria == frame.criteria("대방어", "site") and any("손질" in c for c in post.criteria)
    assert post.constraints[0].startswith("제철 식재료는") and post.checklist == frame.checklist("대방어", "site")
    assert post.products[0].facts == ["중량·수량: 500g (상품명 표기)", "로켓배송 표시 (검색 결과 표시)"]
    assert svc.check(post) == []


def test_page_order_follows_frame(tmp_path):
    svc, post = _made(tmp_path)
    html = render.post_page(post.model_copy(update={"status": "approved", "approved_at": "2026-11-16T03:00:00+00:00"}), T0)
    marks = [policy.COUPANG_DISCLOSURE, "먼저 답부터", frame.experience_line("대방어", "site"), "왜 뜨고 있을까",
             "고르기 전에 볼 것", "구매 전에 알아 둘 것", "상품 비교", frame.checklist("대방어", "site"),
             "중량·수량: 500g", "판매처에서 보기", "가격 참고"]
    at = [html.index(m) for m in marks]
    assert at == sorted(at)


def test_old_posts_without_frame_render_the_old_way(tmp_path):
    svc, post = _made(tmp_path)
    old = post.model_copy(update={"question": None, "answer": [], "criteria": [], "constraints": [], "checklist": None,
                                  "status": "approved", "approved_at": "2026-11-16T03:00:00+00:00"})
    html = render.post_page(old, T0)
    assert "먼저 답부터" not in html and "재료·상품" in html and "고르기 전에 볼 것" not in html
    # 예전 JSON (새 칸 없음) 도 그대로 읽힌다
    raw = old.model_dump(mode="json")
    for k in ("experience", "question", "answer", "criteria", "constraints", "checklist"):
        raw.pop(k)
    for p in raw["products"]:
        p.pop("facts")
    assert Post.model_validate(raw).answer == []


def test_first_hand_words_and_numbers_in_frame_fields_are_blocked(tmp_path):
    svc, post = _made(tmp_path)
    bad = post.model_copy(update={"answer": ["직접 먹어 봤어요 정말 좋아요"]})
    assert "experience" in {i["code"] for i in svc.check(bad)}
    priced = post.model_copy(update={"criteria": ["3만원 이하로 고르세요"]})
    assert "numbers" in {i["code"] for i in svc.check(priced)}
    edited = svc.update(post.id, {"criteria": ["필요한 양부터 정하세요."]})
    assert edited.criteria == ["필요한 양부터 정하세요."]


def test_amounts_keep_ranges_and_skip_prices():
    assert frame.amounts("해남 절임배추 10kg (3-5포기) 2박스") == ["10kg", "3-5포기", "2박스"]
    assert frame.amounts("귤 3~5kg 29,900원") == ["3~5kg"]
    assert frame.product_facts("아무 표기 없음", None) == []


# ── 단조로움 줄이기 (2026-11-20): 유형 규칙표 · 문장 변형 · 채널별 말투 ──────────
def test_keyword_type_table():
    got = {k: frame.keyword_type(k) for k in ("절임배추20kg", "김장용생새우", "새우젓", "대방어", "과메기", "생굴", "귤",
                                               "빼빼로", "수능선물", "답례품", "굴소스", "쌈배추", "두쫀쿠")}
    assert got == {"절임배추20kg": "kimjang", "김장용생새우": "kimjang", "새우젓": "kimjang", "대방어": "seasonal",
                   "과메기": "seasonal", "생굴": "seasonal", "귤": "seasonal", "빼빼로": "anniversary", "수능선물": "event",
                   "답례품": "gift", "굴소스": "general", "쌈배추": "general", "두쫀쿠": "general"}


def test_types_bring_different_criteria():
    kim, sea, ev = (frame.criteria(k, "site") for k in ("절임배추", "대방어", "빼빼로"))
    assert any("포기" in c for c in kim) and len(kim) == 4
    assert any("손질" in c for c in sea) and any("수량" in c or "받는 사람" in c for c in ev)
    assert not set(kim) & set(sea) and not set(sea) & set(ev)


def test_same_keyword_same_words_every_time():
    for k in ("절임배추", "대방어", "빼빼로"):
        for ch in ("site", "blog"):
            assert frame.question(k, ch) == frame.question(k, ch)
            assert frame.answer(k, True, True, ch) == frame.answer(k, True, True, ch)


def test_site_and_blog_never_share_a_sentence():
    for k in ("절임배추", "대방어", "과메기", "귤", "빼빼로", "수능선물", "두쫀쿠", "새우젓", "설선물세트", "송편",
              "어버이날선물", "생일케이크", "크리스마스케이크", "한우선물세트", "호빵", "팥빙수", "파전", "눈오는날간식"):
        site = [frame.question(k, "site"), *frame.answer(k, True, True, "site"), *frame.criteria(k, "site"),
                *frame.constraints(k, "site"), frame.experience_line(k, "site"), frame.checklist(k, "site")]
        blog = [frame.question(k, "blog"), *frame.answer(k, True, True, "blog"), *frame.criteria(k, "blog"),
                *frame.constraints(k, "blog"), frame.experience_line(k, "blog"), frame.checklist(k, "blog")]
        assert not set(site) & set(blog), k


def test_variants_spread_across_keywords():
    words = ["대방어", "과메기", "굴", "귤", "딸기", "꼬막", "대게", "한라봉", "곶감", "도루묵"]
    assert len({frame.question(k, "blog").replace(k, "") for k in words}) >= 2
    assert len({frame.criteria(k, "site")[0] for k in words}) == 2


def test_blog_hook_uses_report_numbers_only():
    assert frame.blog_hook({"keyword": "귤", "status": "surging", "ratio_recent": 2.4}).count("2.4") == 1
    assert "를" in frame.blog_hook({"keyword": "과메기", "status": "new"}) or "가" in frame.blog_hook(
        {"keyword": "과메기", "status": "new"})
    assert frame.blog_hook({"keyword": "x", "status": "rising"}) is None


def test_no_prices_or_first_hand_words_in_any_bank():
    import re
    banned = re.compile(r"\d[\d,.]*\s*원|평점|최저가|가성비|내돈내산|써\s*봤어요|먹어\s*봤어요")
    for k in ("절임배추", "대방어", "빼빼로", "두쫀쿠"):
        for ch in ("site", "blog"):
            for t in [frame.question(k, ch), *frame.answer(k, True, True, ch), *frame.criteria(k, ch),
                      *frame.constraints(k, ch), frame.experience_line(k, ch), frame.checklist(k, ch)]:
                assert not banned.search(t), t



# ── 주제 12개 · 글 틀 (2026-11-20 사용자 결정) ────────────────────────────
def test_twelve_topics_from_table_and_status():
    cases = {"설선물세트": "seollal", "떡국떡": "seollal", "추석송편": "chuseok", "차례상": "holiday",
             "어버이날선물": "family_month", "카네이션": "family_month", "생일케이크": "birthday", "미역국": "birthday",
             "크리스마스케이크": "anniversary", "발렌타인초콜릿": "anniversary", "복날": "event", "동지팥죽": "event",
             "한우선물세트": "gift", "호빵": "weather", "팥빙수": "weather", "파전": "weather", "절임배추": "kimjang",
             "대방어": "seasonal", "두쫀쿠": "general"}
    assert {k: frame.keyword_type(k) for k in cases} == cases
    assert frame.keyword_type("두쫀쿠", status="new") == "viral"            # 표에 없고 새로 등장 → 급상승 신상
    assert frame.keyword_type("대방어", status="new") == "seasonal"         # 표에 있으면 표가 먼저
    assert [frame.weather_kind(k) for k in ("호빵", "팥빙수", "파전", "눈오는날간식")] == ["cold", "hot", "rain", "snow"]
    assert "설날" in frame.question("떡국떡", "site") or "설날" in frame.answer("떡국떡", True)[0]


def test_default_template_per_topic():
    from app.services.trend_posts import templates as T
    from app.services.trend_posts.model import PostRecipe

    two = [{"title": "상품 1kg", "rocket": True}, {"title": "상품 2kg", "rocket": False}]
    rec = PostRecipe(name="굴국밥", source_label="농식품정보누리(EPIS)", ingredients=["굴", "밥", "무"])
    pick = lambda k, **kw: T.choose(k, products=kw.pop("products", two), **kw).id   # noqa: E731
    assert pick("절임배추") == "05" and pick("설선물세트") == "14" and pick("떡국떡") == "28"
    assert pick("어버이날선물") == "14" and pick("크리스마스케이크") == "14" and pick("수능선물") == "28"
    assert pick("한우선물세트") == "14" and pick("두쫀쿠", status="new") == "32"
    assert pick("생굴", recipe=rec) == "26" and pick("생굴") == "06" and pick("생굴", products=two[:1]) == "01"
    assert pick("호빵") == "03" and pick("두쫀쿠") == "06"


def test_override_and_fallback_notes():
    from app.services.trend_posts import templates as T

    one = [{"title": "귤 3kg", "rocket": False}]
    ok = T.choose("귤", products=one, override="03")
    assert ok.id == "03" and ok.note == "" and ok.sections and "3kg" in ok.sections[0][1][0]
    no = T.choose("귤", products=one, override="26")
    assert no.id != "26" and "필요한 자료" in no.note
    exp = T.choose("귤", products=one, override="21")
    assert exp.id != "21" and "실제 사용 기록" in exp.note
    manual = T.choose("귤", products=one, override="44")
    assert "사람이 직접" in manual.note


def test_site_post_carries_template_sections(tmp_path):
    from .helpers import report as rep, item, search_result, recipe_result, service
    svc = service(tmp_path)
    post, _ = svc.create_from_surge(rep(item("대방어")), "대방어", find_products=lambda k: search_result(),
                                    find_recipe=lambda k: recipe_result("숙성 대방어"))
    assert post.template == "26" and post.topic_kind == "seasonal" and post.title.startswith("[광고] ")
    assert post.sections[0].heading == "만들 요리와 재료" and any("숙성 대방어" in x for x in post.sections[0].items)
    assert svc.check(post) == []
    html = render.post_page(post.model_copy(update={"status": "approved", "approved_at": "2026-11-16T03:00:00+00:00"}), T0)
    assert html.index("만들 요리와 재료") < html.index("고르기 전에 볼 것")
    svc2 = service(tmp_path / "b")
    p2, _ = svc2.create_from_surge(rep(item("대방어")), "대방어", find_products=lambda k: search_result(), template="05")
    assert p2.template == "05" and p2.sections[0].heading == "쓰는 날과 받는 날"


def test_template_titles_differ_by_template_and_channel():
    from app.services.trend_posts import templates as T
    two = [{"title": "절임배추 10kg", "rocket": True}, {"title": "절임배추 20kg", "rocket": False}]
    site = {T.choose("절임배추", products=two, override=t).title for t in ("01", "03", "05", "06")}
    blog = {T.choose("절임배추", products=two, override=t, channel="blog").title for t in ("01", "03", "05", "06")}
    assert len(site) == 4 and len(blog) == 4 and not site & blog



def test_gift_keyword_title_does_not_repeat_gift():
    from app.services.trend_posts import templates as T
    for ch in ("site", "blog"):
        t = T.choose("어버이날선물", products=[{"title": "x 1kg"}], channel=ch).title
        assert "선물 선물" not in t and "선물선물" not in t and t.count("선물") == 1
