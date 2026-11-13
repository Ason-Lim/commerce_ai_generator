"""2026-11-10: '맛있어'의 '있어'를 보유량으로 읽어 귤 구매 질문이 '어떤 요리에 쓸 재료인가요?'로 빠졌다."""
from app.services.recipe_chat.parsing import says_have


def test_have_sentences_are_still_read():
    for t in ("우유 200mL 있어요", "버터 30g 남았어", "양파 반 개 남아 있어", "냉장고에 계란 3개 있어"):
        assert says_have(t), t


def test_taste_and_buying_sentences_are_not_stock():
    for t in ("귤 10kg 박스로 사려는데 크기(로얄과/소과)별로 뭐가 맛있어?", "사과 5kg 중에 뭐가 맛있어?",
              "이 초콜릿 멋있어", "1kg으로 만들 수 있어?", "삼겹살 2kg 살까 하는데 남아도 괜찮아?",
              "한우 1kg 사야 하는데 뭐가 좋아?"):
        assert not says_have(t), t


def test_buying_question_with_a_weight_goes_to_shopping(sqlite_db, shopping):
    from app.services.chat.service import ChatService

    shopping.items = [{"product_name": "제주 감귤 로얄과 10kg", "price": 29900, "shipping_fee": 0, "is_coupang": True,
                       "product_url": "https://shop.example.com/1"}]
    res = ChatService(sqlite_db, shopping=shopping).handle(
        None, message="귤 10kg 박스로 사려는데 크기(로얄과/소과)별로 뭐가 맛있어?")
    assert res["stage"] != "recipe_needed"
    assert shopping.calls                                  # 상품을 찾았다
