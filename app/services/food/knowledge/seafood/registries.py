from __future__ import annotations


SEAFOOD_SPECIES_REGISTRY = {
    "salmon": {
        "display_name": "연어",
        "group": "fish",
        "aliases": (
            "salmon",
            "연어",
            "생연어",
        ),
    },
    "tuna": {
        "display_name": "참치",
        "group": "fish",
        "aliases": (
            "tuna",
            "참치",
        ),
    },
    "mackerel": {
        "display_name": "고등어",
        "group": "fish",
        "aliases": (
            "mackerel",
            "고등어",
        ),
    },
    "cod": {
        "display_name": "대구",
        "group": "fish",
        "aliases": (
            "cod",
            "대구",
        ),
    },
    "pollock": {
        "display_name": "명태",
        "group": "fish",
        "aliases": (
            "pollock",
            "명태",
        ),
    },
    "anchovy": {
        "display_name": "멸치",
        "group": "fish",
        "aliases": (
            "anchovy",
            "멸치",
        ),
    },
    "shrimp": {
        "display_name": "새우",
        "group": "crustacean",
        "aliases": (
            "shrimp",
            "prawn",
            "새우",
            "대하",
        ),
    },
    "crab": {
        "display_name": "게",
        "group": "crustacean",
        "aliases": (
            "crab",
            "게",
            "꽃게",
            "대게",
            "킹크랩",
            "snow crab",
            "blue crab",
            "king crab",
        ),
    },
    "lobster": {
        "display_name": "랍스터",
        "group": "crustacean",
        "aliases": (
            "lobster",
            "랍스터",
            "로브스터",
        ),
    },
    "oyster": {
        "display_name": "굴",
        "group": "mollusk",
        "aliases": (
            "oyster",
            "굴",
            "석화",
        ),
    },
    "clam": {
        "display_name": "조개",
        "group": "mollusk",
        "aliases": (
            "clam",
            "조개",
        ),
    },
    "mussel": {
        "display_name": "홍합",
        "group": "mollusk",
        "aliases": (
            "mussel",
            "홍합",
        ),
    },
    "scallop": {
        "display_name": "가리비",
        "group": "mollusk",
        "aliases": (
            "scallop",
            "가리비",
        ),
    },
    "abalone": {
        "display_name": "전복",
        "group": "mollusk",
        "aliases": (
            "abalone",
            "전복",
        ),
    },
    "squid": {
        "display_name": "오징어",
        "group": "cephalopod",
        "aliases": (
            "squid",
            "오징어",
        ),
    },
    "octopus": {
        "display_name": "문어",
        "group": "cephalopod",
        "aliases": (
            "octopus",
            "문어",
        ),
    },
}


SEAFOOD_KEYWORDS = (
    "수산물",
    "seafood",
    "생물",
    "선어",
    "냉장",
    "냉동",
    "해동",
    "활어",
    "횟감",
    "손질",
    "필렛",
    "자연산",
    "양식",
)


WILD_FARMED_ALIASES = {
    "wild": (
        "wild",
        "자연산",
    ),
    "farmed": (
        "farmed",
        "farm raised",
        "farm-raised",
        "양식",
        "양식산",
    ),
}


PROCESSING_STATE_ALIASES = {
    "live": (
        "활어",
        "live",
    ),
    "fresh": (
        "생물",
        "선어",
        "냉장",
        "fresh",
        "chilled",
    ),
    "frozen": (
        "냉동",
        "frozen",
    ),
    "thawed": (
        "해동",
        "thawed",
        "defrosted",
    ),
}


__all__ = [
    "SEAFOOD_SPECIES_REGISTRY",
    "SEAFOOD_KEYWORDS",
    "WILD_FARMED_ALIASES",
    "PROCESSING_STATE_ALIASES",
]
