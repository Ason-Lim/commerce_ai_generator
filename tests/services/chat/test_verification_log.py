"""확인 기록표 (2026-11-03 p36): 기록표에 적힌 값만 '검증됨'. 값이 다르면 충돌, 기한·형식이 맞지 않으면 무시.
점수 사용은 이 기록으로 열리지 않는다."""
from __future__ import annotations

import csv
import json
from datetime import date
from pathlib import Path

import pytest

from app.domain.commerce import policies
from app.domain.commerce.models import Evidence
from app.domain.commerce.requests import SearchRequest
from app.services.commerce.ocr_evidence import from_offer_result, from_region_bundle
from app.services.commerce.search import search_products
from app.services.partners import verification as V
from tests.services.chat.conftest import FakeShopping

TODAY = date(2026, 11, 3)
FIX = Path(__file__).parent / "fixtures"
OFFER = json.loads((FIX / "ocr_offer_example.json").read_text(encoding="utf-8"))
BUNDLE = json.loads((FIX / "ocr_bundle_example.json").read_text(encoding="utf-8"))
OCR_OK = {"예시몰": {"상태": "허락", "이미지 문자 판독(OCR)": "허용"}}


def row(**kw):
    base = {"업체": "예시몰", "대상": "SAMPLE-1", "항목": "price", "값": "12,900", "단위": "원", "근거 종류": "업체 서면 확인",
            "근거 파일": "예시몰_가격확인_1102.pdf", "확인자": "Ason", "확인일": "2026-11-02", "유효기한": "", "메모": ""}
    return {**base, **kw}


def write(tmp_path, rows) -> Path:
    p = tmp_path / "verified_values.csv"
    with p.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(V.COLUMNS))
        w.writeheader()
        w.writerows(rows)
    return p


def ev(value="12900", **kw):
    return policies.with_usage(Evidence(field="price", value=value, unit="원", method="partner_feed", source="예시몰", **kw))


def test_incomplete_or_badly_dated_rows_are_ignored(tmp_path):
    p = write(tmp_path, [row(), row(확인자=""), row(**{"근거 종류": ""}), row(확인일="11/02"), row(유효기한="내년")])
    assert len(V.load(p)) == 1


def test_same_value_is_verified_with_the_record_note(tmp_path):
    recs = V.load(write(tmp_path, [row()]))
    out = V.apply(ev(), "예시몰", "SAMPLE-1", records=recs, today=TODAY)
    assert out.status == "verified" and "업체 서면 확인 · Ason · 2026-11-02" in out.source
    assert out.usable_for_score is False and not policies.score_usable(out)       # 점수는 열리지 않음
    assert out.policy_version == policies.POLICY_VERSION


def test_different_value_becomes_conflict(tmp_path):
    recs = V.load(write(tmp_path, [row(값="13900")]))
    out = V.apply(ev(), "예시몰", "SAMPLE-1", records=recs, today=TODAY)
    assert out.status == "conflict" and "확인 기록 값과 다름: 13900원" in out.source
    assert {d.use: d.verdict for d in out.usage}["display"] == "hold"


@pytest.mark.parametrize("change", [{"유효기한": "2026-11-01"}, {"확인일": "2026-11-05"}, {"업체": "다른몰"},
                                    {"대상": "SAMPLE-2"}, {"항목": "weight_g"}, {"단위": "달러"}])
def test_records_that_do_not_apply_leave_the_value_unverified(tmp_path, change):
    recs = V.load(write(tmp_path, [row(**change)]))
    assert V.apply(ev(), "예시몰", "SAMPLE-1", records=recs, today=TODAY).status == "unverified"


def test_missing_or_conflicting_values_are_never_verified(tmp_path):
    recs = V.load(write(tmp_path, [row()]))
    for e in (ev(value=None, status="missing"), ev(status="conflict")):
        assert V.apply(e, "예시몰", "SAMPLE-1", records=recs, today=TODAY).status == e.status


def test_ocr_option_value_is_verified_by_image_hash_and_option(tmp_path, monkeypatch):
    target = f"sha256:{OFFER['source_sha256']}#O001"
    monkeypatch.setenv("PARTNER_VERIFIED_CSV", str(write(tmp_path, [
        row(대상=target, 항목="price", 값="12900", **{"근거 종류": "원본 이미지 대조"}),
        row(대상=target, 항목="weight_kg", 값="0.6", 단위="kg", **{"근거 종류": "원본 이미지 대조"})])))
    got = {e.field: e for e in from_offer_result(OFFER, partner="예시몰", permissions=OCR_OK)["evidence"]}
    price, weight = got["option[O001].price"], got["option[O001].weight_kg"]
    assert price.status == "verified" and weight.status == "conflict"          # 0.5 로 읽음 ≠ 기록 0.6
    v = {d.use: d.verdict for d in price.usage}
    assert v["display"] == "allow_labelled" and v["score"] == "block"           # OCR 은 검증돼도 점수 차단
    assert got["option[O002].price"].status == "unverified"                     # 기록 없는 값은 그대로


def test_ocr_region_text_uses_the_original_image_hash(tmp_path, monkeypatch):
    text = BUNDLE["regions"][0]["ocr"]["text"]
    monkeypatch.setenv("PARTNER_VERIFIED_CSV", str(write(tmp_path, [
        row(대상=f"sha256:{BUNDLE['source_sha256']}#R001", 항목="ocr_text", 값=text, 단위="",
            **{"근거 종류": "원본 이미지 대조"})])))
    got = {e.field: e for e in from_region_bundle(BUNDLE, partner="예시몰", permissions=OCR_OK)["evidence"]}
    assert got["region[R001].ocr_text"].status == "verified"


def test_partner_search_marks_recorded_values_without_changing_the_ranking(tmp_path, monkeypatch):
    monkeypatch.setenv("PARTNER_PREVIEW", "1")
    monkeypatch.setenv("PARTNER_DATA_DIR", str(tmp_path))
    with (tmp_path / "permissions.csv").open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["업체", "상태"])
        w.writeheader()
        w.writerow({"업체": "한우이츠", "상태": "요청함"})
    (tmp_path / "hanwooeats").mkdir()
    with (tmp_path / "hanwooeats" / "products_sample.csv").open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(["상품ID", "상품명", "품목", "품종", "중량(g)", "수량", "판매가", "정가", "배송비", "당도(Brix)", "산지",
                    "등급", "상품URL", "이미지URL", "재고상태", "가격기준일시", "비고"])
        w.writerow(["S2", "(예시) 한우 1++등급 등심 구이용 300g", "소", "등심", "", "", "46900", "", "0", "", "", "",
                    "https://hanwooeats.com/", "", "판매중", "2026-11-02 09:00", "예시"])
    items = [{"product_name": "농협안심한우 등심 1등급 300g", "price": 39000,
              "product_url": "https://www.coupang.com/vp/products/1", "platform_name": "쿠팡", "is_coupang": True}]
    sig = lambda r: [(i.product.key, i.score.rank, i.score.role) for i in r.items]  # noqa: E731
    before = search_products(SearchRequest(text="한우 등심 추천"), shopping=FakeShopping(items=items))
    monkeypatch.setenv("PARTNER_VERIFIED_CSV", str(write(tmp_path, [
        row(업체="한우이츠", 대상="S2", 값="46900", 확인일=date.today().isoformat())])))
    after = search_products(SearchRequest(text="한우 등심 추천"), shopping=FakeShopping(items=items))
    assert sig(before) == sig(after)
    price = next(e for i in after.items if i.offer.link_type == "partner" for e in i.evidence if e.field == "price")
    assert price.status == "verified" and "업체 서면 확인" in price.source


def test_unit_must_match_exactly_including_blank(tmp_path):
    """p37: 값이 같아도 단위가 다르거나 한쪽만 비어 있으면 검증하지 않는다."""
    recs = V.load(write(tmp_path, [row(단위="")]))
    assert V.apply(ev(), "예시몰", "SAMPLE-1", records=recs, today=TODAY).status == "unverified"
    recs = V.load(write(tmp_path, [row(단위="원")]))
    no_unit = policies.with_usage(Evidence(field="price", value="12900", method="partner_feed", source="예시몰"))
    assert V.apply(no_unit, "예시몰", "SAMPLE-1", records=recs, today=TODAY).status == "unverified"


def test_disagreeing_valid_records_make_a_conflict_even_if_one_matches(tmp_path):
    recs = V.load(write(tmp_path, [row(값="12900", 확인일="2026-11-01"), row(값="13900", 확인일="2026-11-02")]))
    out = V.apply(ev(), "예시몰", "SAMPLE-1", records=recs, today=TODAY)
    assert out.status == "conflict" and "확인 기록끼리 값이 다름: 12900원, 13900원" in out.source


def test_expired_disagreeing_record_does_not_count(tmp_path):
    recs = V.load(write(tmp_path, [row(값="12900"), row(값="13900", 유효기한="2026-10-31")]))
    assert V.apply(ev(), "예시몰", "SAMPLE-1", records=recs, today=TODAY).status == "verified"


# ── p38: 숫자 비교는 반올림 없이 (GPT 재현: 1,234,567 ↔ 1,234,568 이 '같다'고 판정되던 문제) ─────────

@pytest.mark.parametrize("a, b, same", [
    ("1,234,567", "1234568", False),
    ("1234567", "1,234,567원", True),
    ("12900", "12900.0", True),
    ("0.5", "0.50", True),
    ("0.1234567", "0.1234568", False),
    ("123456.7", "123456.8", False),
    ("1e3", "1000", True),
])
def test_numbers_are_compared_exactly(a, b, same):
    assert (V._norm(a) == V._norm(b)) is same


@pytest.mark.parametrize("bad", ["NaN", "nan", "Infinity", "-inf", "inf"])
def test_non_finite_numbers_are_not_compared(bad):
    assert V._norm(bad) is None


def test_close_but_different_amount_is_a_conflict_not_verified(tmp_path):
    recs = V.load(write(tmp_path, [row(값="1,234,567")]))
    out = V.apply(ev(value="1234568"), "예시몰", "SAMPLE-1", records=recs, today=TODAY)
    assert out.status == "conflict"


def test_two_close_records_are_a_conflict(tmp_path):
    recs = V.load(write(tmp_path, [row(값="1234567"), row(값="1234568", 확인일="2026-11-01")]))
    out = V.apply(ev(value="1234567"), "예시몰", "SAMPLE-1", records=recs, today=TODAY)
    assert out.status == "conflict" and "확인 기록끼리 값이 다름" in out.source


def test_non_finite_values_never_become_verified(tmp_path):
    recs = V.load(write(tmp_path, [row(값="NaN")]))
    assert V.apply(ev(value="NaN"), "예시몰", "SAMPLE-1", records=recs, today=TODAY).status == "unverified"
    recs = V.load(write(tmp_path, [row(값="12900")]))
    assert V.apply(ev(value="inf"), "예시몰", "SAMPLE-1", records=recs, today=TODAY).status == "unverified"


def test_weight_evidence_text_is_not_rounded():
    from app.services.commerce.search import _exact

    assert _exact(123456.7) == "123456.7" and _exact(1000.0) == "1000" and _exact(2.5) == "2.5"
