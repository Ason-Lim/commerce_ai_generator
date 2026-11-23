"""2026-11-23 밤 운영 확인 (첫 화면 예시 질문 3개) — 고친 것들."""
from __future__ import annotations

from app.services.chat.service import shopping_terms
from app.services.trends import highlight as hl


def test_glued_quantity_and_use_word():
    """'김장용 절임배추10kg' — 붙은 양 표기를 떼고, 쓰임새 말('김장용')만으로 검색하지 않는다.
    (전에는 결과가 상품명에 '10kg'·'100%' 가 있는 1~2개만 남았다)"""
    q, terms = shopping_terms("김장용 절임배추10kg 고를 때 뭘 봐야 하고 같이 살 재료 알려줘")
    assert q == "김장용 절임배추" and terms[0] == "절임배추"
    q, terms = shopping_terms("김장용 절임배추10kg 추천해줘")
    assert q.startswith("김장용 절임배추") and terms == ["절임배추"]
    assert shopping_terms("김장용 절임배추 10kg 추천해줘") == ("김장용 절임배추", ["절임배추"])
    assert shopping_terms("사과 추천해줘") == ("사과", ["사과"])


def test_home_keyword_products_compound_keyword_and_gift_category():
    """'결혼식답례품'·'호두정과답례품' — 붙여 쓴 키워드와 쿠팡 '출산/유아' 분류의 먹거리 답례품도 보인다."""
    assert hl.names_keyword("결혼식답례품", "수제쿠키 답례품 결혼식 돌잔치 선물세트")
    assert hl.names_keyword("곶감", "상주 곶감 1kg") and not hl.names_keyword("사과", "배 선물세트")
    items = [
        {"product_name": "호두정과 답례품 결혼 돌잔치 원통형 2구", "product_url": "https://link.coupang.com/a/1", "category_name": "출산/유아"},
        {"product_name": "핸드워시 답례품 4세트 결혼 웨딩", "product_url": "https://link.coupang.com/a/2", "category_name": "출산/유아"},
        {"product_name": "원통형 호두정과 답례품 5세트", "product_url": "https://link.coupang.com/a/3", "category_name": "출산/유아"},
    ]
    got = hl.picks("호두정과답례품", search=lambda kw, n: items)
    assert [g["title"] for g in got] == ["호두정과 답례품 결혼 돌잔치 원통형 2구", "원통형 호두정과 답례품 5세트"]
