"""서비스 입력.  어댑터(REST·MCP)는 자기 형식을 이 모델로 바꿔서 서비스를 부른다."""
from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class SearchRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    text: str = Field(..., min_length=1, max_length=500)    # 고객 문장 그대로 ('5만원 이하 한우 등심')
    priority: Optional[str] = None                          # None → 기존 규칙(_priority)과 같은 판정
    session_id: Optional[str] = Field(None, max_length=64)
    limit: int = Field(10, ge=1, le=10)                     # /api/chat MAX_PRODUCTS


class RecipeRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    recipe_id: Optional[str] = Field(None, max_length=64)
    dish_name: Optional[str] = Field(None, max_length=100)
