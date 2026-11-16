"""트렌드 글 Q&A (2단계 PR2, 2026-11-16) — '요즘 대방어 왜 유행해?' 같은 질문에 승인된 글만 근거로 답한다.

* 근거: 게시된(승인된) 글만.  초안·검토 대기·반려·내린 글은 찾지도 않는다 (service.published()).
* 답: 글 문장 그대로 고른다(AI 호출 없음 — 사용자 결정 2026-11-16).  답 첫 줄에 근거 글(제목·게시일)을,
  각 줄은 그 글의 어느 칸('왜 뜨고 있을까' · '재료·상품')에서 왔는지 밝힌다.  글에 없는 말은 만들지 않는다.
* 가격: 글의 상품 칸 가격만, 확인 시각과 함께.  30일이 넘었거나 시각이 없으면 숫자 없이 '판매처에서 확인'.
* 근거 글이 없으면 지어내지 않고, 평소 답이 상품 추천이면 그 위에 '관련 트렌드 글이 아직 없어요'를 붙인다
  (레시피·급상승 목록 답은 그대로).
* 질문·원문 열람 기록은 남기지 않는다 — 이용 동의·보존기간·열람 권한을 정한 뒤에 (설계 v2).
* 사는 말('추천해줘'·'사고 싶어' 등)이 있으면 Q&A 가 아니라 평소 상품 추천으로 둔다 (순위·화면 불변).
"""
from __future__ import annotations

import re
import unicodedata
from datetime import datetime

from app.services.trend_posts import policy, render
from app.services.trend_posts.model import Post

ASK_WHY = re.compile(r"왜|이유|원인|어째서|무슨\s*일|트렌드|유행(?:이야|이에요|인가|인지|해|하는|한대|이래)|"
                     r"뜨는\s*(?:거|건|이유|중)|뜬\s*(?:거|건|대)|화제(?:야|예요|인|래)|난리(?:야|래|인)")
ASK_COST = re.compile(r"재료비|비용|얼마(?:나|쯤)?\s*(?:들|드|해|정도)|가격(?:이|은)?\s*(?:얼마|어때|어느)")
BUY = re.compile(r"추천|골라|사고\s*싶|살\s*(?:만|래|게|까)|사줘|구매|주문|찾아\s*줘|보여\s*줘|최저|싼\s*거|저렴|배송|장바구니")
NO_POST = "관련 트렌드 글이 아직 없어요. 대신 상품 후보를 보여 드려요."


def _flat(text: str) -> str:
    return re.sub(r"\s+", "", unicodedata.normalize("NFC", text or "")).lower()


def intent(text: str) -> str | None:
    """'why' · 'cost' · None.  사는 말이 있으면 None (평소 상품 추천)."""
    t = (text or "").strip()
    if not t or len(t) > 80 or BUY.search(t):
        return None
    if ASK_COST.search(t):
        return "cost"
    if ASK_WHY.search(t):
        return "why"
    return None


def find(text: str, published: list[Post]) -> Post | None:
    """질문에 주제 이름이 들어 있는 게시 글 — 긴 주제 먼저, 같은 주제면 최근 게시 먼저."""
    flat = _flat(text)
    hits = [p for p in published if p.status == "approved" and _flat(p.topic) and _flat(p.topic) in flat]
    hits.sort(key=lambda p: (len(_flat(p.topic)), p.approved_at or ""), reverse=True)
    return hits[0] if hits else None


def card(post: Post) -> dict:
    """원문 보기 카드 (trend_post 블록) — 화면은 이 주소의 공개 페이지를 옆 패널에 그대로 띄운다."""
    return {"id": post.id, "title": post.title, "summary": post.summary, "url": render.post_url(post),
            "published": render._kst(post.approved_at), "has_ad": bool(post.disclosure and post.products)}


def answer(post: Post, kind: str, now: datetime | None = None) -> dict:
    """{'lines': [...], 'source': '...', 'cost_hidden': bool} — 글 문장 그대로."""
    source = f"「{post.title}」 · {render._kst(post.approved_at)} 게시"
    if kind == "cost":
        if not post.products:
            return {"lines": ["이 글에는 상품·가격 칸이 없어요."], "source": source, "section": None, "cost_hidden": False}
        lines, hidden = [], 0
        for p in post.products:
            line = render.price_line(p, now)
            hidden += line == render.CHECK_AT_MALL
            lines.append(f"{p.title} — {line}")
        note = [post.price_note]
        if hidden == len(post.products):
            note = [f"글의 가격은 확인한 지 {policy.STALE_DAYS}일이 넘었거나 확인 시각이 없어 숫자를 보여 드리지 않아요."]
        return {"lines": lines + note, "source": source, "section": "재료·상품", "cost_hidden": hidden > 0}
    return {"lines": list(post.why), "source": source, "section": "왜 뜨고 있을까", "cost_hidden": False}
