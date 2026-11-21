"""트렌드 글 (2단계) — 로드맵 넘어가는 기준: 미승인 인용 · 오래된 가격 · 광고 표시 누락 차단.

같은 파일에서 링크 방식 · 주류 · 레시피 출처 · 숫자 · 중복 · 상태 흐름 · 저장소를 함께 본다.
"""
from __future__ import annotations

import json

import pytest

from app.services.trend_posts import draft, policy, render
from app.services.trend_posts.model import Post
from app.services.trend_posts.service import PostError
from app.services.trend_posts.store import FilePostStore

from .helpers import T0, Clock, approved, item, recipe_result, report, search_result, service


@pytest.fixture(autouse=True)
def _frame04_format(monkeypatch):
    """이 파일은 프레임 0.4 사이트 글을 검사한다 — 2026-11-21 부터 새 글 기본은 보고서형(test_report.py)."""
    monkeypatch.setenv("TREND_POST_FORMAT", "frame04")


def codes(issues):
    return {i["code"] for i in issues}


# ── 초안 ─────────────────────────────────────────────
def test_draft_follows_template_and_keeps_search_order(tmp_path):
    svc = service(tmp_path)
    post, created = svc.create_from_surge(report(), "대방어", find_products=lambda k: search_result())
    assert created and post.status == "draft" and post.id == "2026-11-15-대방어"
    # 쿠팡 https · picks 만, 검색 결과 순서 그대로 (제휴 여부로 고르거나 바꾸지 않음)
    assert [p.url for p in post.products] == ["https://link.coupang.com/a/aaa", "https://link.coupang.com/a/ccc"]
    assert all(p.price_checked_at == "2026-11-16T03:00:00+00:00" for p in post.products)   # 실시간 조회 = 조회 시각
    assert post.title.startswith("[광고] ") and policy.COUPANG_DISCLOSURE in post.disclosure
    assert any("약 2.7배" in w for w in post.why) and any("464위" in w and "82위" in w for w in post.why)
    assert not any("계기" in w for w in post.why)                  # 원인 '불명'은 쓰지 않음
    assert svc.check(post) == []


def test_public_cause_is_marked_as_estimate_and_private_cause_is_dropped():
    shown = draft.why_lines(item(cause={"cause": "방송에 나왔어요", "kind": "방송", "public": True}), "2026-11-15")
    assert any(w.startswith("계기(추정): 방송에 나왔어요") and "추정" in w for w in shown)
    hidden = draft.why_lines(item(cause={"cause": "어떤 사람 이야기", "kind": "방송", "public": False}), "2026-11-15")
    assert not any("계기" in w for w in hidden)


def test_draft_without_products_has_no_ad_label(tmp_path):
    post, _ = service(tmp_path).create_from_surge(report(), "대방어")
    assert not post.products and not post.title.startswith("[광고]") and post.disclosure is None


def test_alcohol_topic_gets_no_product_links(tmp_path):
    post, _ = service(tmp_path).create_from_surge(report(item("하이볼")), "하이볼", find_products=lambda k: search_result())
    assert post.products == []
    forced = post.model_copy(update={"products": draft.products_from_result(search_result())})
    assert "alcohol" in codes(policy.check(forced, now=T0))
    assert not policy.is_alcohol("맛술") and not policy.is_alcohol("술빵")


def test_recipe_only_same_dish_and_public_source(tmp_path):
    assert draft.recipe_from_result(recipe_result("대방어 회덮밥"), "대방어") is None       # 다른 요리
    assert draft.recipe_from_result(recipe_result("두쫀쿠", level="ai_suggestion"), "두쫀쿠") is None  # AI 제안
    r = draft.recipe_from_result(recipe_result("두쫀쿠"), "두쫀쿠")
    assert r.source_label == "농식품정보누리(EPIS)" and r.step_count == 3 and "원문 그대로가 아" in r.note


def test_word_not_in_report_is_refused(tmp_path):
    with pytest.raises(PostError) as e:
        service(tmp_path).create_from_surge(report(), "없는단어")
    assert e.value.code == "not_in_report"


# ── 미승인 글 차단 ─────────────────────────────────────
@pytest.mark.parametrize("step", ["draft", "pending", "rejected", "withdrawn"])
def test_unapproved_posts_never_reach_the_public_side(tmp_path, step):
    svc = service(tmp_path)
    post, _ = svc.create_from_surge(report(), "대방어", find_products=lambda k: search_result())
    if step in ("pending", "rejected", "withdrawn"):
        svc.submit(post.id)
    if step == "rejected":
        svc.reject(post.id, "사진 권리 확인 필요")
    if step == "withdrawn":
        svc.approve(post.id)
        svc.withdraw(post.id, "내용 수정")
    assert svc.public(post.id) is None and svc.published() == []


def test_public_lookup_rejects_odd_ids(tmp_path):
    svc = service(tmp_path)
    approved(svc)
    for bad in ("../etc/passwd", "2026-11-15-대방어/../x", "", "x" * 80):
        assert svc.public(bad) is None


# ── 광고 표시 ─────────────────────────────────────────
def test_missing_ad_label_or_disclosure_blocks_approval(tmp_path):
    svc = service(tmp_path)
    post, _ = svc.create_from_surge(report(), "대방어", find_products=lambda k: search_result())
    no_label = post.model_copy(update={"title": post.title.removeprefix("[광고] ")})
    assert "ad_label" in codes(policy.check(no_label, now=T0))
    no_disc = post.model_copy(update={"disclosure": "광고"})
    assert "ad_label" in codes(policy.check(no_disc, now=T0))
    svc.store.save(no_label.model_copy(update={"status": "pending"}))
    with pytest.raises(PostError) as e:
        svc.approve(post.id)
    assert e.value.code == "policy" and "ad_label" in codes(e.value.issues)
    assert svc.public(post.id) is None


def test_editing_keeps_ad_label_in_step_with_products(tmp_path):
    svc = service(tmp_path)
    post, _ = svc.create_from_surge(report(), "대방어", find_products=lambda k: search_result())
    edited = svc.update(post.id, {"title": "제목만 바꿈"})               # [광고]를 지워도 다시 붙음
    assert edited.title == "[광고] 제목만 바꿈" and policy.COUPANG_DISCLOSURE in edited.disclosure
    cleared = svc.update(post.id, {"products": []})
    assert cleared.title == "제목만 바꿈" and cleared.disclosure is None


def test_hold_conclusion_drops_every_buy_element(tmp_path):
    """2026-11-20 사용자 결정: 보류 결론 글 — 상품 카드·버튼·/go·결제 확인·상품 비교 안내·구매 전 제약·가격 문구·
    [광고]·고지를 모두 빼고 보류 결론. 판단 근거 출처(확인한 곳)는 남긴다. 결론을 되돌리면 원래 틀."""
    from app.services.trend_posts import frame, templates

    svc = service(tmp_path)
    post, _ = svc.create_from_surge(report(), "대방어", find_products=lambda k: search_result())
    held = svc.update(post.id, {"conclusion": "hold"})
    assert not held.title.startswith("[광고]") and held.disclosure is None and held.products
    assert held.template == "20" and held.checklist is None and held.constraints == []
    assert held.answer[-1] == templates.HOLD_ANSWER["site"]
    html = render.post_page(held.model_copy(update={"status": "approved", "approved_at": "2026-11-16T03:00:00+00:00"}), T0)
    for m in ("판매처에서 보기", "/go/", "class=go href=\"/trends/", "상품 비교", "가격 참고", "구매 전에 알아 둘 것",
              "결제", "판매 페이지에서", policy.COUPANG_DISCLOSURE, "sponsored"):
        assert m not in html, m
    assert not any(x in html for x in frame.COMPARE["site"] + frame.ROCKET["site"] + frame.NO_PRODUCTS["site"])
    assert templates.HOLD_LINE["site"] in html and "필요해지면 볼 기준" in html and "확인한 곳" in html
    assert "datalab.naver.com" in html                                       # 출처 링크는 유지
    back = svc.update(post.id, {"conclusion": "buy"})
    assert back.title.startswith("[광고]") and back.checklist and back.template != "20"
    assert back.answer == frame.answer("대방어", True, True, "site", back.topic_kind)


def test_rendered_page_puts_disclosure_before_any_product_link(tmp_path):
    svc = service(tmp_path)
    post = approved(svc)
    html = render.post_page(post, T0)
    assert html.index(policy.COUPANG_DISCLOSURE) < html.index('class=go') < html.index("판매처에서 보기")
    assert "<title>[광고]" in html and 'rel="sponsored nofollow noopener"' in html
    # 스크립트는 구조화 데이터 1개 + 글 끝 피드백 1개(2026-11-21)뿐 — 피드백 스크립트는 이동·외부 호출 없음
    assert html.count('<script type="application/ld+json">') == 1 and html.count("<script") == 2
    assert render.FEEDBACK_JS in html and "location" not in render.FEEDBACK_JS and "http" not in render.FEEDBACK_JS
    assert "http-equiv" not in html                                      # 자동 이동 없음
    assert "https://link.coupang.com" not in html                       # 상품 주소는 /go 경유로만


# ── 오래된 가격 ───────────────────────────────────────
def test_stale_price_blocks_approval_until_rechecked(tmp_path):
    clock = Clock()
    svc = service(tmp_path, clock)
    post, _ = svc.create_from_surge(report(), "대방어", find_products=lambda k: search_result())
    svc.submit(post.id)
    clock.advance(days=31)
    with pytest.raises(PostError) as e:
        svc.approve(post.id)
    assert "stale_price" in codes(e.value.issues)
    svc.reject(post.id, "가격 다시 확인")
    svc.refresh_products(post.id, lambda k: search_result())
    svc.submit(post.id)
    assert svc.approve(post.id).status == "approved"


def test_price_without_time_is_blocked():
    p = draft.products_from_result(search_result())[0].model_copy(update={"price_checked_at": None})
    post = Post(id="2026-11-15-x", topic="x", title="[광고] x", disclosure=policy.disclosure_text(), products=[p],
                created_at="2026-11-16T00:00:00+00:00", updated_at="2026-11-16T00:00:00+00:00")
    assert "price_time" in codes(policy.check(post, now=T0))
    assert render.price_line(p, T0) == render.CHECK_AT_MALL


def test_published_price_hides_itself_after_30_days(tmp_path):
    clock = Clock()
    svc = service(tmp_path, clock)
    post = approved(svc)
    fresh = render.post_page(post, clock())
    assert "29,900원 · 2026년 11월 16일 12시 확인 가격 · 지금은 다를 수 있어요" in fresh
    clock.advance(days=31)
    stale = render.post_page(svc.public(post.id), clock())
    assert "29,900" not in stale and "45,900" not in stale and stale.count(render.CHECK_AT_MALL) == 2


# ── 링크 · HTML · 숫자 · 가격 우위 문구 ─────────────────
def test_only_coupang_https_links_and_safe_sources(tmp_path):
    svc = service(tmp_path)
    post, _ = svc.create_from_surge(report(), "대방어", find_products=lambda k: search_result())
    p0 = post.products[0]
    for url in ("http://link.coupang.com/a/x", "https://evil.example/x", "https://user:pw@link.coupang.com/a",
                "javascript:alert(1)"):
        bad = post.model_copy(update={"products": [p0.model_copy(update={"url": url})]})
        assert "link" in codes(policy.check(bad, now=T0)), url
    src = post.model_copy(update={"sources": [post.sources[0].model_copy(update={"url": "javascript:x"})]})
    assert "link" in codes(policy.check(src, now=T0))


def test_html_in_text_is_blocked_and_escaped(tmp_path):
    svc = service(tmp_path)
    post, _ = svc.create_from_surge(report(), "대방어")
    bad = post.model_copy(update={"why": ['<img src=x onerror="alert(1)">']})
    assert "html" in codes(policy.check(bad, now=T0))
    html = render.post_page(bad.model_copy(update={"status": "approved"}), T0)
    assert "<img" not in html and "&lt;img" in html


def test_prices_and_price_claims_stay_out_of_sentences(tmp_path):
    svc = service(tmp_path)
    post, _ = svc.create_from_surge(report(), "대방어", find_products=lambda k: search_result())
    for field, text in (("summary", "1kg 3만원이면 사요"), ("summary", "29,900원이에요"), ("why", ["평점 4.9"]),
                        ("summary", "가성비 좋은 방어"), ("title", "[광고] 최저가 대방어")):
        bad = post.model_copy(update={field: text})
        assert codes(policy.check(bad, now=T0)) & {"numbers", "price_claim"}, text
    # 판매처 상품 이름의 표기는 검사에서 뺀다 (고객 화면 상품 이름과 같음)
    named = post.model_copy(update={"products": [post.products[0].model_copy(update={"title": "가성비 대방어 2만원"})]})
    assert policy.check(named, now=T0) == []


# ── 중복 ─────────────────────────────────────────────
def test_same_topic_within_30_days_reuses_the_post(tmp_path):
    clock = Clock()
    svc = service(tmp_path, clock)
    first = approved(svc)
    again, created = svc.create_from_surge(report(data_until="2026-11-20"), "대방어")
    assert not created and again.id == first.id
    clock.advance(days=31)
    newer, created = svc.create_from_surge(report(data_until="2026-12-17"), "대방어")
    assert created and newer.id == "2026-12-17-대방어"


def test_second_live_post_on_same_topic_is_blocked(tmp_path):
    svc = service(tmp_path)
    first = approved(svc)
    twin = first.model_copy(update={"id": "2026-11-16-대방어", "status": "pending"})
    svc.store.save(twin)
    with pytest.raises(PostError) as e:
        svc.approve(twin.id)
    assert "duplicate" in codes(e.value.issues)


# ── 상태 흐름 ─────────────────────────────────────────
def test_status_guards(tmp_path):
    svc = service(tmp_path)
    post, _ = svc.create_from_surge(report(), "대방어")
    with pytest.raises(PostError):
        svc.approve(post.id)                                   # 초안은 바로 승인 못 함
    svc.submit(post.id)
    with pytest.raises(PostError):
        svc.update(post.id, {"title": "x"})                    # 검토 대기 중에는 못 고침
    with pytest.raises(PostError):
        svc.reject(post.id, " ")                               # 반려 사유 필수
    svc.approve(post.id, "확인함")
    with pytest.raises(PostError):
        svc.update(post.id, {"title": "x"})                    # 게시된 글은 내린 뒤 고침
    svc.withdraw(post.id)
    svc.reopen(post.id)
    assert svc.update(post.id, {"title": "고친 제목"}).status == "draft"
    with pytest.raises(PostError):
        svc.update(post.id, {"status": "approved"})            # 상태는 고치기로 못 바꿈
    actions = [h.action for h in svc.get(post.id).history]
    assert actions == ["create", "submit", "approve", "withdraw", "reopen", "update"]


# ── 저장소 ───────────────────────────────────────────
def test_store_round_trip_and_broken_file_is_skipped(tmp_path):
    svc = service(tmp_path)
    post = approved(svc)
    store = FilePostStore(tmp_path / "posts")
    assert store.get(post.id) == post
    (tmp_path / "posts" / "post_broken.json").write_text("{not json", encoding="utf-8")
    assert [p.id for p in store.all()] == [post.id]
    raw = json.loads(store._path(post.id).read_text(encoding="utf-8"))
    assert raw["id"] == "2026-11-15-대방어"



def test_product_thumbnails_only_from_coupang(tmp_path):
    """2026-11-17: 상품 칸에 쿠팡 상품 사진 — 쿠팡 https 사진 주소만, 다른 주소는 넣지 않고 검사에서도 막는다."""
    from .helpers import pick

    result = {"items": [pick("대방어회 500g", "https://link.coupang.com/a/aaa"),
                        pick("필렛", "https://link.coupang.com/a/bbb", image="https://evil.example/x.jpg"),
                        pick("뱃살", "https://link.coupang.com/a/ccc", image="http://thumbnail6.coupangcdn.com/x.jpg")]}
    svc = service(tmp_path)
    post, _ = svc.create_from_surge(report(), "대방어", find_products=lambda k: result)
    assert [p.image_url for p in post.products] == ["https://ads-partners.coupang.com/image1/thumb.jpg", None, None]
    svc.submit(post.id)
    html = render.post_page(svc.approve(post.id), T0)
    assert html.count("<img class=thumb") == 1 and 'referrerpolicy=no-referrer' in html and "evil.example" not in html
    bad = post.model_copy(update={"products": [post.products[0].model_copy(update={"image_url": "https://evil.example/x.jpg"})]})
    assert "link" in codes(policy.check(bad, now=T0))
    assert policy.coupang_image("https://thumbnail10.coupangcdn.com/a.jpg")
    assert not policy.coupang_image("https://coupangcdn.com.evil.example/a.jpg")
