def build_b2c_strategy(product):
    return (
        f"{product['name']}은(는) {product['platform']} 기준 상품입니다. "
        f"100g당 가격은 {product['price_per_100g']}원, "
        f"할인율은 {product['discount_rate']}%입니다. "
        f"{product['brix_label']} 정보가 있어 구매 설득 포인트로 활용할 수 있습니다."
    )


def build_b2b_strategy(product, quantity):
    quantity = quantity or 50
    price = product.get("price")

    target_price = int(price * 0.92) if price else None

    return {
        "negotiation_possible": "보통",
        "quantity": quantity,
        "target_price": target_price,
        "message": (
            f"안녕하세요. {product['name']} 상품을 {quantity}개 단위로 "
            f"대량 구매 검토 중입니다. 현재 판매가 기준으로 "
            f"{target_price}원 수준 협의가 가능한지 문의드립니다."
        ),
    }
