"""블로그 초안의 상품 링크 고르기·넣기 (2026-11-21 사용자 요청).

* 네이버 블로그용: 등록부(naver_connect_links.csv)의 쇼핑커넥트 링크를 키워드마다 골라 넣는다.
  '▶ [여기에 스마트에디터 '쇼핑커넥트'로 상품 삽입: 키워드]' 자리를 링크 묶음으로 바꾼다(빼면 자리 안내로 되돌림).
* 쿠팡용: 쿠팡 파트너스 검색 후보 중에서 골라 키워드 절의 '▶ 쿠팡에서 보기' 묶음을 바꾼다.

본문 안 키워드 절(■ n. 키워드 ~ 다음 ■ 또는 ※ 줄 앞)의 링크 묶음만 바꾸고, 사람이 고친 다른 문장은 건드리지 않는다.
링크는 검사한 주소만(네이버 = naver.me·brandconnect, 쿠팡 = 쿠팡 https). 가격은 넣지 않는다(게시 뒤 바뀌어도 못 고침).
구매 보류 결론 글(쿠팡용)에는 링크를 넣지 않는다. 고지가 없으면 맨 위에 넣고 제목 앞에 [광고]를 붙인다.
"""
from __future__ import annotations

import re

NAVER_HEAD = "▶ 네이버 쇼핑커넥트 상품"
COUPANG_HEAD = "▶ 쿠팡에서 보기"
PLACE = "▶ [여기에 스마트에디터 '쇼핑커넥트'로 상품 삽입: {kw}]"
MAX_LINKS = 3
_SECTION = re.compile(r"^■\s*\d+\.\s*(.+?)\s*$")
FIXED_TAGS = ("트렌드리포트", "요즘뜨는식품", "쿠팡파트너스", "쇼핑커넥트")


class LinkError(ValueError):
    pass


def keywords_of(body: str) -> list[str]:
    return [m.group(1) for ln in (body or "").split("\n") if (m := _SECTION.match(ln))]


def _section(lines: list[str], kw: str) -> tuple[int, int]:
    """키워드 절의 [시작, 끝) 줄 번호. 끝 = 다음 ■ 줄 또는 ※ 줄 (없으면 본문 끝)."""
    start = next((i for i, ln in enumerate(lines) if (m := _SECTION.match(ln)) and m.group(1) == kw), None)
    if start is None:
        raise LinkError(f"본문에서 '■ … {kw}' 절을 찾지 못했어요. 절 제목을 고쳤다면 되돌려 주세요.")
    end = next((i for i in range(start + 1, len(lines)) if _SECTION.match(lines[i]) or lines[i].startswith("※")),
               len(lines))
    while end > start + 1 and not lines[end - 1].strip():      # 절 끝의 빈 줄은 절 밖으로
        end -= 1
    return start, end


def _cut_block(lines: list[str], start: int, end: int, head: str, is_item) -> tuple[list[str], int | None]:
    """절 안의 링크 묶음(머리줄 + 항목 줄)을 빼고, 빠진 자리 번호를 돌려준다."""
    out, at, i = lines[:start], None, start
    while i < end:
        if lines[i].strip() == head:
            at = len(out) if at is None else at
            i += 1
            while i < end and is_item(lines[i]):
                i += 1
            continue
        out.append(lines[i])
        i += 1
    return out + lines[end:], at


def _clean(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "").replace(":", " ")).strip()[:80] or "상품"


# ── 네이버 블로그용 (쇼핑커넥트) ─────────────────────────────────────────
def naver_ok(url: str) -> bool:
    from app.services.affiliate.naver_shopping_connect import validate_link

    return (url or "").startswith("https://") and validate_link(url) is None


def set_naver_links(body: str, kw: str, links: list[dict], disclosure: str) -> str:
    links = links[:MAX_LINKS]
    for x in links:
        if not naver_ok(x.get("url")):
            raise LinkError(f"쇼핑커넥트 발급 링크(naver.me)만 넣을 수 있어요: {x.get('url')}")
    lines = (body or "").split("\n")
    start, end = _section(lines, kw)
    place = PLACE.format(kw=kw)
    lines, at = _cut_block(lines, start, end, NAVER_HEAD, lambda ln: ln.startswith("- ") and "https://" in ln)
    start, end = _section(lines, kw)
    if at is None:
        at = next((i for i in range(start, end) if lines[i].strip() == place), None)
    if at is not None and lines[at].strip() == place:
        del lines[at]
        start, end = _section(lines, kw)
    at = end if at is None else min(at, end)
    block = ([NAVER_HEAD] + [f"- {_clean(x.get('title'))}: {x['url']}" for x in links]) if links else [place]
    lines[at:at] = block
    text = "\n".join(lines)
    if links and disclosure not in text:                   # 링크가 있으면 고지는 맨 위
        text = disclosure + "\n\n" + text
    return text


def connect_options(keywords: list[str], rows: list[dict]) -> dict:
    """키워드마다 등록부 후보 — 키워드 칸이 같은 것 먼저, 그다음 상품명·키워드에 그 말이 들어간 것. 최근 등록이 위.
    주류·실적 제외 유형·발급 링크가 아닌 줄은 뺀다. 'all' = 등록부 전체(직접 고르기용, 최근 60개)."""
    from app.services.affiliate.naver_shopping_connect import is_alcohol_related, validate_product

    def ok(r: dict) -> bool:
        name, link = (r.get("상품명") or "").strip(), (r.get("쇼핑커넥트 링크") or "").strip()
        return bool(name) and naver_ok(link) and not is_alcohol_related(name) and validate_product(name) is None

    good = [r for r in reversed(rows) if ok(r)]

    def opt(r: dict, how: str) -> dict:
        return {"title": (r.get("상품명") or "").strip(), "url": (r.get("쇼핑커넥트 링크") or "").strip(),
                "keyword": (r.get("키워드") or "").strip(), "store": (r.get("스토어명") or "").strip(),
                "issued": (r.get("링크 발급일") or "").strip(), "match": how}

    out = {}
    for kw in keywords:
        k = kw.replace(" ", "")
        exact = [opt(r, "키워드 같음") for r in good if (r.get("키워드") or "").replace(" ", "") == k]
        near = [opt(r, "이름에 포함") for r in good if (r.get("키워드") or "").replace(" ", "") != k
                and (k in (r.get("상품명") or "").replace(" ", "") or k in (r.get("키워드") or "").replace(" ", ""))]
        out[kw] = exact + near
    return {"by_keyword": out, "all": [opt(r, "") for r in good[:60]]}


def auto_naver(body: str, options: dict, disclosure: str, n: int = 2) -> tuple[str, dict[str, int]]:
    """초안 만들 때: 키워드 칸이 같은 등록 링크만 자동으로 넣는다(최근 것부터 n개). 이름만 비슷한 것은 사람이 고른다."""
    used = {}
    for kw, opts in options.get("by_keyword", {}).items():
        exact = [o for o in opts if o["match"] == "키워드 같음"][:n]
        if exact:
            body = set_naver_links(body, kw, exact, disclosure)
            used[kw] = len(exact)
    return body, used


# ── 쿠팡용 ─────────────────────────────────────────────────────────────
def set_coupang_links(title: str, body: str, kw: str, links: list[dict], *, disclosure: str, site_ops: str,
                      ad_prefix: str, hold_line: str) -> tuple[str, str]:
    from app.services.trend_posts import frame, policy

    if hold_line and hold_line in (body or ""):
        raise LinkError("구매 보류 결론 글이라 쿠팡 링크를 넣지 않아요. 링크를 넣으려면 보류를 풀고 초안을 다시 만들어 주세요.")
    links = links[:MAX_LINKS]
    for x in links:
        if not policy.coupang_url(x.get("url") or ""):
            raise LinkError(f"쿠팡 https 링크만 넣을 수 있어요: {x.get('url')}")
    lines = (body or "").split("\n")
    start, end = _section(lines, kw)
    lines, at = _cut_block(lines, start, end, COUPANG_HEAD,
                           lambda ln: (ln.startswith("- ") and "https://" in ln) or ln.startswith("  · "))
    start, end = _section(lines, kw)
    if links:
        block = [COUPANG_HEAD]
        for x in links:
            block.append(f"- {_clean(x.get('title')) if x.get('title') else kw}: {x['url']}")
            facts = frame.product_facts(x.get("title") or "", x.get("rocket"))
            if facts:
                block.append("  · " + " · ".join(facts))
        if at is None:                                    # 처음 넣는 절이면 결제 전 확인 한 줄도 함께
            chk = frame.checklist(kw, "blog")
            if not any(lines[i].strip() == chk for i in range(start, end)):
                block = [chk] + block
            at = end
        lines[at:at] = block
    text = "\n".join(lines)
    if links and disclosure not in text:
        text = f"{disclosure}\n{site_ops}\n\n" + text
        if not text.rstrip().endswith(disclosure):
            text = text.rstrip() + "\n" + disclosure
    if links and not title.lstrip().startswith(ad_prefix):
        title = f"{ad_prefix} {title.strip()}"
    return title, text
