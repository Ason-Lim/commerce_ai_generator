from importlib import import_module

import pytest


def _parse(text: str):
    return import_module("app.services.food.knowledge.sauce.parser").parse_sauce(text)


def test_parse_sauce_is_exported_and_returns_parser_result() -> None:
    package = import_module("app.services.food.knowledge.sauce")
    result_type = package.SauceParseResult
    assert package.parse_sauce("ponzu sauce") == _parse("ponzu sauce")
    assert isinstance(_parse("ponzu sauce"), result_type)


@pytest.mark.parametrize("text", ("", "   ", "recommended please"))
def test_empty_whitespace_and_noise_only_inputs_remain_unknown(text: str) -> None:
    result = _parse(text)
    assert result.family == "unknown"
    assert result.matched_evidence == ()
    assert result.unresolved_evidence


@pytest.mark.parametrize(("text", "family"), (("soy sauce", "fermented-liquid"), ("doenjang sauce", "fermented-paste"), ("mayonnaise sauce", "emulsified"), ("ketchup", "tomato/produce"), ("hot chili sauce", "chili/hot"), ("demi-glace sauce", "savory/reduction"), ("vinaigrette dressing", "dressing/marinade"), ("chocolate dessert sauce", "sweet/dessert"), ("table sauce", "other")))
def test_all_family_values_are_classified_from_explicit_evidence(text: str, family: str) -> None:
    assert _parse(text).family == family


@pytest.mark.parametrize(("text", "texture"), (("thin liquid sauce", "liquid"), ("thick viscous sauce", "viscous"), ("creamy sauce", "creamy"), ("paste-like sauce", "paste-like"), ("chunky salsa sauce", "chunky")))
def test_supported_texture_evidence_is_preserved(text: str, texture: str) -> None:
    assert _parse(text).texture == texture


@pytest.mark.parametrize(("text", "heat"), (("mild chili sauce", "mild"), ("medium hot sauce", "medium"), ("hot sauce", "hot"), ("very hot sauce", "very-hot"), ("mayonnaise sauce", "none")))
def test_supported_heat_evidence_is_preserved(text: str, heat: str) -> None:
    assert _parse(text).heat_level == heat


@pytest.mark.parametrize(("text", "use"), (("dipping sauce", "dipping"), ("salad dressing", "dressing"), ("cooking sauce", "cooking"), ("glaze sauce", "glazing"), ("marinade sauce", "marinating"), ("spread sauce", "spreading"), ("finishing sauce", "finishing")))
def test_supported_intended_use_evidence_is_preserved(text: str, use: str) -> None:
    assert use in _parse(text).intended_uses


@pytest.mark.parametrize(("left", "right"), (("PONZU-SHOYU", "ponzu shoyu"), ("  hot   sauce  ", "hot sauce"), ("yuzu_kosho sauce", "yuzu kosho sauce"), ("catsup", "ketchup")))
def test_case_whitespace_punctuation_and_aliases_normalize_equally(left: str, right: str) -> None:
    assert _parse(left) == _parse(right)


@pytest.mark.parametrize("text", ("wasabi sauce", "karashi mustard sauce", "horseradish cream sauce", "yuzu kosho sauce", "shio kombu sauce"))
def test_distinct_formulated_japanese_sauce_identity_is_included(text: str) -> None:
    assert _parse(text).family != "unknown"
    assert _parse(text).matched_evidence


@pytest.mark.parametrize("text", ("raw wasabi root", "prepared karashi condiment", "yuzu kosho paste", "dry shichimi powder"))
def test_raw_prepared_paste_powder_and_dry_spice_are_not_promoted(text: str) -> None:
    result = _parse(text)
    assert result.family == "unknown"
    assert result.unresolved_evidence


@pytest.mark.parametrize(("text", "included"), (("shio kombu", False), ("seasoned solid kelp", False), ("formulated shio kombu sauce", True), ("shio-kombu dipping sauce", True)))
def test_shio_kombu_requires_distinct_formulated_sauce_identity(text: str, included: bool) -> None:
    assert (_parse(text).family != "unknown") is included


@pytest.mark.parametrize(("text", "included"), (("ponzu shoyu dipping sauce", True), ("tsuyu broth", False), ("tare", False)))
def test_ponzu_tsuyu_and_tare_follow_product_identity(text: str, included: bool) -> None:
    assert (_parse(text).family != "unknown") is included


@pytest.mark.parametrize(("text", "included"), (("rayu chili oil sauce", True), ("ume paste", False), ("nori tsukudani preserve", False)))
def test_rayu_ume_paste_and_nori_tsukudani_preserve_boundaries(text: str, included: bool) -> None:
    assert (_parse(text).family != "unknown") is included


@pytest.mark.parametrize("text", ("salt", "vinegar"))
def test_standalone_cross_domain_ingredients_are_excluded(text: str) -> None:
    result = _parse(text)
    assert result.family == "unknown"
    assert result.unresolved_evidence


def test_conflicting_product_identity_remains_explicit() -> None:
    result = _parse("yuzu kosho sauce paste")
    assert result.conflicts
    assert result.unresolved_evidence


def test_provenance_is_reflected_in_matched_and_unresolved_evidence() -> None:
    explicit = _parse("ponzu shoyu dipping sauce")
    unresolved = _parse("generic condiment paste")
    assert explicit.matched_evidence
    assert unresolved.unresolved_evidence


def test_results_are_deterministic_and_side_effect_free() -> None:
    first = _parse("YUZU-KOSHO dipping sauce")
    second = _parse("YUZU-KOSHO dipping sauce")
    assert first == second
    assert first is not second
