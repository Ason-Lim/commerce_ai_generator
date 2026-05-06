from pydantic import BaseModel
from typing import Optional


class GenerateRequest(BaseModel):
    context: str
    mode: str = "B2C"
    priority: str = "quality"
    quantity: Optional[int] = None
