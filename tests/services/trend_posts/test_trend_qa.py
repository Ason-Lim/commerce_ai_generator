"""트렌드 글 Q&A (2단계 PR2) — 승인된 글만 근거, 글 문장 그대로, 가격은 확인 시각과 30일 규칙."""
from __future__ import annotations

import pytest

from app.services.trend_posts import qa, render

from .helpers import Clock, approved, item, report, service


@pytest.mark.parametrize("text,kind", [
    ("요즘 대방어 왜 유행해?", "why"), ("대방어 왜 이렇게 인기야", "why"), ("대방어가 뜨는 이유", "why"),
    ("대방어 무슨 일이야", "why"), ("대방어 트렌드 알려줘", "why"),
    ("대방어 재료비 얼마나 들어?", "cost"), ("대방어 가격이 얼마야", "cost"),
    # 사는 말이 있으면 Q&A 가 아니라 평소 상품 추천 (순위·화면 불변)
    ("요즘 인기 있는 대방어 추천해줘", None), ("대방어 왜 이렇게 비싸? 싼 거 찾아줘", None), ("대방어", None),
    ("고당도 사과", None), ("부모님 선물 망고", None), ("3만원 이하 샤인머스캣", None), ("선물용 배", None),
])
def test_intent(text, kind):
    assert qa.intent(text) == kind


def test_only_published_posts_are_found(tmp_path):
    svc = service(tmp_path)
    live = approved(svc)
    waiting, _ = svc.create_from_surge(report(item("천수무")), "천수무")
    svc.submit(waiting.id)
    every = svc.store.all()                      # 일부러 승인 안 된 글까지 넘겨도
    assert qa.find("요즘 대방어 왜 유행해", every).id == live.id
    assert qa.find("천수무 왜 유행해", every) is None
    assert qa.find("천수무 왜 유행해", svc.published()) is None


def test_longest_topic_wins(tmp_path):
    svc = service(tmp_path)
    approved(svc, "수능선물", products=False)
    longer = approved(svc, "수능선물추천", products=False)
    assert qa.find("수능선물추천 왜 이렇게 많아", svc.published()).id == longer.id


def test_why_answer_is_the_posts_own_lines(tmp_path):
    svc = service(tmp_path)
    post = approved(svc)
    ans = qa.answer(post, "why")
    assert ans["lines"] == post.why and ans["section"] == "왜 뜨고 있을까"
    assert post.title in ans["source"] and "2026년 11월 16일 게시" in ans["source"]


def test_cost_answer_uses_checked_prices_and_hides_old_ones(tmp_path):
    clock = Clock()
    svc = service(tmp_path, clock)
    post = approved(svc)
    fresh = qa.answer(post, "cost", clock())
    assert fresh["lines"][0] == "대방어회 500g — 29,900원 · 2026년 11월 16일 12시 확인 가격 · 지금은 다를 수 있어요"
    clock.advance(days=31)
    old = qa.answer(post, "cost", clock())
    assert all("원 ·" not in line for line in old["lines"]) and old["cost_hidden"]
    assert old["lines"][-1].startswith("글의 가격은 확인한 지 30일이 넘었거나")


def test_card_points_to_the_public_page(tmp_path):
    svc = service(tmp_path)
    post = approved(svc)
    c = qa.card(post)
    assert c["url"] == render.post_url(post) and c["has_ad"] and c["title"].startswith("[광고]")
