"""Classify the source of sweetness wording shown to customers.

Numeric feature fields alone do not identify the page where they originated.
"""

import re


def brix_claim_source(item, value=None):
    """Return a seller-page claim only when the displayed text supports it."""
    item = item or {}
    text = " ".join(
        str(item.get(key) or "")
        for key in ("product_name", "raw_name", "title", "description", "product_description", "detail_description")
    )
    if value is None:
        return "seller_page_claim" if "고당도" in text else "UNKNOWN"

    try:
        expected = float(value)
    except (TypeError, ValueError):
        return "UNKNOWN"

    for match in re.finditer(r"(\d{1,2}(?:\.\d+)?)\s*(?:brix|브릭스)", text, re.IGNORECASE):
        if float(match.group(1)) == expected:
            return "seller_page_claim"
    for match in re.finditer(r"당도\s*(\d{1,2}(?:\.\d+)?)", text):
        if float(match.group(1)) == expected:
            return "seller_page_claim"
    return "UNKNOWN"
