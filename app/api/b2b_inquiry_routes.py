"""B2B 문의 창구 — 공개 문의 페이지와 접수 API (2026-11-24). 설계 claude/b2b_inquiry_desk_2026-11-24.md.

  GET  /biz/api/faq          자주 묻는 질문 (공통 B2B 매뉴얼)
  GET  /biz/inquiry          임직원 선물 문의 페이지 (사업자등록·공개 결정 전까지 검색 노출 막음)
  POST /biz/api/inquiry      접수 → 접수 번호

운영자 화면·API 는 app/admin/routes.py (/admin/b2b/inquiries, /admin/api/b2b-inquiry/...).
"""

from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Request
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, ConfigDict, Field

from app.api.corpmall_routes import NOINDEX, _client
from app.services.b2b_inquiry import store

router = APIRouter(tags=["b2b-inquiry"], include_in_schema=False)
PAGE = Path(__file__).resolve().parents[1] / "services" / "b2b_inquiry" / "web" / "inquiry.html"


class InquiryIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    company: str = Field("", max_length=60)
    kind: str = Field("company", max_length=20)
    occasion: str = Field("기타", max_length=10)
    due_date: str = Field("", max_length=10)
    headcount: str = Field("", max_length=10)
    budget_per_person: str = Field("", max_length=12)
    delivery: str = Field("undecided", max_length=12)
    notice_url: str = Field("", max_length=300)
    message: str = Field("", max_length=1500)
    website: str = Field("", max_length=50)  # 숨은 칸 (봇)
    contact_name: str = Field("", max_length=30)
    email: str = Field("", max_length=120)
    phone: str = Field("", max_length=20)
    consent: bool = False


@router.get("/biz/inquiry")
def inquiry_page():
    return FileResponse(PAGE, headers=NOINDEX)


@router.get("/biz/api/faq")
def inquiry_faq():
    """자주 묻는 질문 — 공통 B2B 매뉴얼(app/services/corpmall/manual.py)에서. 가격·견적은 사람이 답한다."""
    from app.services.corpmall import manual

    return JSONResponse({"faq": [{"q": q, "a": a} for q, a in manual.BUYER_FAQ]}, headers=NOINDEX)


@router.post("/biz/api/inquiry")
def inquiry_submit(body: InquiryIn, request: Request):
    try:
        got = store.submit(store.engine(), body.model_dump(), _client(request))
    except store.InquiryError as e:
        return JSONResponse({"ok": False, "error": str(e)}, status_code=400, headers=NOINDEX)
    return JSONResponse({"ok": True, "inquiry_id": got["inquiry_id"], "masked": got["masked"]}, headers=NOINDEX)
