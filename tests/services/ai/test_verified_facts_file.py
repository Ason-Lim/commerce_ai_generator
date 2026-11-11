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
        assert f.get("method") in ("source", "human") and f.get("verified_at") and f.get("reviewed_by"), f["id"]
        assert f.get("status") in ("active", "needs_review"), f["id"]
        assert f.get("applies_to") and f.get("conditions") and f.get("source_ref"), f["id"]
        if f["status"] == "active":                                  # 원문 문장 없이 '출처 확인'을 붙이지 않는다
            assert [q for q in f.get("source_quote") or [] if q.strip()], f["id"]
        if f["kind"] == "intrinsic":
            assert f.get("review_after") is None, f["id"]           # 고유 특성은 기한 없음
        else:
            assert f.get("review_after"), f["id"]                    # 시기·시장 정보는 재확인일 필수


def test_geumsil_is_firm_per_source():
    f = facts.find("딸기", "금실", "특성")
    assert "경도" in f["statement"] and any("우수한 경도" in q for q in f["source_quote"])


def test_facts_without_quotes_or_under_review_are_not_used(tmp_path, monkeypatch):
    import json

    p = tmp_path / "f.json"
    p.write_text(json.dumps({"facts": [
        {"id": "a", "food": "딸기", "subject": "금실", "attribute": "특성", "kind": "intrinsic", "statement": "x",
         "source_quote": [], "status": "active"},
        {"id": "b", "food": "딸기", "subject": "설향", "attribute": "특성", "kind": "intrinsic", "statement": "y",
         "source_quote": ["원문"], "status": "needs_review"}]}), encoding="utf-8")
    monkeypatch.setenv("VERIFIED_FACTS_FILE", str(p))
    assert facts.find("딸기", "금실", "특성") is None and facts.find("딸기", "설향", "특성") is None
