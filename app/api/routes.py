from fastapi import APIRouter
from app.schemas.request_schema import GenerateRequest
from app.services.generator_service import generate_product_strategy

router = APIRouter()


@router.get("/health")
def health_check():
    return {"status": "ok"}


@router.post("/generate")
def generate(request: GenerateRequest):
    return generate_product_strategy(request)
