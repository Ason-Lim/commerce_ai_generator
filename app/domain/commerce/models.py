"""공통 계약 모델 — 기존 /api/chat 결과를 의미 손실 없이 담는다 (새 점수·값을 지어내지 않는다).

원칙
- 금액은 정수 원.  배송비를 모르면 None (0원 아님) → 총액도 None.
- 판매처는 platform(쿠팡·네이버 …) · merchant(입점 판매자) · product_url 로 나눈다.
- 근거(Evidence)는 값마다 출처·방식·상태를 붙인다.  '읽었다'와 '계산에 써도 된다'는 따로 판정한다.
- 점수(ScoreDetail)는 기존 엔진이 실제로 낸 값만 옮긴다.  없는 분해값은 채우지 않는다.
"""
from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

SCHEMA_VERSION = "commerce.v1"

Status = Literal["ok", "empty", "needs_followup", "held", "partial", "error"]


class _Model(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


Usage = Literal["display", "filter", "price_compare", "score"]
UsageVerdict = Literal["allow", "allow_labelled", "hold", "block"]


class UsageDecision(_Model):
    """근거 값 하나를 한 용도에 써도 되는지 (2026-11-03 p29).  판정 규칙은 policies.decide_usage 한 곳."""
    use: Usage
    verdict: UsageVerdict                    # allow_labelled = 써도 되지만 화면에 출처 표기를 붙인다
    reason: str                              # 사유 코드 (예: seller_title, page_or_ocr_value)
    label: Optional[str] = None              # allow_labelled 일 때 붙일 표기


class Evidence(_Model):
    """값 하나의 근거.  예: 상품명 '500g x 2팩' → weight_g=1000 (method=title_parse, status=unverified)."""
    field: str
    value: Optional[str] = None
    unit: Optional[str] = None
    method: Literal["api", "title_parse", "html", "ocr", "partner_feed", "registry", "public_api", "ucp_catalog",
                    "unknown"]
    source: Optional[str] = None            # API 이름·판매처·등록부 등
    source_url: Optional[str] = None
    region: Optional[str] = None            # OCR: 이미지·영역 위치
    collected_at: Optional[str] = None
    status: Literal["verified", "unverified", "conflict", "missing"] = "unverified"
    usable_for_score: bool = False           # 판독 성공과 계산 사용 허가는 별개
    usage: list[UsageDecision] = Field(default_factory=list)   # 용도별 판정 (policies.with_usage 가 채움)
    # OCR·이미지 근거 재현용 (2026-11-03 p29, 없으면 None): 원본 해시 · 원본 좌표(x1,y1,x2,y2 px) · 엔진 · 정규화 전 원문
    asset_sha256: Optional[str] = None
    bbox_xyxy_px: Optional[list[float]] = None
    engine: Optional[str] = None
    raw_text: Optional[str] = None
    policy_version: Optional[str] = None


class Product(_Model):
    product_id: Optional[str] = None         # 기존 식별자(카드 pid).  canonical id 는 아직 정하지 않음
    key: str                                 # 기존 카드 key (explain.card_key) — 웹 /go 와 같은 값
    title: str
    image_url: Optional[str] = None
    weight_g: Optional[float] = None
    unit_count: Optional[int] = None
    seller_claims: list[str] = Field(default_factory=list)   # 판매자 표기 (근거 아님)


class Offer(_Model):
    platform: str                            # 화면의 mall (쿠팡 · naver · 네이버 (쇼핑커넥트) …)
    merchant: Optional[str] = None           # 입점 판매자 · 스토어
    product_url: Optional[str] = None        # 안전한 http(s) 주소만 (policies.safe_url)
    price_krw: int
    shipping_krw: Optional[int] = None       # None = 미확인
    total_krw: Optional[int] = None          # 배송비 미확인이면 None
    per100g_krw: Optional[int] = None
    per_unit_krw: Optional[int] = None
    rocket: Optional[bool] = None
    free_shipping: Optional[bool] = None
    link_type: Literal["affiliate", "direct", "partner"] = "direct"
    affiliate_program: Optional[str] = None
    opens_directly: bool = False             # 쇼핑커넥트: 발급 링크로 곧장 이동 (/go 경유 없음 → 자체 클릭 집계 누락)
    seen_at: Optional[str] = None            # 저장·등록된 가격의 확인 시각
    check_at_mall: bool = True


class ScoreReason(_Model):
    text: str
    basis: str                               # calc · mall · you · public(KAMIS) · partner …


class ScoreDetail(_Model):
    """선택 이유.  /api/chat 의 순위는 explain.choose(역할별 선택)이 정한다."""
    rank: int
    role: Optional[str] = None               # value · lowest · fast · ample · gift · alt (None = 다른 후보)
    role_label: Optional[str] = None
    reasons: list[ScoreReason] = Field(default_factory=list)
    engine: str = "chat.explain.choose"
    engine_score: Optional[float] = None     # explicit final_score/v8_final_score only; upstream order can affect display
    # Upstream scores keep their original names; none is assumed to be the displayed rank score.
    upstream_scores: dict[str, float] = Field(default_factory=dict)
    upstream_rank: Optional[int] = None
    fallback_used: Optional[bool] = None      # None = provider path not supplied / not applicable


class Disclosure(_Model):
    has_affiliate: bool
    programs: list[str] = Field(default_factory=list)
    text_ko: Optional[str] = None
    note: str = "응답에 고지를 포함할 뿐, 외부 에이전트의 최종 화면 표시는 보장하지 않음"


class ShoppingItem(_Model):
    section: Literal["picks", "others", "partner_list", "connect"]
    product: Product
    offer: Offer
    score: ScoreDetail
    evidence: list[Evidence] = Field(default_factory=list)
    price_reference: Optional[dict] = None   # KAMIS 시세 참고 (순위·역할에 쓰지 않음)


class RecipeIngredient(_Model):
    name: str
    amount: str = ""
    quantity_known: bool = False
    source_kind: str = "ingredient_table"    # ingredient_table · step_only


class RecipeStep(_Model):
    text: str
    image_url: Optional[str] = None


class RecipeItem(_Model):
    recipe_id: str
    title: str
    summary: str = ""
    source_name: str
    source_level: Literal["source", "ai_suggestion"]   # ai_suggestion = 'AI 제안 레시피' (원문 아님)
    provider: str
    meta: list[str] = Field(default_factory=list)
    ingredients: list[RecipeIngredient] = Field(default_factory=list)
    steps: list[RecipeStep] = Field(default_factory=list)
    tips: list[str] = Field(default_factory=list)
    content_hash: str
    citation: str                            # 화면 한 줄 출처 표기


class Followup(_Model):
    kind: Literal["budget", "choose_recipe", "clarify"]
    question: str
    options: list[dict] = Field(default_factory=list)   # {"id", "label"}


class CommerceError(_Model):
    code: str
    message: str
    scope: Literal["all", "source"] = "all"
    source: Optional[str] = None


class Provenance(_Model):
    sources: list[str] = Field(default_factory=list)
    engine: Optional[str] = None
    recommendation_path: Optional[str] = None  # actual provider branch, not inferred from scores
    preview_data: bool = False                 # p37: 업체 미리 보기(예시) 상품이 결과에 들어갔는지 (명시 값)
    query: Optional[str] = None
    terms: Optional[list[str]] = None


class CommerceResult(_Model):
    schema_version: str = SCHEMA_VERSION
    request_id: str
    status: Status
    items: list = Field(default_factory=list)            # ShoppingItem | RecipeItem
    followup: Optional[Followup] = None
    warnings: list[str] = Field(default_factory=list)
    disclosure: Optional[Disclosure] = None
    provenance: Provenance = Field(default_factory=Provenance)
    errors: list[CommerceError] = Field(default_factory=list)
