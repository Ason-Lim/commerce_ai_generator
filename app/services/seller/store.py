"""셀러 센터 뼈대 ① (창 5, 2026-11-25) — 설계 claude/stage5_seller_design_2026-11-25.md (결정 1~4).

* **입장 = 초대 코드(링크).** 운영자가 셀러를 만들고 초대 코드를 발급한다. 코드는 144비트 무작위 값이며
  링크 ``/seller#k=…`` 의 # 뒤에 들어가 서버·접속 기록에 남지 않는다. 서버에는 해시만 둔다.
  셀러는 링크를 열거나 화면에 코드를 붙여 넣어 들어온다(폐쇄몰 담당자 링크와 같은 방식).
  - 셀러마다 살아 있는 코드는 **하나**. 새로 발급하면 옛 코드는 바로 막힌다(분실·담당자 교체).
  - 잘못된 코드는 폐쇄몰과 같은 입력 제한(접속 주소마다 10분 10번, 전체 10분 300번).
  - 로그인(구글·카카오)은 사업자등록 뒤 이 위에 붙인다(결정 1).
* **셀러 간 격리.** 셀러 쪽 함수는 모두 코드 → 셀러 번호를 먼저 풀고, 그 번호로만 읽고 쓴다.
  셀러 쪽 API 는 셀러 번호를 입력으로 받지 않는다(다른 셀러 번호를 넣어 볼 수 없게).
* **사람이 정하는 것.** 입점 승인·정지·재개·계약 종료는 운영자만 한다. ``by`` 가 운영자(``operator`` / ``operator:…``)가
  아니면 거부한다 — AI·자동 작업(``ai:…``·``system:…``)은 상태를 바꾸지 못한다(로드맵 창 5 통과 조건).
* **개인정보.** 받는 것은 셀러 담당자 연락처(이름·메일·전화 — 하나 이상)뿐, Fernet 암호화
  (폐쇄몰과 같은 키 ``CORPMALL_KEY`` / ``corpmall.key``). 정산 계좌·대표자 주민번호 등은 받지 않는다.
  계약 종료 뒤 **1년**이 지나면 매일 보존 작업에서 연락처를 지운다(결정 3 — 설계안, 법률 검토 전).
* **노출 없음.** 이 단계의 셀러·상품은 관리자 화면에만 있다(결정 2). 추천 순위·고객 화면과 연결하지 않는다.
"""

from __future__ import annotations

import hashlib
import re
import secrets
from datetime import datetime, timedelta

from sqlalchemy import JSON, Column, DateTime, Integer, MetaData, String, Table, Text, and_, select, update

from app.services.corpmall import store as corp

KST = corp.KST
STATUSES = {
    "invited": "초대됨(입점 심사 전)",
    "active": "입점 승인",
    "suspended": "정지",
    "ended": "계약 종료",
}
ENTER_OK = ("invited", "active")  # 정지·종료 셀러는 들어오지 못함
KINDS = {"direct": "직접 재고", "consign": "정식 위탁판매"}
CONTACT_KEEP_DAYS = 365  # 계약 종료 뒤 (결정 3, 2026-11-25)
LIMIT_KEY = "seller"
TOKEN_RE = re.compile(r"^[A-Za-z0-9_-]{24}$")
EMAIL_RE = re.compile(r"^[^@\s]{1,64}@[^@\s]{1,120}\.[A-Za-z]{2,}$")
OPERATOR_RE = re.compile(r"^operator(:[\w.@-]{1,40})?$")

meta = MetaData()
t_seller = Table(
    "seller_account",
    meta,
    Column("seller_id", String(12), primary_key=True),
    Column("name", String(60), nullable=False),  # 상호
    Column("kind", String(8), nullable=False),  # direct | consign
    Column("status", String(10), nullable=False, default="invited"),
    Column("contact_enc", Text),  # 담당자 연락처 (암호화) — 지우면 None
    Column("memo", String(200)),  # 운영자 메모 (개인정보 넣지 않음)
    Column("created_at", DateTime(timezone=True)),
    Column("ended_at", DateTime(timezone=True)),  # 계약 종료일 — 연락처 보존 기간의 시작
    Column("contact_purged_at", DateTime(timezone=True)),
)
t_key = Table(
    "seller_key",
    meta,
    Column("key_id", String(12), primary_key=True),
    Column("seller_id", String(12), index=True, nullable=False),
    Column("token_hash", String(64), unique=True, nullable=False),
    Column("created_at", DateTime(timezone=True)),
    Column("first_used_at", DateTime(timezone=True)),
    Column("revoked_at", DateTime(timezone=True)),
)
t_event = Table(
    "seller_event",
    meta,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("seller_id", String(12), index=True, nullable=False),
    Column("kind", String(20), nullable=False),
    Column("by", String(48)),
    Column("detail", JSON),
    Column("at", DateTime(timezone=True)),
)


class SellerError(ValueError):
    """셀러·운영자에게 그대로 보여 줄 수 있는 오류."""


def now() -> datetime:
    return corp.now()


def engine(url: str | None = None):
    eng = corp.engine(url)  # 같은 B2B DB
    corp.ensure(eng, meta)
    return eng


def _hash(token: str) -> str:
    return hashlib.sha256(f"seller|{token}".encode()).hexdigest()


def _operator(by: str | None) -> str:
    by = (by or "").strip()
    if not OPERATOR_RE.match(by):
        raise SellerError("입점 승인·정지·종료와 초대 코드 발급은 운영자만 할 수 있어요")
    return by


def _event(c, seller_id: str, kind: str, by: str, detail: dict | None = None) -> None:
    c.execute(t_event.insert().values(seller_id=seller_id, kind=kind, by=by, detail=detail or {}, at=now()))


def phone_digits(v) -> str:
    """전화번호 → 숫자만 (DB 에는 '-' 없이). 휴대폰·유선·대표번호(15xx)만 받는다 — 틀리면 SellerError (2026-11-25)."""
    d = re.sub(r"[\s\-().]", "", str(v or ""))
    if not d:
        return ""
    if not d.isdigit():
        raise SellerError("전화번호는 숫자로 넣어 주세요")
    if d.startswith(("15", "16", "18")) and len(d) == 8:
        return d
    if not d.startswith("0") or not 9 <= len(d) <= 12:
        raise SellerError("전화번호 자리 수를 확인해 주세요 (예: 010-1234-5678, 02-123-4567)")
    return d


def fmt_phone(v) -> str:
    """숫자만 → 보기용 '-' (010-1234-5678 · 02-123-4567 · 031-123-4567 · 1588-1234 · 0505-123-4567)."""
    d = re.sub(r"\D", "", str(v or ""))
    if not d:
        return ""
    if d.startswith(("15", "16", "18")) and len(d) == 8:
        return f"{d[:4]}-{d[4:]}"
    if d.startswith("02"):
        return f"02-{d[2:-4]}-{d[-4:]}" if len(d) >= 9 else d
    if d.startswith("050") and len(d) == 12:
        return f"{d[:4]}-{d[4:8]}-{d[8:]}"
    if len(d) in (10, 11):
        return f"{d[:3]}-{d[3:-4]}-{d[-4:]}"
    return d


def _check_contact(raw: dict | None) -> dict:
    raw = raw or {}
    extra = set(raw) - {"name", "email", "phone"}
    if extra:
        raise SellerError("받지 않는 칸이 있어요: " + ", ".join(sorted(extra)))
    name = " ".join(str(raw.get("name") or "").split())[:30]
    email = str(raw.get("email") or "").strip()[:120]
    phone = phone_digits(str(raw.get("phone") or "").strip()[:20])
    if not name:
        raise SellerError("담당자 이름을 넣어 주세요")
    if not (email or phone):
        raise SellerError("담당자 메일이나 전화 중 하나는 넣어 주세요")
    if email and not EMAIL_RE.match(email):
        raise SellerError("메일 주소 모양이 아니에요")
    return {"name": name, "email": email, "phone": phone}


def _mask(ct: dict | None) -> dict | None:
    if not ct:
        return None
    e = ct.get("email") or ""
    if "@" in e:
        u, d = e.split("@", 1)
        e = (u[:2] + "***@" + d) if u else ""
    p = re.sub(r"\D", "", ct.get("phone") or "")
    return {"name": (ct.get("name") or "")[:1] + "**", "email": e, "phone": ("***-" + p[-4:]) if p else ""}


def _row(eng, seller_id: str):
    with eng.connect() as c:
        return c.execute(select(t_seller).where(t_seller.c.seller_id == seller_id)).mappings().first()


def _public(r, *, contact: str = "masked") -> dict:
    ct = corp._dec(r["contact_enc"])
    return {
        "seller_id": r["seller_id"],
        "name": r["name"],
        "kind": r["kind"],
        "kind_label": KINDS.get(r["kind"], r["kind"]),
        "status": r["status"],
        "status_label": STATUSES.get(r["status"], r["status"]),
        "contact": ((dict(ct, phone=fmt_phone(ct.get("phone"))) if ct else ct) if contact == "full" else _mask(ct))
        if contact != "none"
        else None,
        "has_contact": ct is not None,
        "ended_at": r["ended_at"].isoformat() if r["ended_at"] else None,
    }


# ── 운영자 ──────────────────────────────────────────────────────────────
def create_seller(eng, *, name: str, kind: str, contact: dict, by: str, memo: str = "") -> dict:
    by = _operator(by)
    name = " ".join((name or "").split())[:60]
    if not name:
        raise SellerError("상호를 넣어 주세요")
    if kind not in KINDS:
        raise SellerError("셀러 종류를 골라 주세요 (직접 재고 · 정식 위탁판매)")
    ct = _check_contact(contact)
    sid = "S" + secrets.token_hex(4).upper()
    with eng.begin() as c:
        c.execute(
            t_seller.insert().values(
                seller_id=sid,
                name=name,
                kind=kind,
                status="invited",
                contact_enc=corp._enc(ct),
                memo=" ".join((memo or "").split())[:200],
                created_at=now(),
            )
        )
        _event(c, sid, "created", by, {"kind": kind})
    return _public(_row(eng, sid))


def issue_key(eng, seller_id: str, *, by: str) -> dict:
    """초대 코드 발급 — 원문은 이 반환값에만. 옛 코드는 모두 막는다(셀러당 살아 있는 코드 하나)."""
    by = _operator(by)
    r = _row(eng, seller_id)
    if r is None:
        raise SellerError("없는 셀러예요")
    if r["status"] not in ENTER_OK:
        raise SellerError("정지·계약 종료 셀러에게는 초대 코드를 만들 수 없어요")
    token = secrets.token_urlsafe(18)  # 24자 · 144비트
    kid = "K" + secrets.token_hex(4).upper()
    with eng.begin() as c:
        old = c.execute(
            update(t_key)
            .where(and_(t_key.c.seller_id == seller_id, t_key.c.revoked_at.is_(None)))
            .values(revoked_at=now())
        ).rowcount
        c.execute(t_key.insert().values(key_id=kid, seller_id=seller_id, token_hash=_hash(token), created_at=now()))
        _event(c, seller_id, "key_issued", by, {"key_id": kid, "revoked_old": old})
    return {"key_id": kid, "code": token, "link": f"/seller#k={token}", "revoked_old": old}


TRIAL_BY = "system:join"  # 입점 신청 1차 분석(⑩)이 문제없다고 본 신청만 — 체험(초대 상태) 셀러 + 첫 코드


def create_trial(eng, *, name: str, contact: dict, join_id: str) -> dict:
    """입점 신청 자동 체험 코드 (사용자 결정 11-25 16:24 'A'). 셀러는 '초대'(체험) 상태로만 만든다 —
    입점 승인(active)·정지·종료·코드 재발급은 여전히 운영자만(_operator). 고객 화면·미니숍 공개는 active 에서만 열린다."""
    name = " ".join((name or "").split())[:60]
    if not name:
        raise SellerError("상호를 넣어 주세요")
    ct = _check_contact(contact)
    sid = "S" + secrets.token_hex(4).upper()
    token = secrets.token_urlsafe(18)
    kid = "K" + secrets.token_hex(4).upper()
    with eng.begin() as c:
        c.execute(t_seller.insert().values(seller_id=sid, name=name, kind="direct", status="invited",
                                           contact_enc=corp._enc(ct), memo=f"입점 신청 {join_id} 체험", created_at=now()))  # fmt: skip
        _event(c, sid, "created", TRIAL_BY, {"kind": "direct", "join_id": join_id, "trial": True})
        c.execute(t_key.insert().values(key_id=kid, seller_id=sid, token_hash=_hash(token), created_at=now()))
        _event(c, sid, "key_issued", TRIAL_BY, {"key_id": kid, "revoked_old": 0})
    return {"seller_id": sid, "key_id": kid, "code": token, "link": f"/seller#k={token}"}


def revoke_keys(eng, seller_id: str, *, by: str) -> int:
    by = _operator(by)
    with eng.begin() as c:
        n = c.execute(
            update(t_key)
            .where(and_(t_key.c.seller_id == seller_id, t_key.c.revoked_at.is_(None)))
            .values(revoked_at=now())
        ).rowcount
        _event(c, seller_id, "key_revoked", by, {"n": n})
    return n


ALLOWED = {
    "invited": {"active", "ended"},
    "active": {"suspended", "ended"},
    "suspended": {"active", "ended"},
    "ended": set(),
}


def set_status(eng, seller_id: str, status: str, *, by: str, reason: str) -> dict:
    """입점 승인·정지·재개·계약 종료 — 운영자만, 이유 필수. 정지·종료하면 초대 코드도 막는다."""
    by = _operator(by)
    reason = " ".join((reason or "").split())[:200]
    if not reason:
        raise SellerError("이유를 적어 주세요")
    r = _row(eng, seller_id)
    if r is None:
        raise SellerError("없는 셀러예요")
    if status not in ALLOWED.get(r["status"], set()):
        raise SellerError(f"'{STATUSES[r['status']]}' 상태에서 '{STATUSES.get(status, status)}'(으)로 바꿀 수 없어요")
    if status == "active" and r["kind"] == "consign":  # 정식 위탁판매 셀러는 입점 심사표가 먼저 (2026-11-26)
        from app.services.seller import consign

        consign.gate_activate(eng, seller_id)
    vals: dict = {"status": status}
    if status == "ended":
        vals["ended_at"] = now()
    with eng.begin() as c:
        c.execute(update(t_seller).where(t_seller.c.seller_id == seller_id).values(**vals))
        if status not in ENTER_OK:
            c.execute(
                update(t_key)
                .where(and_(t_key.c.seller_id == seller_id, t_key.c.revoked_at.is_(None)))
                .values(revoked_at=now())
            )
        _event(c, seller_id, "status", by, {"from": r["status"], "to": status, "reason": reason})
    return _public(_row(eng, seller_id))


def list_sellers(eng) -> list[dict]:
    """목록에는 연락처를 넣지 않는다(있는지만)."""
    with eng.connect() as c:
        rows = c.execute(select(t_seller).order_by(t_seller.c.created_at)).mappings().all()
    return [_public(r, contact="none") for r in rows]


def detail(eng, seller_id: str) -> dict | None:
    r = _row(eng, seller_id)
    if r is None:
        return None
    with eng.connect() as c:
        keys = c.execute(select(t_key).where(t_key.c.seller_id == seller_id)).mappings().all()
    return {
        **_public(r, contact="full"),
        "memo": r["memo"] or "",
        "keys": [
            {
                "key_id": k["key_id"],
                "created_at": k["created_at"].isoformat() if k["created_at"] else None,
                "first_used_at": k["first_used_at"].isoformat() if k["first_used_at"] else None,
                "revoked": k["revoked_at"] is not None,
            }
            for k in keys
        ],
        "events": events(eng, seller_id),
    }


def events(eng, seller_id: str, limit: int = 50) -> list[dict]:
    with eng.connect() as c:
        rows = (
            c.execute(
                select(t_event).where(t_event.c.seller_id == seller_id).order_by(t_event.c.id.desc()).limit(limit)
            )
            .mappings()
            .all()
        )
    return [{"kind": r["kind"], "by": r["by"], "detail": r["detail"], "at": r["at"].isoformat()} for r in rows]


def purge(eng, at: datetime | None = None) -> int:
    """계약 종료 뒤 1년 지난 셀러의 담당자 연락처 삭제 (매일 보존 작업)."""
    at = at or now()
    cut = at - timedelta(days=CONTACT_KEEP_DAYS)
    with eng.begin() as c:
        ids = [
            r[0]
            for r in c.execute(
                select(t_seller.c.seller_id).where(
                    and_(t_seller.c.status == "ended", t_seller.c.ended_at <= cut, t_seller.c.contact_enc.is_not(None))
                )
            ).all()
        ]
        for sid in ids:
            c.execute(
                update(t_seller).where(t_seller.c.seller_id == sid).values(contact_enc=None, contact_purged_at=at)
            )
            _event(c, sid, "contact_purged", "system:retention", {})
    return len(ids)


# ── 셀러 쪽 (코드로만) ──────────────────────────────────────────────────
def resolve(eng, token: str, client: str):
    """코드 → 셀러 행. 셀러 쪽 함수는 반드시 이것을 거친다."""
    if corp._blocked(client, LIMIT_KEY):
        raise SellerError("여러 번 잘못 넣어 잠시 막았어요. 10분 뒤에 다시 해 주세요")
    token = (token or "").strip()
    if not TOKEN_RE.match(token):
        corp._fail(client, LIMIT_KEY)
        raise SellerError("초대 코드가 맞지 않아요")
    with eng.begin() as c:
        k = (
            c.execute(select(t_key).where(and_(t_key.c.token_hash == _hash(token), t_key.c.revoked_at.is_(None))))
            .mappings()
            .first()
        )
        if k is None:
            corp._fail(client, LIMIT_KEY)
            raise SellerError("초대 코드가 맞지 않거나 더는 쓸 수 없어요. 운영팀에 새 코드를 요청해 주세요")
        r = c.execute(select(t_seller).where(t_seller.c.seller_id == k["seller_id"])).mappings().first()
        if r is None or r["status"] not in ENTER_OK:
            raise SellerError("지금은 셀러 센터를 쓸 수 없어요. 운영팀에 문의해 주세요")
        if k["first_used_at"] is None:
            c.execute(update(t_key).where(t_key.c.key_id == k["key_id"]).values(first_used_at=now()))
            _event(c, r["seller_id"], "key_first_used", "seller", {"key_id": k["key_id"]})
    return r


def me(eng, token: str, client: str) -> dict:
    """셀러 자기 정보 — 연락처는 가려서."""
    r = resolve(eng, token, client)
    return {k: v for k, v in _public(r).items() if k != "seller_id"}


def update_contact(eng, token: str, client: str, contact: dict) -> dict:
    """셀러가 자기 담당자 연락처를 바꾼다 — 자기 행만."""
    r = resolve(eng, token, client)
    ct = _check_contact(contact)
    with eng.begin() as c:
        c.execute(update(t_seller).where(t_seller.c.seller_id == r["seller_id"]).values(contact_enc=corp._enc(ct)))
        _event(c, r["seller_id"], "contact_updated", "seller", {})
    return me(eng, token, client)


__all__ = [
    "SellerError",
    "create_seller",
    "create_trial",
    "detail",
    "engine",
    "issue_key",
    "list_sellers",
    "me",
    "purge",
    "resolve",
    "revoke_keys",
    "set_status",
    "update_contact",
]
