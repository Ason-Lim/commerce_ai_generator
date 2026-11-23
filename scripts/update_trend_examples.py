#!/usr/bin/env python3
"""홈 화면 '이렇게 물어보세요' 예시용 트렌드 키워드 JSON 생성 (표준 라이브러리만 사용).

입력: ~/food_recommend/daily_food_data/food_YYYY-MM-DD.csv (네이버 식품 키워드 일간 순위 500)
      ~/food-trend-automation/data/google_food_data/trends_v4_YYYY-MM-DD.csv (구글 트렌드, 보조 신호)
출력: commerce_ai_generator/frontend/src/data/trend_examples_YYYY-MM-DD.json (실행일 기준)
      (2026-11-04 integrated_system 에서 옮김 — 화면이 11/2 에 frontend/ 로 옮겨 온 뒤 옛 위치에 쌓이던 문제)

2026-11-22 (창 3-C 마지막): 하루 4칸 = ① 지금 오르는 것 ② 때·행사 ③ 오늘의 생활(눈에 띄는 날씨일 때만 날씨,
아니면 제철 재료 레시피) ④ 알뜰·발견 — 칸 규칙은 app/services/trends/home_cards.py. 칸마다 후보 6개를
trend_examples_candidates_<오늘>.json 에 쓰고, scripts/verify_trend_examples.py 가 실제로 눌러 보고 고른다.
아래 카테고리 4개는 이제 '후보를 모으고 질문을 붙이는 틀'이다 (순위가 2주 전보다 오른 키워드 + 직접 적은 질문).
실행: /usr/bin/python3 scripts/update_trend_examples.py [--dry-run]
"""
import csv, glob, json, os, re, statistics, sys, tempfile
from datetime import date, datetime, timedelta
from pathlib import Path

HOME = Path.home()
def _base(name):  # Mac: ~/name, 원격 점검 환경: ~/mnt/name
    for p in (HOME / name, HOME / "mnt" / name):
        if p.exists():
            return p
    return HOME / name

def _env_file(key):
    """launchd 는 .env 를 읽지 않으므로 저장소 .env 에서 이 키만 읽는다 (표준 라이브러리만)."""
    try:
        for line in (Path(__file__).resolve().parents[1] / ".env").read_text(encoding="utf-8").splitlines():
            if line.strip().startswith(key + "="):
                return line.split("=", 1)[1].strip().strip('"').strip("'")
    except OSError:
        pass
    return ""


def _rank_dir():
    """(폴더, 종류). 2026-11-22: 홈 예시가 며칠째 그대로(수능 끝난 뒤에도 '수능선물추천')였다 — 예전 폴더 daily_food_data 는
    2026-07-09 부터 '최근 30일 묶음' 순위라 하루하루 거의 안 움직인다. 하루 단위 폴더(NAVER_DAILY_RANK_DIR,
    기본 ~/food_recommend/daily_food_rank)를 먼저 쓴다 (app/services/trends/period.py 와 같은 순서)."""
    daily = os.environ.get("NAVER_DAILY_RANK_DIR") or _env_file("NAVER_DAILY_RANK_DIR")
    for cand in ([Path(daily).expanduser()] if daily else []) + [_base("food_recommend") / "daily_food_rank"]:
        files = sorted(glob.glob(str(cand / "food_????-??-??.csv")))
        # 하루 단위 폴더가 최근에 채워지고 있을 때만 (백필만 하고 매일 수집이 멈췄으면 예전 폴더로)
        if files and (date.today() - date.fromisoformat(Path(files[-1]).stem[5:])).days <= 3:
            return cand, "daily"
    return Path(os.environ.get("NAVER_DAILY_DIR", _base("food_recommend") / "daily_food_data")), "mixed"


NAVER_DIR, NAVER_KIND = _rank_dir()
GOOGLE_DIR = Path(os.environ.get("GOOGLE_DATA_DIR", _base("food-trend-automation") / "data/google_food_data"))
REPO = Path(__file__).resolve().parents[1]          # commerce_ai_generator
OUT_DIR = Path(os.environ.get("TREND_EXAMPLES_DIR") or REPO / "frontend" / "src" / "data")
if not OUT_DIR.is_absolute():
    OUT_DIR = REPO / OUT_DIR

ICONS = {"선물용": "Gift", "간식/디저트": "Cookie", "제철요리": "Utensils", "제철과일": "Leaf"}

MAX_RANK = 200      # 현재 순위가 이보다 낮으면 후보 제외
LOOKBACK = 14       # 비교 기준: 약 2주 전
RECENT_FILES = int(os.environ.get("TREND_EXAMPLES_RECENT_FILES") or (2 if NAVER_KIND == "daily" else 1))   # 지금 순위: 하루 단위면 최근 2일, 2일 묶음 파일이면 1개
FALL_LIMIT = 10     # 최근 3일 중앙값이 바로 앞 4일보다 이만큼 넘게 나빠졌으면 '내려가는 중' (예: 끝난 행사)
REPEAT_DAYS = 3     # 최근 이만큼 날의 예시에 나온 키워드는 다른 후보가 있으면 쉬게 한다
STALE_DAYS = 2      # 순위 데이터가 이보다 오래되면 경고

# 카테고리: (UI 태그, 키워드 → 질문 문장(없으면 템플릿), 정규식 보조 규칙, 기본 템플릿들)
CATEGORIES = [
    ("선물용", "선물", {
        "답례품": "돌잔치 하객 답례품으로 1만 원대에 받는 사람이 좋아할 만한 먹거리 추천해 줘",
        "결혼식답례품": "결혼식 답례품으로 100명분, 개당 1만 원 안쪽 먹거리 뭐가 좋을까?",
        "결혼답례품": "결혼 답례품으로 실용적인 먹거리 세트 1만 원대로 추천해 줘",
        "곶감": "어르신 선물용 곶감 세트, 5만 원 안쪽으로 포장 깔끔한 거 추천해 줘",
        "정관장": "부모님께 드릴 정관장 홍삼, 10만 원 안쪽에서 뭐가 좋을까?",
        "홍삼": "부모님 선물로 홍삼 제품 10만 원 안쪽에서 비교해 줘",
        "홍삼스틱100포": "홍삼스틱 100포 선물용으로 가성비 좋은 거 2~3개 비교해 줘",
        "산양삼": "어르신 생신 선물로 산양삼 사려는데 몇 뿌리, 얼마짜리가 적당해?",
        "공진단": "부모님 선물용 공진단, 가격대별로 어떤 차이가 있는지 알려줘",
        "경옥고": "부모님 건강 선물로 경옥고 10만 원 안쪽 추천해 줘",
        "침향환": "어르신 선물로 침향환 사려는데 가격대별로 비교해 줘",
        "한우선물세트": "거래처 선물로 한우 선물세트 15만 원 안쪽 추천해 줘",
        "과일선물세트": "집들이 선물로 과일 선물세트 5만 원 안쪽 추천해 줘",
        "빼빼로": "빼빼로데이에 회사 동료 20명한테 돌릴 과자 선물 추천해 줘",
        # 2026-11-16 사용자 지적: 수능선물은 부모님 선물이 아니라 수험생 응원 선물.
        # 상품어를 문장 맨 앞에 둔다 — 긴 문장은 첫 상품어로 검색하기 때문 (shopping_terms)
        "수능선물": "수능선물, 수험생 응원하려는데 3만 원 안쪽으로 2~3개 비교해 줘",
        "수능": "수능선물, 수험생 응원하려는데 3만 원 안쪽으로 2~3개 비교해 줘",
        "수험생선물": "수험생선물, 응원하려는데 3만 원 안쪽으로 2~3개 비교해 줘",
        "수능간식": "수능간식, 시험 날 수험생이 먹기 부담 없는 걸로 추천해 줘",
        "합격엿": "합격엿, 수험생 응원용으로 포장 깔끔한 거 2~3개 비교해 줘",
    }, "gift", [
        "{kw} 선물하려는데 받는 분이 좋아할 만한 구성으로 5만 원 안쪽 추천해 줘",
        "{kw} 보내려는데 포장 깔끔한 거 2~3개 비교해 줘",   # 2026-11-16: 받는 사람(부모님)을 지어 넣지 않음
    ]),
    ("간식/디저트", "간식", {
        "고구마말랭이": "설탕 안 넣은 고구마말랭이 중에 쫀득하고 아이 간식으로 괜찮은 거 있을까?",
        "하루견과": "매일 먹을 하루견과, 30봉 기준으로 가성비 좋은 거 비교해 줘",
        "견과류": "다이어트 중에 먹을 무염 견과류 추천해 줘",
        "그릭요거트": "단백질 많은 그릭요거트 중에 꾸덕하고 덜 신 거 추천해 줘",
        "찹쌀떡": "택배로 받아도 굳지 않는 찹쌀떡 맛집 추천해 줘",
        "피자설기": "요즘 많이 찾는 피자설기, 어디 것이 맛있어?",
        "백년화편": "백년화편 선물용이랑 집에서 먹을 용으로 뭐가 달라?",
        "화과자": "차랑 같이 먹기 좋은 화과자 세트 추천해 줘",
        "약과": "너무 달지 않은 약과 중에 쫀득한 거 추천해 줘",
        "한과": "어르신 간식으로 부드러운 한과 추천해 줘",
        "촉촉한황치즈칩": "촉촉한황치즈칩 어디서 사는 게 제일 싸?",
        "찹쌀누룽지과자": "아이 간식으로 찹쌀누룽지과자 덜 짠 거 추천해 줘",
        "오란다": "수제 오란다 중에 딱딱하지 않은 거 추천해 줘",
        "다크초콜릿": "카카오 70% 이상 다크초콜릿 중에 쓴맛 덜한 거 추천해 줘",
        "도라지정과": "도라지정과 선물용으로 괜찮은 거 비교해 줘",
        "송편": "택배로 시켜 먹을 송편, 굳지 않게 오는 곳 추천해 줘",
        "모시송편": "영광 모시송편 냉동으로 사도 맛있는 곳 알려줘",
        "창억떡": "창억떡 중에 제일 인기 많은 메뉴가 뭐야?",
        "명가삼대떡집": "명가삼대떡집 떡 중에 아침 식사 대용으로 좋은 거 추천해 줘",
        "이대명과": "이대명과 과자 중에 선물용으로 좋은 구성 알려줘",
        "육포": "맥주 안주로 덜 짠 육포 추천해 줘",
        "약단밤": "까먹기 편한 약단밤 간식용으로 추천해 줘",
        "구운계란": "다이어트 간식으로 구운계란 30구 가성비 좋은 거 찾아줘",
        "땅콩버터": "무가당 땅콩버터 중에 꾸덕한 거 추천해 줘",
        "트러플하몽크래커": "트러플하몽크래커 어디서 사는 게 싸?",
    }, "snack", [
        "{kw} 중에 너무 달지 않고 아이랑 같이 먹기 좋은 거 추천해 줘",
        "요즘 인기 있는 {kw}, 가성비 좋은 거 2~3개 비교해 줘",
    ]),
    ("제철요리", "제철요리", {
        "과메기": "과메기 처음 사보는데 비린내 없이 먹는 법이랑 같이 살 거 알려줘",
        "전어": "가을 제철 전어로 집에서 구이랑 회무침 맛있게 하는 법 알려줘",
        "꽃게": "제철 꽃게로 꽃게탕 4인분 끓이려면 몇 마리랑 재료 뭐 사야 해?",
        "활꽃게": "가을 활꽃게 쪄 먹으려면 손질이랑 찌는 시간 어떻게 해?",
        "톱밥꽃게": "톱밥꽃게 받으면 어떻게 손질해서 쪄 먹어?",
        "대하": "제철 대하 소금구이 하려는데 1kg이면 몇 명이 먹어?",
        "생새우": "가을 생새우로 새우장 담그려면 재료 뭐 사야 해?",
        "활새우": "활새우 소금구이 집에서 하는 법 알려줘",
        "간장게장": "제철 꽃게로 간장게장 직접 담그려면 간장 비율 어떻게 해?",
        "새우젓": "김장할 때 절임배추 20kg에 새우젓은 얼마나 넣어야 해?",
        "절임배추": "절임배추 20kg으로 김장하려면 양념 재료 뭐뭐 사야 해?",
        "절임배추20kg": "절임배추 20kg 김장 양념 비율이랑 필요한 재료 알려줘",
        "배추": "가을배추로 겉절이 만들려면 재료 뭐 사야 해?",
        "고춧가루": "김장용 햇고춧가루 몇 근 사야 하고 어떤 걸 골라야 해?",
        "총각김치": "총각무 제철인데 총각김치 담그려면 재료 뭐 사야 해?",
        "고들빼기": "고들빼기 김치 담그려면 재료 뭐 사야 해?",
        "굴": "제철 굴로 굴전이랑 굴국밥 하려면 몇 kg 사야 해?",
        "가리비": "제철 가리비 찜 하려면 1kg에 몇 명 먹고 뭐 같이 사야 해?",
        "홍게": "홍게 쪄 먹으려면 몇 분 찌고 어떻게 손질해?",
        "대게": "대게 집에서 찌는 법이랑 게딱지 볶음밥 하는 법 알려줘",
        "무늬오징어": "가을 무늬오징어 회로 먹으려면 손질 어떻게 해?",
        "갑오징어": "갑오징어 숙회 데치는 시간이랑 손질법 알려줘",
        "문어": "문어 숙회 삶는 시간이랑 손질법 알려줘",
        "전복": "전복 버터구이 하려면 손질부터 어떻게 해?",
        "고등어": "가을 고등어로 조림 비린내 안 나게 하는 법이랑 재료 알려줘",
        "갈치": "가을 제철 갈치로 조림 4인분 하려면 재료 뭐 사야 해?",
        "삼치": "제철 삼치구이 맛있게 굽는 법 알려줘",
        "방어": "방어 제철인데 대방어 회 몇 kg이면 4명이 먹어?",
        "꼬막": "꼬막 해감하고 꼬막무침 만드는 법 알려줘",
        "송이버섯": "송이버섯 향 살려서 먹는 법이랑 보관법 알려줘",
        "자연산송이버섯": "자연산 송이버섯으로 송이밥 짓는 법 알려줘",
        "능이버섯": "가을 능이버섯으로 백숙 하려면 재료 뭐 사야 해?",
        "참송이버섯": "참송이버섯 구워 먹는 법이랑 어울리는 재료 알려줘",
        "표고버섯": "가을 표고버섯으로 만들 수 있는 반찬 추천해 줘",
        "단호박": "제철 단호박으로 만들 수 있는 쉬운 요리 알려줘",
        "더덕": "더덕구이 양념이랑 손질법 알려줘",
        "도라지": "도라지 쓴맛 빼고 무침 만드는 법 알려줘",
        "연근": "제철 연근으로 연근조림 쫀득하게 만드는 법 알려줘",
        "우엉": "우엉조림 만들려면 손질부터 어떻게 해?",
        "햅쌀": "햅쌀로 밥 맛있게 지으려면 물 양을 어떻게 맞춰?",
        "햇밤": "햇밤으로 밤밥 지으려면 껍질 쉽게 까는 법도 알려줘",
        "밤": "가을 밤으로 밤조림이나 밤밥 만드는 법 알려줘",
    }, "seafood|cook+season", [
        "{season} 제철 {kw}로 집에서 만들기 좋은 요리랑 필요한 재료 알려줘",
        "제철 {kw}로 4인분 저녁 메뉴 만들려면 뭐 사야 해?",
    ]),
    ("제철과일", "제철과일", {
        "귤": "요즘 나오는 조생귤 중에 껍질 얇고 달콤한 건 어떻게 골라?",
        "귤10kg": "귤 10kg 박스로 사려는데 크기(로얄과/소과)별로 뭐가 맛있어?",
        "청귤": "청귤청 담그려면 청귤 몇 kg이랑 설탕 얼마나 필요해?",
        "단감": "아삭한 단감 고르는 법이랑 5kg에 몇 개 들어있는지 알려줘",
        "태추단감": "태추단감은 일반 단감이랑 뭐가 달라? 맛있는 거 추천해 줘",
        "대봉감": "대봉감 홍시 만들려면 며칠 두고 어떻게 보관해?",
        "청도반시": "청도반시 홍시로 먹으려면 언제 사야 해?",
        "감홍사과": "감홍사과 처음 사보는데 문경 거랑 다른 산지랑 뭐가 달라?",
        "문경감홍사과": "문경 감홍사과 5kg 선물용으로 괜찮은 곳 추천해 줘",
        "홍옥사과": "새콤한 홍옥사과 지금 사도 맛있어? 고르는 법 알려줘",
        "시나노골드사과": "시나노골드 사과 맛이 어떤지, 어디서 사면 좋은지 알려줘",
        "홍로사과": "홍로사과 지금 사도 맛있어? 보관법도 알려줘",
        "사과": "요즘 제철 사과 품종 중에 아삭하고 단 건 뭐야?",
        "배": "요즘 나오는 배 중에 당도 높은 품종 추천해 줘",
        "나주배": "나주배 7.5kg 선물용으로 크기 몇 과가 적당해?",
        "샤인머스켓": "샤인머스켓 당도 높은 거 고르는 법 알려줘",
        "무화과": "무화과 지금 끝물이야? 맛있는 거 고르는 법 알려줘",
        "청무화과": "청무화과는 일반 무화과랑 맛이 어떻게 달라?",
        "사과대추": "사과대추 생으로 먹기 좋은 거 고르는 법 알려줘",
        "유자": "유자청 담그려면 유자 몇 kg이랑 설탕 얼마나 필요해?",
        "포도": "요즘 맛있는 포도 품종 추천해 줘",
        "딸기": "딸기 언제부터 맛있어? 품종별 차이 알려줘",
    }, "fruit", [
        "요즘 제철 {kw} 맛있는 거 고르는 법이랑 산지 추천해 줘",
        "{kw} 5kg 사려는데 크기별로 뭐가 맛있어?",
    ]),
]

def load_naver():
    files = sorted(f for f in glob.glob(str(NAVER_DIR / "food_????-??-??.csv")))
    data = {}
    for f in files[-(LOOKBACK + 10):]:
        d = date.fromisoformat(Path(f).stem[5:])
        with open(f, encoding="utf-8-sig") as fh:
            data[d] = {r["keyword"].strip(): int(r["rank"]) for r in csv.DictReader(fh) if r.get("rank", "").isdigit()}
    return data

def load_google_terms(days=7):
    terms = set()
    for f in sorted(glob.glob(str(GOOGLE_DIR / "trends_v4_????-??-??.csv")))[-days:]:
        with open(f, encoding="utf-8-sig") as fh:
            for r in csv.DictReader(fh):
                terms.add(r.get("query", "").strip())
    return terms

def median_rank(data, dates, kw):
    return statistics.median(data[d].get(kw, 501) for d in dates)

# 2026-11-22 (창 3-C ①): 카테고리 정규식을 태그 규칙표(data/keyword_tags.csv, app/services/trends/tags.py)로 옮김 —
# 홈 '지금 순위' 카테고리 탭과 같은 표. CATEGORIES 넷째 칸 = 태그 규칙 ("a|b" 하나라도, "a+b" 모두).
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.services.trends import tags as _tags  # noqa: E402  (표준 라이브러리만 쓰는 모듈)

_SEASON = None


def _kw_tags(kw):
    global _SEASON
    if _SEASON is None:
        try:
            _SEASON = _tags.season_events(date.today())
        except Exception:  # noqa: BLE001 — 달력이 없으면 시즌 없이
            _SEASON = []
    return set(_tags.tags_for(kw, events=_SEASON))


def _rule_hit(rule, have):
    return any(all(t in have for t in alt.split("+")) for alt in rule.split("|"))


# 2026-11-22 사용자: '제철 해남절임배추로 4인분 저녁 메뉴…' — 절임배추를 사는 이유는 김장철이기 때문.
# 행사 준비 기간(태그 규칙표의 시즌 = 행사 달력)에 든 키워드는 그 행사에 맞는 질문으로 묻는다.
EVENT_QUESTIONS = {
    "김장 시즌": ["{kw}로 김장하려는데 4인 가족이면 얼마나 사고 양념 재료는 뭐가 필요해?",
                 "김장용 {kw} 고를 때 뭘 봐야 하고 같이 살 재료 알려줘"],
    "설날": ["설에 쓸 {kw}, 가족 모임 인원에 맞게 얼마나 사야 해?",
             "설 명절 {kw} 고르는 법이랑 같이 준비할 것 알려줘"],
    "추석": ["추석에 쓸 {kw}, 가족 모임 인원에 맞게 얼마나 사야 해?",
             "추석 명절 {kw} 고르는 법이랑 같이 준비할 것 알려줘"],
    "동지": ["동지에 {kw}로 만들 음식이랑 필요한 재료 알려줘"],
    "정월대보름": ["정월대보름에 {kw} 준비하려는데 얼마나 사야 해?"],
}
EVENT_GENERIC = "{event} 준비로 {kw} 사려는데 고르는 법이랑 같이 살 것 알려줘"
SEASON_NAMES = {12: "겨울", 1: "겨울", 2: "겨울", 3: "봄", 4: "봄", 5: "봄", 6: "여름", 7: "여름", 8: "여름"}


_SEASON_BY_DAY = {}


def _season_on(day):
    if day not in _SEASON_BY_DAY:
        try:
            _SEASON_BY_DAY[day] = _tags.season_events(day)
        except Exception:  # noqa: BLE001 — 달력이 없으면 시즌 없이
            _SEASON_BY_DAY[day] = []
    return _SEASON_BY_DAY[day]


def ro(word):
    """'(으)로' — 받침 있으면 '으로'(ㄹ 받침은 '로'), 영문 단위(kg·g)는 '으로'."""
    w = (word or "").strip()
    if not w:
        return "로"
    last = w[-1]
    if "가" <= last <= "힣":
        jong = (ord(last) - 0xAC00) % 28
        return "로" if jong in (0, 8) else "으로"
    return "으로" if w.lower().endswith(("kg", "g")) else "로"


def season_word(d=None):
    return SEASON_NAMES.get((d or date.today()).month, "가을")


def question_for(kw, lex, templates, day):
    """키워드의 예시 질문 — ① 직접 적은 문장 ② 행사 준비 기간이면 그 행사 질문 ③ 칸 기본 틀(계절 말은 오늘 기준)."""
    if kw in lex:
        return lex[kw]
    events = _tags.season_match(kw, _season_on(day))
    if events:
        ev = events[0]
        qs = EVENT_QUESTIONS.get(ev) or []
        stem = ev.split()[0]
        qs = [q for q in qs if not (stem in kw and stem + "용" in q)] or qs    # '김장용 김장용생새우' 방지
        if qs:
            return qs[day.toordinal() % len(qs)].replace("{kw}로", "{kw}{ro}").format(kw=kw, ro=ro(kw))
        return EVENT_GENERIC.format(event=ev, kw=kw)
    t = templates[day.toordinal() % len(templates)].replace("{kw}로", "{kw}{ro}")
    return t.format(kw=kw, ro=ro(kw), season=season_word(day))


def classify(kw):
    for i, (_, _, lex, _rule, _) in enumerate(CATEGORIES):
        if kw in lex:
            return i
    have = _kw_tags(kw)
    for i, (_, _, _, rule, _) in enumerate(CATEGORIES):
        if _rule_hit(rule, have):
            return i
    return None

# 2026-11-22 사용자: 가게 이름은 빼기 ('명가삼대떡집'·'정가네찹쌀견과호떡' 같은 가게·상호가 예시에 뽑혔다)
_SHOP = re.compile(r"(떡집|떡방|상회|농원|농장|목장|식품|푸드|몰$|마켓|상점|본점|공방|제과|베이커리|방앗간|정육점|수산$|"
                   r"명가|삼대|대가|본가|할매|할머니|엄마손|원조|[가-힣]{1,3}네(?=[가-힣])|[가-힣]{2}네$)")
SHOP_MAX_LEN = 8    # 이보다 긴 낱말은 상품명·상호인 경우가 많아 예시에서 뺀다 ('무화과호두파이무설탕')


def is_shop_name(kw):
    return bool(_SHOP.search(kw)) or len(kw) > SHOP_MAX_LEN


def recent_keywords(days=REPEAT_DAYS):
    """최근 며칠(오늘 제외) 예시 파일에 나온 키워드."""
    seen = set()
    for n in range(1, days + 1):
        f = OUT_DIR / f"trend_examples_{(date.today() - timedelta(days=n)).isoformat()}.json"
        try:
            seen |= {r.get("keyword") for r in json.loads(f.read_text(encoding="utf-8")) if isinstance(r, dict)}
        except (OSError, ValueError):
            continue
    return seen - {None}


from app.services.trends import home_cards as hc  # noqa: E402  (표준 라이브러리만)
ALCOHOL = _tags.ALCOHOL
SLOT_MAX = 6        # 칸마다 후보 수 (검증이 떨어뜨리면 다음 후보)
EVENT_QUESTIONS.update({
    "크리스마스": ["크리스마스에 {kw} 준비하려는데 몇 명이면 얼마나 사야 해?"],
    "크리스마스이브": ["크리스마스이브에 {kw} 준비하려는데 몇 명이면 얼마나 사야 해?"],
    "연말 모임": ["연말 모임에 {kw} 준비하려는데 인원별로 얼마나 사야 해?"],
})


def ordered(cands, shown_before):
    """고르는 순서: 2주 전보다 오름 · 최근 내려가지 않음 · 최근 3일 예시에 없음 → 차례로 조건을 풀어 가며.
    2026-11-22 사용자: '매일 바뀌게' — 최근 3일 예시에 나온 키워드는 오르는 후보가 없어도 되도록 피한다."""
    pools = [[c for c in cands if c[4] > 0 and not c[5] and c[1] not in shown_before],
             [c for c in cands if c[4] > 0 and c[1] not in shown_before],
             [c for c in cands if not c[5] and c[1] not in shown_before],
             [c for c in cands if c[1] not in shown_before],
             [c for c in cands if c[4] > 0 and not c[5]],
             cands]
    out = []
    for pool in pools:
        for c in sorted(pool, reverse=True):
            if c[1] not in out:
                out.append(c[1])
    return out


def core_name(kw):
    """'귤10kg' → '귤', '절임배추20kg' → '절임배추' (크기·단위 뗌)."""
    return re.sub(r"\d+(?:\.\d+)?\s*(?:kg|g|ml|l|개|입|박스|구|포기)?$", "", kw, flags=re.IGNORECASE).strip() or kw


def _cat(name):
    return next(c for c in CATEGORIES if c[0] == name)


def _event_question(kw, ev, day):
    qs = EVENT_QUESTIONS.get(ev) or []
    stem = ev.split()[0]
    qs = [q for q in qs if not (stem in kw and stem + "용" in q)] or qs
    if qs:
        return qs[day.toordinal() % len(qs)].replace("{kw}로", "{kw}{ro}").format(kw=kw, ro=ro(kw))
    return EVENT_GENERIC.format(event=ev, kw=kw)


def build_slots(by_cat, shown_before, latest, today=None, surge=None, weather=None):
    """하루 4칸 후보 {칸 이름: [카드 …최대 6]}. 칸 사이 같은 키워드는 검증 단계에서도 다시 거른다."""
    today = today or date.today()
    surge = set(hc.surge_top() if surge is None else surge)          # ① 급상승 상위 6과 겹치지 않게 — 모든 칸에 적용
    events = hc.order_events(_season_on(today))
    is_event = lambda kw: bool(events) and bool(_tags.season_match(kw, events))  # noqa: E731
    cat_of = {c[1]: name for name, cands in by_cat.items() for c in cands}
    ok = lambda kw: kw not in surge and not ALCOHOL.search(kw) and not is_shop_name(kw)  # noqa: E731
    slots = {}

    # ① 지금 오르는 것 — 모든 카테고리, 오른 것만, 행사 품목은 ②로
    allc = [c for cands in by_cat.values() for c in cands if c[4] > 0 and ok(c[1]) and not is_event(c[1])]
    rows = []
    for kw in ordered(allc, shown_before)[:SLOT_MAX]:
        lex = _cat(cat_of[kw])[2]
        # 직접 적은 질문이 없으면 중립 문장 — 칸 기본 틀('제철 ○○로 4인분 저녁 메뉴')은 말린 간식·가공품에 어색하다 (해각포)
        rows.append({"category": hc.SLOT_RISING, "icon": hc.ICON[hc.SLOT_RISING], "keyword": kw,
                     "question": lex.get(kw) or hc.rising_question(kw), "note": f"오르는 검색어 · {kw}",
                     "kind": "product"})
    slots[hc.SLOT_RISING] = rows

    # ② 때·행사 — 순위에 품목이 올라온 행사(근거 있음)를 먼저, 그 안에서 가까운 순. 달력 품목은 식품 태그가 붙는 말만.
    rows = []
    allc = [c for cands in by_cat.values() for c in cands]
    mine = {ev["event"]: [c for c in allc if _tags.season_match(c[1], [ev]) and ok(c[1])] for ev in events}
    for ev in sorted(events, key=lambda e: (not mine[e["event"]], max(e.get("d_day", 0), 0))):
        items = [i for i in ev["items"] if ok(i) and _tags.tags_for(i, events=[])]
        for kw in ordered(mine[ev["event"]], shown_before) + items:
            if len(rows) >= SLOT_MAX:
                break
            if any(r["keyword"] == kw for r in rows):
                continue
            rows.append({"category": hc.SLOT_EVENT, "icon": hc.ICON[hc.SLOT_EVENT], "keyword": kw,
                         "question": _event_question(kw, ev["event"], today), "note": hc.event_note(ev),
                         "kind": "product"})
    if not rows:   # 준비 기간인 행사가 없으면 선물 상황 카드
        name, _, lex, _, templates = _cat("선물용")
        rows = [{"category": hc.SLOT_EVENT, "icon": hc.ICON[hc.SLOT_EVENT], "keyword": kw,
                 "question": question_for(kw, lex, templates, latest), "note": "선물 고르기", "kind": "product"}
                for kw in ordered([c for c in by_cat.get(name, []) if ok(c[1])], shown_before)[:SLOT_MAX]]
    slots[hc.SLOT_EVENT] = rows

    # ③ 오늘의 생활 — 눈에 띄는 날씨면 날씨, 아니면 제철 재료 레시피
    w = hc.load_weather(today) if weather is None else weather
    rows = hc.weather_cards(w, exclude=surge)[:SLOT_MAX]
    if not rows:   # 요리 재료 먼저(과일은 레시피가 드묾), 크기 뗀 이름, ① 첫 카드·행사 품목(②)과 다른 재료
        top1 = {r["keyword"] for r in slots[hc.SLOT_RISING][:1]}
        ing = []
        for name in ("제철요리", "제철과일"):
            for kw in ordered([c for c in by_cat.get(name, []) if ok(c[1]) and not is_event(c[1])], shown_before):
                k = core_name(kw)
                if k not in ing and kw not in top1 and k not in top1:
                    ing.append(k)
        rows = hc.recipe_cards(ing[:SLOT_MAX], today)
    slots[hc.SLOT_LIFE] = rows

    # ④ 알뜰·발견 — 제철 과일·간식·요리 재료 고르는 법 (① 앞 3개·③ 첫 카드와 다른 키워드부터, 크기 뗀 이름)
    taken = {r["keyword"] for r in slots[hc.SLOT_RISING][:3]} | {r["keyword"] for r in slots[hc.SLOT_LIFE][:1]}
    names = []
    for name in ("제철과일", "간식/디저트", "제철요리"):
        for kw in ordered([c for c in by_cat.get(name, []) if ok(c[1]) and not is_event(c[1])], shown_before):
            k = core_name(kw)
            if k not in names:
                names.append(k)
    names = [k for k in names if k not in taken] + [k for k in names if k in taken]
    slots[hc.SLOT_FIND] = [{"category": hc.SLOT_FIND, "icon": hc.ICON[hc.SLOT_FIND], "keyword": kw,
                            "question": hc.find_question(kw, today, n), "note": "고르는 법 · 보관", "kind": "product"}
                           for n, kw in enumerate(names[:SLOT_MAX])]
    # 허용 표현표 밖의 말(긴급성·가격 단정·구매 강요)이 든 카드는 뺀다 — 예: 직접 적은 질문 '어디서 사는 게 제일 싸?'
    return {k: [r for r in rows if hc.copy_ok(r["question"]) and hc.copy_ok(r["note"])] for k, rows in slots.items()}


def main(dry=False):
    data = load_naver()
    if len(data) < 4:
        sys.exit(f"네이버 순위 파일이 부족합니다: {NAVER_DIR}")
    dates = sorted(data)
    latest = dates[-1]
    print(f"  순위 폴더: {NAVER_DIR} ({'하루 단위' if NAVER_KIND == 'daily' else 'daily_food_data — 11-22부터 파일마다 최근 2일 묶음 (그전 7-09~11-21 은 30일 묶음)'}),"
          f" 최신 {latest}", file=sys.stderr)
    if (date.today() - latest).days > STALE_DAYS:
        print(f"  경고: 순위 데이터가 {latest} 로 {(date.today() - latest).days}일 지났어요 — 순위 수집을 확인하세요",
              file=sys.stderr)
    # 2026-11-22: 수집기(~/food_recommend/trend_pipeline/collect_datalab_popular.py)가 이제 파일마다 '최근 2일 묶음'
    # 순위를 저장한다 (이전 30일 묶음) → 지금 순위는 최신 파일 하나로 본다 (이미 2일로 다듬어져 있음).
    recent = dates[-RECENT_FILES:]
    prior = dates[-(RECENT_FILES + 4):-RECENT_FILES] or dates[:-RECENT_FILES]
    shown_before = recent_keywords()
    target = latest - timedelta(days=LOOKBACK)
    past_pool = sorted(dates, key=lambda d: abs((d - target).days))[:3]
    gterms = load_google_terms()

    # 2026-11-22 (창 3-C 마지막): 카테고리 4칸 → 하루 4칸 성격 (app/services/trends/home_cards.py).
    # 예전 카테고리는 '후보를 모으고 질문을 붙이는 틀'로만 남는다 (키워드 → 카테고리 → 직접 적은 질문/기본 틀).
    by_cat = {}
    for i, (cat, tag, lex, pat, templates) in enumerate(CATEGORIES):
        cands = []
        for kw in data[latest]:
            if classify(kw) != i or is_shop_name(kw) or ALCOHOL.search(kw):
                continue
            now = median_rank(data, recent, kw)
            if now > MAX_RANK:
                continue
            before = median_rank(data, past_pool, kw)
            rise = before - now
            falling = now - median_rank(data, prior, kw) > FALL_LIMIT    # 최근 며칠 내려가는 중 (끝난 행사 등)
            score = rise / (now ** 0.5) + (3 if kw in gterms else 0) + (1 if kw in lex else 0)
            cands.append((score, kw, int(now), int(before), rise, falling))
        by_cat[cat] = cands
    alternates = build_slots(by_cat, shown_before, latest, today=date.today())
    picks = []
    used = set()
    for slot, items in alternates.items():
        # 레시피 카드는 실제 요리 이름을 검증 단계가 찾는다 — 검증 전 파일엔 넣지 않음 (검증이 안 돌면 3장)
        item = next((x for x in items if x["keyword"] not in used and x.get("kind") != "recipe"), None)
        if item:
            used.add(item["keyword"])
            picks.append({k: item[k] for k in ("category", "icon", "keyword", "question", "note")})
            print(f"  {slot}: {item['keyword']} — {item['note']} (후보 {len(items)})", file=sys.stderr)

    out = picks
    txt = json.dumps(out, ensure_ascii=False, indent=2)
    if dry:
        print(txt); return
    OUT = OUT_DIR / f"trend_examples_{date.today().isoformat()}.json"
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=OUT_DIR, suffix=".tmp")
    with os.fdopen(fd, "w", encoding="utf-8") as fh:
        fh.write(txt + "\n")
    os.replace(tmp, OUT)
    (OUT_DIR / f"trend_examples_candidates_{date.today().isoformat()}.json").write_text(
        json.dumps(alternates, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"[{datetime.now():%Y-%m-%d %H:%M:%S}] 저장: {OUT} (순위 데이터 {latest}, {len(picks)}개)")

if __name__ == "__main__":
    main(dry="--dry-run" in sys.argv)
