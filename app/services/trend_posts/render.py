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
import json
import os
from urllib.parse import quote

from app.services.trend_posts import frame, policy
from app.services.trend_posts.model import KST, Post, PostProduct, parse_time

CHECK_AT_MALL = "가격은 판매처에서 확인해 주세요"
SITE = "AI 식품 추천"

NAV_ITEMS = (("chat", "대화", "/#"), ("hot", "지금 뜨는 식품", "/#/hot"), ("posts", "트렌드 글", "/trends"))

CSS = """body{margin:0;font-family:system-ui,-apple-system,'Apple SD Gothic Neo',sans-serif;background:#f6f7f4;color:#1d211d;line-height:1.65}
main{max-width:720px;margin:0 auto;padding:20px 18px 60px}a{color:#24533a}nav{font-size:14px;margin-bottom:14px}
h1{font-size:24px;line-height:1.35;margin:6px 0 8px}h2{font-size:18px;margin:28px 0 8px}
.ad{background:#fff4d6;border:1px solid #e8c766;border-radius:10px;padding:10px 12px;font-size:15px;font-weight:600;margin:0 0 14px}
.meta{color:#5d635c;font-size:13px}.card{background:#fff;border:1px solid #e3e5df;border-radius:12px;padding:12px 14px;margin:8px 0}
.price{font-size:14px;color:#3b403a}.muted{color:#6b706a;font-size:13px}ul{padding-left:20px}
.pcard{display:flex;gap:14px;align-items:flex-start}.thumb{width:84px;height:84px;flex:0 0 84px;border-radius:10px;object-fit:cover;background:#eef0ea;border:1px solid #e3e5df}
.pcard .info{min-width:0;flex:1}
.go{display:inline-block;margin-top:6px;padding:7px 12px;border-radius:8px;background:#1d211d;color:#fff;text-decoration:none;font-size:14px}
.list a.t{font-size:17px;font-weight:700;text-decoration:none;color:#1d211d}
.top{position:sticky;top:0;z-index:5;background:rgba(246,247,244,.95);border-bottom:1px solid #e3e5df}
.top .in{max-width:720px;margin:0 auto;display:flex;align-items:center;justify-content:space-between;gap:12px;padding:12px 18px}
.logo{font-weight:700;font-size:17px;color:#1d211d;text-decoration:none}
.menu{display:flex;gap:8px}.menu a{padding:7px 14px;border-radius:999px;color:#4d534c;text-decoration:none;font-size:14px}
.menu a[aria-current=page]{background:#1d211d;color:#fff;font-weight:600}
.tabbar{display:none}
@media (max-width:639px){.menu{display:none}main{padding-bottom:96px}
 .tabbar{display:flex;position:fixed;left:0;right:0;bottom:0;height:60px;padding-bottom:env(safe-area-inset-bottom);background:rgba(246,247,244,.96);border-top:1px solid #e3e5df;z-index:5}
 .tabbar a{flex:1;display:flex;align-items:center;justify-content:center;font-size:12px;color:#6b706a;text-decoration:none}
 .tabbar a[aria-current=page]{color:#24533a;font-weight:700}}"""


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


def _menu(current: str, cls: str) -> str:
    return (f'<nav class={cls} aria-label="주요 메뉴">'
            + "".join(f'<a href="{href}"' + (' aria-current=page' if key == current else "") + f">{label}</a>"
                      for key, label, href in NAV_ITEMS) + "</nav>")


def site_url() -> str:
    """검색엔진에 알려 줄 사이트 주소 (canonical·sitemap·구조화 데이터). .env SITE_URL 로 바꾼다."""
    return (os.environ.get("SITE_URL") or "https://app.trendguide.kr").rstrip("/")


def _page(title: str, body: str, description: str = "", current: str = "posts", head: str = "") -> str:
    """앱(대화·지금 뜨는 식품)과 같은 공통 머리줄 — 로고는 본문 왼쪽 끝, 메뉴는 오른쪽 (2026-11-18 헤더 B안),
    모바일은 아래 탭. head: canonical·구조화 데이터 같은 <head> 추가분."""
    top = f'<header class=top><div class=in><a class=logo href="/#">{SITE}</a>{_menu(current, "menu")}</div></header>'
    return (f"<!doctype html><html lang=ko><head><meta charset=utf-8>"
            f"<meta name=viewport content=\"width=device-width,initial-scale=1\">"
            f"<title>{escape(title)} | {SITE}</title>"
            + (f"<meta name=description content=\"{escape(description)}\">" if description else "")
            + head
            + f"<style>{CSS}</style></head><body>{top}<main>{body}</main>{_menu(current, 'tabbar')}</body></html>")


def _canonical(path: str) -> str:
    return f'<link rel=canonical href="{escape(site_url() + path)}">'


def article_ld(post: Post) -> dict:
    """schema.org Article (2026-11-18) — 검색엔진용. 상품 이미지는 판매처 것이라 넣지 않는다."""
    ld = {"@context": "https://schema.org", "@type": "Article", "headline": post.title[:110],
          "inLanguage": "ko-KR", "mainEntityOfPage": site_url() + post_url(post),
          "author": {"@type": "Organization", "name": SITE, "url": site_url() + "/"},
          "publisher": {"@type": "Organization", "name": SITE, "url": site_url() + "/"},
          "about": post.topic}
    if post.summary:
        ld["description"] = post.summary
    if post.approved_at:
        ld["datePublished"] = post.approved_at
    if post.updated_at:
        ld["dateModified"] = post.updated_at
    return ld


def _ld_script(data: dict) -> str:
    # </script> 가 글 안에 있어도 태그가 끊기지 않게 '<' 를 이스케이프
    return ('<script type="application/ld+json">' + json.dumps(data, ensure_ascii=False).replace("<", "\\u003c")
            + "</script>")


def sitemap_xml(posts: list[Post]) -> str:
    """/sitemap.xml — 첫 화면·트렌드 글 목록·게시된 글. 앱의 # 주소(지금 뜨는 식품)는 검색엔진이 따로 읽지 않아 뺀다."""
    base = site_url()
    rows = [("/", None), ("/trends", posts[0].approved_at if posts else None)]
    rows += [(post_url(p), p.updated_at or p.approved_at) for p in posts]
    out = ['<?xml version="1.0" encoding="UTF-8"?>', '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for path, mod in rows:
        when = parse_time(mod)
        out.append(f"<url><loc>{escape(base + path)}</loc>"
                   + (f"<lastmod>{when.astimezone(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')}</lastmod>" if when else "")
                   + "</url>")
    out.append("</urlset>")
    return "\n".join(out)


def robots_txt() -> str:
    return ("User-agent: *\nDisallow: /admin\nDisallow: /b2b\nDisallow: /api/\nDisallow: /trends/*/go/\n"
            f"Sitemap: {site_url()}/sitemap.xml\n")


def card(post: Post) -> dict:
    """앱 화면(첫 화면 '오늘의 트렌드', 지금 뜨는 식품)이 쓰는 글 요약."""
    return {"id": post.id, "title": post.title, "summary": post.summary, "topic": post.topic,
            "approved_at": post.approved_at, "url": post_url(post)}


def post_page(post: Post, now: datetime | None = None) -> str:
    now = now or datetime.now(timezone.utc)
    e = escape
    parts = ['<nav><a href="/trends">← 트렌드 글 목록</a></nav><article>']
    if post.disclosure and post.products:
        parts.append(f'<p class=ad role=note>{e(post.disclosure)}</p>')
    parts.append(f"<h1>{e(post.title)}</h1>")
    parts.append(f'<p class=meta>게시 {e(_kst(post.approved_at))}'
                 + (f" · 데이터 기준 {e(_kst(post.data_until))}까지" if post.data_until else "") + "</p>")
    if post.summary:
        parts.append(f"<p>{e(post.summary)}</p>")
    framed = bool(post.question or post.answer)      # 2026-11-20 프레임 0.4 글 (예전 글은 아래 예전 순서)
    if framed:
        parts.append("<h2>먼저 답부터</h2>")
        if post.question:
            parts.append(f"<p><b>{e(post.question)}</b></p>")
        if post.answer:
            parts.append("<p>" + " ".join(e(a) for a in post.answer) + "</p>")
        if post.experience == "data":
            parts.append(f"<p class=muted>{e(frame.experience_line(post.topic, 'site'))}</p>")
    if post.why:
        parts.append("<h2>왜 뜨고 있을까</h2><ul>" + "".join(f"<li>{e(w)}</li>" for w in post.why) + "</ul>")
    for sec in post.sections if framed else []:
        if sec.items:
            parts.append(f"<h2>{e(sec.heading)}</h2><ul>" + "".join(f"<li>{e(x)}</li>" for x in sec.items) + "</ul>")
    if framed and post.criteria:
        parts.append("<h2>고르기 전에 볼 것</h2><ol>" + "".join(f"<li>{e(c)}</li>" for c in post.criteria) + "</ol>")
    if framed and post.products and post.constraints:
        parts.append("<h2>구매 전에 알아 둘 것</h2><ul>" + "".join(f"<li>{e(c)}</li>" for c in post.constraints)
                     + "</ul>")

    def recipe_html():
        if not post.recipe:
            return
        r = post.recipe
        src = (f'<a href="{e(r.source_url)}" rel="nofollow noopener" target=_blank>{e(r.source_label)}</a>'
               if r.source_url else e(r.source_label))
        parts.append(f"<h2>레시피 요약 — {e(r.name)}</h2>")
        if r.ingredients:
            parts.append("<p>재료: " + e(", ".join(r.ingredients)) + "</p>")
        if r.step_count:
            parts.append(f"<p class=muted>조리 {r.step_count}단계 — 자세한 순서는 원문에서 확인해 주세요.</p>")
        parts.append(f"<p class=muted>출처: {src} · {e(r.note)}</p>")

    if not framed:
        recipe_html()
    if post.products:
        parts.append("<h2>상품 비교</h2>" if framed else "<h2>재료·상품</h2>")
        if framed and post.checklist:
            parts.append(f"<p class=muted>{e(post.checklist)}</p>")
        for n, p in enumerate(post.products, start=1):
            badge = " · 로켓배송" if p.rocket else ""
            img = (f'<img class=thumb src="{e(p.image_url)}" alt="" loading=lazy referrerpolicy=no-referrer '
                   f'width=84 height=84>' if p.image_url and policy.coupang_image(p.image_url) else "")
            facts = ("<ul class=muted style=\"margin:4px 0\">" + "".join(f"<li>{e(f)}</li>" for f in p.facts) + "</ul>"
                     if framed and p.facts else "")
            parts.append(f'<div class="card pcard">{img}<div class=info><div>{e(p.title)}</div>'
                         f'<div class=price>{e(p.platform)}{badge} · {e(price_line(p, now))}</div>{facts}'
                         f'<a class=go href="{post_url(post)}/go/{n}" rel="sponsored nofollow noopener" '
                         f'target=_blank>판매처에서 보기</a></div></div>')
    if framed:
        recipe_html()
    if post.products:
        parts.append(f"<h2>가격 참고</h2><p class=muted>{e(post.price_note)}</p>")
    if post.sources:
        items = "".join(
            f'<li><a href="{e(s.url)}" rel="nofollow noopener" target=_blank>{e(s.label)}</a></li>' if s.url
            else f"<li>{e(s.label)}</li>" for s in post.sources)
        parts.append(f"<h2>확인한 곳</h2><ul class=muted>{items}</ul>")
    ask = f"요즘 {post.topic} 왜 유행해?"
    parts.append(f'<p style="margin-top:28px"><a class=go href="/?ask={quote(ask)}">이 주제 더 물어보기</a> '
                 f'<a class=go style="background:#fff;color:#1d211d;border:1px solid #d9dcd5" href="/#/hot">지금 뜨는 식품 전체 보기</a></p>')
    parts.append("</article>")
    return _page(post.title, "".join(parts), post.summary,
                 head=_canonical(post_url(post)) + _ld_script(article_ld(post)))


def index_page(posts: list[Post]) -> str:
    e = escape
    body = ['<h1>트렌드 글</h1>'
            '<p class=meta>검색이 갑자기 늘어난 식품을 데이터로 살펴본 글이에요. 운영자가 확인한 글만 올려요.</p>']
    if not posts:
        body.append("<p>아직 게시된 글이 없어요.</p>")
    body.append("<div class=list>")
    for p in posts:
        body.append(f'<div class=card><a class=t href="{post_url(p)}">{e(p.title)}</a>'
                    f'<div class=meta>{e(_kst(p.approved_at))}</div><div>{e(p.summary)}</div></div>')
    body.append("</div>")
    return _page("트렌드 글", "".join(body), "검색이 갑자기 늘어난 식품 트렌드 글", head=_canonical("/trends"))
