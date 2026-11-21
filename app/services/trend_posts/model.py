"""트렌드 글 한 편 (파일 한 개).  가격은 상품 칸에만, 확인 시각과 함께 둔다 — 본문 문장에는 가격을 쓰지 않는다."""
from __future__ import annotations

import re
import unicodedata
from datetime import datetime, timedelta, timezone
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

KST = timezone(timedelta(hours=9))
Status = Literal["draft", "pending", "approved", "rejected", "withdrawn"]
STATUS_LABEL = {"draft": "초안", "pending": "검토 대기", "approved": "게시됨", "rejected": "반려", "withdrawn": "내림"}
EDITABLE = {"draft", "rejected"}


class _M(BaseModel):
    model_config = ConfigDict(extra="forbid")


class PostProduct(_M):
    title: str
    url: str
    platform: str = "쿠팡"
    link_type: Literal["affiliate", "direct", "partner"] = "affiliate"
    affiliate_program: Optional[str] = "쿠팡 파트너스"
    price_krw: Optional[int] = None
    price_checked_at: Optional[str] = None      # ISO 시각 — 없으면 가격을 그리지 않는다
    rocket: Optional[bool] = None
    keyword: Optional[str] = None               # 어떤 재료·검색어로 찾은 상품인지
    image_url: Optional[str] = None             # 2026-11-17: 쿠팡 상품 사진 (쿠팡 https 주소만, 없으면 사진 없이)
    facts: list[str] = Field(default_factory=list)  # 2026-11-20 프레임 0.4: 근거 줄 ('중량·수량: 500g (상품명 표기)')


class PostSource(_M):
    kind: Literal["data", "blog", "video", "recipe"] = "data"
    label: str
    url: Optional[str] = None


class PostRecipe(_M):
    name: str
    source_label: str                            # 예: 농식품정보누리(EPIS)
    source_url: Optional[str] = None
    recipe_id: Optional[str] = None
    ingredients: list[str] = Field(default_factory=list)
    step_count: int = 0
    note: str = "공공 레시피를 참고했으며 원문 그대로가 아니에요."


class PostSection(_M):
    """2026-11-20 템플릿 절 (소제목 + 줄). 템플릿 번호는 Post.template."""
    heading: str
    items: list[str] = Field(default_factory=list)


class PostImage(_M):
    """2026-11-20 대표 그림 — 보류 글의 AI 그림 (var/trend_images/<file>). 구매 글은 따로 저장하지 않고
    상품 사진(쿠팡) 중 첫 장을 대표로 그린다."""
    file: str                                    # 예: 2026-11-19-페레로로쉐.webp (VALID_IMAGE, 예전 글은 .png)
    kind: Literal["ai"] = "ai"
    caption: str = "AI로 만든 그림 · 실제 상품 사진이 아니에요"
    created_at: Optional[str] = None


class HistoryEntry(_M):
    at: str
    action: str                                  # create · update · submit · approve · reject · withdraw · refresh
    note: Optional[str] = None


class Post(_M):
    id: str                                      # 주소 조각: {날짜}-{주제}
    topic: str
    data_until: Optional[str] = None
    title: str
    summary: str = ""
    why: list[str] = Field(default_factory=list)           # 트렌드 이유 (데이터 사실 · 추정은 '추정'으로)
    recipe: Optional[PostRecipe] = None
    products: list[PostProduct] = Field(default_factory=list)
    price_note: str = "가격은 확인한 시각 기준이에요. 지금은 다를 수 있으니 판매처에서 확인해 주세요."
    sources: list[PostSource] = Field(default_factory=list)
    disclosure: Optional[str] = None             # 제휴 상품이 있으면 본문 맨 위 고지
    # 2026-11-20 프레임 0.4 (고지 → 질문과 조건부 답 → 선택 기준 → 근거 붙은 상품 → 구매 전 제약 → 확인 링크).
    # 예전 글에는 없는 칸 — 비어 있으면 예전 모양으로 그린다.
    experience: Literal["direct", "data"] = "data"   # direct = 직접 사용 기록이 있을 때만
    question: Optional[str] = None
    answer: list[str] = Field(default_factory=list)
    criteria: list[str] = Field(default_factory=list)
    constraints: list[str] = Field(default_factory=list)
    checklist: Optional[str] = None
    template: Optional[str] = None               # 글 틀 번호 (55종 중 자동 8종: 01·03·05·06·14·26·28·32)
    topic_kind: Optional[str] = None             # 주제 (frame.keyword_type: kimjang·seasonal·seollal·… )
    sections: list[PostSection] = Field(default_factory=list)
    conclusion: Literal["buy", "hold"] = "buy"   # 2026-11-20 hold = 구매 보류 결론 — 구매 링크·광고 고지 없음
    cover: Optional[PostImage] = None            # 2026-11-20 보류 글 대표 그림 (AI). 구매 글은 상품 사진으로 그린다
    # 2026-11-21 보고서형 (report.py). format 이 비어 있으면 예전 글 — 질문·답이 있으면 프레임 0.4, 없으면 첫 형식.
    format: Optional[Literal["frame04", "report"]] = None
    rules_version: Optional[str] = None          # 글을 만든 규칙 판 (예: 'report v1.0') — 피드백 집계 묶음
    summary_lines: list[str] = Field(default_factory=list)   # 요약 3줄: 무엇이 · 얼마나 · 왜
    data_change: list[str] = Field(default_factory=list)     # ① 관심 변화
    data_events: list[str] = Field(default_factory=list)     # ① 확인된 관련 행사·보도 (출처 있는 것만)
    data_reading: list[str] = Field(default_factory=list)    # ① 가능한 해석 (추정이라고 밝힘)
    data_unknown: list[str] = Field(default_factory=list)    # ① 확인되지 않은 부분
    status: Status = "draft"
    created_at: str
    updated_at: str
    submitted_at: Optional[str] = None
    approved_at: Optional[str] = None
    reviewer_note: Optional[str] = None
    history: list[HistoryEntry] = Field(default_factory=list)


def now_iso(now: datetime | None = None) -> str:
    return (now or datetime.now(timezone.utc)).astimezone(timezone.utc).isoformat(timespec="seconds")


def parse_time(v) -> datetime | None:
    if not v:
        return None
    try:
        t = datetime.fromisoformat(str(v).replace("Z", "+00:00"))
    except ValueError:
        return None
    return t if t.tzinfo else t.replace(tzinfo=timezone.utc)


_SLUG_BAD = re.compile(r"[^0-9a-z가-힣]+")


def topic_slug(topic: str) -> str:
    s = _SLUG_BAD.sub("-", unicodedata.normalize("NFC", topic or "").lower()).strip("-")
    return s[:40] or "trend"


def post_id(day: str, topic: str) -> str:
    return f"{day}-{topic_slug(topic)}"


VALID_IMAGE = re.compile(r"^\d{4}-\d{2}-\d{2}-[0-9a-z가-힣-]{1,40}(?:-\d+)?\.(?:png|webp)$")   # v1.1: webp
VALID_ID = re.compile(r"^\d{4}-\d{2}-\d{2}-[0-9a-z가-힣-]{1,40}$")
