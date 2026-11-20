"""글 틀(템플릿) — 상품 홍보·구매 안내 블로그 템플릿 55종 v1.1(2026-11-20) 중 앱이 자동으로 채울 수 있는 8종.

프레임 0.4 순서(고지 → 질문과 조건부 답 → [템플릿 절] → 선택 기준 → 구매 전 제약 → 결제 전 확인 → 상품)는 그대로 두고,
템플릿은 '질문과 답' 다음에 들어가는 절(소제목·내용)과 제목을 정한다.
* 주제(frame.keyword_type)마다 기본 템플릿 순서가 있고, 필요한 자료가 없으면 다음 후보 → 마지막엔 01.
* 관리자가 번호를 지정할 수 있다 (자료가 모자라면 01 로 내려가고 그 사실을 note 로 남긴다).
* 21~25(실사용 후기형)는 자동 초안에 쓰지 않는다 — 실제 사용 기록이 필요하다 (55종 문서 공통 사용법 6).
* 나머지 47종은 사람이 직접 쓸 때 보는 지침 (55종 문서 원본).
"""
from __future__ import annotations

from dataclasses import dataclass, field

from app.services.trend_posts import frame

NAMES = {"01": "첫 구매 안내", "03": "용량·수량 선택", "05": "주문·수령 일정", "06": "두 상품 비교",
         "14": "선물 선택", "26": "요리 재료 연결", "28": "계절·행사 준비", "32": "유행 상품 구매 전 검토"}
EXPERIENCE_ONLY = {"21", "22", "23", "24", "25"}
# 2026-11-20 55종 v1.2: 결론이 '구매 보류'인 글은 구매 링크를 넣지 않는다 (20·32번 취지)
HOLD_LINE = {"site": "지금은 사지 않아도 되는 경우가 많아요. 그래서 이 글에는 구매 링크를 넣지 않았어요. "
                     "가진 제품으로 해결되지 않을 때 위의 기준으로 다시 비교해 보세요.",
             "blog": "지금 당장 사지 않아도 괜찮아요. 그래서 이 글에는 구매 링크를 넣지 않았어요. "
                     "갖고 있는 것으로 부족할 때 위 기준으로 다시 골라 보세요."}
# 보류 결론 글의 틀: 급상승 신상(viral)은 32(유행과 필요 구분), 그 밖은 20(구매 보류 판단). 자동 선택·관리자 지정 대상 아님.
HOLD_NAMES = {"20": "구매 보류 판단", "32": "유행 상품 구매 전 검토"}
HOLD_ANSWER = {"site": "가진 제품이나 비슷한 기존 상품으로 해결된다면 지금 새로 살 필요는 없어요.",
               "blog": "갖고 있는 것이나 비슷한 기존 제품으로 충분하다면, 지금 굳이 새로 사지 않아도 돼요."}
HOLD_CRITERIA_HEAD = {"site": "필요해지면 볼 기준", "blog": "나중에 필요해지면 볼 기준"}
HOLD_TITLES = {
    "site": {"20": ["{k}, 지금 꼭 사야 할까? 먼저 확인할 것", "{k} 사기 전에, 정말 필요한지부터"],
             "32": ["화제인 {k}, 가진 것으로 충분하지 않을까", "요즘 많이 찾는 {k}, 유행과 필요는 따로"]},
    "blog": {"20": ["{k}, 지금 꼭 사야 할까요?", "{k} 사기 전에 정말 필요한지부터 봐요"],
             "32": ["요즘 다들 찾는 {k}, 나한테도 필요할까", "{k} 유행, 지금 가진 걸로 충분할 수도 있어요"]},
}
HOLD_SECTIONS = {
    "site": {"20": ("사지 않아도 되는 경우", [
                 "비슷한 용도의 제품이 이미 있다면 그것으로 해결되는지 먼저 확인하세요.",
                 "다시 검토할 때: 쓸 일이 정해졌거나, 기존 제품으로 해결되지 않을 때."]),
             "32": ("유행과 필요 나눠 보기", [
                 "검색 증가는 관심의 변화일 뿐, 판매량이나 품질을 뜻하지 않아요.",
                 "비슷한 기존 상품으로 충분하다면 유행과 상관없이 사지 않아도 됩니다.",
                 "다시 검토할 때: 기존 상품으로 대신할 수 없는 쓰임이 생겼을 때."])},
    "blog": {"20": ("사지 않아도 되는 경우", [
                 "비슷한 걸 이미 갖고 있다면 그걸로 되는지부터 봐 주세요.",
                 "이럴 때 다시 보세요: 쓸 일이 정해졌거나, 갖고 있는 걸로는 안 될 때."]),
             "32": ("유행이랑 필요는 따로", [
                 "검색이 늘었다는 건 관심이 늘었다는 뜻이지, 많이 팔렸다거나 품질이 좋다는 뜻은 아니에요.",
                 "비슷한 기존 제품으로 충분하다면 유행과 상관없이 안 사셔도 돼요.",
                 "이럴 때 다시 보세요: 갖고 있는 걸로는 대신할 수 없는 쓰임이 생겼을 때."])},
}


def hold(topic: str, *, status: str | None = None, channel: str = "site") -> Chosen:
    """구매 보류 결론 글 — 구매를 이끄는 절(옵션·주문·결제·상품 줄)은 넣지 않는다 (사용자 결정 2026-11-20 16:18)."""
    c = channel if channel in HOLD_TITLES else "site"
    kind = frame.keyword_type(topic, status=status)
    tid = "32" if kind == "viral" else "20"
    head, lines = HOLD_SECTIONS[c][tid]
    ch = Chosen(id=tid, name=HOLD_NAMES[tid], kind=kind, note="구매 보류 결론")
    ch.sections = [(head, list(lines))]
    ch.title = frame.pick(HOLD_TITLES[c][tid], topic, "th" + c).format(k=topic)
    return ch


def hold_answer(topic: str, kind: str, channel: str = "site") -> list[str]:
    """질문에 대한 답 — 상품 비교로 이끄는 마지막 줄 대신 보류 결론."""
    c = channel if channel in HOLD_ANSWER else "site"
    return frame.answer(topic, False, False, c, kind)[:-1] + [HOLD_ANSWER[c]]

# 주제별 기본 템플릿 (앞이 먼저, 자료가 없으면 다음). 사용자 결정 2026-11-20 15:55 '주제를 나눠 기본 템플릿을 정해 달라'.
DEFAULTS = {
    "kimjang": ["05", "03", "01"],          # 김장 날짜에 맞춘 도착일 → 양
    "seasonal": ["26", "06", "01"],         # 제철: 해 먹는 법(레시피) → 두 상품 비교
    "seollal": ["28", "14", "01"],          # 설날·추석·명절: 준비 일정 → 선물
    "chuseok": ["28", "14", "01"],
    "holiday": ["28", "14", "01"],
    "family_month": ["14", "28", "01"],     # 가정의 달: 선물
    "birthday": ["26", "14", "01"],         # 생일: 생일상(레시피) → 선물
    "anniversary": ["14", "05", "01"],      # 기념일: 선물 → 날짜
    "event": ["28", "05", "01"],            # 시즌 이벤트(수능·복날·동지·연말…): 준비 → 날짜
    "gift": ["14", "06", "01"],             # 선물
    "weather": ["26", "03", "01"],          # 날씨: 해 먹는 법 → 양
    "viral": ["32", "01"],                  # 급상승 신상: 유행 상품 구매 전 검토
    "general": ["06", "01"],
}
GIFT_WORDS = ("선물", "세트", "답례", "기프트")


@dataclass
class Chosen:
    id: str
    name: str
    kind: str                                 # 주제
    note: str = ""                            # 지정한 템플릿을 못 쓴 이유 등 (운영자용)
    sections: list[tuple[str, list[str]]] = field(default_factory=list)
    title: str = ""


def _ok(tid: str, products: list[dict], recipe) -> bool:
    if tid == "26":
        return bool(recipe and getattr(recipe, "ingredients", None))
    if tid == "06":
        return len(products) >= 2
    if tid == "03":
        return any(frame.amounts(p.get("title") or "") for p in products)
    return tid in NAMES


def candidates(topic: str, kind: str) -> list[str]:
    order = list(DEFAULTS.get(kind, DEFAULTS["general"]))
    # 명절·생일 키워드에 '선물'이 들어 있으면 선물 틀을 먼저 (설선물세트 → 14)
    if kind in ("seollal", "chuseok", "holiday", "birthday") and any(w in topic for w in GIFT_WORDS):
        order = ["14"] + [t for t in order if t != "14"]
    return order


def choose(topic: str, *, status: str | None = None, products: list[dict] = (), recipe=None,
           override: str | None = None, channel: str = "site") -> Chosen:
    """products: [{'title', 'rocket'}] — 사이트 글은 PostProduct, 블로그는 쿠팡 링크 dict 를 같은 모양으로 넘긴다."""
    kind = frame.keyword_type(topic, status=status)
    note = ""
    tid = None
    if override:
        if override in EXPERIENCE_ONLY:
            note = f"{override}번은 실제 사용 기록이 필요해 자동 초안에 쓰지 않아요."
        elif override not in NAMES:
            note = f"{override}번은 아직 자동으로 채울 수 없어요 (사람이 직접 쓰는 지침)."
        elif not _ok(override, list(products), recipe):
            note = f"{override}번({NAMES[override]})에 필요한 자료가 없어요."
        else:
            tid = override
    if tid is None:
        tid = next((t for t in candidates(topic, kind) if _ok(t, list(products), recipe)), "01")
        if note:
            note += f" 대신 {tid}번({NAMES[tid]})으로 만들었어요."
    ch = Chosen(id=tid, name=NAMES[tid], kind=kind, note=note)
    ch.sections = sections(tid, topic, kind, list(products), recipe, channel)
    ch.title = title(tid, topic, kind, channel, recipe)
    return ch


# ── 제목 ───────────────────────────────────────────────────────────────
TITLES = {
    "site": {"01": ["{k} 처음 산다면? 고르기 전 확인할 것", "{k} 고르는 법, 먼저 정할 세 가지"],
             "03": ["{k} 얼마나 사야 할까? 양 정하는 기준", "{k} 용량 고르기, 큰 구성이 늘 나을까"],
             "05": ["{k}, 쓰는 날짜에 맞춰 받으려면", "{k} 주문 전, 받을 날짜부터 확인하세요"],
             "06": ["{k} 두 상품 비교: 무엇이 다른가", "{k} 비교, 같은 기준으로 놓고 보면"],
             "14": ["{k} 선물, 구성·포장·받는 날 비교", "{k}, 받는 분 기준으로 고르는 법"],
             "26": ["{r} 만들 때 {k}, 필요한 재료부터", "{r}에 쓸 {k}, 재료와 고르는 법"],
             "28": ["{h_or_k} 준비, {k} 언제 무엇을 확인할까", "{k} 준비 일정과 고르는 기준"],
             "32": ["요즘 많이 찾는 {k}, 사기 전에 확인할 것", "화제인 {k}, 나에게도 필요할까"]},
    "blog": {"01": ["{k} 처음 사신다면, 이것부터 정하세요", "{k} 고르는 법, 먼저 정할 세 가지"],
             "03": ["{k} 얼마나 사야 할지 고민이라면", "{k}, 큰 걸 살까 작은 걸 살까"],
             "05": ["{k} 날짜 맞춰 받는 법, 주문 전에 꼭 보세요", "{k} 주문, 받는 날부터 거꾸로 계산해요"],
             "06": ["{k} 두 가지, 뭐가 다른지 나란히 봤어요", "{k} 비교, 같은 기준으로 나란히 놓으면"],
             "14": ["{k} 선물로 고민 중이라면 이것부터", "{k} 선물, 받는 분 조건에 맞춰 고르는 법"],
             "26": ["{r} 해 먹을 {k}, 재료부터 챙겨요", "{r} 만들 때 {k} 고르는 법"],
             "28": ["{h_or_k} 준비, {k} 이렇게 챙겨요", "{k} 준비, 언제 주문하면 될까요"],
             "32": ["요즘 다들 찾는 {k}, 사기 전에 한 번만 생각해 봐요", "{k} 유행, 나도 사야 할까"]},
}


# 키워드에 이미 '선물·세트'가 들어 있으면 ('어버이날선물') 제목에서 '선물'을 되풀이하지 않는다
TITLES_GIFT_WORD = {"site": ["{k}, 고르기 전에 확인할 것", "{k}, 받는 분 기준으로 고르는 법"],
                    "blog": ["{k} 고민 중이라면 이것부터", "{k}, 구성·포장·받는 날 비교하기"]}


def title(tid: str, topic: str, kind: str, channel: str = "site", recipe=None) -> str:
    c = channel if channel in TITLES else "site"
    bank = TITLES_GIFT_WORD[c] if tid == "14" and any(w in topic for w in GIFT_WORDS) else TITLES[c][tid]
    t = frame.pick(bank, topic, "t" + c)
    r = getattr(recipe, "name", None) or topic
    h_or_k = frame.HOLIDAY_NAME.get(kind) or {"family_month": "가정의 달", "event": "행사",
                                              "anniversary": "기념일", "birthday": "생일"}.get(kind, topic)
    out = t.format(k=topic, r=r, h_or_k=h_or_k)
    return out.replace(f"{topic} 준비, {topic} ", f"{topic} 준비, ")   # '추석 준비, 추석 …' 되풀이 막기


# ── 절 (소제목 + 줄) ─────────────────────────────────────────────────────
HEAD = {"site": {"03": ["양 정하기"], "05": ["쓰는 날과 받는 날"], "06": ["두 상품의 차이"], "14": ["보내기 전에 확인할 것"],
                 "26": ["만들 요리와 재료"], "28": ["준비 일정"], "32": ["화제와 내 필요 나눠 보기"]},
        "blog": {"03": ["얼마나 살지 정하기", "양부터 정해요"], "05": ["쓰는 날 ≠ 받는 날", "받는 날 정하기"],
                 "06": ["두 상품 나란히 보기", "같은 기준으로 비교"], "14": ["보내기 전 체크", "선물 보내기 전에"],
                 "26": ["무엇을 만들까", "만들 요리부터"], "28": ["준비는 날짜부터 거꾸로", "준비 순서"],
                 "32": ["유행과 필요는 따로", "사기 전에 한 번 더"]}}


def _amount_line(p: dict) -> str:
    amt = frame.amounts(p.get("title") or "")
    rocket = " · 로켓배송 표시" if p.get("rocket") else ""
    return f"{p.get('title') or ''} — " + (", ".join(amt) + " (상품명 표기)" if amt else "중량·수량 표기 없음") + rocket


def sections(tid: str, topic: str, kind: str, products: list[dict], recipe, channel: str = "site") -> list[tuple[str, list[str]]]:
    c = channel if channel in HEAD else "site"
    if tid == "01":
        return []                          # 첫 구매 안내 = 질문과 답 + 선택 기준 (따로 절을 두지 않음)
    head = frame.pick(HEAD[c][tid], topic, "s" + tid)
    blog = c == "blog"
    if tid == "03":
        lines = [_amount_line(p) for p in products[:3] if frame.amounts(p.get("title") or "")]
        lines.append("자주 쓰지 않거나 보관할 자리가 부족하면 큰 구성이 오히려 남을 수 있어요." if blog else
                     "큰 구성이 늘 알뜰한 것은 아니에요. 쓰는 빈도와 보관 공간을 먼저 정하세요.")
    elif tid == "05":
        lines = ["쓰는 날과 도착일을 꼭 같은 날로 잡을 필요는 없어요. 미리 받으면 보관할 자리만 챙기세요." if blog else
                 "쓰는 날과 도착일은 다를 수 있어요. 미리 받는다면 보관 조건을 먼저 확인하세요.",
                 ("판매 페이지에서 볼 것: 도착일을 고를 수 있는지, 주문 마감, 지역별 배송 조건이에요." if blog else
                  "판매 페이지에서 확인할 것: 도착일 지정 여부, 주문 마감, 지역별 배송 조건.")]
        if any(p.get("rocket") for p in products):
            lines.append("로켓배송 표시는 정리한 시점의 검색 결과 기준이에요. 도착 보장 여부는 결제 화면에서 보세요." if blog else
                         "로켓배송 표시는 확인 시점의 검색 결과 기준이며, 도착 보장 여부는 결제 화면에서 확인하세요.")
    elif tid == "06":
        a, b = products[0], products[1]
        lines = [_amount_line(a), _amount_line(b),
                 "중량·수량을 같은 단위로 바꾸고, 배송 방식이 내 일정에 맞는지로 고르면 돼요." if blog else
                 "같은 단위로 바꿔 비교하고, 배송 방식이 일정에 맞는 쪽을 고르세요."]
    elif tid == "14":
        lines = ["받는 분 주소와 받을 수 있는 날을 먼저 물어보세요. 신선식품은 특히 중요해요." if blog else
                 "받는 분 주소와 수령 가능한 날을 먼저 확인하세요 (신선식품은 특히).",
                 "원재료·알레르기 표시와 보관 방법은 판매 페이지에서 확인해 함께 알려 드리면 좋아요." if blog else
                 "원재료·알레르기 표시와 보관 방법을 판매 페이지에서 확인하세요.",
                 "포장·쇼핑백·메시지 카드가 필요하면 옵션에 들어 있는지 보세요." if blog else
                 "선물 포장·메시지 카드가 필요하면 옵션 포함 여부를 확인하세요."]
    elif tid == "26":
        name = getattr(recipe, "name", "") or topic
        ings = list(getattr(recipe, "ingredients", []) or [])
        src = getattr(recipe, "source_label", "") or ""
        lines = [(f"오늘 만들 요리: {name}. 재료 {len(ings)}가지 중 '{topic}'{frame._j(topic, '을', '를')} 고르는 글이에요." if blog else
                  f"만들 요리: {name} — 재료 {len(ings)}가지 중 '{topic}'{frame._j(topic, '을', '를')} 고르는 글이에요."),
                 ("재료: " + ", ".join(ings[:10]) + (" 외" if len(ings) > 10 else "")),
                 # 공개 글은 독자의 보유량을 모른다 (55종 v1.2) — 단정 대신 대입하는 방법
                 "레시피 분량에서 집에 있는 양을 빼 보세요. 남는 양이 이번에 살 양이에요." if blog else
                 "살 양 = 레시피 분량 − 가진 양. 집마다 달라서 직접 대입해 보세요."]
        if src:
            lines.append(f"레시피 출처: {src} (참고했으며 원문 그대로가 아니에요)")
    elif tid == "28":
        lines = ["날짜를 기준으로 거꾸로 계산해요: 주문 → 도착 → 보관 → 사용." if blog else
                 "날짜에서 거꾸로 정하세요: 주문 → 도착 → 보관 → 사용.",
                 "준비 목록을 적고 집에 있는 것에 표시해 보세요. 표시 안 된 것만 새로 사면 돼요." if blog else
                 "준비 목록에서 가진 것을 표시하고, 남은 것만 새로 살 목록으로 두세요.",
                 "주문 마감과 도착일은 판매처마다 달라요. 판매 페이지에서 확인하세요." if blog else
                 "판매처별 주문 마감과 도착일은 판매 페이지에서 확인하세요."]
    elif tid == "32":
        lines = ["검색이 늘었다는 건 관심이 늘었다는 뜻이지, 많이 팔렸다거나 품질이 좋다는 뜻은 아니에요." if blog else
                 "검색 증가는 관심의 변화일 뿐, 판매량이나 품질을 뜻하지 않아요.",
                 "처음이라면 작은 구성부터, 비슷한 기존 상품과 같은 기준으로 견줘 보세요." if blog else
                 "처음이라면 작은 구성부터 보고, 비슷한 기존 상품과 같은 기준으로 비교하세요.",
                 "총액·보관·대안을 유행과 별개로 따져 보세요." if blog else "총액·보관·대안은 유행과 별개로 확인하세요.",
                 "갖고 있는 것으로 충분하다면 굳이 사지 않아도 돼요." if blog else "가진 제품으로 해결된다면 사지 않아도 됩니다."]
    else:
        lines = []
    return [(head, lines)] if lines else []
