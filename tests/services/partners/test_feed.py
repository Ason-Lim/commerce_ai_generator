"""업체 제공 상품 (2026-11-02): 허락 기록부의 '허용' 범위대로만 쓰고, 미리 보기는 예시 데이터로만 보여 준다."""
from __future__ import annotations

import csv

import pytest

from app.services.partners import feed

PERM_HEAD = ["업체", "상태", "허락일", "허락 근거(메일·문서 파일명)", "업체 담당자", "상품 표시", "이미지 표시",
             "가격 비교·순위 계산", "외부 AI 전송", "AI 학습", "제휴 링크·수수료", "갱신 주기", "출처 표시 문구", "유효기간", "메모"]
PROD_HEAD = ["상품ID", "상품명", "품목", "품종", "중량(g)", "수량", "판매가", "정가", "배송비", "당도(Brix)", "산지", "등급",
             "상품URL", "이미지URL", "재고상태", "가격기준일시", "비고"]
ROW = ["OB-1", "당도선별 부사 사과", "사과", "부사", "3000", "", "32900", "39900", "0", "14", "경북 청송", "특",
       "https://www.onbrix.co.kr/p/1", "https://img.example/1.jpg", "판매중", "2026-11-02 09:00", ""]


def write(path, head, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(head)
        w.writerows(rows)


@pytest.fixture
def partners(tmp_path, monkeypatch):
    monkeypatch.setenv("PARTNER_DATA_DIR", str(tmp_path))
    monkeypatch.setenv("PARTNER_PREVIEW", "0")
    monkeypatch.setenv("KAMIS_REFERENCE", "0")
    monkeypatch.delenv("NAVER_CONNECT_REGISTRY_CSV", raising=False)

    def setup(status="허락", display="허용", image="미확인", compare="허용", real=True, sample=True):
        write(tmp_path / "permissions.csv", PERM_HEAD,
              [["온브릭스", status, "", "", "", display, image, compare, "미확인", "불가", "", "", "", "", ""]])
        if real:
            write(tmp_path / "onbrix" / "products_20261102.csv", PROD_HEAD, [ROW])
        if sample:
            write(tmp_path / "onbrix" / "products_sample.csv", PROD_HEAD, [["S1", "(예시) 부사 사과 3kg"] + ROW[2:]])
    return setup


def apple(t):
    return "사과" in t


def test_nothing_is_used_before_permission(partners):
    partners(status="요청 전", display="미확인", compare="미확인")
    assert feed.offers(apple) == []


def test_granted_partner_is_compared_and_image_needs_its_own_permission(partners):
    partners()
    [it] = feed.offers(apple)
    assert it["partner_mode"] == "compare" and it["product_name"] == "당도선별 부사 사과 3kg"
    assert it["thumbnail_url"] is None and it["partner_preview"] is False
    assert "당도 14Brix" in feed.note_line(it)["text"] and "가격 기준 2026-11-02 09:00" in feed.note_line(it)["text"]


def test_display_only_partner_goes_to_a_separate_list(partners):
    partners(compare="미확인")
    assert feed.offers(apple)[0]["partner_mode"] == "list"


def test_preview_shows_only_sample_data_for_partners_not_yet_granted(partners, monkeypatch):
    partners(status="요청 전", display="미확인", compare="미확인", real=False)
    assert feed.offers(apple) == []
    monkeypatch.setenv("PARTNER_PREVIEW", "1")
    [it] = feed.offers(apple)
    assert it["partner_preview"] is True and it["platform_name"] == "온브릭스 (예시)"
    assert feed.note_line(it)["text"].startswith("미리 보기 예시 데이터")



def test_a_memo_with_an_unquoted_comma_does_not_break_reading(tmp_path, monkeypatch):
    """2026-11-04: 메모 칸의 쉼표가 따옴표 없이 들어가 칸이 넘치자 MCP 상품 검색이 멈췄다 — 넘친 내용은 메모에 이어 붙인다."""
    from app.services.partners import feed

    (tmp_path / "permissions.csv").write_text(
        "업체,상태,메모\n딜리셔스마켓,요청 전,KAMIS 비교 대상 아님, 중량 100g당 비교\n", encoding="utf-8-sig")
    monkeypatch.setenv("PARTNER_DATA_DIR", str(tmp_path))
    perm = feed.permissions()
    assert perm["딜리셔스마켓"]["메모"] == "KAMIS 비교 대상 아님, 중량 100g당 비교"
    assert feed.offers(lambda t: True) == []
