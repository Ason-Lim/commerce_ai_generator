def calculate_discount_rate(original_price, price):
    if not original_price or not price:
        return None
    if original_price <= 0:
        return None
    if original_price <= price:
        return 0
    return round((original_price - price) / original_price * 100, 1)


def calculate_price_per_100g(price, weight_g):
    if not price or not weight_g:
        return None
    if weight_g <= 0:
        return None
    return round(price / weight_g * 100, 1)


def calculate_final_price(price, shipping_fee=0):
    if price is None:
        return None
    return price + (shipping_fee or 0)
