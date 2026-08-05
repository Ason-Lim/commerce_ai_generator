from __future__ import annotations

import pytest

from app.services.food.knowledge.tea.origin_registry import (
    TeaOrigin,
    TeaOriginRegistry,
)

from app.services.food.knowledge.tea.flavor_registry import (
    TeaFlavor,
    TeaFlavorRegistry,
)

from app.services.food.knowledge.tea.oxidation_registry import (
    TeaOxidation,
    TeaOxidationRegistry,
)

from app.services.food.knowledge.tea.processing_registry import (
    TeaProcessing,
    TeaProcessingRegistry,
)
from app.services.food.knowledge.tea.type_registry import (
    TeaType,
    TeaTypeRegistry,
)

from app.services.food.knowledge.tea.variety_registry import (
    TeaVariety,
    TeaVarietyRegistry,
)


@pytest.mark.parametrize(
    (
        "text",
        "expected_key",
    ),
    [
        ("녹차", "green"),
        ("green tea", "green"),
        ("홍차", "black"),
        ("black tea", "black"),
        ("우롱차", "oolong"),
        ("white tea", "white"),
        ("황차", "yellow"),
        ("보이차", "puerh"),
        ("pu-erh tea", "puerh"),
        ("허브티", "herbal"),
    ],
)
def test_tea_type_registry_matches_alias(
    text: str,
    expected_key: str,
) -> None:
    match = TeaTypeRegistry().match(text)

    assert match is not None
    assert match.entry.registry_key == expected_key
    assert match.tea_type is match.entry
    assert match.matched_alias
    assert match.normalized_alias
    assert 0.0 <= match.confidence <= 1.0
    assert match.match_start >= 0
    assert match.match_end > match.match_start
    assert match.exact_match is True


@pytest.mark.parametrize(
    (
        "text",
        "expected_key",
    ),
    [
        ("녹차", "green"),
        ("홍차", "black"),
        ("우롱차", "oolong"),
        ("백차", "white"),
        ("황차", "yellow"),
        ("보이차", "puerh"),
        ("허브티", "herbal"),
    ],
)
def test_tea_type_registry_lookup_returns_entry(
    text: str,
    expected_key: str,
) -> None:
    entry = TeaTypeRegistry().lookup(text)

    assert isinstance(entry, TeaType)
    assert entry.registry_key == expected_key
    assert entry.canonical_name
    assert entry.aliases
    assert 0.0 <= entry.score <= 100.0


def test_tea_type_registry_returns_none_for_unknown_text() -> None:
    match = TeaTypeRegistry().match(
        "등록되지 않은 임의의 문자열"
    )

    assert match is None


def test_tea_type_registry_includes_canonical_name_in_aliases() -> None:
    entry = TeaTypeRegistry().lookup("녹차")

    assert entry is not None
    assert entry.canonical_name == "green"
    assert "green" in entry.aliases


def test_tea_type_registry_entries_are_immutable() -> None:
    entry = TeaTypeRegistry().lookup("홍차")

    assert entry is not None

    with pytest.raises(
        (AttributeError, TypeError),
    ):
        entry.canonical_name = "changed"  # type: ignore[misc]


def test_tea_type_registry_clamps_score_range() -> None:
    entry = TeaTypeRegistry().lookup("보이차")

    assert entry is not None
    assert entry.score == 0.0
    assert entry.premium is False



@pytest.mark.parametrize(
    (
        "text",
        "expected_key",
    ),
    [
        ("다즐링", "darjeeling"),
        ("Assam tea", "assam"),
        ("우지 녹차", "uji"),
        ("시즈오카 차", "shizuoka"),
        ("제주 녹차", "jeju"),
        ("보성차", "boseong"),
        ("윈난 차", "yunnan"),
        ("푸젠 차", "fujian"),
        ("실론티", "ceylon"),
    ],
)
def test_tea_origin_registry_matches_alias(
    text: str,
    expected_key: str,
) -> None:
    match = TeaOriginRegistry().match(text)

    assert match is not None
    assert match.entry.registry_key == expected_key
    assert match.tea_origin is match.entry
    assert match.matched_alias
    assert match.normalized_alias
    assert 0.0 <= match.confidence <= 1.0
    assert match.match_start >= 0
    assert match.match_end > match.match_start


@pytest.mark.parametrize(
    (
        "text",
        "expected_key",
        "expected_country_code",
    ),
    [
        ("다즐링", "darjeeling", "IN"),
        ("아삼", "assam", "IN"),
        ("우지", "uji", "JP"),
        ("제주", "jeju", "KR"),
        ("보성", "boseong", "KR"),
        ("윈난", "yunnan", "CN"),
        ("실론", "ceylon", "LK"),
    ],
)
def test_tea_origin_registry_lookup_returns_entry(
    text: str,
    expected_key: str,
    expected_country_code: str,
) -> None:
    entry = TeaOriginRegistry().lookup(text)

    assert isinstance(entry, TeaOrigin)
    assert entry.registry_key == expected_key
    assert entry.country_code == expected_country_code
    assert entry.canonical_name
    assert entry.aliases
    assert 0.0 <= entry.score <= 100.0


def test_tea_origin_registry_metadata() -> None:
    entry = TeaOriginRegistry().lookup(
        "다즐링"
    )

    assert entry is not None
    assert entry.registry_key == "darjeeling"
    assert entry.country_code == "IN"
    assert entry.country_name == "India"
    assert entry.region_name == "Darjeeling"


def test_tea_origin_registry_returns_none_for_unknown_text() -> None:
    match = TeaOriginRegistry().match(
        "등록되지 않은 차 산지"
    )

    assert match is None


@pytest.mark.parametrize(
    (
        "text",
        "expected_key",
    ),
    [
        ("중국소엽종", "sinensis"),
        ("Camellia sinensis var. assamica", "assamica"),
        ("야부키타", "yabukita"),
        ("Saemidori", "saemidori"),
        ("오쿠미도리", "okumidori"),
        ("베니후키", "benifuuki"),
        ("Longjing 43", "longjing_43"),
        ("금훤", "jinxuan"),
        ("TTES No. 12", "jinxuan"),
    ],
)
def test_tea_variety_registry_matches_alias(
    text: str,
    expected_key: str,
) -> None:
    match = TeaVarietyRegistry().match(text)

    assert match is not None
    assert match.entry.registry_key == expected_key
    assert match.tea_variety is match.entry
    assert match.matched_alias
    assert match.normalized_alias
    assert 0.0 <= match.confidence <= 1.0
    assert match.match_start >= 0
    assert match.match_end > match.match_start


@pytest.mark.parametrize(
    (
        "text",
        "expected_key",
        "expected_kind",
        "expected_country_code",
    ),
    [
        (
            "소엽종",
            "sinensis",
            "botanical_variety",
            None,
        ),
        (
            "아사미카",
            "assamica",
            "botanical_variety",
            None,
        ),
        (
            "야부키타",
            "yabukita",
            "cultivar",
            "JP",
        ),
        (
            "오쿠미도리",
            "okumidori",
            "cultivar",
            "JP",
        ),
        (
            "롱징 43",
            "longjing_43",
            "cultivar",
            "CN",
        ),
        (
            "진쉬안",
            "jinxuan",
            "cultivar",
            "TW",
        ),
    ],
)
def test_tea_variety_registry_lookup_returns_entry(
    text: str,
    expected_key: str,
    expected_kind: str,
    expected_country_code: str | None,
) -> None:
    entry = TeaVarietyRegistry().lookup(text)

    assert isinstance(entry, TeaVariety)
    assert entry.registry_key == expected_key
    assert entry.variety_kind == expected_kind
    assert entry.country_code == expected_country_code
    assert entry.canonical_name
    assert entry.aliases
    assert 0.0 <= entry.score <= 100.0


def test_tea_variety_registry_metadata() -> None:
    entry = TeaVarietyRegistry().lookup(
        "TTES No. 12"
    )

    assert entry is not None
    assert entry.registry_key == "jinxuan"
    assert entry.variety_kind == "cultivar"
    assert entry.country_code == "TW"
    assert (
        entry.botanical_name
        == "Camellia sinensis"
    )


def test_tea_variety_registry_returns_none_for_unknown_text() -> None:
    match = TeaVarietyRegistry().match(
        "등록되지 않은 차 품종"
    )

    assert match is None


@pytest.mark.parametrize(
    (
        "text",
        "expected_key",
    ),
    [
        ("증제차", "steamed"),
        ("pan-fired green tea", "pan_fired"),
        ("위조 공정", "withered"),
        ("유념 공정", "rolled"),
        ("배전차", "roasted"),
        ("천일건조", "sun_dried"),
        ("후발효차", "post_fermented"),
        ("wet piling", "wet_piled"),
        ("훈연차", "smoked"),
    ],
)
def test_tea_processing_registry_matches_alias(
    text: str,
    expected_key: str,
) -> None:
    match = TeaProcessingRegistry().match(text)

    assert match is not None
    assert match.entry.registry_key == expected_key
    assert match.tea_processing is match.entry
    assert match.matched_alias
    assert match.normalized_alias
    assert 0.0 <= match.confidence <= 1.0
    assert match.match_start >= 0
    assert match.match_end > match.match_start


@pytest.mark.parametrize(
    (
        "text",
        "expected_key",
        "expected_category",
    ),
    [
        (
            "증제",
            "steamed",
            "heat_fixation",
        ),
        (
            "덖음차",
            "pan_fired",
            "heat_fixation",
        ),
        (
            "위조",
            "withered",
            "moisture_reduction",
        ),
        (
            "유념",
            "rolled",
            "shaping",
        ),
        (
            "일광건조",
            "sun_dried",
            "drying",
        ),
        (
            "후발효",
            "post_fermented",
            "microbial_fermentation",
        ),
        (
            "훈연",
            "smoked",
            "smoking",
        ),
    ],
)
def test_tea_processing_registry_lookup_returns_entry(
    text: str,
    expected_key: str,
    expected_category: str,
) -> None:
    entry = TeaProcessingRegistry().lookup(text)

    assert isinstance(entry, TeaProcessing)
    assert entry.registry_key == expected_key
    assert entry.process_category == expected_category
    assert entry.canonical_name
    assert entry.aliases
    assert 0.0 <= entry.score <= 100.0


def test_tea_processing_registry_heat_fixation_metadata() -> None:
    entry = TeaProcessingRegistry().lookup(
        "pan-fired"
    )

    assert entry is not None
    assert entry.registry_key == "pan_fired"
    assert entry.heat_fixation is True
    assert entry.microbial_fermentation is False
    assert entry.smoke_applied is False


def test_tea_processing_registry_fermentation_metadata() -> None:
    entry = TeaProcessingRegistry().lookup(
        "wet piling"
    )

    assert entry is not None
    assert entry.registry_key == "wet_piled"
    assert entry.heat_fixation is False
    assert entry.microbial_fermentation is True
    assert entry.smoke_applied is False


def test_tea_processing_registry_smoking_metadata() -> None:
    entry = TeaProcessingRegistry().lookup(
        "훈연차"
    )

    assert entry is not None
    assert entry.registry_key == "smoked"
    assert entry.smoke_applied is True
    assert entry.microbial_fermentation is False


def test_tea_processing_registry_returns_none_for_unknown_text() -> None:
    match = TeaProcessingRegistry().match(
        "등록되지 않은 차 가공법"
    )

    assert match is None


@pytest.mark.parametrize(
    (
        "text",
        "expected_key",
    ),
    [
        ("비산화차", "unoxidized"),
        ("lightly oxidized tea", "light"),
        ("부분 산화 우롱차", "medium"),
        ("강산화 우롱차", "high"),
        ("fully oxidized tea", "full"),
        ("완전산화 홍차", "full"),
    ],
)
def test_tea_oxidation_registry_matches_alias(
    text: str,
    expected_key: str,
) -> None:
    match = TeaOxidationRegistry().match(text)

    assert match is not None
    assert match.entry.registry_key == expected_key
    assert match.tea_oxidation is match.entry
    assert match.matched_alias
    assert match.normalized_alias
    assert 0.0 <= match.confidence <= 1.0
    assert match.match_start >= 0
    assert match.match_end > match.match_start


@pytest.mark.parametrize(
    (
        "text",
        "expected_key",
        "expected_level",
    ),
    [
        (
            "비산화",
            "unoxidized",
            0,
        ),
        (
            "약산화",
            "light",
            1,
        ),
        (
            "중산화",
            "medium",
            2,
        ),
        (
            "고산화",
            "high",
            3,
        ),
        (
            "완전 산화",
            "full",
            4,
        ),
    ],
)
def test_tea_oxidation_registry_lookup_returns_entry(
    text: str,
    expected_key: str,
    expected_level: int,
) -> None:
    entry = TeaOxidationRegistry().lookup(text)

    assert isinstance(entry, TeaOxidation)
    assert entry.registry_key == expected_key
    assert entry.oxidation_level == expected_level
    assert entry.canonical_name
    assert entry.aliases
    assert 0.0 <= entry.score <= 100.0


def test_tea_oxidation_registry_partial_metadata() -> None:
    entry = TeaOxidationRegistry().lookup(
        "부분 산화"
    )

    assert entry is not None
    assert entry.registry_key == "medium"
    assert entry.oxidation_level == 2
    assert entry.oxidation_min_percent == 25.0
    assert entry.oxidation_max_percent == 60.0
    assert entry.fully_oxidized is False


def test_tea_oxidation_registry_full_metadata() -> None:
    entry = TeaOxidationRegistry().lookup(
        "완전산화"
    )

    assert entry is not None
    assert entry.registry_key == "full"
    assert entry.oxidation_level == 4
    assert entry.oxidation_min_percent == 90.0
    assert entry.oxidation_max_percent == 100.0
    assert entry.fully_oxidized is True


def test_tea_oxidation_registry_returns_none_for_unknown_text() -> None:
    match = TeaOxidationRegistry().match(
        "등록되지 않은 산화 표현"
    )

    assert match is None


@pytest.mark.parametrize(
    (
        "text",
        "expected_key",
    ),
    [
        ("꽃향 우롱차", "floral"),
        ("자스민 향 녹차", "jasmine"),
        ("난향 우롱차", "orchid"),
        ("풀향 녹차", "grassy"),
        ("감칠맛 말차", "umami"),
        ("꿀향 홍차", "honey"),
        ("맥아향 아삼 홍차", "malty"),
        ("배전향 우롱차", "roasted"),
        ("훈연향 홍차", "smoky"),
        ("시트러스 홍차", "citrus"),
        ("복숭아향 백차", "stone_fruit"),
        ("흙향 보이차", "earthy"),
        ("미네랄리티 우롱차", "mineral"),
        ("떫은맛 홍차", "astringent"),
        ("쓴맛 녹차", "bitter"),
    ],
)
def test_tea_flavor_registry_matches_alias(
    text: str,
    expected_key: str,
) -> None:
    match = TeaFlavorRegistry().match(text)

    assert match is not None
    assert match.entry.registry_key == expected_key
    assert match.tea_flavor is match.entry
    assert match.matched_alias
    assert match.normalized_alias
    assert 0.0 <= match.confidence <= 1.0
    assert match.match_start >= 0
    assert match.match_end > match.match_start


@pytest.mark.parametrize(
    (
        "text",
        "expected_key",
        "expected_family",
        "expected_dimension",
    ),
    [
        (
            "꽃향",
            "floral",
            "floral",
            "aroma",
        ),
        (
            "감칠맛",
            "umami",
            "savory",
            "taste",
        ),
        (
            "꿀향",
            "honey",
            "sweet",
            "both",
        ),
        (
            "맥아향",
            "malty",
            "grain",
            "both",
        ),
        (
            "시트러스",
            "citrus",
            "fruity",
            "both",
        ),
        (
            "흙향",
            "earthy",
            "earthy",
            "both",
        ),
        (
            "떫은맛",
            "astringent",
            "structural",
            "taste",
        ),
    ],
)
def test_tea_flavor_registry_lookup_returns_entry(
    text: str,
    expected_key: str,
    expected_family: str,
    expected_dimension: str,
) -> None:
    entry = TeaFlavorRegistry().lookup(text)

    assert isinstance(entry, TeaFlavor)
    assert entry.registry_key == expected_key
    assert entry.flavor_family == expected_family
    assert (
        entry.sensory_dimension
        == expected_dimension
    )
    assert entry.canonical_name
    assert entry.aliases
    assert 0.0 <= entry.score <= 100.0


def test_tea_flavor_registry_aroma_metadata() -> None:
    entry = TeaFlavorRegistry().lookup(
        "자스민 향"
    )

    assert entry is not None
    assert entry.registry_key == "jasmine"
    assert entry.flavor_family == "floral"
    assert entry.sensory_dimension == "aroma"
    assert entry.aroma_dominant is True
    assert entry.taste_dominant is False


def test_tea_flavor_registry_taste_metadata() -> None:
    entry = TeaFlavorRegistry().lookup(
        "감칠맛"
    )

    assert entry is not None
    assert entry.registry_key == "umami"
    assert entry.sensory_dimension == "taste"
    assert entry.aroma_dominant is False
    assert entry.taste_dominant is True


def test_tea_flavor_registry_both_metadata() -> None:
    entry = TeaFlavorRegistry().lookup(
        "꿀향"
    )

    assert entry is not None
    assert entry.registry_key == "honey"
    assert entry.sensory_dimension == "both"
    assert entry.aroma_dominant is True
    assert entry.taste_dominant is True


def test_tea_flavor_registry_returns_none_for_unknown_text() -> None:
    match = TeaFlavorRegistry().match(
        "등록되지 않은 차 향미"
    )

    assert match is None
