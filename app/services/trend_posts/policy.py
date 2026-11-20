"""게시 차단 검사 (설계 v2 'B2C 트렌드 글 자동화' 정책 검사 항목 + 로드맵 2단계 넘어가는 기준).

check(post, others, now) → 위반 목록.  하나라도 있으면 승인할 수 없다(검토 대기로 남는다).
자동 검사는 권리·약관 준수를 최종 인증하지 않는다 — 운영자 검토가 따로 있다.

항목
  ad_label        제휴 상품이 있으면 제목 맨 앞 [광고], 본문 맨 위 대가성 문구 + 사이트 운영 문구
  link            상품 링크는 쿠팡 주소(https)만, 출처 링크는 http(s)만 — 자동 이동·숨김 링크는 그리는 쪽에서 만들지 않음
  html            글 칸에 HTML·스크립트 조각 금지 (그릴 때도 모두 이스케이프)
  alcohol         주류 주제 글에는 상품 링크 없음
  recipe_source   레시피를 붙였으면 원문 출처 한 줄 + '참고했으며 원문 그대로가 아님'
  numbers         가격은 상품 칸(확인 시각 포함)에만 — 제목·요약·이유 문장에 '○○원'·평점 금지
  price_claim     '최저가'·'가성비' 같은 가격 우위 문구 금지 (price_claims.CLAIM 과 같은 기준)
  price_time      가격이 있는 상품은 확인 시각 필수
  stale_price     승인 시점에 확인한 지 30일(STALE_DAYS)이 넘은 가격 → 가격을 다시 확인한 뒤 승인
  experience      (2026-11-20 프레임 0.4) 직접 사용 기록이 없는 글(experience=data)에 사용 후기 표현 금지
  duplicate       최근 30일 안에 같은 주제로 게시된 글이 있으면 새 글 대신 그 글을 갱신
"""
from __future__ import annotations

import re
from datetime import datetime, timedelta, timezone
from urllib.parse import urlsplit

from app.services.commerce.price_claims import CLAIM, STALE_DAYS
from app.services.trend_posts.model import Post, parse_time

COUPANG_DISCLOSURE = "이 게시물은 쿠팡 파트너스 활동의 일환으로, 이에 따른 일정액의 수수료를 제공받습니다."
SITE_OPS = "수수료는 사이트 무료 운영에 쓰이며, 상품 순서에는 반영하지 않아요."
AD_PREFIX = "[광고]"
COUPANG_HOSTS = {"link.coupang.com", "www.coupang.com", "coupang.com", "m.coupang.com"}
DUPLICATE_DAYS = 30

_ALCOHOL = re.compile(r"와인|맥주|소주|막걸리|전통주|위스키|사케|하이볼|보드카|데킬라|리큐르|양주|청주|약주|과실주|"
                      r"칵테일|샴페인|브랜디|코냑|(?:^|[^가-힣])술(?![빵떡])|안주")
_PRICE_TEXT = re.compile(r"\d[\d,.]*\s*(?:천\s*|만\s*)?원|평점|별점|리뷰\s*\d")
_FIRST_HAND = re.compile(r"내돈내산|직접\s*(?:먹어|써|사용해|구매해|사서)\s*(?:봤|보니|본)|먹어\s*봤어요|써\s*봤어요")
_HTML = re.compile(r"<\s*/?\s*[a-zA-Z!]|javascript:|on[a-z]+\s*=", re.I)


def is_alcohol(text: str) -> bool:
    t = re.sub(r"맛술|미림|술빵|술떡|요리술", "", text or "")
    return bool(_ALCOHOL.search(t))


def disclosure_text() -> str:
    return f"광고 · {COUPANG_DISCLOSURE} {SITE_OPS}"


def has_affiliate(post: Post) -> bool:
    return any(p.link_type == "affiliate" for p in post.products)


def coupang_url(url: str) -> bool:
    parts = urlsplit(url or "")
    return (parts.scheme == "https" and (parts.hostname or "") in COUPANG_HOSTS
            and not parts.username and not parts.password)


IMAGE_HOSTS = ("coupang.com", "coupangcdn.com")


def coupang_image(url: str | None) -> bool:
    """쿠팡 상품 사진 주소 (https · 쿠팡 도메인)."""
    parts = urlsplit(url or "")
    host = (parts.hostname or "").lower()
    return (parts.scheme == "https" and not parts.username and not parts.password
            and any(host == h or host.endswith("." + h) for h in IMAGE_HOSTS))


def http_url(url: str | None) -> bool:
    parts = urlsplit(url or "")
    return parts.scheme in {"http", "https"} and bool(parts.netloc) and not parts.username and not parts.password


def is_stale(checked_at, now: datetime | None = None) -> bool:
    """확인 시각이 없거나 STALE_DAYS 를 넘으면 오래된 가격 (그릴 때 숨기고, 승인을 막는다)."""
    t = parse_time(checked_at)
    now = now or datetime.now(timezone.utc)
    return t is None or now - t > timedelta(days=STALE_DAYS)


def _texts(post: Post) -> list[tuple[str, str]]:
    out = [("title", post.title), ("summary", post.summary)] + [(f"why[{i}]", w) for i, w in enumerate(post.why)]
    if post.recipe:
        out += [("recipe.name", post.recipe.name)] + [(f"recipe.ingredients[{i}]", x)
                                                      for i, x in enumerate(post.recipe.ingredients)]
    out += [("question", post.question or ""), ("checklist", post.checklist or "")]
    out += [(f"answer[{i}]", x) for i, x in enumerate(post.answer)]
    out += [(f"criteria[{i}]", x) for i, x in enumerate(post.criteria)]
    out += [(f"constraints[{i}]", x) for i, x in enumerate(post.constraints)]
    for i, sec in enumerate(post.sections):
        out += [(f"sections[{i}].heading", sec.heading)] + [(f"sections[{i}].items[{j}]", x) for j, x in enumerate(sec.items)]
    out += [(f"products[{i}].title", p.title) for i, p in enumerate(post.products)]
    out += [(f"products[{i}].facts[{j}]", f) for i, p in enumerate(post.products) for j, f in enumerate(p.facts)]
    out += [(f"sources[{i}].label", s.label) for i, s in enumerate(post.sources)]
    return out


def check(post: Post, others: list[Post] | tuple = (), now: datetime | None = None) -> list[dict]:
    now = now or datetime.now(timezone.utc)
    issues: list[dict] = []

    def bad(code: str, message: str, where: str | None = None):
        issues.append({"code": code, "message": message, **({"where": where} if where else {})})

    # 광고 표시
    if has_affiliate(post):
        if not post.title.startswith(AD_PREFIX):
            bad("ad_label", "제휴 상품이 있는 글은 제목 맨 앞에 [광고]를 붙여야 해요.", "title")
        d = post.disclosure or ""
        if COUPANG_DISCLOSURE not in d or "사이트 무료 운영" not in d:
            bad("ad_label", "본문 맨 위 쿠팡 파트너스 대가성 문구와 사이트 운영 문구가 빠졌어요.", "disclosure")
    # HTML 조각
    for where, text in _texts(post) + [("disclosure", post.disclosure or ""), ("price_note", post.price_note)]:
        if _HTML.search(text or ""):
            bad("html", "글 칸에 HTML·스크립트 조각이 있어요.", where)
    # 링크
    for i, p in enumerate(post.products):
        if not coupang_url(p.url):
            bad("link", "상품 링크는 쿠팡 https 주소만 쓸 수 있어요.", f"products[{i}].url")
    for i, p in enumerate(post.products):
        if p.image_url and not coupang_image(p.image_url):
            bad("link", "상품 사진은 쿠팡 https 주소만 쓸 수 있어요.", f"products[{i}].image_url")
    for i, s in enumerate(post.sources):
        if s.url and not http_url(s.url):
            bad("link", "출처 링크는 http(s) 주소만 쓸 수 있어요.", f"sources[{i}].url")
    # 주류
    if post.products and (is_alcohol(post.topic) or is_alcohol(post.title)):
        bad("alcohol", "주류 관련 글에는 상품 링크를 넣지 않아요.", "products")
    # 레시피 출처
    if post.recipe:
        if not (post.recipe.source_label or "").strip():
            bad("recipe_source", "레시피 원문 출처가 빠졌어요.", "recipe.source_label")
        if "원문 그대로가 아" not in (post.recipe.note or ""):
            bad("recipe_source", "'참고했으며 원문 그대로가 아님' 표기가 빠졌어요.", "recipe.note")
        if post.recipe.source_url and not http_url(post.recipe.source_url):
            bad("link", "레시피 출처 링크는 http(s) 주소만 쓸 수 있어요.", "recipe.source_url")
    # 숫자 · 가격 우위 문구 (상품 이름은 판매처 표기라 이 두 검사에서 뺀다 — HTML 검사는 그대로)
    for where, text in _texts(post):
        if where.startswith("products["):
            continue
        if _PRICE_TEXT.search(text or ""):
            bad("numbers", "가격·평점 숫자는 문장에 쓰지 않고 상품 칸(확인 시각 포함)에만 둬요.", where)
        if CLAIM.search(text or ""):
            bad("price_claim", "'최저가'·'가성비' 같은 가격 우위 문구는 쓰지 않아요.", where)
    # 가격 확인 시각 · 오래된 가격
    for i, p in enumerate(post.products):
        if p.price_krw is None:
            continue
        if not parse_time(p.price_checked_at):
            bad("price_time", "가격에 확인 시각이 없어요.", f"products[{i}].price_checked_at")
        elif is_stale(p.price_checked_at, now):
            bad("stale_price", f"확인한 지 {STALE_DAYS}일이 넘은 가격이에요. 가격을 다시 확인한 뒤 승인해 주세요.",
                f"products[{i}].price_checked_at")
    # 프레임 0.4: 자료 정리 글이 직접 사용 후기처럼 보이지 않게
    if post.experience == "data":
        for where, text in _texts(post):
            if _FIRST_HAND.search(text or ""):
                bad("experience", "직접 사용 기록이 없는 글에 '써 봤어요'·'내돈내산' 같은 사용 후기 표현이 있어요.", where)
    # 중복
    for o in others:
        if o.id == post.id or o.topic != post.topic or o.status != "approved":
            continue
        t = parse_time(o.approved_at)
        if t and now - t <= timedelta(days=DUPLICATE_DAYS):
            bad("duplicate", f"최근 {DUPLICATE_DAYS}일 안에 같은 주제 글({o.id})이 게시돼 있어요. 그 글을 갱신해 주세요.",
                "topic")
    return issues
