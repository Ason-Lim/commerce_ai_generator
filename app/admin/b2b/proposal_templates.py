"""제안서 디자인 템플릿 — 기본 4종 + 사용자 등록 템플릿.

템플릿 = 색(palette) · 폰트 · 표지 스타일 · 모션 여부 + (선택) 로고 · 레퍼런스 이미지 · 회사 PPTX 양식.
같은 템플릿이 HTML 슬라이드 · PPTX · PDF 에 모두 적용된다 (HWPX · Word 는 문서형이라 색만 일부 반영).

등록 템플릿 저장 위치: <ADMIN_DATA_DIR>/proposal_templates/<id>/template.json (+ 로고·이미지·PPTX 파일)
레퍼런스 이미지만 올리고 색을 비워 두면 이미지에서 주색·보조색을 자동으로 뽑는다 (영상의 '디자인 레퍼런스' 방식).
"""
from __future__ import annotations

import base64
import colorsys
import io
import json
import re
import shutil
import uuid
from datetime import datetime
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field

from app.admin.shared.config import data_dir

HEX = re.compile(r"^#[0-9a-fA-F]{6}$")
Cover = Literal["split", "bold", "minimal"]
FONT_STACK = '"Pretendard Variable",Pretendard,"Apple SD Gothic Neo","Malgun Gothic","Noto Sans KR",system-ui,sans-serif'


class Palette(BaseModel):
    primary: str = "#C2185B"     # 강조 (제목 키워드 · 차트 · 버튼)
    accent: str = "#7A1240"      # 보조 강조 (차트 2번째 계열 · 표지 그라데이션)
    ink: str = "#16181D"         # 본문 글자
    muted: str = "#6B7079"       # 보조 글자
    bg: str = "#FFFFFF"          # 슬라이드 배경
    surface: str = "#FBF3F6"     # 카드 배경
    line: str = "#ECE3E7"        # 구분선
    on_primary: str = "#FFFFFF"  # 주색 위 글자


class Template(BaseModel):
    id: str
    name: str
    description: str = ""
    builtin: bool = False
    palette: Palette = Field(default_factory=Palette)
    font_css: str = FONT_STACK          # HTML 슬라이드 · PDF
    # 2026-11-12: 제안서 글꼴 Pretendard (SIL OFL 1.1 — 상업 사용·문서 임베딩 가능, 글꼴 파일 단독 판매만 금지).
    # 발표 PC 에 Pretendard 가 없으면 PowerPoint·한글이 다른 글꼴로 바꿔 보여 준다 → 설치하거나 PDF 로 제출.
    font_office: str = "Pretendard"     # PPTX · Word · HWPX
    cover: Cover = "split"
    motion: bool = True                 # 등장 애니메이션 · 숫자 카운트업
    logo: str | None = None             # 템플릿 폴더 안 파일명
    reference: str | None = None        # 레퍼런스 이미지 파일명
    pptx_base: str | None = None        # 회사 PPTX 양식 파일명 (있으면 PPTX 를 그 양식 위에 만든다)
    created: str | None = None


BUILTINS: list[Template] = [
    Template(id="modern_magenta", name="모던 마젠타", builtin=True, cover="split",
             description="흰 배경 + 마젠타 키워드 강조. 숫자 카운트업·호버 반응이 있는 발표용 기본 템플릿",
             palette=Palette()),
    Template(id="public_navy", name="공공 네이비", builtin=True, cover="minimal",
             description="공공기관 제출용. 차분한 네이비, 표 중심, 모션 최소화",
             motion=False,
             palette=Palette(primary="#1D4E89", accent="#0F2C52", ink="#141A22", muted="#5F6B7A",
                             bg="#FFFFFF", surface="#F1F5FA", line="#DCE3EC")),
    Template(id="fresh_green", name="신선 그린", builtin=True, cover="bold",
             description="식품·농수산 선물 제안용. 그린 + 따뜻한 옐로 포인트",
             palette=Palette(primary="#2E7D4F", accent="#E9A23B", ink="#17211B", muted="#5E6B62",
                             bg="#FFFFFF", surface="#F2F7F1", line="#DDE8DC")),
    Template(id="mono_yellow", name="모노 옐로", builtin=True, cover="bold",
             description="블랙 타이포 + 형광 옐로 하이라이트. 임팩트 있는 발표용",
             palette=Palette(primary="#16181D", accent="#FFD400", ink="#16181D", muted="#62656C",
                             bg="#FFFFFF", surface="#FAF9F2", line="#E7E5DA", on_primary="#FFFFFF")),
]
DEFAULT_ID = "modern_magenta"


# ── 저장소 ────────────────────────────────────────────────────
def root() -> Path:
    d = data_dir() / "proposal_templates"
    d.mkdir(parents=True, exist_ok=True)
    return d


def folder(t: Template) -> Path:
    return root() / t.id


def list_all() -> list[Template]:
    out = list(BUILTINS)
    for f in sorted(root().glob("*/template.json")):
        try:
            out.append(Template(**json.loads(f.read_text(encoding="utf-8"))))
        except Exception:  # noqa: BLE001 — 깨진 파일은 건너뛴다
            continue
    return out


def get(tid: str | None) -> Template:
    for t in list_all():
        if t.id == tid:
            return t
    return next(t for t in BUILTINS if t.id == DEFAULT_ID)


def find_in_text(text: str) -> Template | None:
    """프롬프트에 템플릿 이름·ID가 들어 있으면 그 템플릿 (예: '공공 네이비로 제안서 만들어줘')."""
    s = re.sub(r"\s+", "", text or "").lower()
    for t in sorted(list_all(), key=lambda x: -len(x.name)):
        if re.sub(r"\s+", "", t.name).lower() in s or t.id.lower() in s:
            return t
    return None


def _clean_hex(v: str | None) -> str | None:
    if not v:
        return None
    v = v.strip()
    if not v.startswith("#"):
        v = "#" + v
    return v.upper() if HEX.match(v) else None


def create(name: str, *, description: str = "", colors: dict | None = None, font_office: str | None = None,
           font_css: str | None = None, cover: str = "split", motion: bool = True, base: str | None = None,
           logo: tuple[str, bytes] | None = None, reference: tuple[str, bytes] | None = None,
           pptx_base: tuple[str, bytes] | None = None) -> Template:
    """새 템플릿 등록. colors 에 없는 색은 (레퍼런스 이미지 → 자동 추출) 또는 base 템플릿 색을 쓴다."""
    name = (name or "").strip()[:40]
    if not name:
        raise ValueError("템플릿 이름이 필요합니다")
    if cover not in ("split", "bold", "minimal"):
        cover = "split"
    start = get(base)
    pal = start.palette.model_dump()
    if reference:
        pal.update(extract_palette(reference[1]))
    for k, v in (colors or {}).items():
        if k in pal and (h := _clean_hex(v)):
            pal[k] = h
    pal["on_primary"] = _on(pal["primary"])
    t = Template(id="u_" + uuid.uuid4().hex[:8], name=name, description=description.strip()[:200],
                 palette=Palette(**pal), font_office=(font_office or start.font_office).strip()[:40],
                 font_css=(f'"{font_css.strip()}",' + FONT_STACK) if font_css and font_css.strip() else start.font_css,
                 cover=cover, motion=motion, created=datetime.now().isoformat(timespec="seconds"))
    d = folder(t)
    d.mkdir(parents=True, exist_ok=True)
    for attr, item, allowed in (("logo", logo, (".png", ".jpg", ".jpeg", ".svg", ".webp")),
                                ("reference", reference, (".png", ".jpg", ".jpeg", ".webp")),
                                ("pptx_base", pptx_base, (".pptx", ".potx"))):
        if not item:
            continue
        ext = Path(item[0] or "").suffix.lower()
        if ext not in allowed:
            shutil.rmtree(d, ignore_errors=True)
            raise ValueError(f"{attr} 파일 형식이 맞지 않습니다 ({', '.join(allowed)})")
        if attr == "pptx_base":
            _check_pptx(item[1])
            ext = ".pptx"
        fn = f"{attr}{ext}"
        (d / fn).write_bytes(item[1])
        setattr(t, attr, fn)
    (d / "template.json").write_text(t.model_dump_json(indent=2), encoding="utf-8")
    return t


def delete(tid: str) -> None:
    t = get(tid)
    if t.id != tid:
        raise KeyError(tid)
    if t.builtin:
        raise ValueError("기본 템플릿은 삭제할 수 없습니다")
    shutil.rmtree(folder(t), ignore_errors=True)


def asset(t: Template, attr: str) -> Path | None:
    fn = getattr(t, attr, None)
    if not fn or t.builtin:
        return None
    p = folder(t) / fn
    return p if p.exists() else None


def logo_data_uri(t: Template) -> str | None:
    p = asset(t, "logo")
    if not p:
        return None
    mime = {".svg": "image/svg+xml", ".png": "image/png", ".webp": "image/webp"}.get(p.suffix.lower(), "image/jpeg")
    return f"data:{mime};base64," + base64.b64encode(p.read_bytes()).decode()


def public(t: Template) -> dict:
    d = t.model_dump(exclude={"font_css"})
    d["has_logo"], d["has_reference"], d["has_pptx_base"] = bool(t.logo), bool(t.reference), bool(t.pptx_base)
    return d


def _check_pptx(data: bytes) -> None:
    from pptx import Presentation
    try:
        Presentation(io.BytesIO(data))
    except Exception as e:  # noqa: BLE001
        raise ValueError(f"PPTX 양식을 열 수 없습니다: {e}") from None


# ── 색 ────────────────────────────────────────────────────────
def _rgb(h: str) -> tuple[float, float, float]:
    return tuple(int(h[i:i + 2], 16) / 255 for i in (1, 3, 5))  # type: ignore[return-value]


def _hex(r: float, g: float, b: float) -> str:
    return "#" + "".join(f"{max(0, min(255, round(x * 255))):02X}" for x in (r, g, b))


def luminance(h: str) -> float:
    def ch(c: float) -> float:
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = _rgb(h)
    return 0.2126 * ch(r) + 0.7152 * ch(g) + 0.0722 * ch(b)


def contrast(a: str, b: str) -> float:
    la, lb = sorted((luminance(a), luminance(b)), reverse=True)
    return (la + 0.05) / (lb + 0.05)


def _on(h: str) -> str:
    return "#FFFFFF" if contrast(h, "#FFFFFF") >= contrast(h, "#16181D") else "#16181D"


def _tint(h: str, light: float) -> str:
    hh, _, s = colorsys.rgb_to_hls(*_rgb(h))
    return _hex(*colorsys.hls_to_rgb(hh, light, min(s, 0.45)))


def _readable(h: str, min_ratio: float = 3.2) -> str:
    """흰 배경 위 강조색으로 쓸 수 있을 만큼 어둡게."""
    hh, l, s = colorsys.rgb_to_hls(*_rgb(h))
    while contrast(_hex(*colorsys.hls_to_rgb(hh, l, s)), "#FFFFFF") < min_ratio and l > 0.08:
        l -= 0.03
    return _hex(*colorsys.hls_to_rgb(hh, l, s))


def extract_palette(image: bytes) -> dict:
    """레퍼런스 이미지에서 주색·보조색 추출 → 카드 배경·선 색은 주색을 옅게 만들어 맞춘다."""
    from PIL import Image

    im = Image.open(io.BytesIO(image)).convert("RGB")
    im.thumbnail((240, 240))
    q = im.quantize(colors=12, method=Image.Quantize.MEDIANCUT)
    pal = q.getpalette()[: 12 * 3]
    counts = sorted(q.getcolors() or [], reverse=True)
    total = sum(c for c, _ in counts) or 1
    cands = []
    for cnt, idx in counts:
        r, g, b = (x / 255 for x in pal[idx * 3: idx * 3 + 3])
        h, l, s = colorsys.rgb_to_hls(r, g, b)
        if s < 0.25 or l < 0.12 or l > 0.9:      # 무채색·너무 어둡거나 밝은 색 제외
            continue
        cands.append((s * (0.35 + cnt / total), h, _hex(r, g, b)))
    cands.sort(reverse=True)
    if not cands:
        return {}
    primary = _readable(cands[0][2])
    accent = next((c[2] for c in cands[1:] if min(abs(c[1] - cands[0][1]), 1 - abs(c[1] - cands[0][1])) > 0.06), None)
    accent = accent or _hex(*colorsys.hls_to_rgb(colorsys.rgb_to_hls(*_rgb(primary))[0],
                                                 max(0.15, colorsys.rgb_to_hls(*_rgb(primary))[1] - 0.15),
                                                 colorsys.rgb_to_hls(*_rgb(primary))[2]))
    return {"primary": primary, "accent": accent.upper(), "surface": _tint(primary, 0.965),
            "line": _tint(primary, 0.905), "on_primary": _on(primary)}
