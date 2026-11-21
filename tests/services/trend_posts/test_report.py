"""사이트 트렌드 글 보고서형 report v1.0 (2026-11-21) — 설계 claude/trend_post_format_feedback_2026-11-20.md §2.

넘어가는 기준
* 순서: 고지 → 제목 → 날짜 → 요약 3줄 → ① 데이터(관심 변화 → 확인된 행사·보도 → 가능한 해석 → 확인되지 않은 부분)
  → ② 이번에 볼 기준 → ③ 상품 표 + 결제 전 확인 → 가격 참고 → ④ 레시피 → 확인한 곳.  '먼저 답부터' 없음.
* 원인 미확인이면 그렇게 쓰고, 출처 있는 행사·보도가 없으면 제목에 '왜 뜨는지·이유'를 쓰지 않는다(정책 검사).
* 일반 문장('지금은 다를 수 있어요')은 가격 참고 한 곳에만. 구매 전 제약은 키워드 고유 문장만.
* 보류 결론은 형식과 상관없이 구매 유도 요소 전체 제거, 데이터 절·출처는 유지.
* .env TREND_POST_FORMAT=frame04 로 되돌릴 수 있고, 예전 글은 예전 순서 그대로 (test_frame.py).
"""
from __future__ import annotations

import pytest

from app.services.trend_posts import draft, frame, policy, render, report as R, templates

from .helpers import T0, item, recipe_result, report, search_result, service

PUBLIC_CAUSE = {"cause": "김장철을 맞아 활용법 글이 늘어난 듯", "kind": "선물·시즌", "public": True}


@pytest.fixture(autouse=True)
def _default_format(monkeypatch):
    monkeypatch.delenv("TREND_POST_FORMAT", raising=False)


def codes(issues):
    return {i["code"] for i in issues}


def _make(tmp_path, it=None, products=True, recipe=False):
    svc = service(tmp_path)
    it = it or item()
    post, _ = svc.create_from_surge(report(it), it["keyword"],
                                    find_products=(lambda k: search_result()) if products else None,
                                    find_recipe=(lambda k: recipe_result(title="숙성 대방어")) if recipe else None)
    return svc, post


def _page(post):
    return render.post_page(post.model_copy(update={"status": "approved", "approved_at": "2026-11-16T03:00:00+00:00"}), T0)


# ── 초안 ─────────────────────────────────────────────
def test_new_site_post_is_report_with_three_line_summary_and_data_parts(tmp_path):
    svc, post = _make(tmp_path)
    assert post.format == "report" and post.rules_version == R.RULES_VERSION
    assert len(post.summary_lines) == 3 and post.summary_lines[2] == R.NO_CAUSE      # helpers 계기는 '불명'
    assert any("약 2.7배" in x for x in post.data_change) and any("82위" in x for x in post.data_change)
    assert post.data_reading == [] and post.data_events == []
    assert post.data_unknown[:2] == [R.NO_CAUSE, R.UNKNOWN_EVENTS] and R.UNKNOWN_SALES in post.data_unknown
    assert post.question is None and post.answer == [] and post.sections == []        # 블로그식 절은 사이트에서 뺌
    assert post.why                                                                    # 대화 답(qa.py)용 이유 줄은 유지
    assert svc.check(post) == []


def test_guess_goes_to_reading_and_is_marked_unconfirmed(tmp_path):
    _, post = _make(tmp_path, item(cause=PUBLIC_CAUSE))
    assert post.data_reading == ["블로그 제목으로 본 추정(AI): 김장철을 맞아 활용법 글이 늘어난 듯."]
    assert post.data_unknown[0] == R.UNKNOWN_GUESS and "확인되지 않았어요" in post.summary_lines[2]
    assert not any("김장철" in x for x in post.summary_lines)          # 요약에는 추정 원인을 쓰지 않음


def test_criteria_are_two_to_three_and_carry_a_keyword_fact(tmp_path):
    _, post = _make(tmp_path)
    assert 2 <= len(post.criteria) <= 3
    assert post.criteria[-1].startswith("이번에 확인한 상품 구성: 500g·1kg")
    _, none = _make(tmp_path / "b", products=False)
    assert none.criteria == frame.criteria("대방어", "site")[:3] and none.checklist is None


def test_only_keyword_specific_constraints(tmp_path):
    _, post = _make(tmp_path)
    assert post.constraints == ["제철 식재료는 시기와 산지에 따라 크기·상태가 달라질 수 있어요."]
    assert not set(post.constraints) & set(frame.CONSTRAINTS_COMMON["site"])


def test_env_switch_back_to_frame04(tmp_path, monkeypatch):
    monkeypatch.setenv("TREND_POST_FORMAT", "frame04")
    _, post = _make(tmp_path)
    assert post.format == "frame04" and post.question and not post.summary_lines


# ── 제목 · 행사·보도 ─────────────────────────────────
def test_title_is_change_centred_without_sourced_events(tmp_path):
    svc, post = _make(tmp_path)
    assert post.title.startswith("[광고] ") and "왜" not in post.title and "이유" not in post.title
    bad = post.model_copy(update={"title": "[광고] 대방어 왜 뜨는지 알아봤어요"})
    assert "report_title" in codes(policy.check(bad, now=T0))


def test_sourced_event_allows_cause_title_and_renders_link(tmp_path):
    ev = {"label": "○○수산 대방어 축제 개막 보도", "url": "https://news.example/a1", "date": "2026-11-10"}
    junk = {"label": "출처 없는 소문", "url": "javascript:alert(1)"}
    svc, post = _make(tmp_path, item(events=[ev, junk], cause=PUBLIC_CAUSE))
    assert len(post.data_events) == 1 and "https://news.example/a1" in post.data_events[0]
    assert "이유" in post.title and svc.check(post) == []
    assert R.UNKNOWN_EVENTS not in post.data_unknown and R.UNKNOWN_GUESS not in post.data_unknown
    html = _page(post)
    assert 'href="https://news.example/a1"' in html and "javascript:" not in html
    bad = post.model_copy(update={"data_events": ["출처 없는 보도"]})
    assert "report_data" in codes(policy.check(bad, now=T0))


def test_data_section_required_lines(tmp_path):
    _, post = _make(tmp_path)
    for upd in ({"data_change": []}, {"data_unknown": []}, {"summary_lines": []},
                {"summary_lines": ["a", "b", "c", "d"]}):
        assert "report_data" in codes(policy.check(post.model_copy(update=upd), now=T0)), upd


def test_numbers_and_html_rules_cover_new_fields(tmp_path):
    _, post = _make(tmp_path)
    bad = post.model_copy(update={"data_reading": ["지금 19,900원으로 최저가예요"],
                                  "summary_lines": ['<img src=x onerror="alert(1)">', "b", "c"]})
    assert {"numbers", "price_claim", "html"} <= codes(policy.check(bad, now=T0))
    html = _page(bad)
    assert "<img src=x" not in html and "&lt;img" in html


# ── 화면 ─────────────────────────────────────────────
def test_page_order_follows_report(tmp_path):
    _, post = _make(tmp_path, item(cause=PUBLIC_CAUSE), recipe=True)
    html = _page(post)
    marks = [policy.COUPANG_DISCLOSURE, "<h1>", "class=sum", "① 데이터로 본 변화", "관심 변화", "가능한 해석",
             "확인되지 않은 부분", "② 이번에 볼 기준", "③ 상품", "class=pt", "결제 전 확인", "구매 전에 알아 둘 것",
             "가격 참고", "④ 레시피", "확인한 곳", frame.experience_line("대방어", "site")]
    pos = [html.index(m) for m in marks]
    assert pos == sorted(pos), list(zip(marks, pos))
    assert "먼저 답부터" not in html and "왜 뜨고 있을까" not in html and "고르기 전에 볼 것" not in html
    assert html.count("다를 수 있") == 1                       # 가격이 바뀔 수 있다는 말은 가격 참고 한 곳에만
    assert html.count("/go/") == 2 and 'rel="sponsored nofollow noopener"' in html


def test_table_thumbnails_only_from_coupang(tmp_path):
    from .helpers import pick
    result = {"items": [pick("대방어회 500g", "https://link.coupang.com/a/aaa"),
                        pick("필렛", "https://link.coupang.com/a/bbb", image="https://evil.example/x.jpg")]}
    svc = service(tmp_path)
    post, _ = svc.create_from_surge(report(), "대방어", find_products=lambda k: result)
    html = _page(post)
    assert html.count("<img class=tthumb") == 1 and "evil.example" not in html


def test_stale_price_hidden_in_table(tmp_path):
    _, post = _make(tmp_path)
    old = post.model_copy(update={"products": [p.model_copy(update={"price_checked_at": "2026-09-01T00:00:00+00:00"})
                                               for p in post.products]})
    html = _page(old)
    assert "원 (" not in html and render.CHECK_AT_MALL in html


# ── 보류 결론 ─────────────────────────────────────────
def test_hold_report_drops_every_buy_element_and_keeps_data(tmp_path):
    svc, post = _make(tmp_path)
    held = svc.update(post.id, {"conclusion": "hold"})
    assert held.format == "report" and not held.title.startswith("[광고]") and held.disclosure is None
    assert "사야 할까" in held.title or "필요한지" in held.title
    assert held.checklist is None and held.constraints == [] and held.data_change == post.data_change
    html = _page(held)
    for m in ("판매처에서 보기", "/go/", "class=pt", "③ 상품", "가격 참고", "구매 전에 알아 둘 것",
              "결제", "판매 페이지에서", policy.COUPANG_DISCLOSURE, "sponsored", "class=tthumb"):
        assert m not in html, m
    assert "① 데이터로 본 변화" in html and "② 필요해지면 볼 기준" in html
    assert templates.HOLD_LINE["site"] in html and "datalab.naver.com" in html
    assert frame.experience_line("대방어", "site", True) in html
    back = svc.update(post.id, {"conclusion": "buy"})
    assert back.title == post.title and back.checklist and back.criteria == post.criteria
    assert back.constraints == post.constraints and back.question is None


def test_old_framed_posts_still_render_their_own_way(tmp_path, monkeypatch):
    monkeypatch.setenv("TREND_POST_FORMAT", "frame04")
    _, post = _make(tmp_path)
    html = _page(post)
    assert "먼저 답부터" in html and "① 데이터로 본 변화" not in html


def test_format_switch_changes_only_new_drafts(tmp_path, monkeypatch):
    """TREND_POST_FORMAT 은 새 초안의 기본 형식만 바꾼다 — 이미 만든 글은 저장된 format 대로 그린다(전체 되돌리기 아님)."""
    svc, post = _make(tmp_path)
    monkeypatch.setenv("TREND_POST_FORMAT", "frame04")
    assert "① 데이터로 본 변화" in _page(svc.get(post.id))
    newer, _ = svc.create_from_surge(report(item("방어회")), "방어회", find_products=lambda k: search_result())
    assert newer.format == "frame04" and "먼저 답부터" in _page(newer)


def test_conclusion_switch_rewrites_only_listed_fields(tmp_path):
    """결론을 바꿀 때 다시 쓰는 칸: 제목·기준·제약·결제 전 확인(·보류면 결론 문단). 요약·데이터 절·상품·출처는 사람이 고친 그대로."""
    svc, post = _make(tmp_path)
    edited = svc.update(post.id, {"data_change": ["운영자가 고친 줄"], "summary_lines": ["a", "b", "c"]})
    held = svc.update(post.id, {"conclusion": "hold"})
    assert held.data_change == ["운영자가 고친 줄"] and held.summary_lines == ["a", "b", "c"]
    assert held.products == edited.products and held.sources == edited.sources
