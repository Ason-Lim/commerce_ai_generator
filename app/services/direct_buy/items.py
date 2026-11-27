"""해외 직구 품목표 (2026-11-27) — 대화 검색어가 이 표에 맞을 때만 결과 아래에 해외 직구(Shopify) 칸을 붙인다.

status
- ok        일반 가공식품. 상품을 보여 준다 (그래도 위해식품 목록·성분 확인은 손님 몫 — 도우미 단계로 안내)
- caution   검역·수량 등 조건이 있음. 상품을 보여 주되 칸 위에 조건 한 줄
- blocked   축산물·유제품·생과일 등 반입이 막히는 품목. 상품을 보여 주지 않음.
            손님이 '직구·해외'를 말했을 때만 안내 한 줄 (평소 '사과'·'치즈' 검색에는 아무것도 붙이지 않음 — 화면 군더더기 방지)

근거(2026-11-27 확인, 법률 자문 아님 — 최종은 통관·검역 현장 결과):
- 관세청 '실패 없는 해외직구 필수 체크리스트'(2026-01-08): 면세 한도, 건강기능식품 1인 6병, 유해성분은 식품안전나라 해외직구 정보.
- 농림축산검역본부(정책브리핑): 해외직구·국제우편 동식물류도 검역 신고. 생과일·생채소·종자·묘목·한약재가 검역 대상, 대부분의 생과일은 금지품.
- 검역본부 휴대 반입 금지 대표 품목(2025-08 보도): 햄·소시지·육포·베이컨·고기 든 즉석식품, 생곡물·생땅콩, 치즈·버터·분유·요거트 등 유제품,
  씨가 든 일부 건조 과일.
- 우체국 EMS 국제우편 검역 안내: 상업적으로 제조된 일부 축산물·가공 농산물은 반입 가능, 5kg 미만 멸균 통조림·병조림·레토르트 축산물 가능
  (소고기 포함 불가). 반입 제한 예: 껍질 있는 호두, 생고추, 생대추, 망고.
- 식물방역법 개정(2026-12-17 시행): 우편물·탁송품에 정확한 품명 기재 의무.
- 커피 생두/볶은 원두 구분은 2차 자료 — 볶은 원두·드립백 등 가공품 위주로만 찾는다.
문서: 프로젝트 claude/direct_buy_import_items_2026-11-27.md
"""
from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class Item:
    key: str
    label: str
    aliases: tuple[str, ...]
    query: str                 # Shopify 검색어(영어가 잘 찾아짐)
    status: str                # ok · caution · blocked
    note: str = ""
    must: str = ""             # 상품명에 있어야 하는 말(정규식, 대소문자 무시) — 엉뚱한 상품 거르기 (2026-11-27)
    allow: str = ""            # 가공식품 재료로 흔한 검역 낱말(butter·milk·honey…)은 이 품목에서 걸러 내지 않음 (2026-11-27)


ITEMS: tuple[Item, ...] = (
    # ── ok: 일반 가공식품
    Item("olive_oil", "올리브유", ("올리브유", "올리브 오일", "올리브오일", "엑스트라버진", "엑스트라 버진"), "extra virgin olive oil", "ok"),
    Item("olives", "올리브 절임", ("올리브 절임", "올리브절임", "블랙 올리브", "블랙올리브", "그린 올리브", "그린올리브", "칼라마타",
                                 "올리브 병조림", "올리브"),
         "kalamata olives jar", "ok", "병·캔으로 가공한 제품만 찾았어요. 생올리브는 들여올 수 없어요."),
    Item("balsamic", "발사믹 식초", ("발사믹",), "balsamic vinegar of modena", "ok"),
    Item("maple", "메이플 시럽", ("메이플 시럽", "메이플시럽", "메이플"), "pure maple syrup", "ok"),
    Item("truffle_oil", "트러플 오일", ("트러플 오일", "트러플오일", "트러플 소스"), "truffle oil", "ok"),
    Item("pasta", "파스타 면", ("파스타", "스파게티", "펜네", "링귀네"), "dried italian pasta", "ok"),
    Item("chocolate", "초콜릿", ("초콜릿", "초콜렛"), "dark chocolate bar", "ok", allow="milk|butter|honey"),
    Item("jam", "잼", ("잼", "마멀레이드"), "fruit jam jar", "ok"),
    Item("hot_sauce", "핫소스", ("핫소스", "핫 소스", "타바스코"), "hot sauce", "ok"),
    Item("tea", "차(티백·잎차)", ("홍차", "얼그레이", "허브티", "말차"), "loose leaf tea", "ok"),
    # 2026-11-27 추가 — 국내 해외직구몰(쿠팡 로켓직구 등)에서 많이 파는 가공식품 품목명만 조사해 넣음 (가격·상품 정보는 저장 안 함)
    Item("vinegar", "사과식초", ("사과식초", "애사비", "애플사이다", "애플 사이다"), "apple cider vinegar", "ok"),
    Item("salt", "소금", ("=소금", "천일염", "핑크솔트", "히말라야 소금", "히말라야소금", "플뢰르 드 셀", "게랑드 소금", "말돈"),
         "sea salt flakes", "ok"),
    Item("coconut_oil", "코코넛 오일", ("코코넛오일", "코코넛 오일"), "organic coconut oil", "ok"),
    Item("avocado_oil", "아보카도 오일", ("아보카도오일", "아보카도 오일"), "avocado oil", "ok"),
    Item("nut_butter", "땅콩버터", ("땅콩버터", "땅콩 버터", "피넛버터", "피넛 버터", "아몬드버터", "아몬드 버터"), "peanut butter", "ok",
         allow="butter|honey"),
    Item("mayo", "마요네즈", ("마요네즈", "=마요", "큐피"), "japanese mayonnaise", "ok"),
    Item("chili_oil", "칠리오일", ("칠리오일", "칠리 오일", "고추기름", "라유", "칠리크리스프", "칠리 크리스프"), "chili crisp oil", "ok"),
    Item("candy", "사탕·캔디", ("사탕", "캔디", "목캔디", "젤리빈"), "hard candy", "ok", allow="butter|milk|honey"),
    Item("cookie", "쿠키·비스킷", ("쿠키", "비스킷", "크래커", "웨하스"), "cookies", "ok",
         must=r"cookie|biscuit|shortbread|cracker|wafer|biscotti|sabl[eé]", allow="butter|milk|egg|honey"),
    Item("bar", "에너지바·프로틴바", ("에너지바", "프로틴바", "단백질바", "그래놀라바", "시리얼바"), "protein bar", "ok",
         allow="butter|milk|honey"),
    Item("sweetener", "감미료", ("감미료", "스테비아", "알룰로스", "에리스리톨", "몽크푸르트", "나한과"), "stevia sweetener", "ok"),
    # ── caution: 조건 있음
    Item("coffee", "커피 원두", ("원두", "커피콩", "드립백"), "roasted coffee beans", "caution",
         "볶은 원두·드립백 같은 가공품만 찾았어요. 볶지 않은 생두는 식물검역 대상이에요."),
    Item("honey", "꿀", ("=꿀", "벌꿀", "마누카", "아카시아꿀", "야생화꿀", "천연꿀"), "raw honey", "caution",
         "꿀은 성분·원산지에 따라 위해식품 목록·검역 확인이 필요할 수 있어요. 결제 전 확인해 주세요."),
    Item("nuts", "견과류", ("견과", "아몬드", "캐슈", "마카다미아", "피스타치오", "피칸"), "roasted nuts", "caution",
         "볶거나 가공한 견과류만 권해요. 껍질 있는 호두·생땅콩 등은 반입이 제한돼요."),
    Item("dried_fruit", "건조 과일", ("건조 과일", "말린 과일", "건과일", "건망고", "건자두", "대추야자", "데이츠"), "dried fruit", "caution",
         "씨가 든 건조 과일 일부는 들여올 수 없어요. 씨 없는 가공품인지 확인해 주세요."),
    Item("spice", "향신료", ("향신료", "시나몬", "사프란", "파프리카 가루", "커민", "스파이스"), "ground spices", "caution",
         "가루로 가공한 향신료 위주로 찾았어요. 씨앗 형태·생 허브는 검역 대상일 수 있어요."),
    Item("granola", "그래놀라·시리얼", ("그래놀라", "뮤즐리", "시리얼", "오트밀"), "granola", "caution",
         "가공한 시리얼만 찾았어요. 생곡물은 들여올 수 없어요."),
    Item("supplement", "건강기능식품", ("영양제", "비타민", "오메가3", "유산균", "프로바이오틱"), "vitamin supplement", "caution",
         "건강기능식품은 1인 6병까지 자가사용으로 인정돼요. 성분은 식품안전나라 해외직구 정보에서 확인해 주세요."),
    Item("protein", "단백질 보충제", ("프로틴 파우더", "프로틴파우더", "단백질 보충제", "단백질보충제", "웨이 프로틴", "웨이프로틴"),
         "whey protein powder", "caution",
         "유청(우유) 단백질 제품은 성분에 따라 통관이 막힐 수 있어요. 식품안전나라 해외직구 정보에서 제품을 확인해 주세요."),
    # ── blocked: 상품 없음 (직구를 말했을 때만 안내)
    Item("dairy", "치즈·버터 등 유제품", ("치즈", "버터", "요거트", "요구르트", "분유", "생크림"), "", "blocked",
         "치즈·버터·분유·요거트 같은 유제품은 검역 대상이라 직구로 들여오기 어려워요(기준에 맞지 않으면 반송·폐기)."),
    Item("meat", "육가공품", ("햄", "소시지", "육포", "베이컨", "살라미", "하몽", "프로슈토", "고기"), "", "blocked",
         "햄·소시지·육포·베이컨 같은 육가공품은 반입이 금지돼요. 멸균 통조림 일부만 예외예요(소고기 포함 불가)."),
    Item("fresh", "생과일·생채소", ("생과일", "생올리브", "생채소", "망고", "체리", "아보카도"), "", "blocked",
         "생과일·생채소는 식물검역 대상이고 대부분 수입이 금지돼요."),
    Item("seed", "씨앗·생곡물", ("씨앗", "종자", "묘목", "생땅콩", "생곡물"), "", "blocked",
         "씨앗·묘목·생곡물·생땅콩은 들여올 수 없거나 검역증명서가 필요해요."),
)

# 손님 검색어의 꾸밈말 → 영어 (Shopify 검색어 앞에 붙임). 아는 말만 쓴다 — 없는 말은 지어내지 않음 (2026-11-27 '버터 쿠키')
MODIFIERS: tuple[tuple[str, str], ...] = (
    ("버터", "butter"), ("초코칩", "chocolate chip"), ("초코", "chocolate"), ("초콜릿", "chocolate"), ("오트", "oat"),
    ("귀리", "oat"), ("말차", "matcha"), ("녹차", "green tea"), ("아몬드", "almond"), ("땅콩", "peanut"), ("피넛", "peanut"),
    ("생강", "ginger"), ("진저", "ginger"), ("쇼트브레드", "shortbread"), ("데니쉬", "danish"), ("덴마크", "danish"),
    ("레몬", "lemon"), ("코코넛", "coconut"), ("시나몬", "cinnamon"), ("바닐라", "vanilla"), ("유기농", "organic"),
    ("무설탕", "sugar free"), ("글루텐프리", "gluten free"), ("비건", "vegan"), ("마누카", "manuka"), ("다크", "dark"),
    ("밀크", "milk"), ("트러플", "truffle"), ("훈제", "smoked"), ("스페인", "spanish"), ("이탈리아", "italian"),
    ("그리스", "greek"), ("프랑스", "french"), ("일본", "japanese"),
)


def query_for(it: Item, term: str | None) -> str:
    """품목 기본 검색어 + 손님 말의 꾸밈말 ('버터 쿠키' → 'butter cookies'). 기본 검색어에 이미 있는 말은 더하지 않음."""
    t = (term or "")
    mods = {ko for ko, _en in MODIFIERS}
    for a in sorted((a.lstrip("=") for a in it.aliases), key=len, reverse=True):
        if a not in mods:                             # '마누카'처럼 별칭이자 꾸밈말인 것은 남김
            t = t.replace(a, " ")                     # 품목 이름 자체는 빼고 꾸밈말만
    words: list[str] = []
    for ko, en in MODIFIERS:
        if ko in t and en not in it.query and en not in words and not any(en in w for w in words):
            words.append(en)
            t = t.replace(ko, " ")
    return " ".join(words[:2] + [it.query]).strip()


def relevant(it: Item, title: str | None) -> bool:
    return not it.must or bool(re.search(it.must, title or "", re.I))


_INTENT = re.compile(r"직구|해외|수입산|외국\s*(거|것|제품|상품)")


def match(label: str | None, text: str | None = None) -> Item | None:
    """검색어(label)·문장에서 가장 긴 별칭이 맞는 품목. blocked 는 '직구·해외'를 말했을 때만 돌려준다.
    blocked 별칭이 더 길게 맞으면(예: '생올리브' ⊃ '올리브') blocked 가 이긴다 — 반입 금지 품목을 상품으로 보이지 않게."""
    hay = " ".join(f"{label or ''} {text or ''}".split())
    if not hay:
        return None
    lab = " ".join((label or "").split())
    best: tuple[int, Item] | None = None
    for it in ITEMS:
        for a in it.aliases:
            hit = (lab == a[1:]) if a.startswith("=") else (a in hay)   # '=꿀' — 검색어가 딱 '꿀'일 때만 ('꿀고구마' 제외)
            if hit and (best is None or len(a) > best[0]):
                best = (len(a), it)
    if best is None:
        return None
    it = best[1]
    if it.status == "blocked" and not _INTENT.search(text or ""):
        return None
    return it


def by_key(key: str) -> Item | None:
    return next((it for it in ITEMS if it.key == key), None)
