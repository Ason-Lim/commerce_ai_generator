"""제안서 디자인 자산 (2026-11-12~14) — 사용자가 가진 파워포인트·그림 자료에서 뽑아 '학습'한 아이콘·그림·배경을
제안 내용(장 주제·공고 품목)에 맞춰 골라 제안서(PPTX·HTML 슬라이드)에 넣는다.

* 자산 위치: <ADMIN_DATA_DIR>/proposal_assets/<묶음>/ (manifest.json + 그림 파일). git 에 올리지 않는다
  (스톡 이미지 — 클립아트코리아·통로이미지 등 — 이용 허락은 자료를 산 계정의 약관을 따른다. 재배포·단독 판매 금지가 보통).
* 만들기: scripts/learn_ppt_assets.py <폴더> — 파워포인트(.ppt·.pptx)의 그림·배경·슬라이드 모양, 그림 시트(.jpg·.png)를
  하나씩 잘라 내고 Claude 가 그림마다 종류·주제 낱말·어울리는 장을 붙인다.
* 고르기: 장(section id)마다 주제 낱말을 정해 두고, 공고 품목(식품·농산물·생활용품…)과 제목 낱말을 더해 가장 많이 겹치는 자산.
  한 제안서 안에서 같은 그림을 두 번 쓰지 않는다. 자산이 없으면 아무것도 넣지 않는다 (지금처럼 도형·색만).
"""
from __future__ import annotations

import json
import re
from functools import lru_cache
from pathlib import Path

from app.admin.shared.config import data_dir

# 장마다 어울리는 낱말 (Claude 가 붙인 tags·topics 와 견준다)
SECTION_WORDS: dict[str, list[str]] = {
    "cover": ["선물", "배송", "물류", "쇼핑", "비즈니스", "택배", "트럭", "신선"],
    "summary": ["비즈니스", "목표", "체크", "성장"],
    "understanding": ["비즈니스", "분석", "데이터", "회의", "기업"],
    "strategy": ["전략", "목표", "성장", "아이디어", "비즈니스"],
    "evaluation": ["평가", "차트", "데이터", "분석", "그래프", "체크"],
    "compliance": ["체크리스트", "문서", "계약", "체크", "서류"],
    "products": ["선물", "식품", "상자", "장보기", "농산물", "과일", "채소", "식료품", "마트"],
    "mall": ["모바일", "앱", "스마트폰", "쇼핑", "온라인", "웹", "컴퓨터", "결제"],
    "delivery": ["배송", "택배", "트럭", "운송", "배달", "물류", "상자"],
    "operations": ["창고", "물류", "지게차", "상자", "선반", "재고", "포장", "출고"],
    "schedule": ["일정", "타임라인", "달력", "시계", "단계", "체크리스트"],
    "price": ["돈", "결제", "카드", "계산기", "금융", "동전", "가격", "은행"],
    "risk": ["보안", "경고", "방패", "안전", "자물쇠", "점검"],
    "company": ["기업", "건물", "회사", "팀", "사람", "비즈니스"],
    "questions": ["질문", "체크리스트", "문서", "상담"],
    "closing": ["선물", "감사", "배송", "고객", "웃음"],
}
CATEGORY_WORDS = {"식품": ["식품", "식료품", "음식"], "농산물": ["농산물", "과일", "채소", "신선"], "수산물": ["수산물", "생선", "신선"],
                  "축산물": ["고기", "정육", "신선"], "가공식품": ["식품", "식료품", "마트"], "생활용품": ["생활용품", "마트", "상자"],
                  "건강기능식품": ["건강", "식품"], "농축수산물": ["농산물", "신선", "식료품"]}


# 학습한 자료의 색으로 만든 제안서 템플릿 (2026-11-14 — 클립아트코리아·통로이미지 자료를 보고 고른 색)
LEARNED_TEMPLATES = [
    ("물류 민트", "물류·배송 일러스트 자료(민트·네이비)", {"primary": "#0F9E80", "accent": "#393E49", "surface": "#EAF8F4", "line": "#CFEDE4"}),
    ("로지스틱 블루", "창고·배송 아이콘 자료(블루·옐로)", {"primary": "#1F6FB8", "accent": "#F2A900", "surface": "#EEF4FA", "line": "#D6E4F2"}),
    ("프레시 그린", "신선·에너지 자료(그린)", {"primary": "#4E7A12", "accent": "#97C33B", "surface": "#F3F8E8", "line": "#DDEBC4"}),
    ("핀테크 코랄", "결제·핀테크 자료(코랄·네이비)", {"primary": "#D84A3E", "accent": "#2E3A59", "surface": "#FFF1EE", "line": "#F6D6D0"}),
    ("앱 퍼플", "모바일 앱 자료(퍼플)", {"primary": "#5B45D6", "accent": "#A054F7", "surface": "#F3F1FD", "line": "#E1DCF8"}),
]


def ensure_templates() -> list[str]:
    """학습한 색 템플릿을 등록 (이미 있으면 건너뜀). 만든 이름 목록."""
    from app.admin.b2b import proposal_templates as T

    have = {t.name for t in T.list_all()}
    made = []
    for name, desc, colors in LEARNED_TEMPLATES:
        if name not in have:
            T.create(name, description=desc + " · 학습한 그림과 함께 쓰기 좋음", colors=colors)
            made.append(name)
    return made


def root() -> Path:
    return data_dir() / "proposal_assets"


@lru_cache(maxsize=4)
def _load(stamp: float) -> list[dict]:
    items: list[dict] = []
    for mf in sorted(root().glob("*/manifest.json")):
        try:
            data = json.loads(mf.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        for a in data.get("assets") or []:
            if a.get("keep", True) and (mf.parent / a["file"]).exists():
                items.append(dict(a, path=str(mf.parent / a["file"]), pack=mf.parent.name))
    return items


def assets() -> list[dict]:
    files = list(root().glob("*/manifest.json")) if root().exists() else []
    stamp = max((f.stat().st_mtime for f in files), default=0.0)
    return _load(stamp)


def _words(a: dict) -> set[str]:
    return {w.strip() for w in (a.get("tags") or []) + (a.get("topics") or []) if isinstance(w, str) and w.strip()}


def score(a: dict, want: list[str], sid: str | None = None) -> float:
    have = _words(a)
    s = sum(1.0 for w in want if any(w in h or h in w for h in have if len(h) >= 2))
    if sid and sid in (a.get("sections") or []):
        s += 2.0
    if s and str(a.get("file", "")).endswith(".png"):
        s += 0.5                                   # 배경이 투명한 그림이 슬라이드에 잘 얹힌다
    if a.get("from") == "whole" and a.get("kind") != "background":
        s -= 2.5                                   # 통째 그림(포스터 등)은 글자가 들어 있는 경우가 많다
    return s


def pick(sid: str, kinds: tuple[str, ...], extra: list[str] | None = None, used: set[str] | None = None) -> dict | None:
    want = SECTION_WORDS.get(sid, []) + list(extra or [])
    best, best_s = None, 0.0
    for a in assets():
        if a.get("kind") not in kinds or (used and a["path"] in used):
            continue
        s = score(a, want, sid)
        if s > best_s:
            best, best_s = a, s
    if best and used is not None:
        used.add(best["path"])
    return best if best_s >= 1.0 else None


def plan(sections: list, categories: list[str] | None = None, title: str = "") -> dict:
    """제안서 한 부에 넣을 그림: {'cover': 자산, 'closing': 자산, 'sections': {sid: 자산}}. 같은 그림은 한 번만."""
    if not assets():
        return {"cover": None, "closing": None, "sections": {}}
    extra = [w for c in categories or [] for w in CATEGORY_WORDS.get(c, [c])]
    extra += [w for w in re.findall(r"[가-힣]{2,}", title or "") if w in {"선물", "명절", "설", "추석", "식품", "기념품"}]
    used: set[str] = set()
    cover = pick("cover", ("illustration", "photo", "background"), extra, used)
    out = {"cover": cover, "sections": {}, "closing": None}
    for sec in sections:
        sid = getattr(sec, "id", None) or (sec.get("id") if isinstance(sec, dict) else None)
        if not sid or sid.startswith("appendix") or sid in out["sections"]:
            continue
        a = pick(sid, ("icon", "illustration"), extra if sid in ("products", "cover") else None, used)
        if a:
            out["sections"][sid] = a
    out["closing"] = pick("closing", ("illustration", "photo"), extra, used)
    return out


def for_proposal(p) -> dict:
    """제안서(Proposal) 한 부의 그림 계획 — 공고 품목·제목·장 목록으로."""
    cats = [c.get("name") for c in ((getattr(p, "facts", None) or {}).get("categories") or []) if c.get("name")]
    return plan(p.sections, cats, getattr(p, "title", ""))


def fit(path: str, w: float, h: float) -> tuple[float, float]:
    """(w,h) 상자 안에 비율을 지켜 넣을 크기."""
    from PIL import Image

    with Image.open(path) as im:
        iw, ih = im.size
    k = min(w / iw, h / ih)
    return iw * k, ih * k


@lru_cache(maxsize=256)
def data_uri(path: str, max_px: int = 640) -> str:
    """HTML 슬라이드용 — 줄여서 파일 하나에 넣는다 (투명 PNG 는 PNG, 나머지는 JPEG)."""
    import base64
    import io

    from PIL import Image

    with Image.open(path) as im:
        im.thumbnail((max_px, max_px))
        buf = io.BytesIO()
        if im.mode in ("RGBA", "LA", "P"):
            im.convert("RGBA").save(buf, "PNG", optimize=True)
            mime = "image/png"
        else:
            im.convert("RGB").save(buf, "JPEG", quality=82)
            mime = "image/jpeg"
    return f"data:{mime};base64," + base64.b64encode(buf.getvalue()).decode()
