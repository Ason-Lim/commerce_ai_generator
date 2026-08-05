from __future__ import annotations

from dataclasses import asdict
from pathlib import Path

import pytest

from app.services.food.knowledge.tea.flavor_registry import (
    TEA_FLAVOR_REGISTRY_ID,
    TeaFlavorRegistry,
)
from app.services.food.knowledge.tea.origin_registry import (
    TEA_ORIGIN_REGISTRY_ID,
    TeaOriginRegistry,
)
from app.services.food.knowledge.tea.oxidation_registry import (
    TEA_OXIDATION_REGISTRY_ID,
    TeaOxidationRegistry,
)
from app.services.food.knowledge.tea.processing_registry import (
    TEA_PROCESSING_REGISTRY_ID,
    TeaProcessingRegistry,
)
from app.services.food.knowledge.tea.type_registry import (
    TEA_TYPE_REGISTRY_ID,
    TeaTypeRegistry,
)
from app.services.food.knowledge.tea.variety_registry import (
    TEA_VARIETY_REGISTRY_ID,
    TeaVarietyRegistry,
)


REGISTRY_DATA_ROOT = Path(
    "app/services/food/registry_data/tea"
)


@pytest.mark.parametrize(
    (
        "registry_id",
        "expected_filename",
    ),
    [
        (
            TEA_TYPE_REGISTRY_ID,
            "types.yaml",
        ),
        (
            TEA_ORIGIN_REGISTRY_ID,
            "origins.yaml",
        ),
        (
            TEA_VARIETY_REGISTRY_ID,
            "varieties.yaml",
        ),
        (
            TEA_PROCESSING_REGISTRY_ID,
            "processes.yaml",
        ),
        (
            TEA_OXIDATION_REGISTRY_ID,
            "oxidations.yaml",
        ),
        (
            TEA_FLAVOR_REGISTRY_ID,
            "flavors.yaml",
        ),
    ],
)
def test_tea_registry_id_maps_to_expected_yaml(
    registry_id: str,
    expected_filename: str,
) -> None:
    domain_name, registry_name = registry_id.split(
        ".",
        maxsplit=1,
    )

    assert domain_name == "tea"
    assert registry_name
    assert (
        REGISTRY_DATA_ROOT / expected_filename
    ).is_file()


@pytest.mark.parametrize(
    (
        "registry",
        "sample_text",
        "expected_key",
    ),
    [
        (
            TeaTypeRegistry(),
            "우롱차",
            "oolong",
        ),
        (
            TeaOriginRegistry(),
            "다즐링",
            "darjeeling",
        ),
        (
            TeaVarietyRegistry(),
            "야부키타",
            "yabukita",
        ),
        (
            TeaProcessingRegistry(),
            "증제차",
            "steamed",
        ),
        (
            TeaOxidationRegistry(),
            "부분 산화",
            "medium",
        ),
        (
            TeaFlavorRegistry(),
            "꽃향",
            "floral",
        ),
    ],
)
def test_all_tea_registries_load_and_lookup(
    registry: object,
    sample_text: str,
    expected_key: str,
) -> None:
    entry = registry.lookup(  # type: ignore[attr-defined]
        sample_text
    )

    assert entry is not None
    assert entry.registry_key == expected_key
    assert entry.canonical_name
    assert entry.aliases
    assert 0.0 <= entry.score <= 100.0


def test_tea_registries_extract_independent_dimensions() -> None:
    product_name = (
        "다즐링 야부키타 부분 산화 "
        "증제 꽃향 우롱차"
    )

    tea_type = TeaTypeRegistry().match(
        product_name
    )
    origin = TeaOriginRegistry().match(
        product_name
    )
    variety = TeaVarietyRegistry().match(
        product_name
    )
    processing = TeaProcessingRegistry().match(
        product_name
    )
    oxidation = TeaOxidationRegistry().match(
        product_name
    )
    flavor = TeaFlavorRegistry().match(
        product_name
    )

    assert tea_type is not None
    assert tea_type.entry.registry_key == "oolong"

    assert origin is not None
    assert origin.entry.registry_key == "darjeeling"

    assert variety is not None
    assert variety.entry.registry_key == "yabukita"

    assert processing is not None
    assert processing.entry.registry_key == "steamed"

    assert oxidation is not None
    assert oxidation.entry.registry_key == "medium"

    assert flavor is not None
    assert flavor.entry.registry_key == "floral"


def test_tea_registries_preserve_domain_metadata() -> None:
    origin = TeaOriginRegistry().lookup(
        "다즐링"
    )
    variety = TeaVarietyRegistry().lookup(
        "야부키타"
    )
    processing = TeaProcessingRegistry().lookup(
        "증제"
    )
    oxidation = TeaOxidationRegistry().lookup(
        "부분 산화"
    )
    flavor = TeaFlavorRegistry().lookup(
        "꽃향"
    )

    assert origin is not None
    assert origin.country_code == "IN"
    assert origin.region_name == "Darjeeling"

    assert variety is not None
    assert variety.variety_kind == "cultivar"
    assert variety.country_code == "JP"

    assert processing is not None
    assert processing.process_category == "heat_fixation"
    assert processing.heat_fixation is True

    assert oxidation is not None
    assert oxidation.oxidation_level == 2
    assert oxidation.oxidation_min_percent == 25.0
    assert oxidation.oxidation_max_percent == 60.0

    assert flavor is not None
    assert flavor.flavor_family == "floral"
    assert flavor.sensory_dimension == "aroma"


@pytest.mark.parametrize(
    "registry",
    [
        TeaTypeRegistry(),
        TeaOriginRegistry(),
        TeaVarietyRegistry(),
        TeaProcessingRegistry(),
        TeaOxidationRegistry(),
        TeaFlavorRegistry(),
    ],
)
def test_tea_registries_return_none_for_unknown_text(
    registry: object,
) -> None:
    match = registry.match(  # type: ignore[attr-defined]
        "등록되지 않은 완전히 임의의 표현"
    )

    assert match is None


@pytest.mark.parametrize(
    (
        "registry",
        "sample_text",
    ),
    [
        (
            TeaTypeRegistry(),
            "우롱차",
        ),
        (
            TeaOriginRegistry(),
            "다즐링",
        ),
        (
            TeaVarietyRegistry(),
            "야부키타",
        ),
        (
            TeaProcessingRegistry(),
            "증제",
        ),
        (
            TeaOxidationRegistry(),
            "부분 산화",
        ),
        (
            TeaFlavorRegistry(),
            "꽃향",
        ),
    ],
)
def test_tea_registry_lookup_is_deterministic(
    registry: object,
    sample_text: str,
) -> None:
    first = registry.lookup(  # type: ignore[attr-defined]
        sample_text
    )
    second = registry.lookup(  # type: ignore[attr-defined]
        sample_text
    )

    assert first is not None
    assert second is not None
    assert first == second
    assert asdict(first) == asdict(second)


@pytest.mark.parametrize(
    (
        "registry",
        "sample_text",
    ),
    [
        (
            TeaTypeRegistry(),
            "녹차",
        ),
        (
            TeaOriginRegistry(),
            "제주",
        ),
        (
            TeaVarietyRegistry(),
            "금훤",
        ),
        (
            TeaProcessingRegistry(),
            "후발효",
        ),
        (
            TeaOxidationRegistry(),
            "완전 산화",
        ),
        (
            TeaFlavorRegistry(),
            "감칠맛",
        ),
    ],
)
def test_tea_registry_entries_are_serializable(
    registry: object,
    sample_text: str,
) -> None:
    entry = registry.lookup(  # type: ignore[attr-defined]
        sample_text
    )

    assert entry is not None

    payload = asdict(entry)

    assert isinstance(payload, dict)
    assert payload["registry_key"]
    assert payload["canonical_name"]
    assert isinstance(payload["aliases"], tuple)
    assert isinstance(payload["metadata"], dict)


def test_tea_registry_longest_alias_match_is_preserved() -> None:
    origin_match = TeaOriginRegistry().match(
        "제주 녹차"
    )
    processing_match = TeaProcessingRegistry().match(
        "전통 덖음차"
    )
    flavor_match = TeaFlavorRegistry().match(
        "자스민 향 녹차"
    )

    assert origin_match is not None
    assert origin_match.matched_alias == "제주 녹차"

    assert processing_match is not None
    assert processing_match.matched_alias == "덖음차"

    assert flavor_match is not None
    assert flavor_match.matched_alias == "자스민 향"


def test_processing_and_flavor_roasted_remain_independent() -> None:
    product_name = "배전향 배전 우롱차"

    processing = TeaProcessingRegistry().match(
        product_name
    )
    flavor = TeaFlavorRegistry().match(
        product_name
    )

    assert processing is not None
    assert processing.entry.registry_key == "roasted"
    assert processing.entry.process_category == "finishing"

    assert flavor is not None
    assert flavor.entry.registry_key == "roasted"
    assert flavor.entry.flavor_family == "roasted"

    assert (
        processing.entry.registry_key
        == flavor.entry.registry_key
    )
    assert (
        processing.entry.__class__
        is not flavor.entry.__class__
    )
