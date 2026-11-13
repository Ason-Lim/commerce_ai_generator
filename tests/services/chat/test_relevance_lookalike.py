"""검색어를 품은 다른 품목 이름 (2026-11-10) — '망고' 검색에 '샤인머스켓 망고포도'가 섞이던 문제."""
import pytest

from app.services.chat.service import relevant


@pytest.mark.parametrize("title", [
    "고당도 샤인머스켓 망고포도 샤인머스켓 농장 제철 거봉 2kg",
    "고당도샤인머스켓 수출용 프리미엄 선물용 샤인머스캣 망고 포도 2kg",
    "태국 망고스틴 1kg",
])
def test_lookalike_names_do_not_match_mango(title):
    assert relevant(title, ["망고"]) is False


@pytest.mark.parametrize("title", [
    "태국 무지개 망고 마하차녹 항공직송",
    "제주 애플망고 3kg 선물세트",
    "애플망고 & 망고스틴 혼합 선물세트",          # 진짜 망고도 들어 있으면 남긴다
])
def test_real_mango_still_matches(title):
    assert relevant(title, ["망고"]) is True


def test_grape_queries_keep_mango_grape():
    t = "고당도 샤인머스켓 망고포도 샤인머스켓 농장 제철 거봉 2kg"
    assert relevant(t, ["샤인머스캣"]) is True
    assert relevant(t, ["포도"]) is True
    assert relevant(t, ["과일"]) is True


def test_apple_jujube_is_not_apple():
    assert relevant("사과대추 1kg 생대추", ["사과"]) is False
    assert relevant("사과 5kg 부사", ["사과"]) is True
