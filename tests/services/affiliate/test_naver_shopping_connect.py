"""쇼핑커넥트 등록부 도구 (2026-11-02): 등록부 점검·발급 요청 대기열·급상승 식품 → 대기열.

화면에 링크를 붙이는 것은 chat.service.connect_links() 하나뿐 — 이 모듈은 운영 도구다.
"""
from __future__ import annotations

import sqlite3

from app.services.affiliate import naver_shopping_connect as sc

HEAD = "상품명,스토어명,판매가,정가,수수료율(%),링크 발급일,쇼핑커넥트 링크,키워드,링크 확인일,사용처(블로그/사이트),메모\n"


def _registry(tmp_path, rows):
    path = tmp_path / "naver_connect_links.csv"
    path.write_text(HEAD + "".join(r + "\n" for r in rows), encoding="utf-8-sig")
    return path


def _db(tmp_path):
    conn = sc.connect(tmp_path / "sc.sqlite3")
    sc.init_db(conn)
    return conn


def test_import_reads_the_korean_registry_and_explains_rejections(tmp_path):
    reg = _registry(tmp_path, [
        "카페블룸 두바이 쫀득 쿠키 두쫀쿠 50g,카페 블룸,3900,,5,2026.10.21,https://naver.me/GDQuBPc8,두쫀쿠 두바이쫀득쿠키,2026.11.2,사이트,",
        "잇루트 카다이프 300g,잇루트,20900,35900,14,2026.11.2,,두쫀쿠 카다이프,,사이트,링크 직접 입력 필요",
        "청송 사과 3kg,청송,19900,,5,2026.11.2,https://smartstore.naver.com/x/products/1,사과,,사이트,",
        "사과 정기배송 4주,과일,49000,,5,2026.11.2,https://naver.me/sub,사과,,사이트,",
        "국산 막걸리 6병,양조장,20000,,15,2026.11.2,https://naver.me/mak,막걸리,,사이트,",
    ])
    conn = _db(tmp_path)
    res = sc.import_issued_links(conn, reg)
    assert (res.inserted, res.updated) == (1, 0)
    assert [why for _, _, why in res.rejected] == [
        "허용되지 않은 링크 도메인: (없음)", "상품 URL은 실적 불인정 — 브랜드커넥트 발급 링크 필요",
        "실적 제외 유형(정기배송)", "주류 상품은 링크풀에서 제외"]
    row = conn.execute("select issued_at, price, commission_rate from sc_links").fetchone()
    assert tuple(row) == ("2026-10-21", 3900, 5.0)
    assert sc.import_issued_links(conn, reg).updated == 1          # 다시 읽어도 중복되지 않는다


def test_cooking_words_are_not_alcohol():
    assert sc.is_alcohol_related("국산 막걸리") and sc.is_alcohol_related("와인 안주")
    assert not sc.is_alcohol_related("맛술 500ml") and not sc.is_alcohol_related("쑥 술빵")


def test_queue_counts_repeats_and_reopens_after_issue(tmp_path):
    conn = _db(tmp_path)
    sc.queue_request(conn, "과메기")
    sc.queue_request(conn, "과메기")
    assert [tuple(r) for r in conn.execute("select keyword, hit_count, status from sc_link_requests")] == [("과메기", 2, "open")]
    reg = _registry(tmp_path, ["구룡포 과메기,바다,20000,,5,2026.11.2,https://naver.me/g,과메기,,사이트,"])
    sc.import_issued_links(conn, reg)                               # 발급되면 열린 요청이 닫힌다
    sc.queue_request(conn, "과메기")                                 # 다시 요청이 생겨도 충돌하지 않는다
    assert sorted(r[0] for r in conn.execute("select status from sc_link_requests")) == ["issued", "open"]


def test_trending_foods_without_links_go_to_the_queue(tmp_path, monkeypatch):
    reg = _registry(tmp_path, ["카페블룸 두바이 쫀득 쿠키 두쫀쿠 50g,카페 블룸,3900,,5,2026.10.21,https://naver.me/d,두쫀쿠,,사이트,"])
    monkeypatch.setenv("NAVER_CONNECT_REGISTRY_CSV", str(reg))
    report = {"items": [
        {"keyword": "두쫀쿠", "status": "surging"},          # 이미 등록 → 올리지 않음
        {"keyword": "휘태커스초콜릿", "status": "surging"},   # 미등록 → 올림
        {"keyword": "버터떡", "status": "new"},
        {"keyword": "할로윈사탕", "status": "spike_faded"},   # 반짝하고 꺼진 것 → 올리지 않음
        {"keyword": "하이볼", "status": "surging"},           # 주류 → 올리지 않음
    ]}
    conn = _db(tmp_path)
    assert sc.queue_trends(conn, report) == ["휘태커스초콜릿", "버터떡"]
    assert sc.queue_trends(conn, report) == ["휘태커스초콜릿", "버터떡"]
    rows = [tuple(r) for r in conn.execute("select keyword, reason, hit_count from sc_link_requests order by id")]
    assert rows == [("휘태커스초콜릿", "trend_dish", 2), ("버터떡", "trend_dish", 2)]


def test_trend_hook_is_off_unless_enabled(tmp_path, monkeypatch):
    monkeypatch.setattr(sc, "DB_PATH", tmp_path / "hook.sqlite3")
    monkeypatch.delenv("SC_REQUEST_QUEUE", raising=False)
    report = {"items": [{"keyword": "버터떡", "status": "new"}]}
    assert sc.queue_trends_from_report(report) == [] and not (tmp_path / "hook.sqlite3").exists()
    assert sc.queue_trends_from_report(report, enabled=True) == ["버터떡"]
    assert sqlite3.connect(tmp_path / "hook.sqlite3").execute("select count(*) from sc_link_requests").fetchone() == (1,)
