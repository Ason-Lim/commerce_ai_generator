from app.services.food.knowledge.alias_resolution import (
    AliasNormalizer,
)


def test_normalizer_is_deterministic() -> None:
    normalizer = AliasNormalizer()

    assert normalizer.normalize("  Coffee  ") == "coffee"
    assert normalizer.normalize("ＣＯＦＦＥＥ") == "coffee"
    assert normalizer.normalize("커피   원두") == "커피 원두"


def test_normalizer_handles_empty_values() -> None:
    normalizer = AliasNormalizer()

    assert normalizer.normalize(None) == ""
    assert normalizer.normalize("") == ""
    assert normalizer.normalize("   ") == ""
