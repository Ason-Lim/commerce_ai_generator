"""합성 재현 사례 (2026-11-23, 3-D ⑥ — 설계 claude/improve_without_training_proposal_2026-11-22.md §4·§5).

`synthetic_cases.jsonl` 한 줄 = 사례 하나. 관리자 '개선 목록'에서 '오류 확인'한 점검 후보로 만든 초안을 사람이 다듬어
'준비됨'으로 내보낸 것을 여기에 붙인다. **손님 문장을 그대로 옮기지 않고 유형·조건만 남긴 합성 문장**(origin: synthetic),
원래 신호는 종류·날짜만. 역할 넷: fixed(고친 사례) · normal(정상 사례) · counter(반례) · multiturn(여러 턴).

기대값 (마지막 차례 또는 차례마다 쿠팡에 보낸 검색어):
  search      검색어가 정확히 이것        search_has  이 말이 모두 들어감        search_not  이 말이 하나도 안 들어감
  searches    여러 턴 — 차례마다 첫 검색어
등록한 회귀 사례를 다시 어기면 시험이 실패한다 (시험이 모든 실수를 잡지는 않음).
"""
from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

from app.services.chat.service import shopping_terms
from app.services.privacy import pii

FILE = Path(__file__).with_name("synthetic_cases.jsonl")
ROLES = {"fixed", "normal", "counter", "multiturn"}
CASES = [json.loads(line) for line in FILE.read_text(encoding="utf-8").splitlines() if line.strip()]


def test_cases_are_synthetic_and_well_formed():
    ids = [c["id"] for c in CASES]
    assert len(ids) == len(set(ids))
    groups: dict[str, set] = {}
    for c in CASES:
        assert c["origin"] == "synthetic" and c["role"] in ROLES and c["turns"]
        assert set(c["signal"]) <= {"kind", "date"}                       # 원래 신호는 종류·날짜만 (세션·원문 없음)
        assert set(c["expect"]) <= {"search", "search_has", "search_not", "searches"} and c["expect"]
        for t in c["turns"]:
            assert pii.mask(t)[1] == [], c["id"]                           # 개인정보처럼 보이는 내용 없음
            assert len(t) <= 80 and not re.search(r"\d{6,}", t), c["id"]
        groups.setdefault(c["group"], set()).add(c["role"])
    assert all("fixed" in roles for roles in groups.values())            # 묶음마다 고친 사례가 있다


def _check(search: str, expect: dict, cid: str):
    if "search" in expect:
        assert search == expect["search"], cid
    for w in expect.get("search_has") or []:
        assert w in search, cid
    for w in expect.get("search_not") or []:
        assert w not in search, cid


@pytest.mark.parametrize("case", [c for c in CASES if len(c["turns"]) == 1], ids=lambda c: c["id"])
def test_single_turn(case):
    _check(shopping_terms(case["turns"][0])[0], case["expect"], case["id"])


@pytest.mark.parametrize("case", [c for c in CASES if len(c["turns"]) > 1], ids=lambda c: c["id"])
def test_multi_turn(case, make_service, shopping):
    svc, sid, firsts = make_service(), None, []
    for t in case["turns"]:
        before = len(shopping.calls)
        res = svc.handle(sid, message=t)
        sid = res["session_id"]
        firsts.append(shopping.calls[before][0] if len(shopping.calls) > before else None)
    if "searches" in case["expect"]:
        assert firsts == case["expect"]["searches"], case["id"]
    rest = {k: v for k, v in case["expect"].items() if k != "searches"}
    if rest:
        _check(firsts[-1] or "", rest, case["id"])
