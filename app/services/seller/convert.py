"""판매처 엑셀 변환기 (창 5, 2026-11-26) — 판매처에서 내려받은 상품 파일(엑셀·CSV)을 그대로 받아 표준 칸으로.

* 받는 파일: 스마트스토어 '상품 조회/수정' 다운로드(.xlsx 또는 .csv, UTF-8·EUC-KR), 우리 표준 칸 CSV.
  모르는 양식이면 찾은 칸 이름을 알려 주고 멈춘다(추측해서 넣지 않음).
* 미리보기만 한다 — 저장은 셀러가 '반영하기'를 눌러야(기존 따라가기 경로: 바뀐 칸만, 확인 필요 칸은 검수).
* '같은 상품끼리 묶기': 그룹상품번호가 없는 스마트스토어 상품 중 이름이 같고 용량만 다른 것(200ml·500ml·1L…)을
  한 그룹 + 판매 단위로 묶는다(네이버 그룹상품·쿠팡 옵션처럼). 같은 용량이 겹치면 묶지 않는다.
* 파일은 서버에 남기지 않는다(메모리에서 읽고 버림).
"""

from __future__ import annotations

import base64
import csv
import io

from app.services.seller import catalog, store

MAX_BYTES = 5 * 1024 * 1024
FORMATS = {"naver_export": "스마트스토어 상품 조회 파일", "std": "표준 칸 CSV"}


class ConvertError(store.SellerError):
    pass


def _xlsx_to_csv(raw: bytes) -> str:
    from openpyxl import load_workbook

    try:
        wb = load_workbook(io.BytesIO(raw), read_only=True, data_only=True)
    except Exception as e:  # noqa: BLE001
        raise ConvertError(
            "엑셀 파일을 열지 못했어요 (.xlsx 만 — 옛 .xls 는 엑셀에서 .xlsx 나 CSV 로 저장해 주세요)"
        ) from e
    ws = wb.worksheets[0]
    out = io.StringIO()
    w = csv.writer(out)
    head_seen = False
    for row in ws.iter_rows(values_only=True):
        vals = ["" if v is None else (str(int(v)) if isinstance(v, float) and v.is_integer() else str(v)) for v in row]
        if not head_seen:
            if sum(1 for v in vals if v.strip()) < 3:  # 위쪽 안내 줄은 건너뛴다
                continue
            head_seen = True
        w.writerow(vals)
    wb.close()
    return out.getvalue()


def read_file(filename: str, data: str) -> str:
    """업로드(base64 또는 data URL) → CSV 글."""
    data = (data or "").split(",", 1)[-1] if (data or "").startswith("data:") else (data or "")
    try:
        raw = base64.b64decode(data, validate=True)
    except ValueError:
        raise ConvertError("파일을 읽지 못했어요") from None
    if not raw:
        raise ConvertError("파일을 골라 주세요")
    if len(raw) > MAX_BYTES:
        raise ConvertError("5MB 까지 올릴 수 있어요")
    name = (filename or "").lower()
    if raw[:4] == b"PK\x03\x04" or name.endswith(".xlsx"):
        return _xlsx_to_csv(raw)
    if raw[:8] == b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1" or name.endswith(".xls"):
        raise ConvertError(
            "옛 엑셀(.xls)은 읽지 못해요 — 엑셀에서 '다른 이름으로 저장 → .xlsx 또는 CSV'로 바꿔 올려 주세요"
        )
    for enc in ("utf-8-sig", "cp949"):
        try:
            return raw.decode(enc)
        except UnicodeDecodeError:
            continue
    raise ConvertError("글자 인코딩을 알 수 없어요 (UTF-8 또는 EUC-KR CSV)")


def detect(text: str) -> tuple[str, list[str]]:
    heads = [h.strip() for h in (next(csv.reader(io.StringIO(text.lstrip("﻿"))), None) or [])]
    if catalog.is_naver_export(heads):
        return "naver_export", heads
    if "상품번호" in heads and "상품명" in heads and all(h in catalog.STD_HEADERS for h in heads if h):
        return "std", heads
    raise ConvertError("아직 모르는 판매처 양식이에요. 찾은 칸: " + ", ".join(h for h in heads[:12] if h)
                       + (" …" if len(heads) > 12 else "") + " — 스마트스토어 상품 조회 파일이나 표준 칸 CSV 를 올려 주세요")  # fmt: skip


def preview(eng, token: str, client: str, filename: str, data: str, *, group_same: bool = True) -> dict:
    """변환 미리보기 — 아무것도 저장하지 않는다. {format, label, csv, rows, groups, notes, sample}"""
    s = store.resolve(eng, token, client)
    text = read_file(filename, data)
    fmt, heads = detect(text)
    if fmt == "std":
        n = max(0, len([ln for ln in text.splitlines() if ln.strip()]) - 1)
        return {"format": fmt, "label": FORMATS[fmt], "csv": text, "rows": n, "groups": [], "notes": [], "sample": []}
    slug = catalog.store_slug(catalog.store_urls(eng).get(s["seller_id"]))
    rows, notes = catalog.naver_export_rows(text, store_slug=slug, group_same=group_same)
    groups = [{"name": g["name"], "units": g["units"]} for g in (notes.get("groups") or {}).values()]
    msgs = [x for x in [
        f"옵션이 있는 상품 {len(notes['option_products'])}개는 옵션별 가격·재고가 파일에 없어 대표 가격 한 줄로 들어가요." if notes["option_products"] else "",
        "이 파일에는 원산지가 없어요 — 식품이면 원산지를 적어 주세요(검수 때 필요)." if notes["no_origin"] and rows and any("식품" in r["category"] for r in rows) else "",
        f"판매중지·전시중지 상품 {notes['off']}개는 판매 꺼짐으로 들어가요." if notes["off"] else "",
        f"http 사진 주소 {notes['http_images']}개는 안전하지 않아 비웠어요." if notes["http_images"] else "",
        "" if slug else "판매처 링크는 운영팀이 몰 주소를 넣으면 채워져요.",
    ] if x]  # fmt: skip
    sample = [{"ext_no": r["ext_no"], "name": r["name"], "volume": r["volume"], "option": r["option"], "price": r["price"],
               "stock": r["stock"], "on": r["display"] == "", "group": r["group_name"] if r["group_no"] else ""}
              for r in rows[:50]]  # fmt: skip
    return {
        "format": fmt,
        "label": FORMATS[fmt],
        "csv": text,
        "rows": len(rows),
        "groups": groups,
        "notes": msgs,
        "sample": sample,
    }


__all__ = ["ConvertError", "detect", "preview", "read_file"]
