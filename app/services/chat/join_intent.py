"""대화창 '입점하고 싶어요' 알아보기 (2026-11-25) — 셀러 데이터는 읽지 않는다(말만 본다).
입점 신청 처리 자체는 app/services/seller/join.py."""

from __future__ import annotations

import re

JOIN_RE = re.compile(r"입점|셀러\s*(?:등록|가입|신청)|판매자\s*(?:등록|가입|신청|로)|(?:상품|물건)을?\s*(?:팔고|판매하고)\s*싶|"
                     r"여기서\s*(?:팔|판매)|판매\s*(?:제휴|입점)")  # fmt: skip


def asks_to_join(text: str) -> bool:
    """'입점하고 싶어요' — 쇼핑 질문('입점 상품 추천')은 아니게."""
    t = text or ""
    return bool(JOIN_RE.search(t)) and not re.search(r"추천|골라|사고\s*싶|구매", t)
