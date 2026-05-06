import re


def extract_budget(text: str):
    text = text.replace(",", "").replace(" ", "")

    # 5만원, 10만원 이하
    m = re.search(r"(\d+)만원", text)
    if m:
        return int(m.group(1)) * 10000

    # 50000원, 50000 이하
    m = re.search(r"(\d+)원", text)
    if m:
        return int(m.group(1))

    return None


def detect_target(text: str):
    targets = {
        "부모님": ["부모님", "엄마", "아빠", "어머니", "아버지"],
        "친구": ["친구", "지인", "동료"],
        "거래처": ["거래처", "고객사", "상사", "회사"],
        "가족": ["가족", "아이", "자녀", "배우자"],
        "연인": ["연인", "남자친구", "여자친구", "애인"],
    }

    for label, words in targets.items():
        if any(w in text for w in words):
            return label

    return None


def detect_occasion(text: str):
    occasions = {
        "생일": ["생일", "생신"],
        "추석": ["추석", "한가위"],
        "설날": ["설날", "설", "명절"],
        "감사선물": ["감사", "고마움", "답례"],
        "집들이": ["집들이"],
        "병문안": ["병문안", "회복"],
    }

    for label, words in occasions.items():
        if any(w in text for w in words):
            return label

    return None


def detect_priority(text: str):
    if any(w in text for w in ["싸", "저렴", "가성비", "가격", "최저가"]):
        return "price"

    if any(w in text for w in ["할인", "특가", "세일"]):
        return "discount"

    if any(w in text for w in ["맛있는", "고당도", "프리미엄", "좋은", "품질", "선물"]):
        return "quality"

    return "quality"


def detect_intent(text: str):
    if any(w in text for w in ["추천", "골라", "찾아", "뭐가 좋아", "알려줘"]):
        return "recommendation"

    if any(w in text for w in ["선물", "생일", "추석", "설날", "거래처"]):
        return "gift"

    if any(w in text for w in ["싸", "저렴", "최저가", "가격"]):
        return "price_search"

    return "product_search"


def normalize_keyword(text: str, target=None, occasion=None):
    fruit_words = [
        "사과", "배", "딸기", "샤인머스캣", "포도", "감귤", "귤",
        "오렌지", "망고", "복숭아", "과일"
    ]

    found = [w for w in fruit_words if w in text]

    if found:
        base = found[0]
    else:
        base = "과일"

    if "고당도" in text or "맛있는" in text:
        return f"고당도 {base}"

    if "선물" in text or target or occasion:
        return f"{base} 선물세트"

    return base


def analyze_user_query(raw_query: str):
    text = raw_query.strip()

    target = detect_target(text)
    occasion = detect_occasion(text)
    budget_max = extract_budget(text)
    priority = detect_priority(text)
    intent_type = detect_intent(text)
    normalized_keyword = normalize_keyword(text, target, occasion)

    needs_followup = False
    followup_question = None

    # 선물 의도인데 대상/예산이 없으면 추가 질문 후보
    if ("선물" in text or occasion) and (not target or not budget_max):
        needs_followup = True
        followup_question = "선물을 드릴 대상이나 예산대를 알려주시면 더 구체적으로 추천해드릴 수 있습니다."

    return {
        "raw_query": raw_query,
        "normalized_keyword": normalized_keyword,
        "intent_type": intent_type,
        "gift_target": target,
        "occasion": occasion,
        "budget_max": budget_max,
        "priority": priority,
        "needs_followup": needs_followup,
        "followup_question": followup_question,
    }


def build_related_keywords(intent):
    keyword = intent["normalized_keyword"]
    target = intent.get("gift_target")
    occasion = intent.get("occasion")

    related = [
        keyword,
        keyword.replace("선물세트", "고당도"),
        keyword.replace("선물세트", "프리미엄"),
        keyword.replace("선물세트", "특가"),
    ]

    if target:
        related.append(f"{target} 과일 선물")

    if occasion:
        related.append(f"{occasion} 과일 선물세트")

    # 중복 제거
    result = []
    for r in related:
        r = r.strip()
        if r and r not in result:
            result.append(r)

    return result[:6]
