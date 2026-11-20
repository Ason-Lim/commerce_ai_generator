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
    assert post.experience == "data" and post.question == frame.question("대방어")
    assert post.answer[0].startswith("필요한 양과 받을 날짜") and any("로켓배송" in a for a in post.answer)
    assert len(post.criteria) == 3 and post.constraints == frame.constraints() and post.checklist == frame.CHECKLIST
    assert post.products[0].facts == ["중량·수량: 500g (상품명 표기)", "로켓배송 표시 (검색 결과 표시)"]
    assert svc.check(post) == []


def test_page_order_follows_frame(tmp_path):
    svc, post = _made(tmp_path)
    html = render.post_page(post.model_copy(update={"status": "approved", "approved_at": "2026-11-16T03:00:00+00:00"}), T0)
    marks = [policy.COUPANG_DISCLOSURE, "먼저 답부터", frame.EXPERIENCE_DATA, "왜 뜨고 있을까", "고르기 전에 볼 것",
             "구매 전에 알아 둘 것", "상품 비교", frame.CHECKLIST, "중량·수량: 500g", "판매처에서 보기", "가격 참고"]
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
