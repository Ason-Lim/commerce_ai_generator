"""홈 '함께 보면 좋은 상품' (2026-11-23, 사용자 결정 10:09 '트렌드 상품 → 함께 보면 좋은 상품').

검토 claude/home_rank_reco_review_2026-11-23.md §4 의 1차 — **서버에 개인 기록을 새로 만들지 않는다.**
* 출발점(seeds) = 이 브라우저가 최근 누른 품목 낱말 최대 5개 (브라우저 localStorage, POST 본문으로만 받음 — 주소·기록에 안 남김).
  출발점이 없거나 고객이 '맞춤 끄기'를 하면 → 쿠팡 식품 랭킹 1위 품목을 출발점으로 (personal=false, 문구로 밝힘).
* 상품 묶음(pool) = 쿠팡 식품 랭킹(메모리 10분, 파일 저장 없음) + 승인된 트렌드 글 상품.
* 고르는 순서 (칸마다 이유 한 줄):
  1. 레시피 짝 — 출발점으로 레시피를 찾아(레시피 서비스, 공공 레시피) 함께 쓰는 재료가 든 상품. \"굴 요리(두부굴찌개)에 함께 쓰는 재료\"
  2. 같은 태그 — 출발점과 같은 카테고리 태그(keyword_tags.csv). \"최근 본 귤과 같은 과일\"
  3. 새로 둘러보기 — 출발점 태그와 다른 태그 상품, 칸의 약 1/4 (최소 1). \"새로 둘러보기 · 정육/계란\"
* 순서 안에서는 쿠팡 순위(트렌드 글 상품은 그 뒤) — 제휴 수수료는 순서에 쓰지 않음. '인기'·'구매' 말을 쓰지 않음.
* 다른 고객 클릭 기반(함께 누른 상품·많이 누른 상품)은 2차 — 클릭이 쌓이고 기준(서로 다른 세션 3·5곳)을 넘을 때만.
"""
from __future__ import annotations

import datetime as dt
import re
import threading
from functools import lru_cache

from app.services.trends import coupang_best as cb, tags as tagmod

MAX_SEEDS = 5
SEED_MAX_LEN = 20
LIMITS = {"home": 30, "full": 30}     # 2026-11-23 사용자 요청: 30개(화면은 6개 + 더보기)
TRIVIAL = {"소금", "설탕", "물", "식용유", "참기름", "들기름", "후추", "깨소금", "통깨", "깨", "간장", "식초", "다진마늘",
           "다진파", "마늘", "파", "대파", "청주", "맛술", "올리고당", "물엿", "꿀", "밀가루", "전분", "녹말", "고춧가루"}
DISCLOSURE = ("이 영역의 상품 링크는 쿠팡 파트너스 활동의 일환으로, 이에 따른 일정액의 수수료를 제공받습니다. "
              "수수료는 순서에 영향을 주지 않아요.")
NOTE_PERSONAL = "맞춤 추천 · 이 브라우저에서 최근 누른 품목 기준"   # 개인정보 설명은 처리방침 한 곳(/#/privacy)
NOTE_GENERAL = "일반 추천 · 쿠팡 식품 랭킹 1위 '{seed}' 기준과 여러 카테고리 둘러보기"
_SEED_OK = re.compile(r"^[가-힣A-Za-z0-9 ]{1,20}$")
_LOCK = threading.Lock()


def clean_seeds(raw) -> list[str]:
    """브라우저가 보낸 낱말 — 한글·영문·숫자·공백 20자 이하, 최대 5개, 중복 없음. 나머지는 버림."""
    out = []
    for s in (raw or [])[:MAX_SEEDS * 2]:
        s = " ".join(str(s or "").split())[:SEED_MAX_LEN]
        if s and _SEED_OK.match(s) and s not in out:
            out.append(s)
    return out[:MAX_SEEDS]


def _tokens(title: str) -> list[str]:
    return [w for w in re.split(r"[\s,()\[\]/·+]+", title or "") if w]


def has_ingredient(title: str, ing: str) -> bool:
    """상품명 낱말이 재료와 같거나 재료로 끝남 ('국내산 무' ← 무, '무항생제' ✗)."""
    return any(t == ing or (len(ing) >= 2 and t.endswith(ing)) for t in _tokens(title))


@lru_cache(maxsize=256)
def _recipe_ingredients(seed: str, day: str) -> tuple[str, tuple[str, ...]]:
    """출발점 → (요리 이름, 재료들). 레시피 서비스(get_recipe — food_get_recipe 와 같은 경로). 하루 단위 기억."""
    from app.domain.commerce.requests import RecipeRequest
    from app.services.commerce.recipes import get_recipe

    resolver = _resolver()
    res = get_recipe(RecipeRequest(dish_name=seed), resolver=resolver)
    ids = []
    if res.status == "ok" and res.items:
        it = res.items[0]
        return it.title, tuple(i.name for i in it.ingredients)
    if res.status == "needs_followup" and res.followup:
        ids = [(o["id"], o["label"]) for o in res.followup.options][:3]
    for rid, label in ids:
        r2 = get_recipe(RecipeRequest(recipe_id=rid), resolver=resolver)
        if r2.status == "ok" and r2.items and len(r2.items[0].ingredients) >= 2:
            return r2.items[0].title, tuple(i.name for i in r2.items[0].ingredients)
    return "", ()


_RESOLVER = None


def _resolver():
    global _RESOLVER
    with _LOCK:
        if _RESOLVER is None:
            from app.api.chat_routes import build_default_service

            _RESOLVER = build_default_service().recipe.resolver
    return _RESOLVER


def pool(today: dt.date, now: dt.datetime, posts=None, snap=None) -> list[dict]:
    """쿠팡 식품 랭킹(메모리 10분) + 승인된 트렌드 글 상품. 같은 상품번호는 한 번."""
    items = cb.ranked(today, now, 100, snap=snap)["items"]
    from app.services.cs import blocked as cs_blocked

    out = [{**it, "source": "coupang_best"} for it in items]       # cb.ranked 가 노출 중지 상품을 이미 뺌
    seen = {it["product_id"] for it in out} | set(cs_blocked.blocked_ids())
    try:
        from app.services.trend_posts import policy, render
        from app.services.trend_posts.service import TrendPosts
        from app.services.trends.home_rankings import _image, product_id

        for post in (posts or TrendPosts()).published():
            if post.conclusion == "hold":
                continue
            for n, p in enumerate(post.products, 1):
                pid = product_id(p.url)
                if pid in seen:
                    continue
                seen.add(pid)
                hidden = p.price_krw is None or policy.is_stale(p.price_checked_at, now)
                out.append({"rank": None, "product_id": pid, "title": p.title, "image": _image(p.image_url),
                            "price_krw": None if hidden else p.price_krw, "price_hidden": hidden,
                            "rocket": bool(p.rocket) and not hidden, "seed": cb.seed_of(p.title),
                            "go_url": f"{render.post_url(post)}/go/{n}", "source": "trend_post"})
    except Exception:  # noqa: BLE001 — 글이 없어도 쿠팡 랭킹만으로
        pass
    return out


def _tags(word: str) -> set[str]:
    return set(tagmod.tags_for(word, events=[])) - {"season"}


def _wa(word: str) -> str:
    """받침 있으면 '과', 없으면 '와' (굴과 · 귤과 · 바나나와)."""
    last = word[-1:] if word else ""
    return "과" if "가" <= last <= "힣" and (ord(last) - 0xAC00) % 28 else "와"


def _label(tag: str) -> str:
    return next((t.label for t in tagmod.load() if t.tag == tag), tag)


def build(seeds: list[str], view: str = "home", *, today: dt.date | None = None, now: dt.datetime | None = None,
          posts=None, snap=None, recipe=None) -> dict:
    """recipe: 시험용 (seed → (요리, 재료들)) 함수. 기본은 레시피 서비스."""
    now = now or dt.datetime.now(dt.timezone(dt.timedelta(hours=9)))
    today = today or now.date()
    limit = LIMITS.get(view, LIMITS["home"])
    snap = snap if snap is not None else cb.current()      # 메모리 10분 랭킹 (없으면 1번 받음)
    items = pool(today, now, posts, snap)
    if not items:
        return {"status": "none", "personal": False, "items": [], "disclosure": DISCLOSURE, "note": ""}
    personal = bool(seeds)
    if not seeds:
        top = next((it for it in items if it["source"] == "coupang_best" and it["seed"]), None)
        seeds = [top["seed"]] if top else []
    recipe = recipe or (lambda s: _recipe_ingredients(s, today.isoformat()))
    seed_words = set(seeds)
    seed_tags = set().union(*(_tags(s) for s in seeds)) if seeds else set()
    picked: list[dict] = []
    used: set[str] = set()

    def take(it, kind, why, seed):
        if it["product_id"] in used or it["seed"] in seed_words or len(picked) >= limit:
            return
        used.add(it["product_id"])
        picked.append({k: it[k] for k in ("product_id", "title", "image", "price_krw", "price_hidden", "rocket",
                                          "seed", "source")}
                      | {"kind": kind, "why": why,
                         "go_url": it["go_url"] + ("?from=together" if it["source"] == "coupang_best" else "")})

    n_explore = max(1, limit // 4)
    # 1. 레시피 짝 — 재료마다 상품 하나, 고른 것들은 쿠팡 순위 순으로
    found: list[tuple[dict, str, str]] = []
    for s in seeds:
        try:
            dish, ings = recipe(s)
        except Exception:  # noqa: BLE001 — 레시피를 못 찾아도 다음 방법으로
            dish, ings = "", ()
        for ing in [i for i in ings if i not in TRIVIAL and i != s]:
            it = next((x for x in items if has_ingredient(x["title"], ing) and x["seed"] not in seed_words
                       and all(x is not f[0] for f in found)), None)
            if it:
                found.append((it, f"{s} 요리({dish})에 함께 쓰는 재료 · {ing}", s))
    for it, why, s in sorted(found, key=lambda f: (f[0]["rank"] is None, f[0]["rank"] or 0)):
        if len(picked) >= limit - n_explore:
            break
        take(it, "recipe", why, s)
    # 2. 같은 태그 — 맞춤이면 칸의 절반까지, 일반 추천이면 2개까지 (나머지는 둘러보기로 골고루)
    tag_cap, n_tag = (limit // 2 if personal else 2), 0
    for it in items:
        if len(picked) >= limit - n_explore or n_tag >= tag_cap:
            break
        before = len(picked)
        common = _tags(it["seed"] or it["title"]) & seed_tags
        if common:
            s = next((x for x in seeds if _tags(x) & common), seeds[0])
            take(it, "tag", f"{'최근 본' if personal else '랭킹 1위'} {s}{_wa(s)} 같은 {_label(sorted(common)[0])}", s)
            n_tag += len(picked) - before
    # 3. 새로 둘러보기 — 출발점 태그와 다른 태그, 태그마다 하나씩
    shown_tags: set[str] = set()
    for it in items:
        if len(picked) >= limit:
            break
        t = _tags(it["seed"] or it["title"])
        new = t - seed_tags - shown_tags
        if t and new:
            tag = sorted(new)[0]
            before = len(picked)
            take(it, "explore", f"새로 둘러보기 · {_label(tag)}", "")
            if len(picked) > before:
                shown_tags.add(tag)
    if not picked:
        return {"status": "none", "personal": personal, "items": [], "disclosure": DISCLOSURE, "note": ""}
    return {"status": "ok", "personal": personal, "items": picked, "disclosure": DISCLOSURE,
            "note": NOTE_PERSONAL if personal else NOTE_GENERAL.format(seed=seeds[0] if seeds else ""),
            "fetched_at": (snap or {}).get("fetched_at")}
