"""제안서 상품 구성안의 상품 이미지 (2026-11-17).

고르는 순서
1. 공급사가 준 이미지 — <ADMIN_DATA_DIR>/proposal_assets/_products/ 에 '<후보 ID>.jpg' 또는 '<상품명>.jpg' 로 넣은 파일.
   사용 허락이 있는 이미지로 보고 제출본·내부 검토본 모두에 넣는다.
2. 판매처·도매몰 상품 이미지 (후보의 image_url — 쿠팡·네이버 검색, 도매꾹 썸네일) — 사용 허락을 확인하지 않았으므로
   **내부 검토본에만** '사용 허락 확인 필요' 표시와 함께 넣는다. 제출본에는 넣지 않는다.
3. 없으면 None → 슬라이드는 품목에 맞는 예시 그림(학습한 일러스트)과 '공급사 이미지 확정 후 교체' 문구를 쓴다.
내려받은 이미지는 _cache/ 에 저장해 다시 쓰고(https 만, 5MB 이하, 이미지인지 확인), 실패해도 제안서는 만든다.
"""
from __future__ import annotations

import hashlib
import io
import re
from pathlib import Path

from app.admin.shared.config import data_dir

EXTS = (".jpg", ".jpeg", ".png", ".webp")
MAX_BYTES = 5 * 1024 * 1024


def folder() -> Path:
    return data_dir() / "proposal_assets" / "_products"


def cache_dir() -> Path:
    return data_dir() / "proposal_assets" / "_cache"


def _slug(s: str) -> str:
    return re.sub(r"[\s/\\:*?\"<>|]+", "_", (s or "").strip())[:80]


def supplier_image(candidate_id: str | None, name: str | None) -> Path | None:
    d = folder()
    if not d.exists():
        return None
    for stem in (candidate_id, _slug(name or "")):
        if not stem:
            continue
        for ext in EXTS:
            f = d / f"{stem}{ext}"
            if f.is_file():
                return f
    return None


def download(url: str, timeout: float = 6.0) -> Path | None:
    """원격 이미지를 JPEG(최대 900px)로 캐시. 실패하면 None."""
    if not url or not url.startswith("https://"):
        return None
    out = cache_dir() / (hashlib.sha1(url.encode()).hexdigest()[:20] + ".jpg")
    if out.is_file():
        return out
    try:
        import httpx
        from PIL import Image

        r = httpx.get(url, timeout=timeout, follow_redirects=True, headers={"User-Agent": "commerce_ai-proposal/1.0"})
        if r.status_code != 200 or not r.headers.get("content-type", "").startswith("image/") or len(r.content) > MAX_BYTES:
            return None
        with Image.open(io.BytesIO(r.content)) as im:
            im = im.convert("RGB")
            im.thumbnail((900, 900))
            out.parent.mkdir(parents=True, exist_ok=True)
            im.save(out, "JPEG", quality=86)
        return out
    except Exception:  # noqa: BLE001 — 이미지가 없어도 제안서는 만든다
        return None


def resolve(c, mode: str) -> dict | None:
    """후보(Candidate) 한 개의 이미지 → {'path', 'source', 'label'} 또는 None."""
    f = supplier_image(getattr(c, "candidate_id", None), getattr(c, "name", None))
    if f:
        return {"path": str(f), "source": "supplier", "label": ""}
    if mode != "internal":
        return None                                    # 제출본: 사용 허락 확인 전 이미지는 넣지 않는다
    url = getattr(c, "image_url", None)
    if url and (p := download(url)):
        src = getattr(c, "image_source", None) or "retail"
        return {"path": str(p), "source": src, "label": "판매처 이미지 · 사용 허락 확인 필요"}
    return None
