"""업체 제공 상품 (2026-11-02) — data/partners/ 의 허락 기록부와 업체 CSV 를 읽는다.

원칙
* 페이지를 수집하지 않는다. 업체가 보내 주거나 서면으로 허락한 파일만 읽는다.
* 허락 기록부(permissions.csv) 칸이 '허용'일 때만 그 용도로 쓴다. '미확인'·'불가'·빈칸은 쓰지 않는다.
    - 상품 표시=허용        → 화면에 보여 준다 (별도 목록)
    - 가격 비교·순위 계산=허용 → 쿠팡 등 후보와 같은 기준으로 견준다 (같은 목록)
    - 이미지 표시=허용       → 대표 이미지를 보여 준다
    - 외부 AI 전송: 이 모듈의 데이터는 어떤 외부 AI 요청에도 넣지 않는다 (허용이어도 지금은 쓰지 않음)
* 미리 보기(PARTNER_PREVIEW=1, 개발용): 허락 전 업체도 products_sample.csv 의 '예시' 데이터로 화면 모양만 보여 준다.
  업체 문의용 화면을 만들 때만 켠다 — 실제 운영에서는 끈다.
"""
from __future__ import annotations

import csv
import os
import re
from pathlib import Path
from typing import Callable

_ROOT = Path(__file__).resolve().parents[3]
OK = "허용"
FIELDS = {"display": "상품 표시", "image": "이미지 표시", "compare": "가격 비교·순위 계산",
          "external_ai": "외부 AI 전송", "training": "AI 학습",
          # 2026-11-03 p29: 업체 제공 이미지의 문자 판독(OCR) — '이미지 표시' 허락과 별개. 열이 없으면 허락 없음
          "ocr": "이미지 문자 판독(OCR)"}
FOLDERS = {"온브릭스": "onbrix", "미트프렌즈": "meatfriends", "한우이츠": "hanwooeats", "현덕축산": "hyundeok",
           "도드람몰": "dodrammall", "딜리셔스마켓": "deliciousmarket", "새농": "saenong"}


def data_dir() -> Path:
    return Path(os.getenv("PARTNER_DATA_DIR") or (_ROOT / "data" / "partners"))


def preview_on() -> bool:
    return (os.getenv("PARTNER_PREVIEW") or "0").strip() == "1"


def _clean(row: dict, fields: list[str]) -> dict:
    """한 줄 → {칸: 값}.  따옴표 없이 쉼표가 들어가 칸이 넘친 줄(2026-11-04 딜리셔스마켓 메모)은
    넘친 내용을 마지막 칸에 ', ' 로 이어 붙인다 — 멈추지도, 내용을 버리지도 않는다."""
    extra = row.pop(None, None)
    out = {(k or "").strip(): (v or "").strip() if isinstance(v, str) else "" for k, v in row.items()}
    if extra and fields:
        last = (fields[-1] or "").strip()
        out[last] = ", ".join([out.get(last, "")] + [str(x).strip() for x in extra if str(x).strip()]).strip(", ")
    return out


def _read(path: Path) -> list[dict]:
    try:
        with open(path, encoding="utf-8-sig", newline="") as f:
            reader = csv.DictReader(f)
            return [_clean(row, reader.fieldnames or []) for row in reader]
    except OSError:
        return []


def permissions() -> dict[str, dict]:
    return {r["업체"]: r for r in _read(data_dir() / "permissions.csv") if r.get("업체")}


def allowed(perm: dict, use: str) -> bool:
    return (perm.get(FIELDS[use]) or "") == OK


def _product_file(folder: Path, preview: bool) -> Path | None:
    real = sorted(p for p in folder.glob("products_*.csv") if re.fullmatch(r"products_\d{8}\.csv", p.name))
    if real:
        return real[-1]
    sample = folder / "products_sample.csv"
    return sample if preview and sample.exists() else None


def _int(v) -> int | None:
    try:
        return int(float(re.sub(r"[^\d.]", "", str(v)) or "x"))
    except ValueError:
        return None


def _title(row: dict) -> str:
    name = row.get("상품명") or ""
    extra = []
    if row.get("중량(g)") and not re.search(r"\d\s*(kg|g)\b", name, re.I):
        g = _int(row["중량(g)"])
        if g:
            extra.append(f"{g / 1000:g}kg" if g >= 1000 else f"{g}g")
    return " ".join([name] + extra)


def offers(match: Callable[[str], bool], *, preview: bool | None = None) -> list[dict]:
    """허락된 업체의 관련 상품 → 추천 항목(dict).  partner_mode: 'compare'(같이 견줌) | 'list'(별도 목록).
    preview: 미리 보기(허락 전·예시) 상품 포함 여부 — None 이면 PARTNER_PREVIEW 설정, 호출한 쪽이 정하면 그 값 (p37)."""
    out: list[dict] = []
    preview = preview_on() if preview is None else bool(preview)
    for name, perm in permissions().items():
        granted = (perm.get("상태") == "허락") and allowed(perm, "display")
        if not granted and not preview:
            continue
        is_preview = not granted
        folder = data_dir() / FOLDERS.get(name, name)
        path = _product_file(folder, is_preview)
        if path is None:
            continue
        is_sample = path.name == "products_sample.csv"
        if is_sample and not preview:
            continue
        for row in _read(path):
            title = _title(row)
            url = row.get("상품URL") or ""
            price = _int(row.get("판매가"))
            if not title or not price or not url.startswith("https://") or row.get("재고상태") in ("품절", "판매중지"):
                continue
            if not (match(title) or match(" ".join(filter(None, [row.get("품목"), row.get("품종")])))):
                continue
            ship = _int(row.get("배송비"))
            out.append({
                "product_name": title,
                "price": price,
                "original_price": _int(row.get("정가")),
                "shipping_fee": ship if row.get("배송비") != "" else None,
                "product_url": url,
                "thumbnail_url": row.get("이미지URL") if (is_preview or allowed(perm, "image")) else None,
                "platform_name": name + (" (예시)" if is_sample else ""),
                "seller_name": name,
                "product_id": row.get("상품ID") or None,
                "partner": name,
                "partner_preview": is_preview or is_sample,
                "partner_mode": "compare" if (is_preview or allowed(perm, "compare")) else "list",
                "partner_seen_at": row.get("가격기준일시") or "",
                "partner_claims": [f"당도 {row['당도(Brix)']}Brix" for _ in [0] if row.get("당도(Brix)")]
                                  + [f"등급 {row['등급']}" for _ in [0] if row.get("등급") and row.get("품목") in ("소", "돼지", "한우", "한돈")]
                                  + [f"산지 {row['산지']}" for _ in [0] if row.get("산지")],
            })
    return out


def note_line(item: dict) -> dict:
    """카드의 '왜 추천했나요'에 붙이는 출처 한 줄 (판매처 표시)."""
    seen = item.get("partner_seen_at") or "미기재"
    claims = " · ".join(item.get("partner_claims") or [])
    text = f"{item['partner']} 제공 정보 (가격 기준 {seen}{' · ' + claims if claims else ''}, 업체 표기)"
    if item.get("partner_preview"):
        text = "미리 보기 예시 데이터 — " + text
    return {"text": text, "basis": "mall"}
