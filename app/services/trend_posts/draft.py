"""급상승 리포트 항목 → 트렌드 글 초안 (2026-11-20 프레임 0.4: 고지 → 질문과 조건부 답 → 트렌드 이유 → 선택 기준 →
구매 전 제약·결제 전 확인 → 근거 붙은 상품 → 레시피 → 가격 참고).

* 이유 문장은 리포트에 있는 데이터 사실만 쓴다(배수·시작일·순위·블로그 글 수).  원인은 AI 가 블로그 제목으로
  추정한 것이라 '추정'으로 적고, 공개 불가로 표시된 원인·'불명'은 쓰지 않는다 (surge.blog_draft 와 같은 기준).
* 외부 블로그·영상 글은 본문을 옮기지 않는다 — 초안에는 글 수만 쓰고 링크를 넣지 않는다.
* 상품은 공통 검색(search_products) 결과의 순서 그대로, 쿠팡 https 링크만 최대 4개.  가격은 확인 시각과 함께
  상품 칸에만 둔다(실시간 조회 가격은 조회한 시각).  제휴 여부로 고르거나 순서를 바꾸지 않는다.
* 레시피는 공공 레시피(source_level=source)이고 이름이 그 주제로 끝날 때만 붙인다 (1단계 '같은 요리만' 규칙).
"""
from __future__ import annotations

from datetime import datetime, timezone

from app.services.trend_posts import frame, policy
from app.services.trend_posts.model import (HistoryEntry, Post, PostProduct, PostRecipe, PostSource, now_iso,
                                            post_id)

MAX_PRODUCTS = 4
SOURCE_LABEL = {"naver_datalab": ("네이버 데이터랩 검색어 트렌드", "https://datalab.naver.com/"),
                "naver_food_rank": ("네이버 식품 검색어 순위", None),
                "naver_blog": ("네이버 블로그 검색 (글 제목·날짜만)", None),
                "youtube": ("유튜브 영상 제목·게시일", None)}


def _md(day: str | None) -> str:
    return f"{int(day[5:7])}월 {int(day[8:10])}일" if day and len(day) >= 10 else ""


def why_lines(item: dict, data_until: str | None) -> list[str]:
    from app.services.trends.surge import _public

    kw = item["keyword"]
    until = f"{_md(data_until)}까지 " if data_until else ""
    lines = []
    if item.get("status") == "surging" and item.get("ratio_recent"):
        lines.append(f"{until}최근 3일 '{kw}' 네이버 검색량이 평소(약 한 달 전)의 약 {item['ratio_recent']:.1f}배예요.")
    else:
        lines.append(f"'{kw}'은(는) 한 달 전에는 거의 검색되지 않다가 최근 검색되기 시작했어요.")
    if item.get("onset"):
        lines.append(f"검색이 늘기 시작한 때는 {_md(item['onset'])} 무렵이에요.")
    rank = item.get("rank_trend") or {}
    if rank.get("status") == "ok" and rank.get("first") and rank.get("last"):
        lines.append(f"네이버 식품 검색어 순위는 {_md(rank['first']['date'])} {rank['first']['rank']}위에서 "
                     f"{_md(rank['last']['date'])} {rank['last']['rank']}위가 됐어요.")
    blog = item.get("blog") or {}
    if blog.get("status") == "ok" and blog.get("last7"):
        lines.append(f"최근 7일 이 단어가 들어간 블로그 글이 {blog['last7']}건 있었어요.")
    cause = item.get("cause")
    if cause and cause.get("kind") != "불명" and _public(cause):
        lines.append(f"계기(추정): {cause['cause']} — 블로그 제목을 바탕으로 한 추정이라 확정된 사실은 아니에요.")
    lines.append("숫자는 그 단어의 평소 검색량과 비교한 배수이고, 다른 단어와 검색량 크기를 비교한 값은 아니에요.")
    return lines


def products_from_result(result: dict | None, now: datetime | None = None, keyword: str | None = None,
                         limit: int = MAX_PRODUCTS) -> list[PostProduct]:
    checked = now_iso(now)
    out = []
    for it in (result or {}).get("items") or []:
        if it.get("section") != "picks":
            continue
        offer, prod = it.get("offer") or {}, it.get("product") or {}
        url = offer.get("product_url")
        if not url or not policy.coupang_url(url):
            continue
        out.append(PostProduct(
            title=prod.get("title") or "", url=url, platform=offer.get("platform") or "쿠팡",
            link_type=offer.get("link_type") or "direct", affiliate_program=offer.get("affiliate_program"),
            price_krw=offer.get("price_krw"), price_checked_at=offer.get("seen_at") or checked,
            rocket=offer.get("rocket"), keyword=keyword,
            image_url=prod.get("image_url") if policy.coupang_image(prod.get("image_url")) else None,
            facts=frame.product_facts(prod.get("title") or "", offer.get("rocket"))))
        if len(out) >= limit:
            break
    return out


def recipe_from_result(result: dict | None, topic: str) -> PostRecipe | None:
    for it in (result or {}).get("items") or []:
        if "recipe_id" not in it or it.get("source_level") != "source":
            continue
        name = (it.get("title") or "").strip()
        if not name.replace(" ", "").endswith(topic.replace(" ", "")):
            continue
        return PostRecipe(name=name, source_label=it.get("source_name") or it.get("provider") or "",
                          recipe_id=it.get("recipe_id"),
                          ingredients=[i.get("name") for i in it.get("ingredients") or [] if i.get("name")][:12],
                          step_count=len(it.get("steps") or []))
    return None


def build(item: dict, data_until: str | None, *, products: list[PostProduct] = (), recipe: PostRecipe | None = None,
          now: datetime | None = None, sources: dict | None = None) -> Post:
    now = now or datetime.now(timezone.utc)
    topic = item["keyword"]
    day = (data_until or now.date().isoformat())[:10]
    products = [] if policy.is_alcohol(topic) else list(products)
    affiliate = any(p.link_type == "affiliate" for p in products)
    title = f"요즘 검색이 크게 늘어난 '{topic}' — 왜 뜨는지와 함께 볼 것"
    used = [k for k in SOURCE_LABEL if k == "naver_datalab" or (sources or {}).get(k)]
    stamp = now_iso(now)
    return Post(
        id=post_id(day, topic), topic=topic, data_until=data_until,
        title=(policy.AD_PREFIX + " " + title) if affiliate else title,
        summary=f"'{topic}' 검색이 왜 늘었는지 데이터로 보고, 함께 볼 레시피와 상품을 정리했어요.",
        why=why_lines(item, data_until), recipe=recipe, products=products,
        sources=[PostSource(kind="data", label=SOURCE_LABEL[k][0], url=SOURCE_LABEL[k][1]) for k in used],
        disclosure=policy.disclosure_text() if affiliate else None,
        experience="data", question=frame.question(topic),
        answer=frame.answer(topic, bool(products), any(p.rocket for p in products)),
        criteria=frame.criteria(topic), constraints=frame.constraints(),
        checklist=frame.CHECKLIST if products else None,
        created_at=stamp, updated_at=stamp,
        history=[HistoryEntry(at=stamp, action="create", note=f"급상승 리포트 {data_until or ''}")])
