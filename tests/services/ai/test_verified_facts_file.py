"""저장소에 들어 있는 확인된 사실 파일 자체를 확인한다 (형식·출처·기한 규칙)."""
from app.services.ai import facts


def test_every_verified_fact_has_a_source_and_follows_the_kind_rule():
    got = facts.all_facts()
    assert got, "verified_facts.json 이 비었거나 읽히지 않는다"
    ids = [f["id"] for f in got]
    assert len(ids) == len(set(ids))
    for f in got:
        assert f["kind"] in ("intrinsic", "seasonal"), f["id"]
        assert f.get("source_name") and f.get("source_url", "").startswith("https://"), f["id"]
        assert f.get("method") in ("source", "human") and f.get("verified_at"), f["id"]
        if f["kind"] == "intrinsic":
            assert f.get("review_after") is None, f["id"]           # 고유 특성은 기한 없음
        else:
            assert f.get("review_after"), f["id"]                    # 시기·시장 정보는 재확인일 필수


def test_geumsil_is_firm_per_source():
    assert "단단" in facts.find("딸기", "금실", "특성")["statement"]
