"""요리 경험 지식 (2026-11-12) — '해 본 사람만 아는' 것을 레시피 생성 지시와 검사에 넣는다.

출처: 사용자·블라인드 평가(Gemini)에서 나온 지적 —
  굴국밥 '굴 가장자리가 오므라들 때까지', 감바스 '새우 물기를 닦아야 기름이 튀지 않음 · 마늘 태우지 않기',
  떡갈비 샌드위치 '고기를 굽기 전에 빵을 먼저 굽기', 두바이 쫀득쿠키 '녹인 초콜릿을 섞는 단계가 빠짐',
  떡갈비 '중심까지 익힘(맑은 육즙·중심 온도 75℃)', 페페론치노 5개는 매울 수 있음(취향 조절).
* must=True 인 규칙은 어기면 검사 실패 → 생성기에 문제를 알려 한 번 다시 만들게 한다 (ai_recipe.validate).
* must=False 는 지시문에만 넣는다 (어겨도 보여 준다).
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Callable


@dataclass(frozen=True)
class Rule:
    id: str
    applies: Callable[[str, str, str], bool]      # (요리 이름, 재료 이름들, 단계 전체) → 해당?
    guidance: str                                  # 지시문에 넣는 문장
    check: Callable[[dict], str | None] | None = None   # 레시피 → 문제 문장 (없으면 None)
    must: bool = True


def _steps(r: dict) -> list[str]:
    return [s["text"] if isinstance(s, dict) else str(s) for s in r.get("steps") or []]


def _ings(r: dict) -> str:
    return " ".join(i["name"] for i in r.get("ingredients") or [])


SEAFOOD = re.compile(r"새우|오징어|관자|홍합|낙지|쭈꾸미|주꾸미|조개|굴|전복|생선|연어|대구|명태")
FRY_OIL = re.compile(r"(?<!참)(?<!들)(?:올리브\s*오일|올리브유|식용유|포도씨유|카놀라유|버터|기름)")
FRY_VERB = re.compile(r"볶|튀|굽|구워|지져|부쳐")
DRY = re.compile(r"물기|키친\s*타월|키친타올|페이퍼\s*타월")
GARLIC_OIL = re.compile(r"마늘[^.。]{0,40}(?:기름|오일|올리브유|식용유|볶)|(?:기름|오일|올리브유|식용유)[^.。]{0,40}마늘")
LOW_HEAT = re.compile(r"약불|중약불|타지|태우지|노릇")
OYSTER_SOUP = re.compile(r"굴")
OYSTER_DONE = re.compile(r"오그라|오므라|속까지|완전히\s*익|충분히\s*익|익을\s*때까지")
BREAD_TOAST = re.compile(r"(?:빵|식빵|바게트|번|치아바타|토스트)[^.。]{0,40}(?:굽|구워|토스트|노릇)")
MEAT_COOK = re.compile(r"(?:떡갈비|패티|고기|햄버그|불고기|베이컨|닭)[^.。]{0,40}(?:굽|구워|익혀|익히|부쳐)")
PATTY = re.compile(r"다진\s*(?:소|돼지|닭)?고기|떡갈비|패티|햄버그|미트볼|동그랑땡")
PATTY_DONE = re.compile(r"육즙|중심|속까지|75\s*(?:도|℃)|완전히\s*익|충분히\s*익")
MELT = re.compile(r"녹(?:여|이|인|일)")
HOT = re.compile(r"페페론치노|청양고추|베트남\s*고추|크러시드\s*레드\s*페퍼|고추\s*플레이크")
TASTE = re.compile(r"취향|기호|조절|가감|매운\s*맛")


# 2026-11-12 (사용자): 김장용 생새우(동백하·젓새우)는 1~2cm로 너무 작아 껍질·내장을 손질할 수 없다 — 통째로 넣는다.
# 추천 레시피 3개(생새우무국·생새우부추전·김장용 생새우 전)가 모두 '껍질 벗기고 내장 빼기'를 썼고, 예시 사진도 큰 새우였다.
SMALL_SHRIMP_DISH = re.compile(r"김장|젓새우|동백하|생새우(?:무국|국|탕|찌개|전골|전|부추전|파전|부침|달걀찜|계란찜|찜|볶음|죽|밥)")
SHRIMP_PREP = re.compile(r"(?:새우|껍질|내장|머리)[^.。]{0,20}(?:벗기|벗겨|제거|까서|까\s|빼\s|빼내|빼고|꺼내|발라)|"
                         r"등[^.。]{0,8}(?:갈라|칼집)|이쑤시개|새우[^.。]{0,15}(?:등분|다져|다지|잘게\s*썰|송송)")


def _small_shrimp(d: str, i: str, s: str) -> bool:
    return bool(SMALL_SHRIMP_DISH.search(re.sub(r"\s+", "", d)) or re.search(r"김장용|동백하|젓새우", i))


def _shrimp_whole(r: dict) -> str | None:
    bad = next((x for x in _steps(r) if "새우" in x and SHRIMP_PREP.search(x)), None)
    return ("김장용 작은 생새우는 껍질·내장을 손질하거나 썰 수 없음 — 이물질만 골라 씻어 물기를 빼고 통째로 넣어야 함"
            if bad else None)


# 2026-11-12 RS6(지인 3명) '오해 소지' 8건: 김치찌개 → "김치국으로 보임", 대게찜 → "작게 잘라 덜 먹음직", 굴국밥 → "굴이 애매"(2명),
# 된장찌개 2명. 요리의 생김새를 짚어 준다 — 묶음마다 처음 맞는 하나만 (김치찌개에 '찌개' 일반 문장이 겹치지 않게).
APPEARANCE: list[list[tuple[re.Pattern, str]]] = [
    [   # 국물 요리의 모양
        (re.compile(r"김치찌개"), "Kimchi jjigae: a thick, reduced, deep red-orange stew served bubbling in a small earthenware "
                                "pot (ttukbaegi); the broth is low so chunks of kimchi, pork and tofu rise above it — NOT a thin, "
                                "watery soup."),
        (re.compile(r"된장찌개"), "Doenjang jjigae: a thick, cloudy brown soybean-paste stew in a ttukbaegi, tofu cubes, zucchini "
                                "and onion visible above the broth — NOT a clear soup."),
        (re.compile(r"찌개|전골"), "A Korean jjigae: thick and reduced, served in a ttukbaegi or shallow pot with ingredients "
                                 "showing above the broth — NOT a thin soup."),
        (re.compile(r"국밥"), "Gukbap: rice in hot broth in a deep earthenware bowl, the toppings clearly visible on the surface."),
    ],
    [   # 주재료가 잘 보이게
        (re.compile(r"대게|홍게|킹크랩"), "A whole steamed crab with a bright red-orange shell and long legs intact, served whole on "
                                       "a large platter — NOT small cut pieces."),
        (re.compile(r"굴"), "The oysters are the focus: plump, glossy grey-white oysters clearly visible on top, several of them."),
        (re.compile(r"꼬막"), "Small blood cockles: seasoned cockle meat clearly visible, some still on the half shell."),
    ],
    [   # 유행 디저트 — 사진만 보고 다른 과자로 오해하기 쉽다
        (re.compile(r"두쫀쿠|두바이쫀득쿠키|두바이\s*쫀득"), "Dubai chewy cookie (두쫀쿠): a palm-sized round cookie with a soft, "
            "chewy marshmallow-and-milk-powder shell dusted with cocoa powder; one cookie cut in half shows a thick filling of "
            "toasted shredded kataifi mixed with green pistachio spread — NOT a flat crunchy biscuit or a chocolate bar."),
    ],
    [   # 조리 방식
        (re.compile(r"조림"), "A Korean braise: the pieces coated in a glossy, reduced sauce, little liquid left."),
    ],
]


# 2026-11-12 (사용자): 라면 레시피 재료에 '스프'만 있고 무슨 스프인지 없다 — 라면 스프는 따로도 판다(신라면·진라면 …).
INSTANT_RAMYEON = re.compile(r"라면")
NOT_INSTANT = re.compile(r"라멘|돈코츠|쇼유|미소라|탄탄")


def _instant_ramyeon(d: str, i: str, s: str) -> bool:
    name = re.sub(r"\s+", "", d)
    return bool(INSTANT_RAMYEON.search(name)) and not NOT_INSTANT.search(name)


def _ramyeon_soup_named(r: dict) -> str | None:
    names = [re.sub(r"\s+", "", str(i.get("name") or "")) for i in r.get("ingredients") or []]
    bare = [n for n in names if re.fullmatch(r"(?:분말|액상|건더기)?스프", n)]
    return ("라면 스프가 어떤 것인지 없음 — '봉지라면 1봉지(면·스프 포함)'처럼 쓰고, 사리면만 쓸 때는 어떤 라면 스프인지 적어야 함"
            if bare else None)


def image_hint(dish: str, ingredients: str = "") -> str:
    """AI 예시 사진에 덧붙일 말 — 결과물을 잘못 상상하게 하지 않도록 (RS6 '오해 소지')."""
    out = []
    if _small_shrimp(dish or "", ingredients or "", ""):
        out.append("The shrimp are tiny whole Korean kimchi-season shrimp (about 1-2 cm, pale pink, unpeeled, many of them) "
                   "scattered through the dish — NOT large peeled prawns.")
    name = re.sub(r"\s+", "", dish or "")
    for group in APPEARANCE:
        hit = next((text for rx, text in group if rx.search(name)), None)
        if hit:
            out.append(hit)
    return " ".join(out)


def _seafood_in_hot_oil(d: str, i: str, s: str) -> bool:
    if re.search(r"감바스|튀김|튀기", d) and SEAFOOD.search(i):
        return True
    return any(SEAFOOD.search(x) and FRY_OIL.search(x) and FRY_VERB.search(x) for x in re.split(r"(?<=[.!?요])\s+", s))


def _seafood_dry(r: dict) -> str | None:
    return None if DRY.search(" ".join(_steps(r))) else "해산물을 뜨거운 기름에 넣기 전에 물기를 닦는 단계가 없음 (기름이 튐)"


def _oyster(r: dict) -> str | None:
    s = " ".join(x for x in _steps(r) if "굴" in x)
    if re.search(r"살짝\s*(?:데|익|끓)", s):
        return "굴을 '살짝'만 익히라고 함 — 가장자리가 오그라들 때까지 속까지 익혀야 함"
    return None if OYSTER_DONE.search(s) else "굴을 언제까지 익히는지(가장자리가 오그라들 때까지·속까지) 없음"


def _bread_first(r: dict) -> str | None:
    steps = _steps(r)
    b = next((i for i, s in enumerate(steps) if BREAD_TOAST.search(s)), None)
    m = next((i for i, s in enumerate(steps) if MEAT_COOK.search(s)), None)
    if b is not None and m is not None and b > m:
        return "고기를 구운 뒤에 빵을 굽는 순서 — 빵을 먼저 굽고 고기를 구워야 함"
    return None


def _patty(r: dict) -> str | None:
    return None if PATTY_DONE.search(" ".join(_steps(r))) else "다진 고기 패티가 속까지 익었는지 확인하는 방법이 없음 (맑은 육즙·중심 온도 75℃)"


STANDALONE_MELT = re.compile(r"녹(?:여|이)(?:\s*(?:주세요|둡니다|두세요|놓아\s*주세요|놓으세요|준비해\s*주세요))?\s*[.。!]?\s*$")


def _melted_used(r: dict) -> str | None:
    """'화이트초콜릿을 전자레인지에 녹여 주세요.'로 끝나고, 그 재료가 뒤 단계에 다시 나오지 않으면 문제.
    ('마시멜로와 버터를 녹이고 코코아파우더를 섞어' 처럼 같은 단계에서 이어 쓰면 반죽이 된 것이라 괜찮다)"""
    steps = _steps(r)
    for n in [i["name"] for i in r.get("ingredients") or []]:
        core = re.sub(r"\(.*?\)|\s+", "", n)
        if len(core) < 2:
            continue
        idx = [i for i, s in enumerate(steps) if core in re.sub(r"\s+", "", s)]
        alone = [i for i in idx if STANDALONE_MELT.search(steps[i].strip())]
        if alone and not [i for i in idx if i > alone[0]]:
            return f"'{n}'을(를) 녹인 뒤 쓰는 단계가 없음"
    return None


def _hot_taste(r: dict) -> str | None:
    text = " ".join(_steps(r) + list(r.get("tips") or []))
    return None if TASTE.search(text) else "매운 재료의 양을 취향대로 조절하라는 안내가 없음"


RULES = [
    Rule("instant_ramyeon_soup", _instant_ramyeon,
         "봉지라면 요리는 재료를 '봉지라면 1봉지(면·분말스프·건더기스프 포함)'처럼 쓴다. '라면 사리'와 '스프'를 따로 적지 않는다. "
         "특정 상품 이름(신라면·진라면 등)을 정하지 않되, 사리면만 쓰는 경우에는 '라면 스프(사용하는 라면의 스프)'처럼 무슨 스프인지 "
         "밝히고, 스프는 라면마다 맵기·짠맛이 달라 넣는 양을 맛보며 조절하라고 팁에 적는다.", _ramyeon_soup_named),
    Rule("small_shrimp_whole", _small_shrimp,
         "김장용 생새우(동백하·젓새우)는 1~2cm로 아주 작아 껍질을 벗기거나 내장을 뺄 수 없다 — 작은 게·꼴뚜기·해초 같은 이물질만 "
         "골라내고 옅은 소금물에 흔들어 씻은 뒤 체에 밭쳐 물기를 빼 통째로 넣는다. 썰거나 다지지 않는다.", _shrimp_whole),
    Rule("seafood_dry", _seafood_in_hot_oil,
         "해산물을 뜨거운 기름에 넣기 전에 키친타월로 물기를 꼼꼼히 닦는다 (기름이 튀지 않게, 밑간도 그 뒤에).", _seafood_dry),
    Rule("garlic_low_heat", lambda d, i, s: bool("마늘" in i and GARLIC_OIL.search(s)),
         "기름에 마늘을 볶을 때는 약불~중약불에서 노릇해질 때까지만 — 태우면 쓴맛이 난다.", None, must=False),
    Rule("oyster_done", lambda d, i, s: bool(OYSTER_SOUP.search(i) and re.search(r"국|탕|찌개|죽|국밥", d)),
         "굴은 마지막에 넣고 가장자리가 오그라들 때까지 속까지 익힌다 (너무 오래 끓이면 질겨진다).", _oyster),
    Rule("bread_before_meat", lambda d, i, s: bool(re.search(r"샌드위치|버거|토스트", d)),
         "빵을 굽는 샌드위치는 빵을 먼저 굽고 고기를 굽는다 (고기가 식거나 빵이 기름을 먹지 않게).", _bread_first),
    Rule("patty_done", lambda d, i, s: bool(PATTY.search(d + " " + i)),
         "다진 고기 패티는 속까지 익었는지 확인하는 방법을 쓴다 (가운데를 눌러 맑은 육즙, 또는 중심 온도 75℃). 생고기를 만진 뒤 손과 도마를 씻는다.",
         _patty),
    Rule("melted_used", lambda d, i, s: bool(MELT.search(s)),
         "녹인 재료(초콜릿·버터·마시멜로 등)는 다음 단계에서 어디에 섞거나 바르는지 반드시 쓴다.", _melted_used),
    Rule("hot_to_taste", lambda d, i, s: bool(HOT.search(i)),
         "매운 재료(페페론치노·청양고추 등)는 양을 취향대로 조절하라고 쓴다.", _hot_taste, must=False),
]


def applicable(dish: str, ingredients: str = "", steps: str = "") -> list[Rule]:
    return [r for r in RULES if r.applies(dish or "", ingredients or "", steps or "")]


def guidance(dish: str) -> list[str]:
    """생성 전: 요리 이름만으로 해당할 만한 규칙의 지시 문장 (재료·단계는 아직 모름 → 이름·흔한 재료 기준)."""
    hint = dish + " " + _likely_ingredients(dish)
    return [r.guidance for r in RULES if r.applies(dish, hint, hint)]


def _likely_ingredients(dish: str) -> str:
    return {"감바스": "새우 마늘 올리브유 페페론치노", "굴국밥": "굴", "굴국": "굴"}.get(re.sub(r"\s+", "", dish), "")


def problems(record: dict, dish: str) -> list[str]:
    """생성 후: 반드시 지켜야 할 규칙을 어긴 곳."""
    steps = " ".join(_steps(record))
    out = []
    for r in applicable(dish, _ings(record), steps):
        if r.must and r.check is not None:
            p = r.check(record)
            if p:
                out.append(p)
    return out
