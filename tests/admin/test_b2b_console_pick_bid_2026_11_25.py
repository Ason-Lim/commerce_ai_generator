"""B2B 콘솔 — 새 대화에서 '제안서 작성해줘'만 누르면 '분석할 공고나 조건을 찾지 못했어요'로 끝나던 문제 (2026-11-25 지인 의견).
공고번호·조건이 없으면 어느 공고로 만들지 고르게 한다."""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from app.admin.b2b import console as C


def bid(bid_id, title, status, *, req=True, legacy=False):
    r = SimpleNamespace(headcount=500, budget_per_person=50000, categories=["식품"]) if req else None
    return SimpleNamespace(bid_id=bid_id, title=title, requirement=r,
                           verification="legacy_unverified" if legacy else "verified",
                           view=lambda today=None, s=status: {"status": s})  # fmt: skip


@pytest.fixture
def con(monkeypatch):
    monkeypatch.setattr(C.bidstore, "list_bids", lambda: [
        bid("IBK서비스-2026008", "IBK 임직원 선물", "입찰중"),
        bid("가공사-2026010", "가공사 명절 선물", "마감임박"),
        bid("나기관-2026011", "조건 없는 공고", "입찰중", req=False),
        bid("옛공고-2025001", "미검증", "입찰중", legacy=True),
        bid("끝-2026001", "마감", "입찰마감"),
    ])  # fmt: skip
    called = []
    c = C.Console.__new__(C.Console)
    c.ws = {}
    monkeypatch.setattr(c, "_analyze", lambda w, p, today: called.append(p) or [], raising=False)
    c.called = called
    return c


@pytest.mark.parametrize("prompt, action", [("제안서 작성해줘", "proposal"), ("견적 요청서 만들어줘", "rfq")])
def test_no_bid_asks_which_bid_with_buttons(con, prompt, action):
    out = con.run(None, prompt)
    assert out["action"] == action and con.called == []  # 분석을 헛돌리지 않는다
    md = "\n".join(b.get("md", "") for b in out["blocks"])
    assert "공고를 먼저 골라" in md and "찾지 못했어요" not in md
    items = next(b["items"] for b in out["blocks"] if b["type"] == "actions")
    word = C.Console.ACTION_WORD[action]
    assert items[:2] == [f"가공사-2026010 {word}", f"IBK서비스-2026008 {word}"]  # 조건 있는 공고, 마감임박 먼저
    assert items[2] == "나기관-2026011 분석해줘"  # 2026-11-26: 조건 읽기 전 공고도 버튼(누르면 공고문 분석)
    assert not any("옛공고" in x or "끝-" in x for x in items)


def test_only_unread_bids_are_still_clickable(con, monkeypatch):
    """조건이 읽힌 공고가 없어도 입찰중 공고는 눌러서 분석할 수 있다 (2026-11-26 '공고문이 클릭이 안돼요')."""
    monkeypatch.setattr(C.bidstore, "list_bids", lambda: [bid("나기관-2026011", "조건 없는 공고", "입찰중", req=False)])
    out = con.run(None, "제안서 작성해줘")
    md = "\n".join(b.get("md", "") for b in out["blocks"])
    items = next(b["items"] for b in out["blocks"] if b["type"] == "actions")
    assert items[0] == "나기관-2026011 분석해줘" and "조건을 읽지 않았어요" in md and "조건 읽기 전" in md


def test_with_bid_number_it_analyzes_first(con):
    con.run(None, "IBK서비스-2026008 제안서 작성해줘")
    assert con.called == ["IBK서비스-2026008 제안서 작성해줘"]


def test_with_conditions_it_analyzes_first(con):
    con.run(None, "직원 300명 1인당 3만원 제안서 작성해줘")
    assert con.called
