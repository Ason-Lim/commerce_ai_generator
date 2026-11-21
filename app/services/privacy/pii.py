"""대화 문장 속 개인정보 가리기 (2026-11-21 결정 — 처리방침 초안 claude/privacy_policy_draft_2026-11-21.md).

서비스는 개인정보를 받지 않는다. 그래도 고객이 대화창에 적으면, **저장·외부 AI(DeepSeek) 전송·실수 신호 기록 전에**
모양으로 찾아 가린다. 가린 사실은 화면에 알린다(무엇을 가렸는지 종류만 — 값은 다시 보여 주지 않는다).

찾는 것: 주민등록·외국인등록번호, 휴대폰·일반 전화번호, 이메일, 카드번호(16자리), 계좌번호 모양(숫자 10~16자리 + 하이픈 2개 이상).
찾지 않는 것: 이름·주소(모양으로 가리기 어렵고, 상품명·지명과 헷갈림) — 그래서 입력창 아래 '개인정보를 적지 마세요' 안내를 늘 둔다.
상품 문장과 헷갈리지 않게: 가격('30,000원'), 무게('500g x 2'), 상품 번호(7자리 숫자)는 건드리지 않는다.
"""
from __future__ import annotations

import re

MASK = "***"

# (종류, 정규식) — 앞에서부터 차례로. 숫자 앞뒤가 다른 숫자에 붙어 있으면 보지 않는다.
_PATTERNS: tuple[tuple[str, re.Pattern], ...] = (
    ("주민등록번호", re.compile(r"(?<!\d)\d{2}(?:0[1-9]|1[0-2])(?:0[1-9]|[12]\d|3[01])\s*[-–]?\s*[1-8]\d{6}(?!\d)")),
    ("이메일", re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")),
    ("카드번호", re.compile(r"(?<!\d)\d{4}[ -]\d{4}[ -]\d{4}[ -]\d{4}(?!\d)|(?<![\d-])\d{16}(?![\d-])")),
    ("전화번호", re.compile(r"(?<!\d)(?:\+?82[ -]?)?0?1[016789][ .-]?\d{3,4}[ .-]?\d{4}(?!\d)")),
    ("전화번호", re.compile(r"(?<!\d)0(?:2|[3-6][1-5]|70)[ .-]\d{3,4}[ .-]\d{4}(?!\d)")),
    ("계좌번호", re.compile(r"(?<![\d-])\d{2,6}-\d{2,6}-\d{2,8}(?:-\d{1,4})?(?![\d-])")),
)


def _account_like(m: re.Match) -> bool:
    digits = re.sub(r"\D", "", m.group(0))
    return 10 <= len(digits) <= 16


def mask(text: str | None) -> tuple[str, list[str]]:
    """(가린 문장, 가린 종류 목록). 찾은 것이 없으면 문장 그대로, 빈 목록."""
    out = text or ""
    kinds: list[str] = []
    for kind, pattern in _PATTERNS:
        def repl(m: re.Match, kind=kind) -> str:
            if kind == "계좌번호" and not _account_like(m):
                return m.group(0)
            if kind not in kinds:
                kinds.append(kind)
            return MASK
        out = pattern.sub(repl, out)
    return out, kinds


def notice(kinds: list[str]) -> str:
    return (f"개인정보로 보이는 부분({'·'.join(kinds)})은 지우고 처리했어요. "
            "이 서비스는 개인정보가 필요 없어요 — 이름·연락처·주소는 적지 않으셔도 돼요.")


INPUT_HINT = "이름·전화번호·주소 같은 개인정보는 적지 마세요. 입력한 문장은 답을 만들기 위해 외부 AI로 보내져요."
