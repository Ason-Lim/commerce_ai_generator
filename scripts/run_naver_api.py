from app.services.naver_shopping_api_collector import collect_naver_products

if __name__ == "__main__":
    keywords = [
        "고당도 사과",
        "샤인머스캣",
        "딸기",
    ]

    for kw in keywords:
        collect_naver_products(kw)
