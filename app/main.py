from fastapi import FastAPI
from pydantic import BaseModel
from app.services.generator_service import generate_product_strategy
from app.services.naver_shopping_api_collector import collect_naver_products

app = FastAPI()


class RequestModel(BaseModel):
    context: str
    mode: str
    priority: str
    quantity: int | None = None


@app.post("/generate")
def generate(request: RequestModel):
    # 🔥 1️⃣ 네이버 API 실시간 수집
    try:
        collect_naver_products(request.context)
    except Exception as e:
        print("네이버 API 실패:", e)

    # 🔥 2️⃣ 기존 추천 엔진 실행
    result = generate_product_strategy(request)

    return result