"""Compound Seasonings Foundation domain core."""

from .parser import parse_compound_seasoning
from .parser_models import CompoundSeasoningParseResult

__all__ = ["CompoundSeasoningParseResult", "parse_compound_seasoning"]
