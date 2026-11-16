"""파워포인트·그림 자료 → 제안서 디자인 자산 '학습' (2026-11-14).

  uv run python scripts/learn_ppt_assets.py "<자료 폴더>" --pack clipartkorea
  uv run python scripts/learn_ppt_assets.py "<자료 폴더>" --pack clipartkorea --no-tag   # 자르기만 (Claude 태그 없이)
  uv run python scripts/learn_ppt_assets.py "<자료 폴더>" --pack clipartkorea --extras   # 2차: WMF·EMF 그림 + 슬라이드 배경

하는 일
1. .ppt 는 LibreOffice 로 .pptx 로 바꾼다. 슬라이드마다 그림(사진·일러스트·아이콘)을 꺼내고, 슬라이드 전체 모습(레이아웃 참고)과
   주요 색(팔레트)을 남긴다.
2. .jpg·.png 그림 시트(아이콘 모음·일러스트 모음)는 흰 배경을 기준으로 그림을 하나씩 잘라 낸다 (가로·세로 빈 줄로 나누기).
   흰 배경은 투명하게 바꿔 PNG 로. 배경이 흰색이 아닌 그림은 통째로 일러스트·배경으로.
3. Claude 가 잘라 낸 그림을 20개씩 보고 종류(icon·illustration·photo·background·mockup)·주제 낱말·어울리는 장을 붙인다.
4. <ADMIN_DATA_DIR>/proposal_assets/<pack>/manifest.json 에 저장 → app/admin/b2b/design_assets 가 제안서에 쓴다.
같은 그림(같은 바이트)은 한 번만. 다시 실행하면 새 그림만 더하고, 이미 붙인 태그는 둔다.
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import io
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from dotenv import dotenv_values  # noqa: E402
from PIL import Image, ImageDraw  # noqa: E402

SECTIONS = ["cover", "summary", "understanding", "strategy", "evaluation", "compliance", "products", "mall", "delivery",
            "operations", "schedule", "price", "risk", "company", "questions", "closing"]
TAG_PROMPT = f"""너는 제안서 디자이너다. 번호가 붙은 그림들을 보고 각 그림을 분류한다. JSON 하나만 출력한다.
{{"items": [{{"n": 번호, "kind": "icon|illustration|photo|background|mockup|skip", "tags": ["한국어 주제 낱말 3~6개"],
  "sections": ["어울리는 장 0~3개"]}}]}}
- icon: 단순한 기호·선 아이콘 한 개. illustration: 장면·사물 그림. photo: 사진. background: 글을 얹을 수 있는 넓은 배경.
  mockup: 휴대폰·화면 모형. skip: 글자뿐인 조각·잘린 조각·너무 작아 쓸 수 없는 것·로고·워터마크.
- tags 예: 배송, 트럭, 창고, 지게차, 상자, 선물, 식료품, 마트, 장보기, 신선, 채소, 과일, 모바일, 앱, 결제, 카드, 돈, 은행, 데이터, 차트,
  분석, 체크리스트, 문서, 보안, 일정, 사람, 고객, 비즈니스, 에너지, 화재, 안전. 그림에 보이는 것만.
- sections 는 이 중에서: {", ".join(SECTIONS)} (cover=표지, products=상품 구성, mall=폐쇄몰·앱, delivery=배송·교환, operations=물류·운영,
  schedule=일정, price=가격·결제, risk=위험·보안, evaluation=평가·데이터, company=제안사 소개, closing=마무리)."""


def sha(b: bytes) -> str:
    return hashlib.sha1(b).hexdigest()[:16]


def to_pptx(src: Path, tmp: Path) -> Path | None:
    if src.suffix.lower() == ".pptx":
        return src
    subprocess.run(["soffice", "--headless", "--convert-to", "pptx", "--outdir", str(tmp), str(src)],
                   capture_output=True, timeout=180)
    out = tmp / (src.stem + ".pptx")
    return out if out.exists() else None


def render(pptx: Path, tmp: Path) -> list[Path]:
    subprocess.run(["soffice", "--headless", "--convert-to", "pdf", "--outdir", str(tmp), str(pptx)],
                   capture_output=True, timeout=180)
    pdf = tmp / (pptx.stem + ".pdf")
    if not pdf.exists():
        return []
    subprocess.run(["pdftoppm", "-r", "60", "-png", str(pdf), str(tmp / (pptx.stem + "_s"))], capture_output=True, timeout=180)
    return sorted(tmp.glob(pptx.stem + "_s*.png"))


def palette(img: Image.Image, n: int = 6) -> list[str]:
    q = img.convert("RGB").resize((160, 120)).quantize(colors=n + 2)
    pal = q.getpalette()
    counts = sorted(q.getcolors(), reverse=True)
    out = []
    for _c, i in counts:
        r, g, b = pal[i * 3:i * 3 + 3]
        if max(r, g, b) > 245 and min(r, g, b) > 235:
            continue                       # 거의 흰색은 빼고
        out.append(f"#{r:02X}{g:02X}{b:02X}")
    return out[:n]


def pictures(shapes):
    for sh in shapes:
        if sh.shape_type == 6:             # group
            yield from pictures(sh.shapes)
        elif sh.shape_type == 13:
            yield sh


# ── 그림 시트 자르기 ───────────────────────────────────────
def _mask(img: Image.Image, scale: float):
    import numpy as np

    small = img.convert("RGB").resize((max(1, int(img.width * scale)), max(1, int(img.height * scale))))
    a = np.asarray(small).astype(int)
    return (a.min(axis=2) < 232)           # 흰색이 아닌 곳


def _xycut(m, x0, y0, x1, y1, gap, out, depth=0):
    import numpy as np

    sub = m[y0:y1, x0:x1]
    if sub.size == 0 or not sub.any():
        return
    rows, cols = np.where(sub.any(axis=1))[0], np.where(sub.any(axis=0))[0]
    y0, y1, x0, x1 = y0 + rows[0], y0 + rows[-1] + 1, x0 + cols[0], x0 + cols[-1] + 1
    sub = m[y0:y1, x0:x1]
    for axis in (0, 1):                    # 0: 가로로 빈 줄 → 위아래로 나눔, 1: 세로
        prof = sub.any(axis=1 - axis) if axis == 0 else sub.any(axis=0)
        cuts, run, start = [], 0, None
        for i, v in enumerate(prof):
            if not v:
                run += 1
                if run == gap:
                    start = i - gap + 1
            else:
                if run >= gap and start is not None:
                    cuts.append((start, i))
                run, start = 0, None
        if cuts and depth < 12:
            edges = [0] + [c for s, e in cuts for c in (s, e)] + [len(prof)]
            for a, b in zip(edges[::2], edges[1::2]):
                if axis == 0:
                    _xycut(m, x0, y0 + a, x1, y0 + b, gap, out, depth + 1)
                else:
                    _xycut(m, x0 + a, y0, x0 + b, y1, gap, out, depth + 1)
            return
    out.append((x0, y0, x1, y1))


def transparent(img: Image.Image) -> Image.Image:
    """테두리에서 이어진 흰 배경만 투명하게 (그림 안의 흰색은 둔다). 이미 투명한 그림은 그대로."""
    if img.mode in ("RGBA", "LA", "P"):
        rgba = img.convert("RGBA")
        if rgba.getextrema()[3][0] < 255:
            return rgba
    rgb = img.convert("RGB")
    key = (255, 0, 255)
    w, h = rgb.size
    for pt in [(0, 0), (w - 1, 0), (0, h - 1), (w - 1, h - 1), (w // 2, 0), (w // 2, h - 1), (0, h // 2), (w - 1, h // 2)]:
        if min(rgb.getpixel(pt)) > 225:
            ImageDraw.floodfill(rgb, pt, key, thresh=40)
    import numpy as np

    arr = np.asarray(rgb.convert("RGBA")).copy()
    hole = (arr[..., 0] == 255) & (arr[..., 1] == 0) & (arr[..., 2] == 255)
    arr[hole] = (0, 0, 0, 0)
    return Image.fromarray(arr, "RGBA")


def slice_sheet(img: Image.Image) -> list[Image.Image]:
    rgb = img.convert("RGB")
    border = [rgb.getpixel(p) for p in [(0, 0), (rgb.width - 1, 0), (0, rgb.height - 1), (rgb.width - 1, rgb.height - 1)]]
    if not all(min(c) > 225 for c in border):
        return []                          # 흰 배경이 아니면 통째로 쓴다
    scale = min(1.0, 900 / max(rgb.size))
    m = _mask(rgb, scale)
    boxes: list = []
    gap = max(4, int(min(m.shape) * 0.012))
    _xycut(m, 0, 0, m.shape[1], m.shape[0], gap, boxes)
    out = []
    mind = min(m.shape) * 0.04
    for x0, y0, x1, y1 in boxes:
        if (x1 - x0) < mind or (y1 - y0) < mind or (x1 - x0) * (y1 - y0) < (mind * 1.6) ** 2:
            continue                       # 글자 한 줄·티끌
        pad = 3
        box = tuple(int(v / scale) for v in (max(0, x0 - pad), max(0, y0 - pad), min(m.shape[1], x1 + pad), min(m.shape[0], y1 + pad)))
        out.append(rgb.crop(box))
    return out


def save(img: Image.Image, folder: Path, prefix: str, alpha: bool) -> tuple[str, str] | None:
    im = transparent(img) if alpha else img.convert("RGB")
    im.thumbnail((1400, 1400))
    buf = io.BytesIO()
    im.save(buf, "PNG" if alpha else "JPEG", **({} if alpha else {"quality": 88}))
    b = buf.getvalue()
    h = sha(b)
    name = f"{prefix}_{h}.{'png' if alpha else 'jpg'}"
    (folder / name).write_bytes(b)
    return name, h


# ── 2차 학습 (2026-11-14): 벡터 그림(WMF·EMF) + 슬라이드 배경 ──────────────
def vector_png(blob: bytes, ext: str, tmp: Path) -> Image.Image | None:
    """WMF·EMF → PDF(LibreOffice) → 600dpi PNG → 그림 부분만 잘라 냄. 빈 그림이면 None."""
    import numpy as np

    f = tmp / f"v_{sha(blob)}.{ext or 'wmf'}"
    f.write_bytes(blob)
    subprocess.run(["soffice", "--headless", "--convert-to", "pdf", "--outdir", str(tmp), str(f)], capture_output=True, timeout=120)
    pdf = f.with_suffix(".pdf")
    if not pdf.exists():
        return None
    subprocess.run(["pdftoppm", "-r", "600", "-png", "-singlefile", str(pdf), str(f.with_suffix(""))], capture_output=True, timeout=120)
    png = f.with_suffix(".png")
    if not png.exists():
        return None
    im = Image.open(png).convert("RGB")
    arr = np.asarray(im)
    ys, xs = np.where(arr.min(axis=2) < 235)
    if not len(xs):
        return None
    box = (max(0, xs.min() - 6), max(0, ys.min() - 6), min(im.width, xs.max() + 7), min(im.height, ys.max() + 7))
    if (box[2] - box[0]) > im.width * 0.95 and (box[3] - box[1]) > im.height * 0.95:
        return None                                   # 페이지 전체 = 빈 그림·배경 틀
    out = im.crop(box)
    return out if min(out.size) >= 80 else None


def background_png(pptx: Path, tmp: Path) -> list[Image.Image]:
    """슬라이드에서 글자·작은 그림·도형을 지우고 배경(바탕 채우기 + 슬라이드의 절반 넘게 덮는 그림)만 남겨 그린다."""
    import numpy as np
    from pptx import Presentation
    from pptx.enum.shapes import MSO_SHAPE_TYPE

    prs = Presentation(str(pptx))
    area = prs.slide_width * prs.slide_height
    for sl in prs.slides:
        for sh in list(sl.shapes):
            big = sh.shape_type == MSO_SHAPE_TYPE.PICTURE and (sh.width or 0) * (sh.height or 0) >= area * 0.5
            if not big:
                sh._element.getparent().remove(sh._element)  # noqa: SLF001
    bare = tmp / f"bg_{pptx.stem}.pptx"
    prs.save(str(bare))
    out = []
    for png in render(bare, tmp):
        im = Image.open(png).convert("RGB")
        arr = np.asarray(im.resize((160, 90))).astype(float)
        if arr.std() < 4:                              # 그냥 한 가지 색(흰 바탕 등) — 템플릿 색으로 충분
            continue
        out.append(im)
    return out


def extras(folder: Path, out: Path, man: dict, seen: set) -> int:
    import io as _io

    from pptx import Presentation

    tmp = Path(tempfile.mkdtemp())
    done = set(man.setdefault("extras_done", []))
    added = 0
    for src in sorted(folder.iterdir()):
        if src.suffix.lower() not in (".ppt", ".pptx") or src.name in done:
            continue
        px = to_pptx(src, tmp)
        if px is None:
            continue
        for sl in Presentation(str(px)).slides:
            for pic in pictures(sl.shapes):
                blob = pic.image.blob
                try:
                    Image.open(_io.BytesIO(blob)).load()
                    continue                           # 1차에서 이미 꺼낸 그림
                except Exception:  # noqa: BLE001
                    pass
                im = vector_png(blob, pic.image.ext, tmp)
                r = save(im, out, "vec_" + src.stem, True) if im else None
                if r and r[1] not in seen:
                    seen.add(r[1])
                    man["assets"].append({"file": r[0], "hash": r[1], "source": src.name, "from": "vector"})
                    added += 1
        for im in background_png(px, tmp):
            r = save(im, out, "bg_" + src.stem, False)
            if r and r[1] not in seen:
                seen.add(r[1])
                man["assets"].append({"file": r[0], "hash": r[1], "source": src.name, "from": "background", "hint": "background"})
                added += 1
        man["extras_done"].append(src.name)
        (out / "manifest.json").write_text(json.dumps(man, ensure_ascii=False, indent=1), encoding="utf-8")
        print(src.name, "→ 2차 자산", added, flush=True)
    shutil.rmtree(tmp, ignore_errors=True)
    return added


# ── Claude 태그 ────────────────────────────────────────────
def contact_sheet(files: list[Path]) -> bytes:
    cell = 220
    cols = 5
    rows = (len(files) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * cell, rows * (cell + 24)), "white")
    d = ImageDraw.Draw(sheet)
    for k, f in enumerate(files):
        im = Image.open(f).convert("RGBA")
        im.thumbnail((cell - 10, cell - 10))
        bg = Image.new("RGB", im.size, (240, 240, 240))
        bg.paste(im, mask=im.split()[-1])
        x, y = (k % cols) * cell, (k // cols) * (cell + 24)
        sheet.paste(bg, (x + 5, y + 24))
        d.rectangle([x, y, x + 34, y + 20], fill="black")
        d.text((x + 6, y + 4), str(k + 1), fill="white")
    buf = io.BytesIO()
    sheet.save(buf, "JPEG", quality=80)
    return buf.getvalue()


def tag(files: list[Path], key: str, model: str) -> list[dict]:
    import httpx

    img = base64.b64encode(contact_sheet(files)).decode()
    r = httpx.post("https://api.anthropic.com/v1/messages", timeout=170,
                   headers={"x-api-key": key, "anthropic-version": "2023-06-01", "content-type": "application/json"},
                   json={"model": model, "max_tokens": 8000, "system": TAG_PROMPT + "\n반드시 JSON 하나만 출력.",
                         "messages": [{"role": "user", "content": [
                             {"type": "image", "source": {"type": "base64", "media_type": "image/jpeg", "data": img}},
                             {"type": "text", "text": f"그림 {len(files)}개 (왼쪽 위부터 1번). 모두 분류해 주세요."}]}]})
    r.raise_for_status()
    text = "".join(b.get("text", "") for b in r.json().get("content", []) if b.get("type") == "text")
    from app.admin.shared.llm import safe_json

    return (safe_json(text) or {}).get("items") or []


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("folder")
    ap.add_argument("--pack", default="user_ppt")
    ap.add_argument("--no-tag", action="store_true")
    ap.add_argument("--tag-only", action="store_true", help="자르기는 건너뛰고 태그 없는 것만 태그")
    ap.add_argument("--model", default="claude-sonnet-5-5")
    ap.add_argument("--limit", type=int, default=0, help="태그 묶음 수 제한 (나눠 돌리기)")
    ap.add_argument("--extras", action="store_true", help="2차: 1차에서 건너뛴 WMF·EMF 그림과 슬라이드 배경만 학습")
    a = ap.parse_args()
    from app.admin.b2b import design_assets

    out = design_assets.root() / a.pack
    out.mkdir(parents=True, exist_ok=True)
    mf = out / "manifest.json"
    man = json.loads(mf.read_text(encoding="utf-8")) if mf.exists() else {"pack": a.pack, "sources": [], "assets": [], "layouts": []}
    seen = {x["hash"] for x in man["assets"]}
    if a.extras:
        print("2차 학습:", extras(Path(a.folder), out, man, seen), "개 추가")
    elif not a.tag_only:
        from pptx import Presentation

        tmp = Path(tempfile.mkdtemp())
        for src in sorted(Path(a.folder).iterdir()):
            ext = src.suffix.lower()
            if src.name in man["sources"]:
                continue                   # 이미 학습한 파일
            if ext in (".ppt", ".pptx"):
                px = to_pptx(src, tmp)
                if px is None:
                    print("변환 실패", src.name)
                    continue
                for k, slide_png in enumerate(render(px, tmp)):
                    im = Image.open(slide_png)
                    name, h = save(im, out, "layout_" + src.stem, False)
                    man["layouts"].append({"file": name, "source": src.name, "slide": k + 1, "palette": palette(im)})
                prs = Presentation(str(px))
                for sl in prs.slides:
                    for pic in pictures(sl.shapes):
                        try:
                            blob = pic.image.blob
                            im = Image.open(io.BytesIO(blob))
                            im.load()
                        except Exception:  # noqa: BLE001 — wmf·emf 등 읽을 수 없는 그림
                            continue
                        if min(im.size) < 80:
                            continue
                        alpha = im.mode in ("RGBA", "LA", "P")
                        r = save(im, out, "pic_" + src.stem, alpha)
                        if r and r[1] not in seen:
                            seen.add(r[1])
                            man["assets"].append({"file": r[0], "hash": r[1], "source": src.name, "from": "pptx"})
                man["sources"].append(src.name)
            elif ext in (".jpg", ".jpeg", ".png"):
                im = Image.open(src)
                im.thumbnail((3000, 3000))             # 아주 큰 시트는 줄여서 자른다 (자산은 최대 1400px)
                parts = slice_sheet(im)
                if not parts:
                    r = save(im, out, "img_" + src.stem, False)
                    if r and r[1] not in seen:
                        seen.add(r[1])
                        man["assets"].append({"file": r[0], "hash": r[1], "source": src.name, "from": "whole"})
                for part in parts:
                    r = save(part, out, "cut_" + src.stem, True)
                    if r and r[1] not in seen:
                        seen.add(r[1])
                        man["assets"].append({"file": r[0], "hash": r[1], "source": src.name, "from": "sheet"})
                man["sources"].append(src.name)
            print(src.name, "→ 자산", len(man["assets"]), flush=True)
            mf.write_text(json.dumps(man, ensure_ascii=False, indent=1), encoding="utf-8")   # 파일마다 저장 (이어서 돌리기)
        shutil.rmtree(tmp, ignore_errors=True)
        mf.write_text(json.dumps(man, ensure_ascii=False, indent=1), encoding="utf-8")
    made = design_assets.ensure_templates()            # 학습한 자료 색 → 제안서 템플릿
    if made:
        print("템플릿 추가:", ", ".join(made))
    if a.no_tag:
        return 0
    env = dotenv_values(ROOT / ".env")
    key = (env.get("ANTHROPIC_API_KEY") or "").strip()
    if not key:
        print("ANTHROPIC_API_KEY 가 없어 태그를 붙이지 못했어요.")
        return 1
    todo = [x for x in man["assets"] if "kind" not in x]
    batches = [todo[i:i + 20] for i in range(0, len(todo), 20)]
    if a.limit:
        batches = batches[:a.limit]
    from concurrent.futures import ThreadPoolExecutor

    def run(batch):
        try:
            return batch, tag([out / x["file"] for x in batch], key, a.model)
        except Exception as e:  # noqa: BLE001
            print("태그 실패", type(e).__name__, str(e)[:120])
            return batch, []

    with ThreadPoolExecutor(max_workers=6) as ex:
        for batch, items in ex.map(run, batches):
            by = {int(i.get("n", 0)): i for i in items if isinstance(i, dict)}
            for k, x in enumerate(batch, 1):
                it = by.get(k)
                if not it:
                    continue
                x["kind"] = it.get("kind") or "skip"
                if x.get("hint") == "background" and x["kind"] != "skip":
                    x["kind"] = "background"           # 배경만 떼어 낸 것은 배경으로
                x["tags"] = [str(t) for t in it.get("tags") or []][:8]
                x["sections"] = [s for s in it.get("sections") or [] if s in SECTIONS]
                x["keep"] = x["kind"] != "skip"
    mf.write_text(json.dumps(man, ensure_ascii=False, indent=1), encoding="utf-8")
    kinds = {}
    for x in man["assets"]:
        kinds[x.get("kind", "미분류")] = kinds.get(x.get("kind", "미분류"), 0) + 1
    print("완료", len(man["assets"]), kinds)
    return 0


if __name__ == "__main__":
    sys.exit(main())
