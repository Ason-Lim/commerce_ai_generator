"""Answers to cooking / substitution questions in the current recipe context.

Two kinds of content are kept apart on purpose:

* 원문 근거 — sentences quoted from the recipe source (steps / ingredient table)
* 일반 조리 제안 — general kitchen knowledge from a small curated table,
  always labelled as not coming from the recipe source.  No quantity in the
  table claims to be the recipe's requirement.
"""
from __future__ import annotations

import re

# keyword(s) in the question → general suggestion (not from the recipe source)
GENERAL_TIPS: tuple[tuple[tuple[str, ...], str], ...] = (
    (("생크림", "대신"), "생크림이 없으면 우유에 버터를 조금 더해 농도를 보충하는 방법을 많이 써요. 생크림보다 묽으니 더 졸여 주세요."),
    (("생크림", "대체"), "생크림이 없으면 우유에 버터를 조금 더해 농도를 보충하는 방법을 많이 써요. 생크림보다 묽으니 더 졸여 주세요."),
    (("생크림", "없으면"), "생크림이 없으면 우유에 버터를 조금 더해 농도를 보충하는 방법을 많이 써요. 생크림보다 묽으니 더 졸여 주세요."),
    (("우유", "대신"), "우유 대신 생크림만 쓰면 더 진해져요. 너무 되직하면 파스타 삶은 물로 농도를 맞춰 보세요."),
    (("베이컨", "대신"), "베이컨 대신 햄이나 버섯을 쓸 수 있어요. 버섯은 수분이 나오니 먼저 충분히 볶아 주세요."),
    (("베이컨", "없으면"), "베이컨 대신 햄이나 버섯을 쓸 수 있어요. 버섯은 수분이 나오니 먼저 충분히 볶아 주세요."),
    (("양파", "대신"), "양파가 없으면 대파 흰 부분으로 단맛과 향을 낼 수 있어요."),
    (("버터", "대신"), "버터 대신 올리브유나 식용유로 볶을 수 있어요. 고소한 맛은 줄어들어요."),
    (("마늘", "대신"), "다진마늘이 없으면 마늘 가루를 조금 쓰거나 생략할 수 있어요."),
    (("바질",), "바질은 재료표에 분량이 없고 조리 과정에만 나와요. 없으면 빼거나 파슬리 같은 허브로 바꿀 수 있어요."),
    (("묽",), "소스가 묽으면 약불에서 조금 더 졸이거나, 면과 버무리면서 수분을 날려 보세요."),
    (("되직",), "소스가 너무 되직하면 우유나 파스타 삶은 물을 조금씩 넣어 농도를 맞춰 보세요."),
    (("걸쭉",), "소스가 너무 되직하면 우유나 파스타 삶은 물을 조금씩 넣어 농도를 맞춰 보세요."),
    (("짜",), "간이 세면 우유나 생크림을 조금 더해 희석해 보세요."),
    (("싱거",), "싱거우면 소금은 조금씩, 맛을 보면서 더해 주세요."),
    (("면", "삶"), "면은 포장지에 적힌 시간보다 1분 정도 덜 삶아 소스에서 마저 익히면 퍼지지 않아요."),
    (("파스타", "삶"), "면은 포장지에 적힌 시간보다 1분 정도 덜 삶아 소스에서 마저 익히면 퍼지지 않아요."),
    (("분리",), "크림 소스는 센불에서 오래 끓이면 분리될 수 있어요. 끓어오르면 약불로 줄여 주세요."),
)

_STEP_HINTS = {
    "소스": ("생크림", "우유", "끓"), "면": ("파스타", "삶"), "삶": ("삶",), "볶": ("볶",),
    "간": ("소금", "후춧가루", "간한다"), "불": ("불",), "끓": ("끓",),
}


def source_steps(question: str, step_texts: list[str], materials: list[dict]) -> list[tuple[int, str]]:
    """(step number, text) of recipe steps relevant to the question (ingredient names or cooking words)."""
    words = {m["name"] for m in materials if m["name"] in question}
    for hint, targets in _STEP_HINTS.items():
        if hint in question:
            words.update(targets)
    return [(n, t) for n, t in enumerate(step_texts, 1) if any(w in t for w in words)]


TIMING_RE = re.compile(r"언제까지|언제\s*넣|언제\s*꺼|언제\s*불|얼마나|어느\s*정도|몇\s*분|다\s*된|다\s*익|어떻게\s*되면|될\s*때까지")
# a cue in the source: "<ingredient>가 투명해질 정도로 볶아지면", "… 노릇해질 때까지", "끓어 오르면"
_CUE_TAIL = r"[^.,]*?(?:정도로|때까지|까지)[^.,]*?(?:면|고|때)(?=[\s,.]|$)"


def timing_answer(question: str, step_texts: list[str], named: list[dict]) -> tuple[int, str, str] | None:
    """For "언제까지 / 얼마나" questions about a named ingredient: (step no, source step text, cue phrase)
    taken verbatim from the source, or None when the source has no such cue."""
    if not TIMING_RE.search(question or "") or not named:
        return None
    for m in named:
        name = re.escape(m["name"])
        for n, text in enumerate(step_texts, 1):
            found = re.search(name + r"[이가은는을를의]?\s*" + _CUE_TAIL, text)
            if found:
                return n, text, found.group(0).strip()
    return None


# question verb → how the source writes it (찜·구이·조림·재우기 …)
_VERBS = (
    (r"쪄|찌", r"쪄|찌"), (r"끓", r"끓"), (r"굽|구워|구우", r"굽|구워|구운|익혀|익힌|익힌다"), (r"볶", r"볶"),
    (r"삶", r"삶"), (r"조려|졸|조리", r"조려|조린|졸|조리"), (r"재워|재우|재울", r"재워|재운|재어|묻혀|배게"),
    (r"데쳐|데치", r"데쳐|데친"), (r"부쳐|부치", r"부쳐|부친|지져"), (r"튀겨|튀기", r"튀겨|튀긴"),
)
_TIME = re.compile(r"\d+\s*(?:분|시간)\s*(?:정도|간|동안|전에|전|이상)?")
_WHEN_ADD = re.compile(r"언제\s*넣|넣는\s*때|넣는\s*시점|넣어야")


_DIGIT_BATCHIM = {"0": True, "1": True, "2": False, "3": True, "4": False, "5": False, "6": True, "7": True,
                  "8": True, "9": False}


def _josa(word: str, pair: tuple[str, str]) -> str:
    """Pick 은/는, 을/를, 과/와 by how the word is read: '두부'→를, '200g'(그램)→과, '1개'→와, '100mL'(리터)→와."""
    w = (word or "").rstrip()
    last = w[-1] if w else ""
    if "가" <= last <= "힣":
        batchim = (ord(last) - 0xAC00) % 28 != 0
    elif w.lower().endswith(("ml", "l", "cc")):
        batchim = False                 # 밀리리터·리터·씨씨
    elif w.lower().endswith(("g", "kg", "cm", "mm")):
        batchim = True                  # 그램·센티미터
    else:
        batchim = _DIGIT_BATCHIM.get(last, False)
    return w + (pair[0] if batchim else pair[1])


_CUE_END = re.compile(r"(?:면|후|뒤|다음|다가)$")
_ITEM = r"[가-힣]{1,8}?(?: [가-힣]{1,8}?)?"
_VERBISH = re.compile(r"(?:후|면|고|어|아|서|게|다가|에|은|는|를|을)$")


def _name_rx(name: str) -> str:
    """'다진마늘' also matches '다진 마늘' in the source."""
    return r"\s?".join(re.escape(ch) for ch in name.replace(" ", ""))


def _cue_before(prefix: str) -> tuple[str, list[str]] | None:
    """('간을 맞춘 뒤', ['마지막으로']) for '…썰어 넣고 간을 맞춘 뒤 마지막으로 ' — the last cue clause and
    what stands between it and the added ingredient."""
    pieces = [p.strip() for p in re.split(r"(?<=[면후뒤]) |(?<=다가) |(?<=다음) |(?<=고) |, ", prefix) if p.strip()]
    for k in range(len(pieces) - 1, -1, -1):
        if _CUE_END.search(pieces[k]):
            start = k - 1 if len(pieces[k]) < 6 and k > 0 else k     # '끓으면' → '애호박을 넣고 끓으면'
            return " ".join(pieces[start:k + 1]), pieces[k + 1:]
    return None


def when_to_add(question: str, step_texts: list[str], named: list[dict]) -> tuple[list[int], str] | None:
    """'두부는 언제 넣어요?' → ([5], '**애호박을 넣고 끓으면** 두부를 넣어요.') — the source clause right before
    '<재료>를 넣', quoted.  When the source adds it in several steps ('모시조개'), every step is named with
    its own source words; when the clause is long, the source words are quoted as they are.
    None when the source does not say."""
    if not _WHEN_ADD.search(question or "") or not named:
        return None
    for m in named:
        obj_rx = (r"((?:" + _ITEM + r"\s*,\s*)*" + _name_rx(m["name"]) + r"(?:\s*,\s*" + _ITEM + r")*)"
                  r"[을를도]?\s*넣[가-힣]*")
        hits = []
        for n, text in enumerate(step_texts, 1):
            add = re.search(obj_rx, text)
            if not add:
                continue
            # the object list holds only ingredient names: '…끓인후, 청고추, 대파, 다진 마늘' → '청고추, 대파, 다진 마늘'
            items = [x.strip() for x in add.group(1).split(",")]
            first = 0
            for k, item in enumerate(items):
                words = item.split(" ")
                if k < len(items) - 1 and _VERBISH.search(words[-1]):
                    first = k + 1                       # '더 끓인후' is not an ingredient
                elif len(words) == 2 and _VERBISH.search(words[0]):
                    items[k], first = words[1], k        # '볶아지면 우유' → '우유', '육수에 표고버섯' → '표고버섯'
            objects = ", ".join(items[first:])
            obj_start = text.find(objects, add.start())
            prefix = text[:obj_start] if obj_start >= 0 else text[:add.start()]
            tail = text[obj_start + len(objects):add.end()] if obj_start >= 0 else add.group(0)
            found = _cue_before(prefix)
            start = max(prefix.rfind(","), prefix.rfind("."))
            if found and len(found[1]) <= 1 and all(len(f) <= 8 for f in found[1]):
                cue = " ".join([found[0], *found[1]])
                hits.append((n, f"**{cue}** {_josa(objects, ('을', '를'))} 넣어요.", f"{cue} {objects}{tail}"))
            else:
                seg = (prefix[start + 1:] + objects + tail).strip()
                hits.append((n, None, seg))
        if not hits:
            continue
        if len(hits) == 1:
            n, line, seg = hits[0]
            return [n], line or f"원문 {n}단계 “{seg}”."
        parts = ", ".join(f"{n}단계 “{seg}”" for n, _line, seg in hits)
        return [n for n, _l, _s in hits], f"원문에서 {_josa(m['name'], ('은', '는'))} {len(hits)}번 넣어요: {parts}."
    return None


def how_long(question: str, step_texts: list[str], named: list[dict] | None = None) -> tuple[int, str, bool] | None:
    """'얼마나 쪄요?', '고기는 얼마나 재워요?' → (step no, the source step with its time / cue in bold)."""
    q = question or ""
    if not re.search(r"얼마나|몇\s*분|몇\s*시간|언제까지|언제", q):
        return None
    for asked, written in _VERBS:
        if not re.search(asked, q):
            continue
        plain = None
        verb = re.compile(rf"(?:{written})(?!는\s)")    # '끓는 물에' is not boiling the dish
        for n, text in enumerate(step_texts, 1):
            if not verb.search(text):
                continue
            if named and not any(m["name"] in text for m in named):
                continue     # '베이컨은 얼마나 볶아요?' — only a step about bacon answers it
            time = _TIME.search(text) or re.search(r"[^,.]{2,30}?(?:정도로|때까지)", text)
            if time:
                return n, text.replace(time.group(0), f"**{time.group(0).strip()}**", 1), True
            # no time in the source: keep the shortest source clause that has the verb ('푹 끓인다')
            clause = next((c.strip() for c in re.split(r",", text)[::-1] if verb.search(c)), None)
            if clause and plain is None:
                plain = (n, f"“{clause}”", False)
        return plain
    return None


def next_action(step: str, phrase: str) -> str | None:
    """What the same source step does right after the cue: '…볶아지면 우유, 생크림, 바질을 넣고 끓이다가'
    → '우유, 생크림, 바질을 넣어요'.  Only an '…을/를 넣' clause, quoted from the source; else None."""
    at = step.find(phrase)
    if at < 0:
        return None
    m = re.match(r"\s*([^.]{1,40}?[을를])\s*넣", step[at + len(phrase):])
    return f"{m.group(1)} 넣어요" if m else None


def general_tip(question: str) -> str | None:
    compact = re.sub(r"\s+", "", question or "")
    for keys, tip in GENERAL_TIPS:
        if all(k in compact for k in keys):
            return tip
    return None


# tips shown on a recipe card when no AI tips are available — general knowledge, labelled
# "일반 조리 팁"; no amounts.
# 2026-10-30: a tip about an action ('마늘 볶기') is shown only when a source step does that action with
# that ingredient — '마늘' in the ingredient list alone is not enough (갈비구이 never fries garlic).
#   (words, title, text, action):  action=None → the word anywhere in the title / ingredients / steps;
#   action=regex → some step sentence has one of the words *and* the action;  words=("@구이",) → dish title ends so
CARD_TIPS: tuple[tuple[tuple[str, ...], str, str, str | None], ...] = (
    (("파스타", "스파게티"), "면 삶기", "면은 포장지 시간보다 조금 덜 삶아 소스에서 마저 익히면 퍼지지 않아요.", r"삶"),
    (("생크림",), "소스 분리 막기", "크림 소스는 끓어오르면 약불로 줄여 주세요. 센불에서 오래 끓이면 분리될 수 있어요.", r"끓"),
    (("생크림",), "생크림이 없다면", "우유에 버터를 조금 더해 농도를 보충할 수 있어요. 더 묽으니 조금 더 졸여 주세요.", None),
    (("우유",), "농도 맞추기", "소스가 되직하면 우유를, 묽으면 약불에서 조금 더 졸여 농도를 맞춰 보세요.", r"끓|졸"),
    (("베이컨",), "베이컨 볶기", "베이컨은 먼저 노릇하게 볶아 기름을 내면 고소한 맛이 살아나요.", r"볶"),
    (("마늘",), "마늘 볶기", "마늘은 약한 불에서 향만 내듯 볶아야 타지 않아요.", r"볶"),
    (("@구이",), "타지 않게 굽기", "양념한 고기·생선은 설탕 때문에 타기 쉬워요. 중약불에서 자주 뒤집어 속까지 익혀 주세요.", None),
    (("@조림",), "국물 졸이기", "뚜껑을 덮어 속까지 익힌 뒤, 마지막에 뚜껑을 열고 국물을 끼얹으며 졸이면 맛이 배어요.", None),
    (("재워", "재운", "재우"), "재우는 시간", "양념에 재울 때는 냉장고에 두고, 원문 시간보다 오래 두면 짜질 수 있어요.", None),
    (("소금",), "간 맞추기", "소금은 마지막에 맛을 보면서 조금씩 더해 주세요.", r"간을|간한|간하|간이|간 맞|간맞"),
)
MAX_CARD_TIPS = 3


def _tip_applies(words, action, title: str, names: list[str], steps: list[str]) -> bool:
    flat_title = re.sub(r"\s+", "", title or "")
    if words[0].startswith("@"):
        return any(flat_title.endswith(w[1:]) for w in words)
    if action is None:
        hay = re.sub(r"\s+", "", " ".join([title, *names, *steps]))
        return any(w in hay for w in words)
    sentences = [x for step in steps for x in re.split(r"(?<=[.다])\s+", step)]
    return any(any(w in x for w in words) and re.search(action, x) for x in sentences)


def card_tips(ingredient_names: list[str], step_texts: list[str], title: str = "") -> list[dict]:
    out = []
    for words, tip_title, text, action in CARD_TIPS:
        if tip_title not in {t["title"] for t in out} and _tip_applies(words, action, title, ingredient_names, step_texts):
            out.append({"title": tip_title, "text": text})
        if len(out) >= MAX_CARD_TIPS:
            break
    return out
