"""눈대중 가늠 — "100g이 어느 정도인지" 집에서 알아볼 수 있는 표현 (2026-10-30, 사용자 승인 초안).

* 원문 분량이 기준이다.  가늠 표현은 그 옆에 붙는 '일반 제안'(원문 아님)이고 보유량 계산·
  충분·부족 판단에는 쓰지 않는다.
* 사람이 정리한 표에 있는 재료·단위에만 붙인다.  표에 없으면 아무것도 붙이지 않는다 (AI 생성 없음).
* 컵·mL 는 붙이지 않는다 — 원문 컵 크기를 모르므로 종이컵·mL 로 바꿔 말하지 않는다.
* 인분을 바꾸면 바뀐 분량으로 다시 계산한다.

근거 (항목별):
* 동전 지름 — 한국은행 현용주화: 10원(2006~) 18.0mm, 50원 21.6mm, 100원 24.0mm, 500원 26.5mm
* 마른 긴 면 — 국내에서 흔한 "마른 긴 면 100g ≈ 500원 동전 굵기 묶음" 한 가지만 참고로 보여 준다.
  (2026-10-30 사용자 결정) 재료명이 '파스타'처럼 면 종류를 알 수 없으면 붙이지 않고, 실측 근거가 없으므로
  다른 무게를 동전 크기로 환산하지 않는다.
* 버터 1큰술(15mL) ≈ 한 변 2.5cm 정육면체 (2.5³ = 15.6mL) — 대략적인 참고로 표시
* 다진마늘 1작은술 ≈ 마늘 1쪽 (흔한 기준, 마늘 크기에 따라 다름) — 대략적인 참고로 표시
* 양파 — 주먹만 한 중간 크기 기준의 비율 — 대략적인 참고로 표시
* 소금·후추 '약간' — 엄지와 검지로 한 꼬집
* 식용유 '약간'은 붙이지 않는다 (2026-10-30: 조리 용도마다 양이 달라 원문의 뜻을 좁힘)
"""
from __future__ import annotations

import re
from fractions import Fraction


# 마른 긴 면임이 이름에서 확인되는 경우만 ('파스타', '파스타면', '생면'은 종류를 알 수 없어 제외)
_LONG_DRY = re.compile(r"^(?:마른|건)?(스파게티|스파게티면|스파게티니|링귀니|링귀네|카펠리니|엔젤헤어)(?:\(건면\))?$")
_FRESH = re.compile(r"생면|생파스타|생스파게티")
APPROX = " (크기에 따라 달라요 · 대략적인 참고)"
_BUTTER = re.compile(r"^(버터|무염버터|가염버터)$")
_GARLIC = re.compile(r"^(다진\s*마늘|다진마늘|마늘\s*다진\s*것)$")
_ONION = re.compile(r"^양파$")
_PINCH = re.compile(r"^(소금|후춧가루|후추|굵은소금|꽃소금)$")
_VAGUE = re.compile(r"^(약간|조금|소량|적당량)$")

_NUMBER = r"(\d+\s*과\s*\d+/\d+|\d+(?:\.\d+)?/\d+|\d+(?:\.\d+)?)"
_AMOUNT = re.compile(r"^\s*(?:약\s*)?" + _NUMBER + r"\s*([가-힣a-zA-Z]+)\s*$")


def _value(text: str) -> Fraction:
    text = re.sub(r"\s+", "", text)
    if "과" in text:
        whole, part = text.split("과")
        return Fraction(int(whole)) + Fraction(part)
    return Fraction(text)


def _parse(amount: str) -> tuple[Fraction, str] | None:
    a = (amount or "").strip()
    if a.startswith("(") and a.endswith(")"):
        a = a[1:-1].strip()
    m = _AMOUNT.match(a)
    if not m:
        return None
    try:
        return _value(m.group(1)), m.group(2)
    except (ValueError, ZeroDivisionError):
        return None


def _count(n: Fraction) -> str:
    """1 → '1개', 1/2 → '반 개', 3/2 → '1개 반', 2 → '2개' (halves only; else rounded)."""
    halves = round(n * 2)
    if halves <= 0:
        return ""
    whole, half = divmod(halves, 2)
    if whole == 0:
        return "반 개"
    return f"{whole}개" + (" 반" if half else "")


def _pasta(grams: Fraction) -> str | None:
    """Only the one reference point — no conversion of other weights to coin sizes (not measured)."""
    return "참고: 마른 긴 면 100g ≈ 500원 동전 굵기 묶음" if grams > 0 else None


_FRACTION_WORDS = {Fraction(1, 4): "4분의 1", Fraction(1, 3): "3분의 1", Fraction(1, 2): "절반",
                   Fraction(2, 3): "3분의 2", Fraction(3, 4): "4분의 3"}


def _onion(n: Fraction) -> str | None:
    if n in _FRACTION_WORDS:
        return f"주먹만 한 양파의 {_FRACTION_WORDS[n]}"
    if n.denominator == 1:
        return f"주먹만 한 양파 {n.numerator}개"
    return None


def gauge(name: str, amount: str) -> str | None:
    """A homely way to picture ``amount`` of ``name`` (already scaled to the current servings), or None."""
    name = re.sub(r"\s+", "", name or "")
    amount = (amount or "").strip()
    if _VAGUE.match(amount):
        return "엄지와 검지로 한 꼬집" if _PINCH.match(name) else None
    parsed = _parse(amount)
    if parsed is None:
        return None
    n, unit = parsed
    if unit in ("컵", "mL", "ml", "L", "cc"):
        return None     # 원문 컵 크기를 모름 — 종이컵·mL로 바꿔 말하지 않는다
    if _LONG_DRY.match(name) and not _FRESH.search(name) and unit in ("g", "kg"):
        return _pasta(n)
    if _BUTTER.match(name):
        cubes = n if unit == "큰술" else n / 3 if unit == "작은술" else None
        if cubes:
            text = _count(cubes)
            return f"한 변 2.5cm 깍둑 조각 {text}{APPROX}" if text else None
        return None
    if _GARLIC.match(name):
        cloves = n if unit == "작은술" else n * 3 if unit == "큰술" else None
        if cloves:
            text = _count(cloves).replace("개", "쪽")
            if text == "반 쪽":
                return f"마늘 반 쪽을 다진 양{APPROX}"
            return f"마늘 {text}을 다진 양{APPROX}" if text else None
        return None
    if _ONION.match(name) and unit == "개":
        text = _onion(n)
        return text + APPROX if text else None
    return None
