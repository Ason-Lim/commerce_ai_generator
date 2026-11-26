"""상세 이미지 글자 읽기 (2026-11-26) — 상품정보제공고시 칸 채우기 도우미.

* 셀러가 고른 상세 이미지(사진 주소 또는 파일 한 장)를 이 서버의 Tesseract 로 읽는다(외부 AI·외부 OCR 전송 없음).
* 읽은 글에서 '원산지 : 국산' 같은 줄을 찾아 **빈 고시 칸의 후보**만 돌려준다. 저장하지 않는다 —
  셀러가 보고 고른 것만 입력 칸에 들어가고, 저장·검수는 지금과 같다(판매자 표기, 운영자 확인).
* 이미지와 읽은 글은 남기지 않는다(처리 뒤 바로 버림). 기록에는 개수만.
* 효능·단정 표현이 이미지 글에 있으면 알려 준다(검수에서 볼 수 있음) — 자동으로 막거나 고치지 않는다.
* 사진 주소는 https 이고 공인 IP 인 곳만 받는다(내부망 주소 차단), 10MB·리다이렉트 없음.
"""

from __future__ import annotations

import ipaddress
import re
import socket
import tempfile
from pathlib import Path
from urllib.parse import urlparse

from app.services.seller import detail_page, store

MAX_BYTES = 10 * 1024 * 1024
MAX_IMAGES = 5
TILE_H = 2400  # 상세 이미지는 세로로 길다 — 잘라서 읽는다
MAX_TILES = 12
DAILY = 30

# 고시 칸 → 이미지에 흔히 쓰는 이름표 (긴 것 먼저)
LABELS: dict[str, tuple[str, ...]] = {
    "origin": ("원산지",),
    "ingredients": ("원재료명 및 함량", "원재료명및함량", "원재료명", "원재료"),
    "producer": ("생산자 및 소재지", "제조원 및 소재지", "생산자", "제조원", "제조사", "제조업소", "생산자명"),
    "dates": ("소비기한", "유통기한", "품질유지기한", "제조연월일", "제조일자", "제조일", "포장일", "생산연도"),
    "volume": ("내용량", "중량", "용량", "포장단위", "수량"),
    "storage": ("보관방법", "보관 방법", "취급방법", "보관"),
    "food_type": ("식품의 유형", "식품유형"),
    "product_name": ("제품명",),
    "item_name": ("품목", "품명", "명칭", "제품명", "상품명"),
    "composition": ("상품구성", "상품 구성", "구성"),
    "cs_phone": ("소비자상담", "소비자 상담", "고객센터", "상담전화", "상담 전화", "문의전화"),
    "caution": ("주의사항", "알레르기", "알레르기 유발물질"),
    "nutrition": ("영양성분", "영양정보"),
    "gmo": ("유전자변형",),
    "gmo_gi": ("유전자변형", "지리적표시", "지리적 표시"),
    "grade": ("등급",),
}
PHONE = re.compile(r"0\d{1,2}[-\s.)]?\d{3,4}[-\s.]?\d{4}|1[568]\d{2}[-\s.]?\d{4}")
IMPORT_SENT = re.compile(r"수입신고를필함")
SEP = re.compile(r"^\s*[:：|\-ㆍ·]\s*")


class OcrError(store.SellerError):
    pass


def _norm(s: str) -> str:
    return re.sub(r"\s+", "", s)


HANGUL = re.compile(r"[가-힣]")


def tidy(s: str) -> str:
    """Tesseract 한국어가 글자마다 띄운 것을 붙인다 — '한 라 농장' → '한라 농장', '2026 년' → '2026년'."""
    out: list[str] = []
    run = False  # 바로 앞 낱말이 한 글자 한글로 이어 붙인 덩어리인가
    for t in s.split():
        one = len(t) == 1 and bool(HANGUL.match(t))
        if out and one and ((HANGUL.match(out[-1][-1]) and (len(out[-1]) == 1 or run)) or out[-1][-1].isdigit()):
            out[-1] += t
            run = True
            continue
        run = one
        out.append(t)
    return re.sub(r"\(\s+", "(", re.sub(r"\s+\)", ")", " ".join(out)))


def parse(text: str, kind: str | None) -> dict[str, dict]:
    """읽은 글 → {칸: {value, line}}. 그 품목에 있는 칸만, 칸마다 이름표 순서대로 처음 찾은 줄."""
    fields = [k for k, _ in detail_page.NOTICE.get(kind or "", {}).get("fields", [])] or list(LABELS)
    lines = [tidy(ln) for ln in (text or "").splitlines() if ln.strip()]
    out: dict[str, dict] = {}
    for key in fields:
        if key == "cs_phone":
            for i, ln in enumerate(lines):
                nxt = lines[i + 1] if i + 1 < len(lines) else ""
                if any(_norm(x) in _norm(ln) for x in LABELS["cs_phone"]) and (m := PHONE.search(ln + " " + nxt)):
                    out[key] = {"value": m.group(0), "line": ln[:120]}
                    break
            continue
        if key in ("import_notice", "imported"):
            for ln in lines:
                if IMPORT_SENT.search(_norm(ln)):
                    out[key] = {"value": "수입식품안전관리 특별법에 따른 수입신고를 필함", "line": ln[:120]}
                    break
            continue
        for lab in LABELS.get(key, ()):
            for i, ln in enumerate(lines):
                flat = _norm(ln)
                pos = flat.find(_norm(lab))
                if pos < 0 or flat[:pos].strip("·-•※*[]()■□▶◆"):
                    continue
                rest = _after_label(ln, lab)
                if not rest and i + 1 < len(lines) and not _is_label(lines[i + 1]):
                    rest = lines[i + 1]
                rest = rest.strip(" :：|-")[:120]
                if rest and not _is_label(rest):
                    out[key] = {"value": rest, "line": ln[:120]}
                    break
            if key in out:
                break
    return out


def _after_label(line: str, label: str) -> str:
    pat = r"\s*".join(map(re.escape, _norm(label)))
    m = re.search(pat, line)
    return SEP.sub("", line[m.end() :]) if m else ""


def _is_label(s: str) -> bool:
    flat = _norm(s)
    return any(flat.startswith(_norm(lab)) for labs in LABELS.values() for lab in labs)


def _public_https(url: str) -> bool:
    try:
        u = urlparse(url)
    except ValueError:
        return False
    if u.scheme != "https" or not u.hostname:
        return False
    try:
        infos = socket.getaddrinfo(u.hostname, 443, proto=socket.IPPROTO_TCP)
    except OSError:
        return False
    return all(ipaddress.ip_address(x[4][0]).is_global for x in infos)


def _get(url: str, http) -> bytes:
    if not _public_https(url):
        raise OcrError("https 공개 사진 주소만 읽을 수 있어요")
    r = http.get(url, timeout=20, stream=True, allow_redirects=False, headers={"User-Agent": "trendguide-seller-ocr/1"})
    if r.status_code != 200:
        raise OcrError(f"사진을 받지 못했어요 ({r.status_code})")
    buf = b""
    for chunk in r.iter_content(64 * 1024):
        buf += chunk
        if len(buf) > MAX_BYTES:
            raise OcrError("사진이 10MB 를 넘어요")
    return buf


def _tiles(raw: bytes) -> list[bytes]:
    """세로로 긴 상세 이미지를 잘라 PNG 로 — 너무 작으면 키운다."""
    import io

    from PIL import Image

    try:
        im = Image.open(io.BytesIO(raw))
        im.load()
    except Exception as e:  # noqa: BLE001
        raise OcrError("그림 파일을 열지 못했어요 (JPG·PNG·WEBP)") from e
    im = im.convert("RGB")
    if im.width < 900:
        r = 900 / im.width
        im = im.resize((900, int(im.height * r)))
    out = []
    for top in range(0, im.height, TILE_H - 100):
        if len(out) >= MAX_TILES:
            break
        b = io.BytesIO()
        im.crop((0, top, im.width, min(top + TILE_H, im.height))).save(b, "PNG")
        out.append(b.getvalue())
    return out


def _ocr_bytes(raw: bytes, ocr) -> str:
    texts = []
    with tempfile.TemporaryDirectory() as tmp:
        for n, tile in enumerate(_tiles(raw)):
            p = Path(tmp) / f"t{n}.png"
            p.write_bytes(tile)
            got = ocr(p)
            texts.append((got or {}).get("text") or "")
    return "\n".join(texts)


def _default_ocr():
    try:
        from commerce_ai_local_ocr import engine
    except ImportError:
        return None
    try:
        engine.check_installation("kor+eng")
    except Exception:  # noqa: BLE001 — Tesseract·한국어 데이터 없음
        return None
    return lambda p: engine.read_image(p, language="kor+eng", psm=4)


def read(eng, token: str, client: str, product_id: str, *, urls: list[str] | None = None, upload: str = "",
         http=None, ocr=None) -> dict:  # fmt: skip
    """상세 이미지 → 빈 고시 칸 후보. {kind, suggestions[{key,label,value,line,image}], filled, warnings, read}"""
    s = store.resolve(eng, token, client)
    d = detail_page.get(eng, token, client, product_id)
    inputs = (d.get("current") or {}).get("inputs") or {}
    kind = inputs.get("notice_kind") or d.get("default_kind")
    have = detail_page.notice_values(kind, inputs.get("notice"))
    srcs: list[tuple[str, bytes | str]] = []
    if upload:
        import base64

        data = upload.split(",", 1)[-1] if upload.startswith("data:") else upload
        try:
            raw = base64.b64decode(data, validate=True)
        except ValueError:
            raise OcrError("파일을 읽지 못했어요") from None
        if len(raw) > MAX_BYTES:
            raise OcrError("파일이 10MB 를 넘어요")
        srcs.append(("올린 파일", raw))
    for u in [x.strip() for x in (urls or []) if x and x.strip()][:MAX_IMAGES]:
        srcs.append((u, u))
    if not srcs:
        raise OcrError("읽을 상세 이미지를 골라 주세요 (사진 주소 또는 파일)")
    ocr = ocr or _default_ocr()
    if ocr is None:
        raise OcrError("이 서버에 글자 읽기(Tesseract 한국어)가 아직 설치되지 않았어요 — 운영팀에 알려 주세요")
    _quota(eng, s["seller_id"])
    if http is None:
        import requests

        http = requests
    found: dict[str, dict] = {}
    problems, texts = [], []
    for name, src in srcs:
        try:
            raw = src if isinstance(src, bytes) else _get(src, http)
            text = _ocr_bytes(raw, ocr)
        except OcrError as e:
            problems.append({"image": name[:80], "error": str(e)})
            continue
        texts.append(text)
        for k, v in parse(text, kind).items():
            found.setdefault(k, {**v, "image": name[:80]})
    labels = dict(detail_page.NOTICE.get(kind or "", {}).get("fields", []))
    sugg = [{"key": k, "label": labels.get(k, k), **v} for k, v in found.items() if not (have.get(k) or "").strip()]
    all_text = "\n".join(texts)
    warnings = []
    for rx, why in ((detail_page.HEALTH, "효능·질병"), (detail_page.HYPE, "단정")):
        hits = sorted({m.group(0) for m in rx.finditer(all_text)})[:5]
        if hits:
            warnings.append(f"이미지 글에 {why} 표현이 있어요: {', '.join(hits)} — 운영팀 검수에서 볼 수 있어요")
    if (m := detail_page.CERT_WORDS.search(all_text)) and not (inputs.get("memo") or "").count(m.group(0)):
        warnings.append(
            f"이미지 글에 '{m.group(0)}' 이 있어요 — 인증은 인증서로 운영팀이 확인한 뒤에만 '확인됨'이 돼요"
        )
    with eng.begin() as c:
        store._event(c, s["seller_id"], "detail_ocr", "seller",
                     {"product_id": product_id, "images": len(srcs), "found": len(found), "suggested": len(sugg)})  # fmt: skip
    return {"kind": kind, "suggestions": sugg, "filled": sorted(k for k in found if (have.get(k) or "").strip()),
            "warnings": warnings, "problems": problems, "read": len(texts)}  # fmt: skip


def _quota(eng, seller_id: str) -> None:
    from datetime import timedelta

    from sqlalchemy import and_, func, select

    with eng.connect() as c:
        n = c.execute(select(func.count()).select_from(store.t_event).where(and_(
            store.t_event.c.seller_id == seller_id, store.t_event.c.kind == "detail_ocr",
            store.t_event.c.at >= store.now() - timedelta(days=1)))).scalar()  # fmt: skip
    if n >= DAILY:
        raise OcrError(f"오늘은 더 읽을 수 없어요 (하루 {DAILY}번)")


__all__ = ["OcrError", "parse", "read"]
