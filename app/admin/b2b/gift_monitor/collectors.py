"""공고 수집기 — 기존 core_crawler.py 를 대체한다.

기존 크롤러는 사이트 접속만 시도하고, 하드코딩된 SIMULATED_NEW_GIFTS 목록을 무작위로 '새 공고'로 넣었다.
여기서는 실제 응답에서 나온 공고만 저장한다. 결과가 없으면 0건이라고 그대로 보고한다.

1) 나라장터 OpenAPI (조달청 나라장터 입찰공고정보서비스 v1.2, 공공데이터포털 일반 인증키 → .env G2B_SERVICE_KEY)
   https://apis.data.go.kr/1230000/ad/BidPublicInfoService/getBidPblancListInfo{Thng|Servc|Etc}PPSSrch
   공고게시일 기준 · 30일 단위 · totalCount 까지 페이지 · 공고 규격서 링크 저장 · 오류 코드별 안내
2) 공고 직접 등록 (URL·제목·본문 붙여넣기)  — 은행·보험사 등 API 가 없는 민간 공고용
3) CSV/JSON 업로드                             — b2b.bids.import_file
4) 기존 smallbiz-monitor DB 가져오기           — legacy_unverified 로 표시
"""
from __future__ import annotations

import io
import re
import sqlite3
import zipfile
from datetime import date, datetime, timedelta

import requests

from app.admin.b2b import bids as store
from app.admin.b2b.gift_monitor import classify
from app.admin.shared.config import get_settings

G2B_BASE = "https://apis.data.go.kr/1230000/ad/BidPublicInfoService"
# 조달청 OpenAPI 참고자료 '나라장터 입찰공고정보서비스' v1.2 (2026-04) — 나라장터 검색조건 오퍼레이션
G2B_OPS = {"물품": "getBidPblancListInfoThngPPSSrch", "용역": "getBidPblancListInfoServcPPSSrch",
           "기타": "getBidPblancListInfoEtcPPSSrch"}
G2B_KINDS = ("물품", "용역")            # 선물 · 기념품 · 통합구매 대행은 대부분 물품/용역 공고
G2B_ROWS = 100                         # 한 페이지 건수
G2B_MAX_PAGES = 10                     # 검색어 하나당 최대 페이지 (1,000건)
G2B_WINDOW_DAYS = 30                   # 조회기간을 30일 단위로 나눠 요청 (긴 기간 오류 방지)
# 기존 targets.py GIFT_KEYWORDS 를 공고명 검색에 맞게 정리
GIFT_KEYWORDS = ["임직원 선물", "명절 선물", "선물세트", "기념품", "온누리상품권", "모바일상품권", "복지몰", "창립기념"]

# 공공데이터포털 공통 오류 (XML 로 오는 경우가 많다) → 조치 안내
G2B_ERRORS = {
    "SERVICE_KEY_IS_NOT_REGISTERED_ERROR": "인증키가 등록되지 않았어요. 활용신청 승인 직후라면 1~2시간 뒤 다시 시도하고, .env 의 G2B_SERVICE_KEY 값(일반 인증키)을 확인해 주세요.",
    "SERVICE_ACCESS_DENIED_ERROR": "이 서비스의 사용 권한이 없어요. 공공데이터포털에서 '나라장터 입찰공고정보서비스' 활용신청 상태를 확인해 주세요.",
    "LIMITED_NUMBER_OF_SERVICE_REQUESTS_EXCEEDS_ERROR": "하루 호출 한도를 넘었어요. 내일 다시 시도하거나 운영계정 전환을 신청해 주세요.",
    "SERVICE_KEY_IS_EXPIRED_ERROR": "인증키 사용기간이 끝났어요. 공공데이터포털에서 연장 신청해 주세요.",
    "UNREGISTERED_IP_ERROR": "등록되지 않은 IP 예요. 활용신청 정보의 IP 제한을 확인해 주세요.",
    "NO_OPENAPI_SERVICE_ERROR": "주소 또는 오퍼레이션 이름이 맞지 않아요.",
}


class G2BError(RuntimeError):
    """나라장터 응답 자체가 오류일 때 (인증 · 한도 · 형식).  메시지는 화면 로그에 그대로 쓴다.
    fatal=True 면 (인증 · 권한 · 한도) 나머지 검색어도 같은 결과라 수집을 멈춘다.
    메시지에 요청 주소를 넣지 않는다 — 주소에 인증키가 들어 있다."""

    def __init__(self, msg: str, fatal: bool = False):
        super().__init__(msg)
        self.fatal = fatal


FATAL_CODES = ("SERVICE_KEY", "ACCESS_DENIED", "EXCEEDS", "EXPIRED", "UNREGISTERED_IP")


def _key_problem(key: str | None) -> str | None:
    """.env 값이 키처럼 보이지 않으면 호출하지 않는다 (예시 문구 · 공백 · 한글)."""
    if not key:
        return None
    k = key.strip()
    if k != key or not k.isascii() or len(k) < 20 or any(c in k for c in " '\"<>"):
        return ("G2B_SERVICE_KEY 값이 인증키 형식이 아니에요 (예시 문구·따옴표·공백이 들어간 것 같아요). "
                "공공데이터포털 마이페이지의 '일반 인증키'를 그대로 넣어 주세요.")
    return None


def _g2b_error_from_text(text: str) -> str | None:
    import re as _re

    m = _re.search(r"<returnAuthMsg>\s*([A-Z_]+)\s*</returnAuthMsg>", text or "")
    code = m.group(1) if m else next((k for k in G2B_ERRORS if k in (text or "")), None)
    if code:
        return f"{code}: {G2B_ERRORS.get(code, '공공데이터포털 오류')}"
    m = _re.search(r"<resultCode>\s*(\d+)\s*</resultCode>\s*<resultMsg>([^<]*)</resultMsg>", text or "")
    if m and m.group(1) != "00":
        return f"결과코드 {m.group(1)}: {m.group(2).strip()}"
    return None


def g2b_documents(it: dict) -> list[dict]:
    """공고 규격서 · 공고서 파일 링크 (ntceSpecFileNm1..10 / ntceSpecDocUrl1..10)."""
    out = []
    for i in range(1, 11):
        name, url = (it.get(f"ntceSpecFileNm{i}") or "").strip(), (it.get(f"ntceSpecDocUrl{i}") or "").strip()
        if name and url.startswith(("https://", "http://")):
            out.append({"name": name, "url": url.replace("&amp;", "&")})
    return out


class G2BCollector:
    def __init__(self, service_key: str | None = None, base: str | None = None, session=None):
        import os
        self.key = service_key if service_key is not None else (os.getenv("G2B_SERVICE_KEY") or os.getenv("DATA_GO_KR_SERVICE_KEY"))
        self.base = (base or os.getenv("G2B_API_BASE") or G2B_BASE).rstrip("/")
        self.http = session or requests

    @property
    def enabled(self) -> bool:
        return bool(self.key)

    def fetch_page(self, keyword: str, kind: str, start: datetime, end: datetime, page: int = 1,
                   rows: int = G2B_ROWS) -> tuple[list[dict], int]:
        """한 페이지 → (공고 목록, 전체 건수).  inqryDiv=1 은 공고게시일시 기준 조회."""
        params = {
            "ServiceKey": self.key, "type": "json", "numOfRows": rows, "pageNo": page, "inqryDiv": 1,
            "inqryBgnDt": start.strftime("%Y%m%d%H%M"), "inqryEndDt": end.strftime("%Y%m%d%H%M"),
            "bidNtceNm": keyword,
        }
        try:
            r = self.http.get(f"{self.base}/{G2B_OPS[kind]}", params=params, timeout=20)
        except requests.RequestException as e:      # 주소(키 포함)를 메시지에 남기지 않는다
            raise G2BError(f"접속 실패 ({type(e).__name__})") from None
        text = getattr(r, "text", "") or ""
        err = _g2b_error_from_text(text) if text.lstrip().startswith("<") else None
        if err:
            raise G2BError(err, fatal=any(c in err for c in FATAL_CODES))
        status = int(getattr(r, "status_code", 200) or 200)
        if status in (401, 403):
            raise G2BError(f"HTTP {status}: 인증키가 맞지 않거나 이 서비스 사용 권한이 없어요. "
                           "공공데이터포털 '나라장터 입찰공고정보서비스' 활용신청 상태와 .env 의 G2B_SERVICE_KEY 를 확인해 주세요. "
                           "(승인 직후라면 1~2시간 뒤 다시 시도)", fatal=True)
        if status == 429:
            raise G2BError("HTTP 429: 호출이 너무 많아요. 잠시 뒤 다시 시도해 주세요.", fatal=True)
        if status >= 400:
            raise G2BError(f"HTTP {status}: 나라장터 서버 오류예요. 잠시 뒤 다시 시도해 주세요.")
        try:
            data = r.json()
        except ValueError:
            raise G2BError(_g2b_error_from_text(text) or f"JSON 이 아닌 응답: {text[:120]}") from None
        resp = data.get("response") or {}
        header = resp.get("header") or {}
        code = str(header.get("resultCode") or "00")
        if code not in ("00", "0"):
            raise G2BError(f"결과코드 {code}: {header.get('resultMsg') or ''}".strip())
        body = resp.get("body") or {}
        items = body.get("items") or []
        if isinstance(items, dict):           # XML→JSON 변환형 응답 {"item": [...]}
            items = items.get("item") or []
        if isinstance(items, dict):
            items = [items]
        try:
            total = int(body.get("totalCount") or len(items))
        except (TypeError, ValueError):
            total = len(items)
        return items, total

    def fetch(self, keyword: str, kind: str, start: datetime, end: datetime, rows: int = G2B_ROWS) -> list[dict]:
        """조회기간을 30일 단위로 나누고, 각 기간을 totalCount 까지 페이지를 넘겨 모은다."""
        out: list[dict] = []
        w_start = start
        while w_start < end:
            w_end = min(end, w_start + timedelta(days=G2B_WINDOW_DAYS))
            page, got = 1, 0
            while page <= G2B_MAX_PAGES:
                items, total = self.fetch_page(keyword, kind, w_start, w_end, page, rows)
                out += items
                got += len(items)
                if not items or got >= total:
                    break
                page += 1
            w_start = w_end
        return out

    @staticmethod
    def to_row(it: dict, kind: str) -> dict:
        no, ordv = it.get("bidNtceNo"), it.get("bidNtceOrd") or "000"
        budget = it.get("asignBdgtAmt") or it.get("bdgtAmt") or it.get("presmptPrce")
        return {
            "bid_id": f"G2B-{no}-{ordv}", "title": it.get("bidNtceNm"),
            "agency": it.get("dminsttNm") or it.get("ntceInsttNm"),
            "deadline": it.get("bidClseDt"), "posted": it.get("bidNtceDt"),
            "budget": int(float(budget)) if budget not in (None, "") else None,
            "url": (it.get("bidNtceDtlUrl") or it.get("bidNtceUrl") or "").strip() or None,
            "manager": it.get("ntceInsttOfclNm"), "contact": it.get("ntceInsttOfclTelNo"),
            "summary": " · ".join(x for x in (
                f"[{kind}]", it.get("ntceInsttNm"), it.get("ntceKindNm"), it.get("cntrctCnclsMthdNm"),
                it.get("bidMethdNm"), it.get("sucsfbidMthdNm"),
                f"개찰 {it['opengDt']}" if it.get("opengDt") else None,
                f"분류 {it['pubPrcrmntClsfcNm']}" if it.get("pubPrcrmntClsfcNm") else None,
                f"구매대상 {it['purchsObjPrdctList']}" if it.get("purchsObjPrdctList") else None) if x),
            "documents": g2b_documents(it),
        }

    def run(self, keywords: list[str] | None = None, days: int = 14, kinds=G2B_KINDS,
            today: datetime | None = None) -> dict:
        log: list[str] = []
        problem = _key_problem(self.key)
        if problem:
            return {"source": "나라장터 OpenAPI", "new": 0, "updated": 0, "found": 0, "log": [problem]}
        if not self.enabled:
            return {"source": "나라장터 OpenAPI", "new": 0, "updated": 0, "found": 0,
                    "log": ["G2B_SERVICE_KEY 가 설정되지 않아 나라장터 수집을 건너뜁니다. (공공데이터포털에서 '조달청_나라장터 입찰공고정보서비스' 활용신청 후 키를 .env 에 넣으세요)"]}
        end = today or datetime.now()
        start = end - timedelta(days=days)
        new = upd = found = 0
        seen: set[str] = set()
        for kind in kinds:
            for kw in keywords or GIFT_KEYWORDS:
                try:
                    items = self.fetch(kw, kind, start, end)
                except G2BError as e:
                    log.append(f"[실패] {kind} '{kw}': {e}")
                    if e.fatal:
                        log.append("[중단] 인증 · 권한 · 한도 오류라 나머지 검색어는 건너뜁니다.")
                        return {"source": "나라장터 OpenAPI", "new": new, "updated": upd, "found": found, "log": log}
                    continue
                except Exception as e:  # noqa: BLE001 — 메시지에 키가 들어 있을 수 있어 종류만 남긴다
                    log.append(f"[실패] {kind} '{kw}': {type(e).__name__}")
                    continue
                log.append(f"[조회] {kind} '{kw}': {len(items)}건")
                for it in items:
                    row = self.to_row(it, kind)
                    if not row["title"] or row["bid_id"] in seen:
                        continue
                    seen.add(row["bid_id"])
                    found += 1
                    old = store.get(row["bid_id"])
                    n = store.normalize(row, "나라장터 OpenAPI", "verified")
                    n.documents = row["documents"]
                    if old:
                        _keep_user_additions(n, old)
                    store.save(n)
                    upd += bool(old)
                    new += not old
        log.append(f"[완료] 고유 공고 {found}건 · 신규 {new}건 · 갱신 {upd}건 (기간 {start:%Y-%m-%d}~{end:%Y-%m-%d})")
        return {"source": "나라장터 OpenAPI", "new": new, "updated": upd, "found": found, "log": log}


def _keep_user_additions(n: store.BidNotice, old: store.BidNotice) -> None:
    """다시 수집해도 사람이 붙인 첨부 원문 · 태그는 유지한다 (API 값만 새로 고침)."""
    if old.attachments:
        n.attachments = old.attachments
        i = old.summary.find("【첨부:")
        if i >= 0:
            n.summary = (n.summary + "\n\n" if n.summary else "") + old.summary[i:]
        store.reparse(n)
    if old.tags:
        n.tags = old.tags


def collect_all(days: int = 14, keywords: list[str] | None = None, kinds=G2B_KINDS) -> dict:
    results = [G2BCollector().run(keywords, days, kinds=kinds)]
    remote = get_settings().b2b_bid_source_url
    if remote:
        try:
            n = store.fetch_remote(remote)
            results.append({"source": remote, "new": n, "updated": 0, "found": n, "log": [f"[완료] {n}건 (원문 대조 전으로 저장)"]})
        except Exception as e:
            results.append({"source": remote, "new": 0, "updated": 0, "found": 0, "log": [f"[실패] {e}"]})
    return {"results": results, "new": sum(r["new"] for r in results), "found": sum(r["found"] for r in results)}


# ── 직접 등록 ─────────────────────────────────────────────────
def add_manual(title: str, agency: str | None, deadline: str | None, url: str | None, text: str = "",
               budget: str | None = None) -> store.BidNotice:
    if not title.strip():
        raise ValueError("공고명이 필요합니다.")
    row = {"title": title.strip(), "agency": agency, "deadline": deadline, "url": url, "summary": text, "budget": budget}
    n = store.normalize(row, "직접 등록", "unverified")
    store.save(n)
    return n


# ── 첨부 원문 → 텍스트 ───────────────────────────────────────
def extract_text(name: str, content: bytes) -> str:
    low = name.lower()
    if low.endswith(".hwpx"):
        with zipfile.ZipFile(io.BytesIO(content)) as z:
            parts = sorted(p for p in z.namelist() if re.match(r"Contents/section\d+\.xml", p))
            xml = " ".join(z.read(p).decode("utf-8", "ignore") for p in parts)
        xml = re.sub(r"</hp:p>", "\n", xml)
        return re.sub(r"[ \t]+", " ", re.sub(r"<[^>]+>", "", xml)).strip()
    if low.endswith(".docx"):
        from docx import Document
        return "\n".join(p.text for p in Document(io.BytesIO(content)).paragraphs)
    if low.endswith(".pdf"):
        try:
            from pypdf import PdfReader
        except ImportError as e:
            raise ValueError("PDF 텍스트 추출에는 pypdf 설치가 필요합니다 (pip install pypdf).") from e
        return "\n".join((p.extract_text() or "") for p in PdfReader(io.BytesIO(content)).pages)
    if low.endswith(".hwp"):
        raise ValueError("HWP(구형) 는 직접 읽을 수 없습니다. 한글에서 HWPX 또는 PDF 로 저장해 올려 주세요.")
    return content.decode("utf-8-sig", "ignore")


def attach(bid_id: str, name: str, content: bytes) -> store.BidNotice:
    n = store.get(bid_id)
    if not n:
        raise KeyError(bid_id)
    text = extract_text(name, content).strip()
    if not text:
        raise ValueError("문서에서 텍스트를 찾지 못했습니다.")
    n.summary = (n.summary + "\n\n" if n.summary else "") + f"【첨부: {name}】\n" + text[:60000]
    n.attachments.append({"name": name, "chars": len(text), "added": date.today().isoformat()})
    store.reparse(n)
    store.save(n)
    return n


# ── 기존 DB 가져오기 ───────────────────────────────────────────
def import_legacy_db(path: str) -> int:
    """anti_online / gift_trend_analyzer 의 data/smallbiz_programs.db 의 gift_bids 를 가져온다.

    이 테이블은 database.py 의 하드코딩 시드와 core_crawler.py 의 SIMULATED_NEW_GIFTS 로 채워진 데이터라
    legacy_unverified 로 저장한다. 소상공인 지원사업(programs) 테이블은 가져오지 않는다.
    """
    con = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    con.row_factory = sqlite3.Row
    rows = [dict(r) for r in con.execute("SELECT * FROM gift_bids")]
    con.close()
    n = 0
    for r in rows:
        r["bid_id"] = f"legacy-{r.get('id')}"
        b = store.normalize(r, "smallbiz-monitor 기존 DB (시드/시뮬레이션)", "legacy_unverified")
        b.tags = sorted(set(b.tags + ["미검증 기존 데이터"]))
        if b.url and b.url.rstrip("/").count("/") <= 2:
            b.tags.append("링크가 사이트 첫 화면")
        store.save(b)
        n += 1
    return n


def legacy_status_counts(today: date | None = None) -> dict:
    out: dict = {}
    for b in store.list_bids():
        if b.verification == "legacy_unverified":
            s = classify.status(b.deadline, today)
            out[s] = out.get(s, 0) + 1
    return out
