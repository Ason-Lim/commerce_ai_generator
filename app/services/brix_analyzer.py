import re

def extract_brix(text: str):
    if not text:
        return None

    patterns = [
        r"브릭스\s*(\d+\.?\d*)",
        r"brix\s*(\d+\.?\d*)",
        r"BRIX\s*(\d+\.?\d*)",
        r"(\d+\.?\d*)\s*브릭스",
        r"(\d+\.?\d*)\s*brix",
        r"(\d+\.?\d*)\s*Brix",
    ]

    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            return float(match.group(1))

    return None


def build_brix_info(product_name: str, description: str = ""):
    text = f"{product_name} {description}"

    brix = extract_brix(text)

    high_sugar_keywords = [
        "고당도",
        "당도선별",
        "당도보장",
        "프리미엄",
        "특상품",
        "선물용",
        "꿀",
        "달콤",
    ]

    has_keyword = any(keyword in text for keyword in high_sugar_keywords)

    if brix:
        return {
            "brix_value": brix,
            "is_high_sugar": brix >= 13,
            "brix_label": f"Brix {brix}+ 고당도" if brix >= 13 else f"Brix {brix}",
            "quality_score": 90 if brix >= 13 else 70,
        }

    if has_keyword:
        return {
            "brix_value": None,
            "is_high_sugar": True,
            "brix_label": "고당도/프리미엄 표시 상품",
            "quality_score": 75,
        }

    return {
        "brix_value": None,
        "is_high_sugar": False,
        "brix_label": "당도 정보 없음",
        "quality_score": 50,
    }
