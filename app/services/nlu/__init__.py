"""Food-domain NLU integrated into commerce_ai_generator.

Ported from the separate food-nlu project (nlu.py) so that the commerce
service no longer loads files from an external folder or edits sys.path.
Only the NLU parts were moved: the LLM client, the dictionary-driven system
prompt, and output validation.  Product search, the HTTP API and the product
DB of food-nlu were intentionally *not* copied; commerce uses its own
recommendation pipeline for shopping.
"""
from .llm_client import LLMClient, LLMConfigError
from .dictionary import NLUResources, validate
from .food_nlu import FoodNLU, load_food_nlu

__all__ = ["LLMClient", "LLMConfigError", "NLUResources", "validate", "FoodNLU", "load_food_nlu"]
