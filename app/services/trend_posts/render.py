"""서버가 그리는 공개 페이지 — 승인된 글만 받는다 (호출하는 쪽이 service.public/published 로 거른다).

* 모든 글 칸은 이스케이프한다.  스크립트·자동 이동·팝업·숨김 링크를 만들지 않는다 — 상품 링크는 고객이 누르는
  /go/t/{글}/{번호} 하나뿐이고 rel="sponsored nofollow" 를 단다.
* 제휴 상품이 있으면 고지(광고 · 쿠팡 파트너스 대가성 문구 · 사이트 운영 문구)를 본문 맨 위, 상품보다 먼저 둔다.
* 가격: 확인 시각이 있고 30일(STALE_DAYS) 안이면 '○월 ○일 확인 가격 · 지금은 다를 수 있어요'와 함께,
  아니면 숫자 없이 '가격은 판매처에서 확인해 주세요' — 그릴 때마다 지금 시각으로 다시 판단한다.
"""
from __future__ import annotations

from datetime import datetime, timezone
from html import escape
from urllib.parse import quote

from app.services.trend_posts import policy
from app.services.trend_posts.model import KST, Post, PostProduct, parse_time

CHECK_AT_MALL = "가격은 판매처에서 확인해 주세요"
SITE = "AI 식품 추천"

CSS = """body{margin:0;font-family:system-ui,-apple-system,'Apple SD Gothic Neo',sans-serif;background:#f6f7f4;color:#1d211d;line-height:1.65}
main{max-width:720px;margin:0 auto;padding:20px 18px 60px}a{color:#24533a}nav{font-size:14px;margin-bottom:14px}
h1{font-size:24px;line-height:1.35;margin:6px 0 8px}h2{font-size:18px;margin:28px 0 8px}
.ad{background:#fff4d6;border:1px solid #e8c766;border-radius:10px;padding:10px 12px;font-size:15px;font-weight:600;margin:0 0 14px}
.meta{color:#5d635c;font-size:13px}.card{background:#fff;border:1px solid #e3e5df;border-radius:12px;padding:12px 14px;margin:8px 0}
.price{font-size:14px;color:#3b403a}.muted{color:#6b706a;font-size:13px}ul{padding-left:20px}
.go{display:inline-block;margin-top:6px;padding:7px 12px;border-radius:8px;background:#1d211d;color:#fff;text-decoration:none;font-size:14px}
.list a.t{font-size:17px;font-weight:700;text-decoration:none;color:#1d211d}"""


def _kst(v, with_time: bool = False) -> str:
    t = parse_time(v)
    if t is None:
        return ""
    t = t.astimezone(KST)
    return f"{t.year}년 {t.month}월 {t.day}일" + (f" {t.hour}시" if with_time else "")


def price_line(p: PostProduct, now: datetime | None = None) -> str:
    if p.price_krw is None or policy.is_stale(p.price_checked_at, now):
        return CHECK_AT_MALL
    return f"{p.price_krw:,}원 · {_kst(p.price_checked_at, True)} 확인 가격 · 지금은 다를 수 있어요"


def post_url(post: Post) -> str:
    return "/trends/" + quote(post.id)


def _page(title: str, body: str, description: str = "") -> str:
    return (f"<!doctype html><html lang=ko><head><meta charset=utf-8>"
            f"<meta name=viewport content=\"width=device-width,initial-scale=1\">"
            f"<title>{escape(title)} | {SITE}</title>"
            + (f"<meta name=description content=\"{escape(description)}\">" if description else "")
            + f"<style>{CSS}</style></head><body><main>{body}</main></body></html>")


def post_page(post: Post, now: datetime | None = None) -> str:
    now = now or datetime.now(timezone.utc)
    e = escape
    parts = ['<nav><a href="/trends">트렌드 글</a> · <a href="/">AI 추천 대화</a></nav><article>']
    if post.disclosure and post.products:
        parts.append(f'<p class=ad role=note>{e(post.disclosure)}</p>')
    parts.append(f"<h1>{e(post.title)}</h1>")
    parts.append(f'<p class=meta>게시 {e(_kst(post.approved_at))}'
                 + (f" · 데이터 기준 {e(_kst(post.data_until))}까지" if post.data_until else "") + "</p>")
    if post.summary:
        parts.append(f"<p>{e(post.summary)}</p>")
    if post.why:
        parts.append("<h2>왜 뜨고 있을까</h2><ul>" + "".join(f"<li>{e(w)}</li>" for w in post.why) + "</ul>")
    if post.recipe:
        r = post.recipe
        src = (f'<a href="{e(r.source_url)}" rel="nofollow noopener" target=_blank>{e(r.source_label)}</a>'
               if r.source_url else e(r.source_label))
        parts.append(f"<h2>레시피 요약 — {e(r.name)}</h2>")
        if r.ingredients:
            parts.append("<p>재료: " + e(", ".join(r.ingredients)) + "</p>")
        if r.step_count:
            parts.append(f"<p class=muted>조리 {r.step_count}단계 — 자세한 순서는 원문에서 확인해 주세요.</p>")
        parts.append(f"<p class=muted>출처: {src} · {e(r.note)}</p>")
    if post.products:
        parts.append("<h2>재료·상품</h2>")
        for n, p in enumerate(post.products, start=1):
            badge = " · 로켓배송" if p.rocket else ""
            parts.append(f'<div class=card><div>{e(p.title)}</div>'
                         f'<div class=price>{e(p.platform)}{badge} · {e(price_line(p, now))}</div>'
                         f'<a class=go href="{post_url(post)}/go/{n}" rel="sponsored nofollow noopener" '
                         f'target=_blank>판매처에서 보기</a></div>')
        parts.append(f"<h2>가격 참고</h2><p class=muted>{e(post.price_note)}</p>")
    if post.sources:
        items = "".join(
            f'<li><a href="{e(s.url)}" rel="nofollow noopener" target=_blank>{e(s.label)}</a></li>' if s.url
            else f"<li>{e(s.label)}</li>" for s in post.sources)
        parts.append(f"<h2>확인한 곳</h2><ul class=muted>{items}</ul>")
    parts.append("</article>")
    return _page(post.title, "".join(parts), post.summary)


def index_page(posts: list[Post]) -> str:
    e = escape
    body = ['<nav><a href="/">AI 추천 대화</a></nav><h1>트렌드 글</h1>'
            '<p class=meta>검색이 갑자기 늘어난 식품을 데이터로 살펴본 글이에요. 운영자가 확인한 글만 올려요.</p>']
    if not posts:
        body.append("<p>아직 게시된 글이 없어요.</p>")
    body.append("<div class=list>")
    for p in posts:
        body.append(f'<div class=card><a class=t href="{post_url(p)}">{e(p.title)}</a>'
                    f'<div class=meta>{e(_kst(p.approved_at))}</div><div>{e(p.summary)}</div></div>')
    body.append("</div>")
    return _page("트렌드 글", "".join(body), "검색이 갑자기 늘어난 식품 트렌드 글")
