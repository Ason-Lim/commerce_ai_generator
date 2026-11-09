"""레거시 추천 점수 엔진 (PM-2 스냅샷·reason_engine·Streamlit이 사용).

00_1 결정(2026-11-09): 이 모듈은 F2-A1 제거 후보가 아니라 보존 대상이다.
compare_snapshot_engine(PM-2)·identity_engine·reason_engine·compare_engine이 의존한다.

점수 정책
- 평점·리뷰 수는 `rating_score_usable is True`로 표시된 상품에서만 점수에 넣는다.
  현재 DB의 평점·리뷰 값은 페이지 보강 스크립트에서 온 것이므로 기본값은 제외다
  (2026-11-02 결정: 스크래핑 평점·리뷰는 DB에 남기되 점수 계산에서 제외).
- 제휴(수수료) 여부는 어떤 점수에도 들어가지 않는다 (2026-11-01 원칙).
"""

from __future__ import annotations

import re
from collections.abc import Mapping

from app.services.food_intelligence.brix_standards import item_brix_tier

# 산식 식별자. 배포 계보가 검증된 버전 번호가 아니다 (SCORE_FORMULA_STATUS 참고).
SCORE_ENGINE_VERSION = "legacy-score-2026-11-09"
SCORE_FORMULA_STATUS = "local_unreleased"  # 로컬 커밋만 됨, 배포·검증 계보 미연결

# 평점·리뷰를 점수에 넣어도 된다는 명시 표시. 검증 로그에 남은 값에만 True를 붙인다.
RATING_SCORE_USABLE_FLAG = "rating_score_usable"

REACTION_LABEL = "사용자 반응 우수 추천"

# 2026-11-04: 품종별 Brix 기준표(food_intelligence/brix_standards)와 같은 구간을 쓴다.
QUALITY_BRIX_TIER_POINTS = {"top": 100, "high": 85, "normal": 45, "below": 0}
QUALITY_BRIX_TEXT_ONLY_POINTS = 20

# 기준표에 없는 품종의 고정 Brix 구간 (이상, 점수)
_FALLBACK_BRIX_TIERS = ((16, 100), (15, 85), (14, 65), (13, 45))

# 100g당 가격 구간 (이하, 점수). 마지막 구간 초과는 15점.
_PRICE_PER_100G_TIERS = ((400, 90), (600, 80), (800, 70), (1000, 60), (1200, 45), (1500, 30))
_PRICE_PER_100G_ABOVE = 15

_RATING_QUALITY_TIERS = ((4.8, 8), (4.5, 5), (4.0, 3))
_REVIEW_QUALITY_TIERS = ((10000, 8), (3000, 6), (1000, 4), (500, 2))
_RATING_TRUST_TIERS = ((4.8, 35), (4.5, 25), (4.0, 15))
_REVIEW_TRUST_TIERS = ((10000, 35), (3000, 25), (1000, 15), (500, 10))
# (최소 평점, 최소 리뷰 수, 점수) — 위에서부터 첫 일치만 적용
_RATING_REVIEW_COMBO_TIERS = ((4.7, 3000, 20), (4.5, 1000, 12), (4.3, 500, 6))

_REACTION_CLICK_TIERS = ((10, 25), (5, 18), (3, 12), (1, 6))
_REACTION_CTR_TIERS = ((10, 25), (5, 18), (3, 10))
_REACTION_CAP = 45

_HIDDEN_GEM_CLICK_TIERS = ((10, 35), (5, 30), (3, 25), (1, 15))
_HIDDEN_GEM_CTR_TIERS = ((20, 40), (10, 30), (5, 20), (3, 10))

# priority별 total 가중치 (quality, price, popularity)
_TOTAL_WEIGHTS = {
    "price": (0.25, 0.60, 0.15),
    "quality": (0.60, 0.15, 0.25),
    "trust": (0.30, 0.20, 0.50),
}
_TOTAL_WEIGHTS_DEFAULT = (0.40, 0.30, 0.30)

_BRIX_FIELDS = ("brix", "brix_value", "avg_brix", "max_brix", "sugar_brix", "display_brix")
_BRIX_TEXT_FIELDS = ("product_name", "raw_name", "name", "title", "description", "summary")
_BRIX_PATTERNS = tuple(
    re.compile(pattern, re.IGNORECASE)
    for pattern in (
        r"(\d{2}(?:\.\d+)?)\s*brix",
        r"(\d{2}(?:\.\d+)?)\s*브릭스",
        r"당도\s*(\d{2}(?:\.\d+)?)",
    )
)
_BRIX_TEXT_RANGE = (8, 30)


# ---------------------------------------------------------------------------
# 공통 도우미
# ---------------------------------------------------------------------------

def get_safe_number(
    value,
    default=0.0,
):
    """
    None, 빈 문자열, 콤마가 포함된 숫자를 안전하게 float로 변환합니다.
    """
    try:
        if value is None:
            return float(default)

        if isinstance(value, str):
            value = value.strip().replace(",", "")

            if not value:
                return float(default)

        return float(value)

    except (TypeError, ValueError):
        return float(default)


def _at_least(value, tiers, default=0):
    """(기준, 점수) 내림차순 구간에서 value >= 기준인 첫 점수."""
    for threshold, points in tiers:
        if value >= threshold:
            return points
    return default


def _base_priority(priority) -> str:
    return str(priority or "trust").replace("_adaptive", "")


def _trend_boost(search_context) -> float:
    if search_context is None:
        return 0.0
    if isinstance(search_context, Mapping):
        raw = search_context.get("trend_boost", 0.0)
    else:
        raw = getattr(search_context, "trend_boost", 0.0)
    return get_safe_number(raw, 0.0)


def rating_signals_usable(item) -> bool:
    """평점·리뷰 수를 점수에 넣어도 되는지. 명시적으로 True일 때만 허용."""
    return (item or {}).get(RATING_SCORE_USABLE_FLAG) is True


def _rating_inputs(item) -> tuple[float, int]:
    """점수에 쓸 (평점, 리뷰 수). 사용 불가 표시면 (0, 0)."""
    if not rating_signals_usable(item):
        return 0.0, 0
    return (
        get_safe_number(item.get("rating"), 0),
        int(get_safe_number(item.get("review_count"), 0)),
    )


def get_cached_identity_validation(
    item,
) -> dict:
    """
    상품에 이미 캐싱된 Identity 검증 결과를 안전하게 반환합니다.

    Identity 엔진 전체 이전 전까지 score_engine이
    UI 계층의 enrich_item_identity()에 의존하지 않도록 합니다.
    값이 없을 때만 50(중립)을 쓰고, 실제 0은 0으로 둡니다.
    """
    item = item or {}

    validation = item.get("_identity_validation")

    if isinstance(validation, dict):
        return validation

    return {
        "identity_score": get_safe_number(item.get("_identity_score"), 50),
        "price_confidence": get_safe_number(item.get("_price_confidence"), 50),
        "brix_confidence": get_safe_number(item.get("_brix_confidence"), 50),
        "identity_key": str(item.get("_product_identity_key") or ""),
        "warnings": [],
    }


# ---------------------------------------------------------------------------
# 세부 점수
# ---------------------------------------------------------------------------

def calculate_price_value_score(item):
    """100g당 가격 기준 가성비 점수 계산"""

    price_per_100g = get_safe_number(item.get("price_per_100g"), 0)

    if price_per_100g <= 0:
        return 0

    for limit, points in _PRICE_PER_100G_TIERS:
        if price_per_100g <= limit:
            return points

    return _PRICE_PER_100G_ABOVE


def _brix_with_source(item) -> tuple[float, str | None]:
    """(brix 값, 출처). 출처는 'field:<이름>' 또는 'text', 없으면 None."""
    for field in _BRIX_FIELDS:
        value = get_safe_number(item.get(field), 0)
        if value > 0:
            return value, f"field:{field}"

    text = " ".join(str(item.get(key) or "") for key in _BRIX_TEXT_FIELDS)

    low, high = _BRIX_TEXT_RANGE
    for pattern in _BRIX_PATTERNS:
        match = pattern.search(text)
        if match:
            value = float(match.group(1))
            if low <= value <= high:
                return value, "text"

    return 0, None


def get_brix_value(item):
    """상품에서 brix 값을 안전하게 추출

    1) API/DB 필드에서 먼저 찾고
    2) 없으면 상품명/설명 텍스트에서 15brix, 15 브릭스, 당도 15 같은 패턴을 추출합니다.
    """
    return _brix_with_source(item)[0]


def calculate_reaction_trust_score(item):
    """클릭/CTR/사용자 반응 기반 안심 점수 보정"""

    click_count = int(get_safe_number(item.get("click_count"), 0))
    ctr_pct = get_safe_number(item.get("ctr_pct"), 0)

    score = 0

    if item.get("final_recommendation_label") == REACTION_LABEL:
        score += 25

    score += _at_least(click_count, _REACTION_CLICK_TIERS)

    if ctr_pct > 0:
        score += _at_least(ctr_pct, _REACTION_CTR_TIERS, default=5)

    return min(score, _REACTION_CAP)


def calculate_hidden_gem_score(item):
    """숨은 인기 상품 점수"""

    impression_count = int(get_safe_number(item.get("impression_count"), 0))
    click_count = int(get_safe_number(item.get("click_count"), 0))
    ctr_pct = get_safe_number(item.get("ctr_pct"), 0)

    score = 0

    # 발견 추천은 너무 적은 노출보다, 어느 정도 검증된 노출을 더 높게 봅니다.
    if 30 <= impression_count <= 150:
        score += 25
    elif 10 <= impression_count < 30:
        score += 15
    elif 150 < impression_count <= 300:
        score += 10

    score += _at_least(click_count, _HIDDEN_GEM_CLICK_TIERS)
    score += _at_least(ctr_pct, _HIDDEN_GEM_CTR_TIERS)

    return min(score, 100)


def calculate_novelty_score(item):
    """탐색 추천용 신규성 점수 계산 (Streamlit 화면과 같은 산식).

    calculate_mode_score(…, "exploration")가 호출한다. 이전에는 이 모듈에
    정의가 없어 탐색 모드에서 NameError가 났다.
    """

    impression_count = int(get_safe_number(item.get("impression_count"), 0))
    click_count = int(get_safe_number(item.get("click_count"), 0))
    ctr_pct = get_safe_number(item.get("ctr_pct"), 0)

    score = 0

    if impression_count == 0:
        score += 35
    elif impression_count <= 10:
        score += 30
    elif impression_count <= 30:
        score += 20
    elif impression_count <= 60:
        score += 10

    if click_count == 0:
        score += 15
    elif click_count <= 2:
        score += 8

    if ctr_pct >= 10:
        score += 25
    elif ctr_pct >= 5:
        score += 15
    elif ctr_pct > 0:
        score += 8

    if item.get("recommendation_mode") == "exploration":
        score += 20

    return min(score, 100)


def calculate_brix_quality_points(item, brix):
    """품질 점수의 Brix 부분 (최대 100).

    기준표에 있는 품종은 그 품종의 고당도·최상 기준으로, 없는 상품은 이전 고정 구간으로 판정한다.
    """
    tier, _standard = item_brix_tier(item, brix)

    if tier is None:
        points = _at_least(brix, _FALLBACK_BRIX_TIERS)
        if points:
            return points
        return QUALITY_BRIX_TEXT_ONLY_POINTS if item.get("is_high_brix") else 0

    if tier == "no_value":
        return QUALITY_BRIX_TEXT_ONLY_POINTS if item.get("is_high_brix") else 0

    return QUALITY_BRIX_TIER_POINTS[tier]


def _quality_score(item, rating, review_count) -> float:
    score = calculate_brix_quality_points(item, get_brix_value(item))
    score += _at_least(rating, _RATING_QUALITY_TIERS)
    score += _at_least(review_count, _REVIEW_QUALITY_TIERS)
    return min(score, 100)


def _trust_score(item, rating, review_count) -> float:
    score = _at_least(rating, _RATING_TRUST_TIERS)
    score += _at_least(review_count, _REVIEW_TRUST_TIERS)

    for min_rating, min_reviews, points in _RATING_REVIEW_COMBO_TIERS:
        if rating >= min_rating and review_count >= min_reviews:
            score += points
            break

    # 리뷰/평점이 부족한(또는 점수에서 제외된) 상품도 실제 클릭/CTR 반응이 있으면
    # 오늘의 베스트와 안심 기준에서 완전히 밀리지 않도록 보정합니다.
    score += calculate_reaction_trust_score(item)

    return min(score, 100)


def _price_score(item) -> float:
    score = calculate_price_value_score(item)

    if item.get("final_discount_rate") or item.get("discount_rate"):
        score += 10

    if get_safe_number(item.get("price_drop_boost"), 0) >= 5:
        score += 15

    return min(score, 100)


def _popularity_score(item, base_priority) -> float:
    score = 0

    if item.get("final_recommendation_label") == REACTION_LABEL:
        score += 30

    if get_safe_number(item.get("ctr_feedback_boost"), 0) >= 7:
        score += 30

    if get_safe_number(item.get("ctr_pct"), 0) >= 20:
        score += 20

    # 발견 추천에서는 실제 클릭/CTR 반응이 있는데도
    # 사용자 반응이 0점으로 보이지 않도록 발견성 점수를 일부 반영합니다.
    if base_priority == "discovery":
        score = max(score, min(calculate_hidden_gem_score(item) * 0.4, 35))

    return score


# ---------------------------------------------------------------------------
# 공개 진입점
# ---------------------------------------------------------------------------

def calculate_ai_scores(item, priority="trust"):
    """상품별 AI 추천 근거 점수 계산.

    반환: quality·trust·price·popularity(각 0~100)와 total.
    total은 화면에 보이는 (상한 적용된) 세부 점수로 계산한다.
    """

    base_priority = _base_priority(priority)
    rating, review_count = _rating_inputs(item)

    quality = _quality_score(item, rating, review_count)
    trust = _trust_score(item, rating, review_count)
    price = _price_score(item)
    popularity = _popularity_score(item, base_priority)

    w_quality, w_price, w_popularity = _TOTAL_WEIGHTS.get(
        base_priority, _TOTAL_WEIGHTS_DEFAULT
    )
    total = quality * w_quality + price * w_price + popularity * w_popularity

    return {
        "quality": round(quality, 1),
        "trust": round(trust, 1),
        "price": round(price, 1),
        "popularity": round(popularity, 1),
        "total": round(total, 1),
    }


def calculate_mode_score(
    item,
    scores,
    base_priority,
    search_context=None,
):
    """추천 모드별 최종 정렬 점수 계산"""

    trend_boost = _trend_boost(search_context)

    quality_score = scores.get("quality", 0)
    price_score = scores.get("price", 0)
    trust_score = scores.get("trust", 0)
    popularity_score = scores.get("popularity", 0)

    if base_priority == "quality":
        brix_confidence = get_cached_identity_validation(item).get("brix_confidence", 0)
        return (
            quality_score * 0.70
            + brix_confidence * 0.20
            + trust_score * 0.07
            + price_score * 0.03
            + trend_boost
        )

    if base_priority == "price":
        price_confidence = get_cached_identity_validation(item).get("price_confidence", 0)
        return (
            price_score * 0.58
            + price_confidence * 0.22
            + quality_score * 0.12
            + trust_score * 0.08
            + trend_boost
        )

    if base_priority == "trust":
        return (
            trust_score * 0.75
            + quality_score * 0.15
            + price_score * 0.10
            + trend_boost
        )

    if base_priority == "exploration":
        return (
            quality_score * 0.55
            + calculate_novelty_score(item) * 0.35
            + price_score * 0.10
            + trend_boost
        )

    if base_priority == "discovery":
        return (
            quality_score * 0.45
            + calculate_hidden_gem_score(item) * 0.45
            + trust_score * 0.10
            + trend_boost
        )

    if base_priority == "mix":
        return (
            quality_score * 0.40
            + price_score * 0.30
            + trust_score * 0.30
            + trend_boost
        )

    return (
        quality_score * 0.35
        + trust_score * 0.25
        + price_score * 0.20
        + popularity_score * 0.10
        + trend_boost
    )


def _rating_exclusion_reason(item) -> str:
    if RATING_SCORE_USABLE_FLAG not in item:
        return "flag_missing"      # 표시 없음 → 기본 제외
    if item.get(RATING_SCORE_USABLE_FLAG) is False:
        return "flag_false"        # 점수 사용 불가로 표시됨
    return "flag_not_true"         # True가 아닌 값(문자열·1 등) → 불확실, 제외


_RATING_EXCLUSION_TEXT = {
    "flag_missing": "평점·리뷰 출처 검증 표시가 없어 점수에서 제외",
    "flag_false": "평점·리뷰가 점수 사용 불가로 표시되어 제외",
    "flag_not_true": "평점·리뷰 검증 표시가 True가 아니어서(불확실) 제외",
}


def explain_score_inputs(item) -> dict:
    """1단계 '추천 근거 표시'용 내부 설명: 점수에 실제로 들어간 값, 기본값, 제외 사유.

    점수 자체는 바꾸지 않는다. formula_status가 'local_unreleased'인 동안
    formula_id를 배포·검증된 버전처럼 화면에 표시하지 않는다.
    """
    item = item or {}
    rating_used = rating_signals_usable(item)
    rating, review_count = _rating_inputs(item)
    brix, brix_source = _brix_with_source(item)

    inputs_used = {
        "brix": {"value": brix, "source": brix_source},
        "price_per_100g": get_safe_number(item.get("price_per_100g"), 0) or None,
        "discount": bool(item.get("final_discount_rate") or item.get("discount_rate")),
        "price_drop_boost": get_safe_number(item.get("price_drop_boost"), 0),
        "click_count": int(get_safe_number(item.get("click_count"), 0)),
        "ctr_pct": get_safe_number(item.get("ctr_pct"), 0),
        "impression_count": int(get_safe_number(item.get("impression_count"), 0)),
        "rating": rating if rating_used else None,
        "review_count": review_count if rating_used else None,
    }

    defaults_applied = []
    if brix_source is None:
        defaults_applied.append({"field": "brix", "default": 0, "reason": "필드·상품명 모두 값 없음"})
    if inputs_used["price_per_100g"] is None:
        defaults_applied.append({"field": "price_per_100g", "default": 0, "reason": "단위가격 없음 → 가성비 0점"})
    if not isinstance(item.get("_identity_validation"), dict):
        for field, key in (("brix_confidence", "_brix_confidence"),
                           ("price_confidence", "_price_confidence")):
            if item.get(key) is None:
                defaults_applied.append({"field": field, "default": 50,
                                         "reason": "Identity 캐시 없음 → 중립값"})

    excluded = []
    has_rating_values = any(
        get_safe_number(item.get(key), 0) > 0 for key in ("rating", "review_count")
    )
    if has_rating_values and not rating_used:
        code = _rating_exclusion_reason(item)
        excluded.append({
            "field": "rating/review_count",
            "code": code,
            "reason": _RATING_EXCLUSION_TEXT[code],
            "source": item.get("review_source"),
        })

    return {
        "formula_id": SCORE_ENGINE_VERSION,
        "formula_status": SCORE_FORMULA_STATUS,
        "rating_used": rating_used,
        "inputs_used": inputs_used,
        "defaults_applied": defaults_applied,
        "excluded": excluded,
        "affiliate_bonus": False,
    }
