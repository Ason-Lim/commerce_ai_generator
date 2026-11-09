"""'요즘 뜨는 식품' — 트렌드 질문을 급상승 리포트로 답한다 (2026-11-06).

예전에는 '요즘 뜨는 식품' 문장 자체가 쿠팡 검색어로 들어가 상품명에 '요즘 뜨는'이 적힌 생수·건강식품이 나왔다.
이제는 매일 아침 만드는 급상승 리포트(surge_YYYY-MM-DD.json)에서 실제로 검색이 늘어난 식품을 고른다.

근거 (리포트에 들어 있는 것만, 고객 화면에 출처를 밝힌다)
  * 네이버 데이터랩 검색어 트렌드 — 그 식품의 평소(약 한 달 전) 대비 배수 (공식 API, 전날까지)
  * 네이버 식품 키워드 순위 · 네이버 블로그 글 제목 증가
  * 유튜브 — 최근 2주 영상 수와 그 전 2주 비교 (YOUTUBE_API_KEY, 제목·게시일만)
  * 구글 트렌드 — 실제 수집이 확인됐을 때만 (지금 CSV 는 예시 데이터라 쓰지 않음)
검색이 늘었다는 것은 관심의 신호일 뿐 맛·품질·안전을 뜻하지 않는다 — 화면에 그렇게 말한다.

판별: 트렌드 말('뜨는·핫한·유행·인기·요즘 잘 팔리는…')이 있고, 구체적인 상품 이름이 없을 때만.
  '요즘 뜨는 식품', '요즘 핫한 먹거리 추천해줘', '요즘 유행하는 과일 뭐야' → 이 답변
  '요즘 인기 있는 사과 추천' (상품 이름 있음) → 평소 쇼핑 검색
  '요즘 유행하는 요리·레시피·음식' → 레시피 트렌드 (recipe_chat.discover, 기존 그대로)
"""
from __future__ import annotations

import datetime as dt
import re

HOT_RE = re.compile(r"뜨는|핫한|핫\s*한|유행|인기|화제|트렌드|급상승|대세|요즘\s*잘\s*(?:나가|팔리)|많이\s*(?:찾는|사는|팔리)"
                    r"|잘\s*팔리는|떠오르는")
DISH_RE = re.compile(r"레시피|요리|만들|해\s*먹|음식|메뉴|만드는")
NOT_HOT_RE = re.compile(r"인기\s*순|순으로|정렬|유행\s*(?:지난|지나)")      # 결과 정렬·부정 표현은 트렌드 질문이 아니다
# 고객 말 → 리포트 식품을 고르는 분류 (식품 이름 사전 — 맞는 게 없으면 전체를 보여 주고 그렇다고 말한다)
CATEGORIES: dict[str, tuple[str, str]] = {
    # 요청 말 정규식, 식품 이름 정규식
    "과일": (r"과일|후식\s*과일", r"귤|감귤|한라봉|천혜향|레드향|황금향|사과|배(?![추])|대봉|홍시|단감|곶감|감(?![자귤])|딸기|포도|샤인|복숭아|멜론|수박"
            r"|키위|망고|바나나|자몽|오렌지|레몬|블루베리|베리|체리|석류|무화과|유자|참외|파인애플"),
    "해산물": (r"해산물|수산물?|생선|회(?!사)|조개", r"과메기|굴|석화|방어|도루묵|새우|꽃게|대게|킹크랩|홍게|전복|오징어|문어|낙지|고등어|갈치|조기"
             r"|연어|참치|광어|우럭|가리비|조개|홍합|미역|멸치|양미리|대구|명태|코다리|황태|과메기|매생이|꼬막|굴비"),
    "간식": (r"간식|과자|디저트|스낵|군것질|빵", r"빼빼로|초콜릿|초코|과자|쿠키|사탕|젤리|케이크|빵|호빵|떡|약과|디저트|아이스크림|스낵|칩|쫀득"),
    "라면": (r"라면|면\s*요리|인스턴트", r"라면|너구리|짜파|불닭|우동|국수|면"),
    "김장": (r"김장", r"김장|절임배추|배추|천수무|무(?![화항])|생새우|젓갈|고춧가루|쪽파|갓"),
    "고기": (r"고기|정육|육류", r"한우|소고기|돼지|삼겹|목살|갈비|등심|닭|오리|양고기|차돌"),
    "선물": (r"선물", r"선물|세트"),
}
_ASK_CAT = {name: re.compile(ask) for name, (ask, _f) in CATEGORIES.items()}
_FOOD_CAT = {name: re.compile(food) for name, (_a, food) in CATEGORIES.items()}
_GENERIC = re.compile(
    r"요즘|요새|최근|지금|재료|이번\s*주|오늘|올해|겨울|가을|제철|식품|상품|먹거리|먹을\s*(?:거리|거|것)|먹는\s*거|제품|아이템|쇼핑|"
    r"뭐(?:가|야|예요|에요|있어|있나요)?|무엇|어떤|어떤\s*게|것|거|게|건|좀|추천(?:해\s*줘|해\s*주세요|해줘|해|좀)?|알려\s*(?:줘|주세요)?|"
    r"보여\s*(?:줘|주세요)?|찾아\s*(?:줘|주세요)?|목록|리스트|순위|top|TOP|있어요?|있나요|해요|인가요|이에요|예요|입니다|"
    r"사\s*(?:볼|먹을|먹)|살\s*만한|만한|사람들|다들|많이|잘|하는|있는|되는|된|이야|야|요|들|중|에서|은|는|이|가|을|를|의|도|로|으로|에|"
    r"뭐\s*먹지|궁금|해|줘|주세요|[?!.,~\s]")


def ask_category(text: str) -> str | None:
    for name, rx in _ASK_CAT.items():
        if rx.search(text or ""):
            return name
    return None


def is_hot_request(text: str) -> dict | None:
    """{'category': None | '과일' …} 이면 트렌드 답변, None 이면 평소 경로."""
    t = (text or "").strip()
    if not t or len(t) > 60 or not HOT_RE.search(t) or DISH_RE.search(t) or NOT_HOT_RE.search(t):
        return None
    category = ask_category(t)
    rest = HOT_RE.sub(" ", t)
    for rx in _ASK_CAT.values():          # '겨울에 인기 있는 과일 선물' — 분류 말은 모두 지운다 (첫 분류로 고름)
        rest = rx.sub(" ", rest)
    rest = _GENERIC.sub("", rest)
    if len(rest) > 1:                 # 상품 이름이 남았다 — '요즘 인기 있는 사과' 는 그 상품 검색
        return None
    return {"category": category}


def food_category(keyword: str) -> set[str]:
    return {name for name, rx in _FOOD_CAT.items() if rx.search(keyword or "")}


def pick(view: dict, category: str | None, limit: int = 6) -> tuple[list[dict], bool]:
    """(items, category_matched).  category 에 맞는 식품이 없으면 전체에서 고르고 False."""
    items = view.get("items") or []
    if category:
        hit = [it for it in items if category in food_category(it["keyword"])]
        if hit:
            return hit[:limit], True
        return items[:limit], False
    return items[:limit], True


def stale_days(view: dict, today: dt.date | None = None) -> int | None:
    until = view.get("data_until")
    if not until:
        return None
    today = today or dt.datetime.now(dt.timezone(dt.timedelta(hours=9))).date()
    return (today - dt.date.fromisoformat(until)).days


def ro(word: str) -> str:
    """'(으)로' — 받침이 있으면 '으로' (ㄹ 받침은 '로'): 라면으로 · 과일로 · 간식으로."""
    last = (word or " ")[-1]
    if not ("가" <= last <= "힣"):
        return "로"
    final = (ord(last) - 0xAC00) % 28
    return "로" if final in (0, 8) else "으로"


def md_date(day: str | None) -> str:
    return f"{int(day[5:7])}/{int(day[8:10])}" if day and len(day) >= 10 else ""


def trend_why(it: dict, data_until: str) -> dict:
    """상품 카드의 첫 사유 — 그 식품의 검색이 늘었다는 사실 (basis 'trend')."""
    since = f"{md_date(it.get('onset'))}부터, " if it.get("onset") else ""
    if it.get("status") == "surging" and it.get("times"):
        text = f"'{it['keyword']}' 네이버 검색량이 평소의 약 {it['times']}배예요 ({since}{md_date(data_until)}까지)"
    else:
        text = f"'{it['keyword']}' 최근 새로 검색되기 시작했어요 ({since}{md_date(data_until)}까지)"
    return {"text": text, "basis": "trend"}


def youtube_line(yt: dict | None) -> str | None:
    if not yt:
        return None
    more = lambda flag: "개 이상" if flag else "개"  # noqa: E731
    return (f"유튜브 최근 {yt['window_days']}일 영상 {yt['recent']}{more(yt.get('recent_more'))} "
            f"(한 달 전 같은 {yt['window_days']}일 {yt['previous']}{more(yt.get('previous_more'))})")


SOURCE_LABEL = {"naver_datalab": "네이버 데이터랩 검색어 트렌드", "naver_food_rank": "네이버 식품 검색어 순위",
                "naver_blog": "네이버 블로그 글 제목", "youtube": "유튜브 영상 제목·게시일", "google": "구글 트렌드"}


def sources_note(sources: dict | None) -> str:
    sources = sources or {}
    used = [SOURCE_LABEL[k] for k in SOURCE_LABEL if sources.get(k)]
    missing = [SOURCE_LABEL[k] for k in ("youtube", "google") if not sources.get(k)]
    text = "**확인한 곳** " + " · ".join(used or [SOURCE_LABEL["naver_datalab"]]) + "."
    if missing:
        text += " 이번 리포트에 쓰지 않은 곳: " + " · ".join(missing) + " (연결 전)."
    text += (" 검색이 늘었다는 것은 **관심이 늘었다는 신호**일 뿐, 맛·품질·안전을 뜻하지 않아요. "
             "계기는 블로그 제목에서 찾은 단서와 AI 추정이에요.")
    return text


_UNIT = re.compile(r"\d+(?:\.\d+)?\s*(?:kg|g|개|입|팩|봉|박스|box|ml|l)?", re.I)


def _flat(text: str) -> str:
    return re.sub(r"[\s·,()\[\]/_\-+]+", "", (text or "").lower())


def names_food(title: str, keyword: str) -> bool:
    """급상승 식품의 상품은 그 이름이 제목에 실제로 있을 때만 (2026-11-06 실제 결과: '볶음너구리'에 불닭볶음면 세트가 섞였다).
    중량·개수 표기는 빼고 견준다: '귤10kg' → '귤', '절임배추20kg' → '절임배추'.  '김장용생새우' 처럼 붙여 쓴 이름은
    앞말('김장용')을 뺀 '생새우'가 제목에 있으면 인정한다."""
    core = _flat(_UNIT.sub("", keyword or ""))
    flat_title = _flat(title)
    if not core:
        return False
    if core in flat_title:
        return True
    for prefix in ("김장용", "국산", "국내산", "제주", "햇", "생"):
        if core.startswith(prefix) and len(core) - len(prefix) >= 2 and core[len(prefix):] in flat_title:
            return True
    return False
