"""쇼핑커넥트 링크 등록부 CSV 관리 (2026-11-17) — 관리자 화면에서 링크를 입력·삭제하면 이 파일에 바로 쓴다.

파일: .env NAVER_CONNECT_REGISTRY_CSV (기본 data/naver_connect_links.csv, 저장소 기준 상대 경로).
화면(chat.service.registry_links)·블로그 초안 점검·발급 요청 정리가 모두 이 파일을 읽는다.
머리줄(열 이름)은 기존 파일 그대로 따른다. 지울 때는 바로 전 상태를 .bak 로 한 벌 남긴다.
"""
from __future__ import annotations

import csv
import io
import os
import shutil
import threading
from datetime import datetime, timedelta, timezone
from pathlib import Path

from app.services.affiliate.naver_shopping_connect import validate_link, validate_product

ROOT = Path(__file__).resolve().parents[3]
KST = timezone(timedelta(hours=9))
HEADER = ["상품명", "스토어명", "판매가", "정가", "수수료율(%)", "링크 발급일", "쇼핑커넥트 링크", "키워드", "링크 확인일",
          "사용처(블로그/사이트)", "메모"]
_LOCK = threading.Lock()


def path(env=None) -> Path:
    source = os.environ if env is None else env
    raw = (source.get("NAVER_CONNECT_REGISTRY_CSV") or "").strip() or "data/naver_connect_links.csv"
    p = Path(raw).expanduser()
    return p if p.is_absolute() else ROOT / p


def _today() -> str:
    d = datetime.now(KST).date()
    return f"{d.year}.{d.month}.{d.day}"           # 기존 파일 표기 ('2026.11.2')


def _read(p: Path) -> tuple[list[str], list[dict]]:
    if not p.is_file():
        return list(HEADER), []
    with open(p, encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        header = list(reader.fieldnames or HEADER)
        return header, [dict(r) for r in reader]


def _write(p: Path, header: list[str], rows: list[dict]) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=header, extrasaction="ignore")
    w.writeheader()
    for r in rows:
        w.writerow({k: r.get(k, "") for k in header})
    tmp = p.with_suffix(p.suffix + ".tmp")
    tmp.write_text("﻿" + buf.getvalue(), encoding="utf-8", newline="")
    os.replace(tmp, p)


def rows(env=None) -> list[dict]:
    _, out = _read(path(env))
    return out


def _clean_price(v) -> str:
    s = "".join(ch for ch in str(v or "") if ch.isdigit())
    return s


def add(items: list[dict], env=None, owner_of=None) -> dict:
    """items: [{keyword, product_name, store_name, price, discount_price, link, commission_rate, memo}] → {'added', 'rejected'}.
    상품명·발급 링크(naver.me·brandconnect)가 맞아야 하고, 이미 있는 링크는 다시 넣지 않는다.
    가격 (2026-11-17, 브랜드커넥트 화면과 맞춤): 화면의 '판매가'(할인 전) = price, '할인가' = discount_price.
    등록부 '판매가' 열에는 실제 파는 값(할인가가 있으면 할인가), '정가' 열에는 할인이 있을 때 할인 전 값을 적는다.
    owner_of(link) → {title, mall} | None (2026-11-18): 브랜드커넥트 수집분이 이 링크를 다른 상품 것으로 알면 막는다
    (한 상품 링크를 다른 상품 줄에 붙여 넣는 실수 방지)."""
    p = path(env)
    added, rejected = [], []
    with _LOCK:
        header, current = _read(p)
        for col in HEADER:                      # 예전 파일에 없는 열이 있으면 뒤에 붙인다
            if col not in header:
                header.append(col)
        have = {(r.get("쇼핑커넥트 링크") or "").strip() for r in current}
        for i, it in enumerate(items, start=1):
            name = (it.get("product_name") or "").strip()
            link = (it.get("link") or "").strip()
            reason = ((not name and "상품명이 없어요") or (not link and "링크가 없어요")
                      or validate_link(link) or validate_product(name))
            if not reason and link in have:
                reason = "이미 등록된 링크예요"
            if not reason and owner_of is not None:
                from app.services.affiliate.brandconnect_finder import same_product
                owner = owner_of(link)
                if owner and not same_product(owner.get("title") or "", name):
                    reason = f"이 링크는 브랜드커넥트에서 '{owner.get('title')}'({owner.get('mall') or '판매처 모름'}) 상품 링크예요"
            if reason:
                rejected.append({"row": i, "product_name": name, "reason": reason})
                continue
            row = {"상품명": name[:200], "스토어명": (it.get("store_name") or "").strip()[:80],
                   "판매가": _clean_price(it.get("discount_price")) or _clean_price(it.get("price")),
                   "정가": _clean_price(it.get("price")) if _clean_price(it.get("discount_price")) else "",
                   "수수료율(%)": "".join(ch for ch in str(it.get("commission_rate") or "") if ch.isdigit() or ch == ".")[:8],
                   "링크 발급일": _today(), "쇼핑커넥트 링크": link,
                   "키워드": (it.get("keyword") or "").strip()[:60], "링크 확인일": _today(),
                   "사용처(블로그/사이트)": "블로그", "메모": (it.get("memo") or "").strip()[:200]}
            current.append(row)
            have.add(link)
            added.append(row)
        if added:
            _write(p, header, current)
    return {"added": added, "rejected": rejected, "file": str(p)}


def delete(link: str, env=None) -> bool:
    p = path(env)
    with _LOCK:
        header, current = _read(p)
        keep = [r for r in current if (r.get("쇼핑커넥트 링크") or "").strip() != link.strip()]
        if len(keep) == len(current):
            return False
        shutil.copy2(p, p.with_suffix(p.suffix + ".bak"))
        _write(p, header, keep)
    return True
