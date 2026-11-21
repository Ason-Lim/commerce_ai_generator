"""사이트 트렌드 글 보고서형 — 규칙 판 report v1.0 (2026-11-21, 채택 2026-11-20 23:41).

순서: 고지 → 제목(변화 중심) → 게시일·데이터 기준일 → 요약 3줄(무엇이·얼마나·왜)
      → ① 데이터(관심 변화 → 확인된 관련 행사·보도 → 가능한 해석 → 확인되지 않은 부분)
      → ② 이번에 볼 기준(2~3줄, 키워드 사실 1줄 이상) → ③ 상품 표 + 결제 전 확인 1줄 + 가격 참고 1줄
      → ④ 레시피(있을 때만) → 확인한 곳(+ 직접 사용 아님 1줄)
규칙 (설계 문서 claude/trend_post_format_feedback_2026-11-20.md §2)
* 원인이 확인되지 않았으면 억지로 채우지 않는다. 제목은 변화 중심 — '왜 뜨는지'는 출처 있는 행사·보도가 있을 때만.
* AI 가 블로그 제목으로 짐작한 계기는 '가능한 해석'에만, 추정이라고 밝혀서.
* 일반 문장('가격은 바뀔 수 있어요')은 가격 참고 한 곳에만. '구매 전에 알아 둘 것'은 키워드 고유 제약이 있을 때만.
* 블로그는 지금 형식(프레임 0.4) 그대로 — 이 모듈은 사이트 글만.
* 보류 결론·광고 고지·가격 규칙·사용 후기 표현 금지 검사는 다른 형식과 공통 (policy).
"""
from __future__ import annotations

import os

from app.services.trend_posts import frame
from app.services.trend_posts.model import Post, PostProduct

FORMAT = "report"
RULES_VERSION = "report v1.1"

TITLE_CHANGE = ["요즘 검색이 늘어난 {k} — 무엇이 달라졌나", "{k} 검색이 늘었어요 — 데이터로 본 변화와 고를 때 볼 것"]
TITLE_CAUSE = ["{k} 검색이 늘어난 이유와 고를 때 볼 것"]          # 출처 있는 행사·보도가 있을 때만
TITLE_HOLD = ["요즘 검색이 늘어난 {k} — 지금 꼭 사야 할까", "{k} 검색이 늘었어요 — 사기 전에 필요한지부터"]

NO_CAUSE = "왜 늘었는지는 아직 확인되지 않았어요."
UNKNOWN_GUESS = "위 해석은 블로그 제목을 바탕으로 한 추정이라, 실제 원인인지는 확인되지 않았어요."
UNKNOWN_EVENTS = "출처로 확인한 관련 행사·보도는 아직 찾지 못했어요."
UNKNOWN_SALES = "검색이 늘었다고 해서 많이 팔렸거나 품질이 좋다는 뜻은 아니에요."
MULTIPLIER_NOTE = "배수는 그 단어의 평소 검색량과 비교한 값이고, 다른 단어와 검색량 크기를 비교한 값은 아니에요."
HEADS = {"change": "관심 변화", "events": "확인된 관련 행사·보도", "reading": "가능한 해석", "unknown": "확인되지 않은 부분"}


def default_format() -> str:
    """**새 초안**의 기본 형식 (기본 report). .env TREND_POST_FORMAT=frame04 면 새 초안만 프레임 0.4 로 만든다.
    이미 만든 글은 저장된 Post.format 대로 그리므로 이 값을 바꿔도 바뀌지 않는다 — 전체 되돌리기가 아님
    (보고서형으로 게시된 글을 되돌리려면 그 글을 내리고 새로 만든다)."""
    return "frame04" if (os.environ.get("TREND_POST_FORMAT") or "").strip().lower() == "frame04" else FORMAT


def _md(day: str | None) -> str:
    return f"{int(day[5:7])}월 {int(day[8:10])}일" if day and len(day) >= 10 else ""


def _cause(item: dict) -> str | None:
    from app.services.trends.surge import _public
    c = item.get("cause")
    if c and c.get("kind") != "불명" and _public(c) and (c.get("cause") or "").strip():
        return c["cause"].strip().rstrip(".")
    return None


def events_of(item: dict) -> list[str]:
    """출처가 붙은 관련 행사·보도만 — item['events'] = [{label, url, date?}] (지금은 수집기가 없어 운영자가 채운다)."""
    out = []
    for e in item.get("events") or []:
        label, url = (e.get("label") or "").strip(), (e.get("url") or "").strip()
        if label and url.startswith(("http://", "https://")):
            out.append((f"{_md(e.get('date'))} " if e.get("date") else "") + f"{label} (출처: {url})")
    return out


def change_lines(item: dict, data_until: str | None) -> list[str]:
    kw = item["keyword"]
    until = f"{_md(data_until)}까지 " if data_until else ""
    out = []
    if item.get("status") == "surging" and item.get("ratio_recent"):
        out.append(f"{until}최근 3일 네이버 검색량이 평소(약 한 달 전)의 약 {item['ratio_recent']:.1f}배예요.")
    else:
        out.append(f"'{kw}'{frame._j(kw, '은', '는')} 한 달 전에는 거의 검색되지 않다가 최근 검색되기 시작했어요.")
    if item.get("onset"):
        out.append(f"검색이 늘기 시작한 때는 {_md(item['onset'])} 무렵이에요.")
    rank = item.get("rank_trend") or {}
    if rank.get("status") == "ok" and rank.get("first") and rank.get("last"):
        out.append(frame.rank_sentence(_md(rank['first']['date']), rank['first']['rank'],
                                          _md(rank['last']['date']), rank['last']['rank']))
    blog = item.get("blog") or {}
    if blog.get("status") == "ok" and blog.get("last7"):
        clue = frame.clue_phrase(blog.get("clues"))
        out.append(f"최근 7일 이 단어가 들어간 블로그 글이 {blog['last7']}건 있었어요"
                   + (f" (그중 {clue})." if clue else "."))
    sig = frame.signals_line(item.get("cross"))
    if sig:
        out.append(sig.rstrip(".") + ".")
    return out


def reading_lines(item: dict) -> list[str]:
    c = _cause(item)
    return [f"블로그 제목으로 본 추정(AI): {c}."] if c else []


def unknown_lines(item: dict, events: list[str], reading: list[str]) -> list[str]:
    out = []
    if not reading and not events:
        out.append(NO_CAUSE)
    elif reading and not events:
        out.append(UNKNOWN_GUESS)
    if not events:
        out.append(UNKNOWN_EVENTS)
    out.append(UNKNOWN_SALES)
    if item.get("status") == "surging" and item.get("ratio_recent"):
        out.append(MULTIPLIER_NOTE)
    return out


def summary_lines(item: dict, data_until: str | None, events: list[str], reading: list[str]) -> list[str]:
    """요약 3줄 — 무엇이 · 얼마나 · 왜 (원인 미확인이면 그렇게)."""
    kw = item["keyword"]
    what = (f"'{kw}' 네이버 검색이 {_md(item['onset'])} 무렵부터 늘었어요." if item.get("onset")
            else f"'{kw}' 네이버 검색이 최근 늘었어요.")
    if item.get("status") == "surging" and item.get("ratio_recent"):
        much = f"최근 3일 검색량은 평소(약 한 달 전)의 약 {item['ratio_recent']:.1f}배예요."
    else:
        much = "한 달 전에는 거의 검색되지 않던 단어예요."
    if events:
        why = "관련 행사·보도가 출처로 확인됐어요 — 아래 데이터 절에 적었어요."
    elif reading:
        why = "원인은 아직 확인되지 않았어요 — 블로그 제목으로 본 추정은 아래 데이터 절에 적었어요."
    else:
        why = NO_CAUSE
    return [what, much, why]


def title(topic: str, *, hold: bool, has_events: bool) -> str:
    bank = TITLE_HOLD if hold else (TITLE_CAUSE if has_events else TITLE_CHANGE)
    return frame.pick(bank, topic, "rt" + ("h" if hold else "b")).format(k=topic)


def amount_fact(products: list[PostProduct]) -> str | None:
    seen: list[str] = []
    for p in products:
        for a in frame.amounts(p.title):
            if a not in seen:
                seen.append(a)
    if not seen:
        return None
    return f"이번에 확인한 상품 구성: {'·'.join(seen[:4])} (상품명 표기 — 같은 단위로 맞춰 비교하세요)."


def look_for(topic: str, kind: str, products: list[PostProduct]) -> list[str]:
    """② 이번에 볼 기준 — 키워드 유형별 기준 2줄 + 이번 상품의 구성(키워드 사실). 상품이 없으면 기준 3줄."""
    crit = frame.criteria(topic, "site", kind)
    fact = amount_fact(products)
    return (crit[:2] + [fact]) if fact else crit[:3]


def own_constraints(topic: str, kind: str) -> list[str]:
    """키워드 고유 제약만 — 공통 문장(가격 바뀜·교환반품)은 가격 참고 한 곳·판매처 안내에 맡긴다."""
    common = set(frame.CONSTRAINTS_COMMON["site"])
    return [c for c in frame.constraints(topic, "site", kind) if c not in common]


def fields(item: dict, data_until: str | None, products: list[PostProduct], kind: str, *, hold: bool = False) -> dict:
    """build 가 Post 에 넣을 보고서형 칸 (제목은 [광고] 전 — 붙이는 건 build·service)."""
    topic = item["keyword"]
    events = events_of(item)
    reading = reading_lines(item)
    summ = summary_lines(item, data_until, events, reading)
    return {"format": FORMAT, "rules_version": RULES_VERSION,
            "title": title(topic, hold=hold, has_events=bool(events)),
            "summary": " ".join(summ[:2]), "summary_lines": summ,
            "data_change": change_lines(item, data_until), "data_events": events, "data_reading": reading,
            "data_unknown": unknown_lines(item, events, reading),
            "criteria": look_for(topic, kind, products), "constraints": own_constraints(topic, kind),
            "checklist": frame.checklist(topic, "site") if products else None}


def apply_conclusion(post: Post, conclusion: str) -> Post:
    """보고서형 글의 결론 바꾸기 — 데이터 절·요약은 그대로, 제목·기준·제약·결론 칸만 다시."""
    from app.services.trend_posts import templates
    from app.services.trend_posts.draft import cause_of
    from app.services.trend_posts.model import PostSection
    topic, has_events = post.topic, bool(post.data_events)
    status = "new" if post.topic_kind == "viral" else None
    if conclusion == "hold":
        ch = templates.hold(topic, status=status, channel="site", cause=cause_of(post))
        return post.model_copy(update={
            "conclusion": "hold", "title": title(topic, hold=True, has_events=has_events),
            "template": ch.id, "topic_kind": ch.kind, "question": ch.question, "answer": ch.answer,
            "criteria": ch.criteria, "constraints": [], "checklist": None,
            "sections": [PostSection(heading=h, items=lines) for h, lines in ch.sections]})
    kind = frame.keyword_type(topic, status=status)
    return post.model_copy(update={
        "conclusion": "buy", "title": title(topic, hold=False, has_events=has_events), "topic_kind": kind,
        "template": None, "question": None, "answer": [], "sections": [],
        "criteria": look_for(topic, kind, post.products), "constraints": own_constraints(topic, kind),
        "checklist": frame.checklist(topic, "site") if post.products else None})
