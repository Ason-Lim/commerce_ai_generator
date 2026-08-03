from app.services.food.knowledge.meat.beef.provider import (
    BeefKnowledgeProvider,
)

from app.services.food.knowledge.meat.beef.grade_registry import (
    BEEF_GRADE_REGISTRY_ID,
    BeefGrade,
    BeefGradeMatch,
    BeefGradeRegistry,
    detect_country_code,
    get_beef_grade,
    get_beef_grade_registry,
    list_beef_grades,
    lookup_beef_grade,
    match_beef_grade,
    normalize_country_code,
    normalize_grade_text,
)


from app.services.food.knowledge.meat.beef.breed_registry import (
    BEEF_BREED_REGISTRY_ID,
    BeefBreed,
    BeefBreedMatch,
    BeefBreedRegistry,
    get_beef_breed,
    get_beef_breed_registry,
    list_beef_breeds,
    lookup_beef_breed,
    match_beef_breed,
)


from app.services.food.knowledge.meat.beef.cut_registry import (
    BEEF_CUT_REGISTRY_ID,
    BeefCut,
    BeefCutMatch,
    BeefCutRegistry,
    beef_cuts_for_cooking,
    get_beef_cut,
    get_beef_cut_registry,
    list_beef_cuts,
    lookup_beef_cut,
    match_beef_cut,
    premium_beef_cuts,
)

__all__ = [
    "BeefKnowledgeProvider",
    "BEEF_GRADE_REGISTRY_ID",
    "BeefGrade",
    "BeefGradeMatch",
    "BeefGradeRegistry",
    "detect_country_code",
    "get_beef_grade",
    "get_beef_grade_registry",
    "list_beef_grades",
    "lookup_beef_grade",
    "match_beef_grade",
    "normalize_country_code",
    "normalize_grade_text",
    "BEEF_BREED_REGISTRY_ID",
    "BeefBreed",
    "BeefBreedMatch",
    "BeefBreedRegistry",
    "get_beef_breed",
    "get_beef_breed_registry",
    "list_beef_breeds",
    "lookup_beef_breed",
    "match_beef_breed",
    "BEEF_CUT_REGISTRY_ID",
    "BeefCut",
    "BeefCutMatch",
    "BeefCutRegistry",
    "beef_cuts_for_cooking",
    "get_beef_cut",
    "get_beef_cut_registry",
    "list_beef_cuts",
    "lookup_beef_cut",
    "match_beef_cut",
    "premium_beef_cuts",
]