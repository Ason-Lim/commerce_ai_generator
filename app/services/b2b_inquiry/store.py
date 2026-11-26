"""B2B 문의 창구 1차 (2026-11-24) — 설계 claude/b2b_inquiry_desk_2026-11-24.md.

기업·기관 담당자가 임직원 선물을 문의하면 → 운영자가 보고 → 콘솔 공고로 등록해 분석·견적 요청서·제안서 초안 →
**사람이 확인하고 직접 보낸다.** 이 서비스에는 밖으로 메일·메시지를 보내는 기능이 없다.

* 받는 것: 회사·기관 이름, 담당자 이름, 연락처(회사 메일 또는 전화 중 하나 이상) — 회신용, 동의 필수, **암호화** 저장.
  그 밖에는 선물 조건(시기·인원·1인 예산·희망일·배송 방식·공고 주소·내용)만. 직원 명단·주민번호 등은 받지 않는다고 화면에 적는다.
* 연락처 보존: 종결(수주 못 함·취소) 뒤 180일이 지나면 연락처를 지운다(설계안 — 법률 검토). 수주한 문의는 계약 관리로 넘어가 여기서 지우지 않는다.
* 내용 문장은 저장 전에 개인정보 모양(휴대폰·메일·주민번호 등)을 가린다 — 연락처 칸 밖에 적힌 연락처도 남지 않게.
* 상태: new(새 문의) → reviewing(검토 중) → quoted(견적·제안 보냄 — **사람 확인 표시 필수**) → won(수주) · lost(수주 못 함) · closed(취소·종결).
* 공고로 등록: 연락처는 빼고 조건만 콘솔 공고(bid-inq…)로 넣는다 → 콘솔에서 '분석 → 견적 요청서 → 제안서'.
* 남용 막기: 숨은 칸(봇), 접속 주소마다 1시간 5건, 전체 1시간 60건.
"""

from __future__ import annotations

import hashlib
import re
import secrets
import threading
import time
from datetime import datetime, timedelta

from sqlalchemy import JSON, Column, DateTime, MetaData, String, Table, Text, select, update

from app.services.corpmall import store as corp
from app.services.privacy import pii

KST = corp.KST
STATUSES = ("new", "reviewing", "quoted", "won", "lost", "closed")
STATUS_LABEL = {
    "new": "새 문의",
    "reviewing": "검토 중",
    "quoted": "견적·제안 보냄",
    "won": "수주",
    "lost": "수주 못 함",
    "closed": "종결",
}
DONE = ("won", "lost", "closed")
OCCASIONS = ("설", "추석", "창립기념", "연말", "가정의 달", "기타")
DELIVERY = ("individual", "bulk", "coupon", "undecided")
KINDS = ("company", "public_bid")  # 기업 자체 구매 · 공공기관 입찰 공고 있음
CONTACT_KEEP_DAYS = 180
PER_CLIENT_HOUR = 5
ALL_HOUR = 60
EMAIL_RE = re.compile(r"^[A-Za-z0-9._%+-]{1,64}@[A-Za-z0-9.-]{1,120}\.[A-Za-z]{2,}$")
PHONE_RE = re.compile(r"^0\d{1,2}\d{7,8}$")

meta = MetaData()
t_inq = Table(
    "b2b_inquiry",
    meta,
    Column("inquiry_id", String(20), primary_key=True),
    Column("status", String(12), nullable=False, default="new"),
    Column("payload", JSON, nullable=False),  # 조건 (개인정보 없음)
    Column("contact_enc", Text),  # 담당자 이름·메일·전화 (암호화) — 지우면 None
    Column("bid_id", String(40)),
    Column("created_at", DateTime(timezone=True)),
    Column("updated_at", DateTime(timezone=True)),
    Column("done_at", DateTime(timezone=True)),
    Column("purged_at", DateTime(timezone=True)),
    Column("events", JSON),
)

_LOCK = threading.Lock()
_HITS: dict[str, list[float]] = {}


class InquiryError(ValueError):
    """화면에 그대로 보여 줄 수 있는 짧은 이유."""


def engine(url: str | None = None):
    eng = corp.engine(url)
    corp.ensure(eng, meta)
    return eng


def now() -> datetime:
    return datetime.now(KST)


# ── 남용 막기 ──
def _limited(client: str) -> bool:
    t = time.monotonic()
    k = hashlib.sha256(client.encode()).hexdigest()
    with _LOCK:
        for key in (k, "*"):
            _HITS[key] = [x for x in _HITS.get(key, []) if t - x < 3600]
        if len(_HITS[k]) >= PER_CLIENT_HOUR or len(_HITS["*"]) >= ALL_HOUR:
            return True
        _HITS[k].append(t)
        _HITS["*"].append(t)
    return False


def reset_limits() -> None:  # 시험용
    with _LOCK:
        _HITS.clear()


def _clean(v, n: int) -> str:
    return " ".join(str(v or "").split())[:n]


def _int(v, lo: int, hi: int, what: str) -> int | None:
    if v in (None, ""):
        return None
    try:
        n = int(re.sub(r"[,\s원명]", "", str(v)))
    except ValueError as e:
        raise InquiryError(f"{what}은(는) 숫자로 적어 주세요") from e
    if not lo <= n <= hi:
        raise InquiryError(f"{what}이(가) 너무 크거나 작아요")
    return n


def check(form: dict) -> tuple[dict, dict]:
    """(조건 payload, 연락처) — 잘못된 입력은 InquiryError."""
    company = _clean(form.get("company"), 60)
    name = _clean(form.get("contact_name"), 30)
    email = _clean(form.get("email"), 120)
    phone = re.sub(r"\D", "", str(form.get("phone") or ""))[:12]
    if not company or not name:
        raise InquiryError("회사·기관 이름과 담당자 이름을 넣어 주세요")
    if not email and not phone:
        raise InquiryError("회신받을 회사 메일이나 전화번호 중 하나는 넣어 주세요")
    if email and not EMAIL_RE.fullmatch(email):
        raise InquiryError("메일 주소를 확인해 주세요")
    if phone and not PHONE_RE.fullmatch(phone):
        raise InquiryError("전화번호를 확인해 주세요")
    if not form.get("consent"):
        raise InquiryError("회신을 위한 연락처 수집·이용에 동의해 주세요")
    occasion = form.get("occasion") or "기타"
    delivery = form.get("delivery") or "undecided"
    kind = form.get("kind") or "company"
    if occasion not in OCCASIONS or delivery not in DELIVERY or kind not in KINDS:
        raise InquiryError("선택 항목을 다시 골라 주세요")
    due = _clean(form.get("due_date"), 10)
    if due:
        try:
            due = datetime.fromisoformat(due).date().isoformat()
        except ValueError as e:
            raise InquiryError("희망일을 날짜로 골라 주세요") from e
    url = _clean(form.get("notice_url"), 300)
    if url and not re.match(r"^https?://", url):
        raise InquiryError("공고 주소는 http(s):// 로 시작해야 해요")
    message, kinds = pii.mask(str(form.get("message") or "")[:1500])
    payload = {
        "company": company,
        "kind": kind,
        "occasion": occasion,
        "headcount": _int(form.get("headcount"), 1, 200_000, "인원"),
        "budget_per_person": _int(form.get("budget_per_person"), 1_000, 5_000_000, "1인 예산"),
        "due_date": due or None,
        "delivery": delivery,
        "notice_url": url or None,
        "message": message.strip(),
        "masked": kinds,
    }
    return payload, {"name": name, "email": email or None, "phone": phone or None}


def _ev(kind: str, by: str, **detail) -> dict:
    return {"at": now().isoformat(timespec="seconds"), "kind": kind, "by": by, **detail}


def submit(eng, form: dict, client: str) -> dict:
    """공개 문의 접수. 숨은 칸(website)이 차 있으면 봇으로 보고 저장하지 않되 똑같이 '받았어요'."""
    if _limited(client):
        raise InquiryError("문의가 너무 많이 들어왔어요. 한 시간 뒤에 다시 보내 주세요")
    payload, contact = check(form)
    if _clean(form.get("website"), 50):
        return {"inquiry_id": f"B{now():%y%m%d}-{secrets.token_hex(2).upper()}", "masked": [], "ignored": True}
    iid = f"B{now():%y%m%d}-{secrets.token_hex(2).upper()}"
    t = now()
    with eng.begin() as c:
        c.execute(
            t_inq.insert().values(
                inquiry_id=iid,
                status="new",
                payload=payload,
                contact_enc=corp._enc(contact),
                created_at=t,
                updated_at=t,
                events=[_ev("created", "customer")],
            )
        )
    try:
        from app.services.cs import notify, tickets

        notify.operator({"id": iid, "label": "B2B 문의", "domain": "b2b"}, tickets.store_dir())
    except Exception:  # noqa: BLE001 — 알림 실패가 접수를 막지 않게
        pass
    return {"inquiry_id": iid, "masked": payload["masked"]}


# ── 관리자 ──
def _row(r, *, with_contact: bool) -> dict:
    d = {
        "inquiry_id": r["inquiry_id"],
        "status": r["status"],
        "status_label": STATUS_LABEL[r["status"]],
        **r["payload"],
        "bid_id": r["bid_id"],
        "created_at": r["created_at"].isoformat() if r["created_at"] else None,
        "has_contact": r["contact_enc"] is not None,
        "purged": r["purged_at"] is not None,
        "events": r["events"] or [],
    }
    if with_contact:
        d["contact"] = corp._dec(r["contact_enc"]) if r["contact_enc"] else None
    return d


def list_inquiries(eng, status: str | None = None) -> list[dict]:
    """목록 — 연락처 없이 (회사 이름·조건·상태)."""
    q = select(t_inq).order_by(t_inq.c.created_at.desc())
    if status:
        q = q.where(t_inq.c.status == status)
    with eng.connect() as c:
        return [_row(r, with_contact=False) for r in c.execute(q).mappings()]


def get(eng, iid: str, *, with_contact: bool = False) -> dict | None:
    with eng.connect() as c:
        r = c.execute(select(t_inq).where(t_inq.c.inquiry_id == iid)).mappings().first()
    return _row(r, with_contact=with_contact) if r else None


def _update(eng, iid: str, ev: dict, **vals) -> dict:
    with eng.begin() as c:
        r = c.execute(select(t_inq).where(t_inq.c.inquiry_id == iid)).mappings().first()
        if r is None:
            raise InquiryError("없는 문의예요")
        c.execute(
            update(t_inq)
            .where(t_inq.c.inquiry_id == iid)
            .values(events=[*(r["events"] or []), ev], updated_at=now(), **vals)
        )
    return get(eng, iid)


def set_status(eng, iid: str, status: str, *, by: str, note: str = "", human_checked: bool = False) -> dict:
    """상태 바꾸기. '견적·제안 보냄'은 사람이 보낼 문서를 확인했다는 표시가 있어야 한다 — AI 초안이 그대로 나가지 않게."""
    if status not in STATUSES:
        raise InquiryError("없는 상태예요")
    if status == "quoted" and not human_checked:
        raise InquiryError("보낸 견적·제안서를 사람이 확인했는지 표시해 주세요")
    vals = {"status": status, "done_at": now() if status in DONE else None}
    return _update(eng, iid, _ev("status", by, to=status, note=_clean(note, 200), human_checked=human_checked), **vals)


def note(eng, iid: str, text: str, *, by: str) -> dict:
    masked, _ = pii.mask(_clean(text, 500))
    return _update(eng, iid, _ev("note", by, text=masked))


def to_bid(eng, iid: str, *, by: str) -> str:
    """조건만(연락처 없이) 콘솔 공고로 등록 → 공고번호. 이미 등록했으면 같은 번호를 다시 만든다(내용 갱신)."""
    from app.admin.b2b import bids as bidstore

    d = get(eng, iid)
    if d is None:
        raise InquiryError("없는 문의예요")
    bid_id = "bid-inq" + iid[1:].replace("-", "").lower()
    lines = [
        f"문의 {iid} ({'공공기관 입찰 공고' if d['kind'] == 'public_bid' else '기업 자체 구매'})",
        f"시기: {d['occasion']}",
    ]
    if d.get("headcount"):
        lines.append(f"인원: {d['headcount']}명")
    if d.get("budget_per_person"):
        lines.append(f"1인 예산: {d['budget_per_person']:,}원")
    if d.get("due_date"):
        lines.append(f"희망 배송·지급일: {d['due_date']}")
    lines.append(
        "배송 방식: "
        + {"individual": "직원 개별 배송", "bulk": "회사 일괄 배송", "coupon": "모바일 쿠폰", "undecided": "미정"}[
            d["delivery"]
        ]
    )
    if d.get("message"):
        lines.append("요청 내용: " + d["message"])
    row = {
        "bid_id": bid_id,
        "title": f"{d['company']} {d['occasion']} 임직원 선물 (문의)",
        "agency": d["company"],
        "deadline": d.get("due_date"),
        "url": d.get("notice_url"),
        "summary": "\n".join(lines),
    }
    if d.get("headcount") and d.get("budget_per_person"):
        row["budget"] = d["headcount"] * d["budget_per_person"]
    n = bidstore.normalize(row, source="inquiry", verification="document_provided")
    bidstore.save(n)
    _update(
        eng,
        iid,
        _ev("to_bid", by, bid_id=bid_id),
        bid_id=bid_id,
        **({"status": "reviewing"} if d["status"] == "new" else {}),
    )
    return bid_id


def purge(eng, at: datetime | None = None) -> int:
    """종결(수주 못 함·취소) 뒤 180일 지난 문의의 연락처를 지운다. 수주는 계약 관리로 넘어가 여기서 지우지 않는다."""
    at = at or now()
    n = 0
    with eng.begin() as c:
        rows = c.execute(
            select(t_inq.c.inquiry_id, t_inq.c.done_at, t_inq.c.status, t_inq.c.events).where(
                t_inq.c.contact_enc.is_not(None), t_inq.c.status.in_(("lost", "closed"))
            )
        ).mappings()
        for r in list(rows):
            d = r["done_at"] if r["done_at"].tzinfo else r["done_at"].replace(tzinfo=KST)
            if d + timedelta(days=CONTACT_KEEP_DAYS) <= at:
                c.execute(
                    update(t_inq)
                    .where(t_inq.c.inquiry_id == r["inquiry_id"])
                    .values(contact_enc=None, purged_at=at, events=[*(r["events"] or []), _ev("purged", "retention")])
                )
                n += 1
    return n


def counts(eng) -> dict:
    with eng.connect() as c:
        rows = c.execute(select(t_inq.c.status)).scalars().all()
    return {s: rows.count(s) for s in STATUSES}
