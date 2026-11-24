"""B2B 입찰 폐쇄몰 1차 (2026-11-24) — 설계 claude/b2b_closed_mall_auth_2026-11-24.md · 로드맵 5단계 'B2B 입찰 폐쇄몰'.

기업 일괄 구매형: 발주처가 인원·금액으로 계약, 임직원은 **선택·수령만**. 결제 없음.

* **입장 = 코드 하나에 선택 하나.** 운영자가 인원 수만큼 코드를 만들어 발주처 담당자에게 넘기고, 발주처가 직원에게 나눠 준다.
  우리가 보장하는 것은 '코드당 주문 하나'까지다. '직원 한 명에 코드 하나' 배포와 대상자 확인은 발주처 몫이고,
  코드를 남에게 넘기거나 대신 쓰는 것까지는 막지 못한다(계약·안내문에 적는다).
  우리는 **명단 없이** 코드 해시·사용 여부만 안다. 코드 원문은 만들 때 한 번만 보여 준다(내려받기).
* **두 가지 입장 수단.** 초대 링크용 긴 무작위 토큰(144비트, 주소의 # 뒤 — 서버·접속 기록에 안 남음)과
  손으로 넣는 짧은 코드(8자). 짧은 코드는 접속 주소마다 10분 10번, 몰 전체 10분 300번 틀리면 잠시 막는다.
* **입장 ≠ 확정.** 링크를 열거나 코드를 넣기만 해서는 아무것도 소진되지 않는다(메일 보안 검사가 링크를 열어도 괜찮음).
  고르면 '선택 저장', 마감(또는 발송 준비) 때 확정. 동시에 두 번 골라도 주문은 하나(코드 해시 유일 제약).
* **배송지 바꾸기는 재확인.** 이미 넣은 배송지는 직원에게도 가려 보여 주고, 바꾸려면 처음 넣은 휴대폰 끝 4자리를 함께 넣어야 한다.
  재발급하면 옛 코드·옛 링크는 막히고 주문은 새 코드로 옮겨진다.
* **개인정보.** 기본 수집 = 개별 배송 몰의 배송 정보(받는 분 이름·휴대폰·주소, 메모는 선택) — 동의 필수,
  **암호화** 저장, 배송 완료 뒤 보존 기간(기본 30일)이 지나면 지운다. 회사 일괄 배송 몰은 받지 않는다.
  그 밖에 남는 것: 코드 번호 ↔ 주문 연결(이름 없음), 운영 기록(건수만). 잘못 입력 제한용 접속 주소는 해시로 메모리에 10분만.
* 발주처마다 따로 — 다른 몰의 코드·주문은 보이지 않는다.
* 상품은 낙찰 제안서 상품만(운영자가 몰을 만들 때 넣음). 가격은 직원에게 보이지 않는다(금액대 선택형이면 금액대 이름만).
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import secrets
import threading
import time
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

import sqlalchemy
from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    Integer,
    MetaData,
    String,
    Table,
    Text,
    and_,
    func,
    select,
    update,
)

from app.admin.shared.config import data_dir, get_settings

KST = timezone(timedelta(hours=9))
ALPHABET = "23456789ABCDEFGHJKLMNPQRSTUVWXYZ"
CODE_LEN = 8
MAX_FAILS = 10
MALL_MAX_FAILS = 300  # 몰 전체 — 여러 주소로 나눠 맞히기 막기 (초대 링크 토큰은 영향 없음)
FAIL_WINDOW = 600
TOKEN_RE = re.compile(r"^[A-Za-z0-9_-]{24}$")
DELIVERY_MODES = ("individual", "bulk", "coupon")  # 개별 배송 · 회사 일괄 배송 · 모바일 쿠폰(번호만 — 2차)
SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9-]{2,39}$")

meta = MetaData()
t_mall = Table(
    "corpmall_mall",
    meta,
    Column("mall_id", String(20), primary_key=True),
    Column("slug", String(40), unique=True, nullable=False),
    Column("payload", JSON, nullable=False),
    Column("status", String(12), nullable=False, default="draft"),  # draft | open | closed | ended
    Column("created_at", DateTime(timezone=True)),
)
t_code = Table(
    "corpmall_code",
    meta,
    Column("code_hash", String(64), primary_key=True),
    Column("mall_id", String(20), index=True, nullable=False),
    Column("link_hash", String(64), unique=True, nullable=False),  # 초대 링크 토큰 해시
    Column("label", Integer, nullable=False),  # 몇 번째 코드 (재발급·분실 처리용, 이름 아님)
    Column("status", String(8), nullable=False, default="unused"),  # unused | used | void
    Column("created_at", DateTime(timezone=True)),
    Column("used_at", DateTime(timezone=True)),
)
t_order = Table(
    "corpmall_order",
    meta,
    Column("order_id", String(20), primary_key=True),
    Column("mall_id", String(20), index=True, nullable=False),
    Column("code_hash", String(64), unique=True, nullable=False),
    Column("item_id", String(40), nullable=False),
    Column("defaulted", Boolean, default=False),  # 마감까지 안 골라 기본 상품으로
    Column("ship_enc", Text),  # 배송 정보 (암호화) — 지우면 None
    Column("ship_status", String(12), default="none"),  # none | requested | exported | shipped | delivered
    Column("chosen_at", DateTime(timezone=True)),
    Column("updated_at", DateTime(timezone=True)),
    Column("delivered_at", DateTime(timezone=True)),
    Column("purged_at", DateTime(timezone=True)),
    Column("tracking", String(40)),  # 송장 번호 (2026-11-24 답변 매뉴얼) — 개인정보 아님. 송장 등록 ≠ 출고
    Column("shipped_at", DateTime(timezone=True)),  # 출고 확인(발송함) 시각 — 배송 상태 확인 필요 판단 기준
)
t_manager = Table(
    "corpmall_manager",
    meta,  # 발주처 담당자 링크 (2026-11-24) — 토큰 해시만, 이름 대신 운영자가 붙인 표시(예: 총무팀)
    Column("manager_id", String(12), primary_key=True),
    Column("mall_id", String(20), index=True, nullable=False),
    Column("token_hash", String(64), unique=True, nullable=False),
    Column("label", String(40)),
    Column("created_at", DateTime(timezone=True)),
    Column("revoked_at", DateTime(timezone=True)),
)
t_po_batch = Table(
    "corpmall_po_batch",
    meta,  # 발주 묶음 (2026-11-24 검토) — 다운로드가 실패해도 같은 묶음을 다시 받을 수 있게
    Column("batch_id", String(16), primary_key=True),
    Column("mall_id", String(20), index=True, nullable=False),
    Column("created_at", DateTime(timezone=True)),
    Column("created_by", String(40)),
    Column("summary", JSON),  # 공급사별 주문·수량, 제외 사유별 건수 (배송 정보 없음)
)
t_po_line = Table(
    "corpmall_po_line",
    meta,  # 발주 묶음에 넣은 주문 한 줄 (배송 정보 없음 — 파일을 다시 만들 때 주문에서 복호화)
    Column("batch_id", String(16), index=True, nullable=False),
    Column("order_id", String(20), nullable=False),
    Column("supplier", String(40)),
    Column("item_id", String(40)),
    Column("sku", String(40)),
    Column("qty", Integer),
)
t_po = Table(
    "corpmall_po",
    meta,  # 정식 발주서 (2026-11-24) — 발주 묶음 × 공급사 하나. 금액·조건은 만들 때 값으로 고정(스냅숏)
    Column("po_no", String(24), primary_key=True),
    Column("batch_id", String(16), index=True, nullable=False),
    Column("mall_id", String(20), index=True, nullable=False),
    Column("supplier_id", String(12)),
    Column("supplier_name", String(40), nullable=False),
    Column("issued_at", DateTime(timezone=True)),
    Column("due_date", String(10)),
    Column("payment_terms", String(120)),
    Column("vat_mode", String(10)),
    Column("lines", JSON),  # [{item_id, name, sku, qty, unit_cost, amount}]
    Column("supply_amount", Integer),
    Column("vat", Integer),
    Column("total", Integer),
    # draft(미확정 — 정식 발주 아님) · issued(정식 발주) · accepted(공급사 수락) · change_requested(공급사 변경 요청 — 운영자 검토)
    # · cancel_requested(전달된 발주 취소 요청 — 공급사 취소 확인 기다림) · cancelled
    Column("status", String(18), nullable=False, default="issued"),
    Column("exempt_amount", Integer),  # 면세 품목 금액 (공급가액에 포함, 부가세 없음)
    Column("ship_by", String(10)),  # 출고 기한 (due_date 와 같은 값 — 뜻을 분명히)
    Column("arrive_by", String(10)),  # 도착 요청일 (몰 매뉴얼) — 출고 기한과 따로
    Column("delivered_at", DateTime(timezone=True)),  # 공급사에 처음 전달된 때(메일·.eml·확인 링크·전달용 파일)
    Column("viewed_at", DateTime(timezone=True)),  # 공급사가 확인 화면을 처음 연 때
    Column("version", Integer),
    Column("history", JSON),  # [{at, by, what, before, after}] — 상태·확정·공급사 응답 변경 이력
    Column("cancel_reason", String(200)),
    Column("ack_token_hash", String(64)),
    Column(
        "ack_token_enc", Text
    ),  # 확인 링크 원문(암호화) — 같은 판에서 재발송할 때 같은 링크를 쓰려고. 재발급은 명시적으로만
    Column("ack_link_at", DateTime(timezone=True)),  # 지금 링크를 만든 때
    Column("ack_at", DateTime(timezone=True)),
    Column("ack_by", String(30)),
    Column("ack_ship_date", String(10)),
    Column("ack_memo", String(300)),
    Column("ack_via", String(10)),  # link · operator
    Column("invoice_received_at", DateTime(timezone=True)),  # 매입 세금계산서 받음 (정산)
    Column("invoice_memo", String(200)),
)
t_po_mail = Table(
    "corpmall_po_mail",
    meta,  # 발주서 메일 (2026-11-24) — 준비 → 운영자 확인 → 보냄. 본문엔 {ACK_LINK} 자리만(링크는 발주서 쪽에 암호화)
    Column("mail_id", String(12), primary_key=True),
    Column("po_no", String(24), index=True, nullable=False),
    Column("mall_id", String(20), index=True, nullable=False),
    Column("to_enc", Text),  # 받는 사람(거래처 발주 담당 메일) — 암호화
    Column("subject", String(200)),
    Column("body", Text),  # {ACK_LINK} 자리 표시 포함
    # draft · sending(보내는 중) · sent(SMTP 접수 완료) · manual(직접 발송 확인) · failed(안 감이 확실) · unknown(결과 불명 — 자동 재발송 안 함)
    Column("status", String(10), nullable=False, default="draft"),
    Column("attach", Boolean),
    Column("created_at", DateTime(timezone=True)),
    Column("sent_at", DateTime(timezone=True)),
    Column("error", String(300)),
    Column("by", String(40)),
)
t_event = Table(
    "corpmall_event",
    meta,  # 운영 기록 (개인정보 없음)
    Column("event_id", String(36), primary_key=True),
    Column("mall_id", String(20), index=True),
    Column("kind", String(24)),
    Column("detail", JSON),
    Column("at", DateTime(timezone=True)),
)

_LOCK = threading.Lock()
_FAILS: dict[str, list[float]] = {}


class MallError(ValueError):
    """화면에 그대로 보여 줄 수 있는 짧은 이유."""


def now() -> datetime:
    return datetime.now(KST)


def engine(url: str | None = None):
    eng = sqlalchemy.create_engine(url or get_settings().b2b_db_url, future=True)
    from app.services.corpmall import suppliers  # noqa: F401 — 거래처 표도 같은 meta 에 (create_all 전에 등록)

    meta.create_all(eng)
    _migrate(eng)
    return eng


def _migrate(eng) -> None:
    """#104 로 이미 만들어진 표에 나중 칸을 붙인다 (create_all 은 있는 표를 바꾸지 않음)."""
    cols = {c["name"] for c in sqlalchemy.inspect(eng).get_columns("corpmall_order")}
    add = {
        "tracking": "VARCHAR(40)",
        "shipped_at": "TIMESTAMP WITH TIME ZONE" if eng.dialect.name == "postgresql" else "DATETIME",
    }
    for name, typ in add.items():
        if name not in cols:
            with eng.begin() as c:
                c.execute(sqlalchemy.text(f"ALTER TABLE corpmall_order ADD COLUMN {name} {typ}"))
    # 발주서 검토 반영(2026-11-24) — 개발 중 먼저 만들어진 corpmall_po 에 새 칸
    insp = sqlalchemy.inspect(eng)
    if insp.has_table("corpmall_po"):
        have = {c["name"] for c in insp.get_columns("corpmall_po")}
        ts = "TIMESTAMP WITH TIME ZONE" if eng.dialect.name == "postgresql" else "DATETIME"
        js = "JSON"
        for name, typ in {
            "exempt_amount": "INTEGER", "ship_by": "VARCHAR(10)", "arrive_by": "VARCHAR(10)", "delivered_at": ts,
            "viewed_at": ts, "version": "INTEGER", "history": js, "cancel_reason": "VARCHAR(200)",
            "ack_token_enc": "TEXT", "ack_link_at": ts,
        }.items():  # fmt: skip
            if name not in have:
                with eng.begin() as c:
                    c.execute(sqlalchemy.text(f"ALTER TABLE corpmall_po ADD COLUMN {name} {typ}"))


# ── 암호화 (배송 정보) ─────────────────────────────────────────────────────
def _fernet():
    from cryptography.fernet import Fernet

    key = os.getenv("CORPMALL_KEY")
    if not key:
        p: Path = data_dir() / "corpmall.key"  # 운영 맥 안에만 — 저장소에 넣지 않음
        if not p.exists():
            p.write_bytes(Fernet.generate_key())
            p.chmod(0o600)
        key = p.read_text().strip()
    return Fernet(key.encode() if isinstance(key, str) else key)


def _enc(d: dict) -> str:
    return _fernet().encrypt(json.dumps(d, ensure_ascii=False).encode()).decode()


def _dec(s: str | None) -> dict | None:
    if not s:
        return None
    return json.loads(_fernet().decrypt(s.encode()).decode())


# ── 코드 ───────────────────────────────────────────────────────────────
def code_hash(mall_id: str, code: str) -> str:
    return hashlib.sha256(f"{mall_id}|{normalize(code)}".encode()).hexdigest()


def normalize(code: str | None) -> str:
    return "".join(ch for ch in (code or "").upper() if ch.isalnum())


def pretty(code: str) -> str:
    return f"{code[:4]}-{code[4:]}"


def _new_code() -> str:
    return "".join(secrets.choice(ALPHABET) for _ in range(CODE_LEN))


def _new_token() -> str:
    return secrets.token_urlsafe(18)  # 24자 · 144비트


def link_hash(mall_id: str, token: str) -> str:
    return hashlib.sha256(f"{mall_id}|link|{token}".encode()).hexdigest()


def _event(conn, mall_id: str, kind: str, detail: dict | None = None) -> None:
    conn.execute(
        t_event.insert().values(event_id=str(uuid.uuid4()), mall_id=mall_id, kind=kind, detail=detail or {}, at=now())
    )


# ── 몰 만들기 (운영자) ─────────────────────────────────────────────────────
def _check_spec(spec: dict) -> dict:
    s = dict(spec)
    if not SLUG_RE.fullmatch(str(s.get("slug") or "")):
        raise MallError("주소 이름은 영문 소문자·숫자·- 3~40자로 써 주세요")
    if s.get("delivery_mode") not in DELIVERY_MODES:
        raise MallError("배송 방식은 individual · bulk · coupon 중 하나예요")
    items = s.get("items") or []
    if not items:
        raise MallError("상품을 하나 이상 넣어 주세요")
    ids = [str(i.get("id") or "") for i in items]
    if len(set(ids)) != len(ids) or not all(re.fullmatch(r"[A-Za-z0-9_-]{1,40}", i) for i in ids):
        raise MallError("상품 id 는 겹치지 않는 영문·숫자 1~40자")
    if s.get("default_item_id") and s["default_item_id"] not in ids:
        raise MallError("기본 상품은 상품 목록 안에서 골라 주세요")
    for k in ("opens_at", "closes_at"):
        try:
            d = datetime.fromisoformat(str(s.get(k)))
        except ValueError as e:
            raise MallError("선택 기간(opens_at · closes_at)을 ISO 시각으로 넣어 주세요") from e
        s[k] = (d if d.tzinfo else d.replace(tzinfo=KST)).isoformat(timespec="minutes")  # 시간대 없으면 한국 시각
    if datetime.fromisoformat(s["closes_at"]) <= datetime.fromisoformat(s["opens_at"]):
        raise MallError("마감이 시작보다 뒤여야 해요")
    s["retention_days"] = int(s.get("retention_days") or 30)
    from app.services.corpmall import manual

    try:
        s["manual"] = manual.check_manual(s.get("manual"))
    except ValueError as e:
        raise MallError(str(e)) from e
    s["items"] = [
        {
            k: i.get(k)
            for k in (
                "id",
                "name",
                "desc",
                "image",
                "tier",
                "supplier_candidate_id",
                "supplier",
                "supplier_id",
                "supplier_sku",
                "unit_cost",
                "tax_type",  # 매입 과세 구분 taxable(기본)·exempt — 세무 검토 뒤 확정
            )
        }
        for i in items
    ]
    for i in s["items"]:
        i["tax_type"] = i.get("tax_type") or "taxable"
        if i["tax_type"] not in ("taxable", "exempt"):
            raise MallError("과세 구분(tax_type)은 taxable(과세)·exempt(면세) 중 하나예요")
        if i["unit_cost"] is not None and (
            not isinstance(i["unit_cost"], int) or not 0 <= i["unit_cost"] <= 10_000_000
        ):
            raise MallError("매입 단가(unit_cost)는 0 이상 원 단위 숫자예요")
    return s


def create_mall(eng, spec: dict) -> dict:
    s = _check_spec(spec)
    mall_id = "M" + secrets.token_hex(4).upper()
    with eng.begin() as c:
        if c.execute(select(t_mall.c.mall_id).where(t_mall.c.slug == s["slug"])).first():
            raise MallError("이미 쓰는 주소 이름이에요")
        c.execute(t_mall.insert().values(mall_id=mall_id, slug=s["slug"], payload=s, status="draft", created_at=now()))
        _event(c, mall_id, "created", {"items": len(s["items"])})
    return {"mall_id": mall_id, **s, "status": "draft"}


def get_mall(eng, *, mall_id: str | None = None, slug: str | None = None) -> dict | None:
    q = select(t_mall).where(t_mall.c.mall_id == mall_id) if mall_id else select(t_mall).where(t_mall.c.slug == slug)
    with eng.connect() as c:
        r = c.execute(q).mappings().first()
    return {"mall_id": r["mall_id"], "status": r["status"], **r["payload"]} if r else None


def list_malls(eng) -> list[dict]:
    with eng.connect() as c:
        rows = c.execute(select(t_mall).order_by(t_mall.c.created_at.desc())).mappings().all()
    return [{"mall_id": r["mall_id"], "status": r["status"], **r["payload"]} for r in rows]


def set_status(eng, mall_id: str, status: str) -> None:
    if status not in ("draft", "open"):
        raise MallError("상태는 draft · open 만 직접 바꿔요 (마감은 close)")
    with eng.begin() as c:
        c.execute(update(t_mall).where(t_mall.c.mall_id == mall_id).values(status=status))
        _event(c, mall_id, "status", {"to": status})


def extend_close(eng, mall_id: str, closes_at: str) -> str:
    """선택 마감 늦추기 (발주처 요청을 운영자가 처리). 마감된 몰은 다시 열지 않는다 — 새로 늦추는 것만."""
    m = get_mall(eng, mall_id=mall_id)
    if m is None:
        raise MallError("없는 몰")
    if m["status"] == "closed":
        raise MallError("이미 마감 처리된 몰은 늦출 수 없어요")
    try:
        d = datetime.fromisoformat(closes_at)
    except ValueError as e:
        raise MallError("마감 시각을 ISO 형식으로 넣어 주세요") from e
    d = d if d.tzinfo else d.replace(tzinfo=KST)
    if d <= datetime.fromisoformat(m["closes_at"]):
        raise MallError("지금 마감보다 뒤로만 늦출 수 있어요")
    new = d.isoformat(timespec="minutes")
    with eng.begin() as c:
        r = c.execute(select(t_mall.c.payload).where(t_mall.c.mall_id == mall_id)).scalar()
        c.execute(update(t_mall).where(t_mall.c.mall_id == mall_id).values(payload={**r, "closes_at": new}))
        _event(c, mall_id, "close_extended", {"from": m["closes_at"], "to": new})
    return new


def issue_codes(eng, mall_id: str, n: int) -> list[tuple[int, str, str]]:
    """코드 n개 → [(번호, 짧은 코드, 링크 토큰)] — 원문은 이 반환값에만 (저장은 해시). 운영자가 바로 내려받아 발주처에 넘긴다."""
    if not 1 <= n <= 5000:
        raise MallError("코드는 한 번에 1~5,000개")
    out = []
    with eng.begin() as c:
        start = (c.execute(select(func.max(t_code.c.label)).where(t_code.c.mall_id == mall_id)).scalar() or 0) + 1
        for i in range(n):
            code, token = _new_code(), _new_token()
            c.execute(
                t_code.insert().values(
                    code_hash=code_hash(mall_id, code),
                    link_hash=link_hash(mall_id, token),
                    mall_id=mall_id,
                    label=start + i,
                    status="unused",
                    created_at=now(),
                )
            )
            out.append((start + i, pretty(code), token))
        _event(c, mall_id, "codes_issued", {"n": n, "from": start})
    return out


def void_and_reissue(eng, mall_id: str, label: int) -> tuple[int, str, str]:
    """분실 — 그 번호 코드·링크를 막고 새 코드 하나 (이미 고른 주문은 새 코드로 옮김)."""
    with eng.begin() as c:
        row = (
            c.execute(select(t_code).where(and_(t_code.c.mall_id == mall_id, t_code.c.label == label)))
            .mappings()
            .first()
        )
        if row is None or row["status"] == "void":
            raise MallError("그 번호의 코드가 없거나 이미 막혔어요")
        code, token = _new_code(), _new_token()
        h = code_hash(mall_id, code)
        new_label = (c.execute(select(func.max(t_code.c.label)).where(t_code.c.mall_id == mall_id)).scalar() or 0) + 1
        c.execute(update(t_code).where(t_code.c.code_hash == row["code_hash"]).values(status="void"))
        c.execute(
            t_code.insert().values(
                code_hash=h,
                link_hash=link_hash(mall_id, token),
                mall_id=mall_id,
                label=new_label,
                status=row["status"],
                created_at=now(),
                used_at=row["used_at"],
            )
        )
        c.execute(update(t_order).where(t_order.c.code_hash == row["code_hash"]).values(code_hash=h))
        _event(c, mall_id, "code_reissued", {"old": label, "new": new_label})
    try:
        from app.services.cs import tickets

        tickets.rename_owner(asker(mall_id, label), asker(mall_id, new_label))
    except Exception:  # noqa: BLE001 — 문의 잇기 실패가 재발급을 막지 않게
        pass
    return new_label, pretty(code), token


# ── 직원 화면 ───────────────────────────────────────────────────────────
def _fail_key(client: str, slug: str) -> str:
    return hashlib.sha256(f"{client}|{slug}".encode()).hexdigest()


def _recent(k: str, t: float) -> int:
    _FAILS[k] = [x for x in _FAILS.get(k, []) if t - x < FAIL_WINDOW]
    return len(_FAILS[k])


def _blocked(client: str, slug: str) -> str | None:
    t = time.monotonic()
    with _LOCK:
        if _recent(_fail_key(client, slug), t) >= MAX_FAILS:
            return "client"
        if _recent(_fail_key("*", slug), t) >= MALL_MAX_FAILS:
            return "mall"
    return None


def _fail(client: str, slug: str) -> None:
    t = time.monotonic()
    with _LOCK:
        _FAILS.setdefault(_fail_key(client, slug), []).append(t)
        _FAILS.setdefault(_fail_key("*", slug), []).append(t)


def reset_limits() -> None:  # 시험용
    with _LOCK:
        _FAILS.clear()


def _window(m: dict, at: datetime) -> str:
    if m["status"] in ("closed", "ended"):
        return "closed"
    if m["status"] != "open":
        return "not_open"
    if at < datetime.fromisoformat(m["opens_at"]).astimezone(KST):
        return "not_open"
    if at >= datetime.fromisoformat(m["closes_at"]).astimezone(KST):
        return "closed"
    return "open"


def public_mall(m: dict) -> dict:
    """직원에게 보여 줄 것만 (가격·공급사·내부 메모 없음)."""
    return {
        "slug": m["slug"],
        "client": m.get("client"),
        "title": m.get("title"),
        "notice": m.get("notice"),
        "opens_at": m["opens_at"],
        "closes_at": m["closes_at"],
        "delivery_mode": m["delivery_mode"],
        "items": [{k: i.get(k) for k in ("id", "name", "desc", "image", "tier")} for i in m["items"]],
        "retention_days": m.get("retention_days", 30),
        "ship_plan": (m.get("manual") or {}).get("ship_plan"),
        "courier": (m.get("manual") or {}).get("courier"),
    }


def _code_row(c, mall_id: str, code: str):
    """초대 링크 토큰(24자)이면 링크 해시로, 아니면 짧은 코드 해시로 찾는다."""
    col, h = (
        (t_code.c.link_hash, link_hash(mall_id, code))
        if TOKEN_RE.fullmatch(code or "")
        else (t_code.c.code_hash, code_hash(mall_id, code))
    )
    return c.execute(select(t_code).where(and_(col == h, t_code.c.mall_id == mall_id))).mappings().first()


def _mask(ship: dict | None) -> dict | None:
    if not ship:
        return None
    name = ship.get("name") or ""
    phone = re.sub(r"\D", "", ship.get("phone") or "")
    return {
        "name": (name[:1] + "*" * max(0, len(name) - 1)) if name else "",  # 끝 4자리는 재확인용이라 보여 주지 않음
        "phone": f"{phone[:3]}-****-****" if len(phone) >= 8 else "",
        "address": (ship.get("address") or "")[:8] + "…",
    }


def _resolve(eng, slug: str, code: str, client: str):
    m = get_mall(eng, slug=slug)
    if m is None or m["status"] == "draft":
        raise MallError("없는 선물 페이지예요")
    is_token = bool(TOKEN_RE.fullmatch(code or ""))
    why = _blocked(client, slug)
    if why == "client" or (why == "mall" and not is_token):
        raise MallError(
            "코드를 여러 번 잘못 넣어 잠시 막았어요. 10분 뒤에 다시 해 주세요"
            + ("" if why == "client" else " (초대 링크로는 들어올 수 있어요)")
        )
    with eng.connect() as c:
        row = _code_row(c, m["mall_id"], code)
        if row is None or row["status"] == "void":
            _fail(client, slug)
            raise MallError("코드가 맞지 않아요. 회사에서 받은 코드를 확인해 주세요")
        order = c.execute(select(t_order).where(t_order.c.code_hash == row["code_hash"])).mappings().first()
    return m, row, order


def _asks(mall_id: str, label: int) -> list[dict]:
    try:
        from app.services.cs import tickets

        return tickets.for_owner(asker(mall_id, label))
    except Exception:  # noqa: BLE001
        return []


def asker(mall_id: str, label: int) -> str:
    """폐쇄몰 문의 티켓의 주인 — 코드 번호만 (이름 없음)."""
    return f"corp:{mall_id}:{label}"


MAX_OPEN_ASKS = 5


def ask(
    eng, slug: str, code: str, text: str, client: str, *, handoff: bool = False, reader=None, at: datetime | None = None
) -> dict:
    """임직원 문의 — 먼저 매뉴얼로 바로 답하고(assist), 매뉴얼 밖·사람 필수·'담당자에게 남기기'면 CS 티켓.

    문장은 개인정보 모양을 가린 뒤에만 쓰인다(AI 로 보내는 것도 가린 뒤, 종류 고르기에만). 답은 같은 코드로 들어오면 보인다.
    """
    from app.services.corpmall import assist
    from app.services.cs import review, tickets
    from app.services.privacy import pii

    m, row, order_row = _resolve(eng, slug, code, client)
    body = " ".join((text or "").split())[:400]
    if len(body) < 2:
        raise MallError("문의 내용을 적어 주세요")
    owner = asker(m["mall_id"], row["label"])
    masked, kinds = pii.mask(body)
    got = enter(eng, slug, code, client, at=at)
    man = m.get("manual") or {}
    if handoff:
        rep = assist.Reply("handoff", "customer", "", ticket="corpmall", offer_handoff=False)
    else:
        rep = assist.respond(m, got["order"], got["window"], masked, reader=reader, today=(at or now()).date())
    ticket_id, answer, offer = None, rep.answer, rep.offer_handoff
    if rep.ticket:
        label = assist.INTENTS.get(rep.intent, "직접 요청")
        if rep.facts.get("check") in assist.CHECK_LABEL:  # 경과일 기준 — 지연 확정이 아니라 확인 필요
            label = assist.CHECK_LABEL[rep.facts["check"]]
        if rep.ticket == "corpmall" and tickets.open_count(owner) >= MAX_OPEN_ASKS:
            answer = (
                answer + " " if answer else ""
            ) + "답을 기다리는 문의가 이미 많아 새로 접수하지 않았어요. 아래 답을 확인한 뒤 다시 남겨 주세요."
        else:
            # 같은 코드·같은 내용을 1시간 안에 다시 보내면(두 번 클릭 등) 같은 티켓을 돌려준다 — tickets.create 의 sid 중복 검사
            sid = hashlib.sha256(f"{owner}|{rep.ticket}|{masked}".encode()).hexdigest()[:8]
            try:
                t = tickets.create(
                    rep.ticket,
                    sid=sid,
                    owner=owner,
                    by="customer",
                    summary=f"[{m['slug']} #{row['label']} {label}] {masked}",
                )
                ticket_id = t["id"] if t else None
            except Exception:  # noqa: BLE001 — 저장 실패면 '접수했어요'라고 하지 않는다
                ticket_id = None
            if ticket_id:
                when = (
                    "식품 안전 문의는 오늘 안에 확인해요."
                    if rep.ticket == "food_safety"
                    else manual_text("reply_time", man)
                )
                answer = " ".join(x for x in (answer, manual_text("handed", ticket=ticket_id), when) if x)
                offer = False
            else:
                answer = " ".join(x for x in (answer, manual_text("hand_failed")) if x)
                offer = True
    with eng.begin() as c:
        _event(c, m["mall_id"], "asked", {"intent": rep.intent, "by": rep.by, "ticket": bool(ticket_id)})
    if not handoff:
        review.record(owner, masked, f"corp_{rep.intent}", rep.by)
    return {
        "intent": rep.intent,
        "intent_label": assist.INTENTS.get(rep.intent, "직접 요청"),
        "by": rep.by,
        "answer": answer,
        "action": rep.action,
        "offer_handoff": offer,
        "ticket_id": ticket_id,
        "masked": kinds,
        "asks": tickets.for_owner(owner),
    }


def manual_text(key: str, man: dict | None = None, **kw) -> str:
    from app.services.corpmall import manual

    return manual.text(key, man, **kw)


def enter(eng, slug: str, code: str, client: str, *, at: datetime | None = None) -> dict:
    """코드(또는 초대 링크 토큰) 확인 → 몰·상품·지금 고른 것. 아무것도 소진하지 않는다."""
    m, row, order = _resolve(eng, slug, code, client)
    mine = None
    if order:
        mine = {
            "item_id": order["item_id"],
            "defaulted": bool(order["defaulted"]),
            "ship_status": order["ship_status"],
            "shipping": _mask(_dec(order["ship_enc"])) if order["ship_enc"] else None,
            "tracking": order.get("tracking"),
            "shipped_on": order["shipped_at"].date().isoformat() if order.get("shipped_at") else None,
            "chosen_at": order["chosen_at"].isoformat() if order["chosen_at"] else None,
        }
    return {
        "mall": public_mall(m),
        "window": _window(m, at or now()),
        "order": mine,
        "label": row["label"],
        "asks": _asks(m["mall_id"], row["label"]),
    }


SHIP_FIELDS = {"name": 30, "phone": 20, "zipcode": 10, "address": 200, "memo": 100}


def _check_ship(ship: dict | None) -> dict:
    s = {k: " ".join(str((ship or {}).get(k) or "").split())[:n] for k, n in SHIP_FIELDS.items()}
    if not s["name"] or not s["address"]:
        raise MallError("받는 분 이름과 주소를 넣어 주세요")
    if not re.fullmatch(r"01[016789]\d{7,8}", re.sub(r"\D", "", s["phone"])):
        raise MallError("받는 분 휴대폰 번호를 확인해 주세요 (배송 연락용)")
    return s


VERIFY_MAX = 5


def _verify_fails(eng, mall_id: str, label: int, at: datetime | None = None) -> int:
    since = now() - timedelta(hours=24)  # 기록 시각(실제 시각) 기준
    with eng.connect() as c:
        rows = c.execute(
            select(t_event.c.detail, t_event.c.at).where(
                and_(t_event.c.mall_id == mall_id, t_event.c.kind == "verify_failed")
            )
        ).mappings()
        return sum(
            1
            for r in rows
            if (r["detail"] or {}).get("label") == label
            and (r["at"] if r["at"].tzinfo else r["at"].replace(tzinfo=KST)) >= since
        )


def _last4(ship: dict | None) -> str:
    return re.sub(r"\D", "", (ship or {}).get("phone") or "")[-4:]


def choose(
    eng,
    slug: str,
    code: str,
    item_id: str,
    client: str,
    *,
    shipping: dict | None = None,
    consent: bool = False,
    verify: str | None = None,
    at: datetime | None = None,
) -> dict:
    """선택 저장(마감 전에는 바꿀 수 있음). 개별 배송 몰이면 배송 정보 + 수집·이용 동의가 있어야 한다.

    이미 배송지를 넣은 주문: 상품만 바꿀 때는 shipping 없이 보내면 배송지를 그대로 둔다.
    배송지를 바꾸려면 처음 넣은 휴대폰 끝 4자리(verify)를 함께 — 코드가 새어도 남이 배송지를 돌리지 못하게.
    """
    m, row, order = _resolve(eng, slug, code, client)
    window = _window(m, at or now())
    if window != "open":
        raise MallError("선택 기간이 아니에요" if window == "not_open" else "선택이 마감됐어요")
    # 바꿀 수 있는 조건은 하나 (manual.EDIT_RULE): 선택 기간 안 + 발송 준비 전 — 아래 검사
    if item_id not in {i["id"] for i in m["items"]}:
        raise MallError("이 페이지에 없는 상품이에요")
    if order and order["ship_status"] in ("exported", "shipped", "delivered"):
        raise MallError("이미 발송 준비가 시작돼 바꿀 수 없어요")
    vals: dict = {"item_id": item_id, "defaulted": False}
    old_ship = _dec(order["ship_enc"]) if order and order["ship_enc"] else None
    if m["delivery_mode"] == "individual":
        if shipping is None and old_ship:
            pass  # 상품만 바꿈 — 배송지 그대로
        else:
            if not consent:
                raise MallError("배송 정보 수집·이용에 동의해야 보낼 수 있어요")
            new = _check_ship(shipping)
            changing = bool(old_ship) and new != old_ship
            if changing:
                # 배송지 바꾸기 = 이 코드(주문 접근 권한) + 처음 휴대폰 끝 4자리. 코드마다 24시간 5번 틀리면 막고 기록.
                if _verify_fails(eng, m["mall_id"], row["label"], at) >= VERIFY_MAX:
                    raise MallError(
                        "본인 확인을 여러 번 틀려 배송지 바꾸기를 잠시 막았어요. 아래 '궁금한 점 묻기'로 담당자에게 남겨 주세요"
                    )
                if not (verify and secrets.compare_digest(re.sub(r"\D", "", verify), _last4(old_ship))):
                    _fail(client, slug)
                    with eng.begin() as c:
                        _event(c, m["mall_id"], "verify_failed", {"label": row["label"]})
                    raise MallError("배송지를 바꾸려면 처음 넣은 휴대폰 번호 끝 4자리를 확인해 주세요")
            vals.update(ship_enc=_enc(new), ship_status="requested")
            if changing:
                vals["_changed"] = True
    ship_changed = vals.pop("_changed", False)
    h = row["code_hash"]
    t = at or now()
    vals["updated_at"] = t
    with eng.begin() as c:
        exists = c.execute(select(t_order.c.order_id).where(t_order.c.code_hash == h)).scalar()
        if not exists:
            try:
                with c.begin_nested():
                    c.execute(
                        t_order.insert().values(
                            order_id="O" + secrets.token_hex(5).upper(),
                            mall_id=m["mall_id"],
                            code_hash=h,
                            chosen_at=t,
                            **{"ship_status": "none", **vals},
                        )
                    )
            except sqlalchemy.exc.IntegrityError:  # 같은 코드로 동시에 두 번 — 주문은 하나만
                exists = c.execute(select(t_order.c.order_id).where(t_order.c.code_hash == h)).scalar()
        if exists:
            # 발송 준비가 동시에 시작됐으면 바꾸지 않는다 (확인과 저장 사이 경쟁 — 조건을 저장 문장에 함께)
            n = c.execute(
                update(t_order)
                .where(
                    and_(
                        t_order.c.order_id == exists, t_order.c.ship_status.not_in(("exported", "shipped", "delivered"))
                    )
                )
                .values(**vals)
            ).rowcount
            if not n:
                raise MallError("이미 발송 준비가 시작돼 바꿀 수 없어요")
        c.execute(update(t_code).where(t_code.c.code_hash == h).values(status="used", used_at=t))
        _event(c, m["mall_id"], "chosen", {"item_id": item_id, "changed": bool(exists)})  # 누가 골랐는지는 남기지 않음
        if ship_changed:
            _event(c, m["mall_id"], "ship_changed", {"label": row["label"]})  # 변경 이력 (값은 남기지 않음)
    return enter(eng, slug, code, client, at=at)


# ── 마감 · 내보내기 · 배송 · 파기 (운영자) ─────────────────────────────────────
def close_mall(eng, mall_id: str) -> dict:
    """마감 — 안 고른 코드는 기본 상품으로.

    회사 일괄 배송 몰은 그대로 발송 대상. 개별 배송 몰은 그 직원 주소가 없으니 'no_address'(주소 없음)로 남기고,
    번호 목록(no_address_labels)을 발주처에 넘겨 회사 일괄 수령 등 계약에 정한 방법으로 처리한다 — 임의로 보내지 않는다."""
    m = get_mall(eng, mall_id=mall_id)
    if m is None:
        raise MallError("없는 몰")
    n_default = 0
    with eng.begin() as c:
        c.execute(update(t_mall).where(t_mall.c.mall_id == mall_id).values(status="closed"))
        if m.get("default_item_id"):
            chosen = set(c.execute(select(t_order.c.code_hash).where(t_order.c.mall_id == mall_id)).scalars())
            for h in c.execute(
                select(t_code.c.code_hash).where(and_(t_code.c.mall_id == mall_id, t_code.c.status == "unused"))
            ).scalars():
                if h in chosen:
                    continue
                c.execute(
                    t_order.insert().values(
                        order_id="O" + secrets.token_hex(5).upper(),
                        mall_id=mall_id,
                        code_hash=h,
                        item_id=m["default_item_id"],
                        defaulted=True,
                        ship_status="no_address" if m["delivery_mode"] == "individual" else "none",
                        chosen_at=now(),
                        updated_at=now(),
                    )
                )
                n_default += 1
        _event(c, mall_id, "closed", {"defaulted": n_default})
    return {"defaulted": n_default}


def stats(eng, mall_id: str) -> dict:
    m = get_mall(eng, mall_id=mall_id) or {}
    with eng.connect() as c:
        codes = dict(
            c.execute(
                select(t_code.c.status, func.count()).where(t_code.c.mall_id == mall_id).group_by(t_code.c.status)
            ).all()
        )
        by_item = dict(
            c.execute(
                select(t_order.c.item_id, func.count()).where(t_order.c.mall_id == mall_id).group_by(t_order.c.item_id)
            ).all()
        )
        ship = dict(
            c.execute(
                select(t_order.c.ship_status, func.count())
                .where(t_order.c.mall_id == mall_id)
                .group_by(t_order.c.ship_status)
            ).all()
        )
        defaulted = c.execute(
            select(func.count()).where(and_(t_order.c.mall_id == mall_id, t_order.c.defaulted.is_(True)))
        ).scalar()
    issued = sum(v for k, v in codes.items() if k != "void")
    chosen = sum(by_item.values()) - (defaulted or 0)
    return {
        "issued": issued,
        "void": codes.get("void", 0),
        "chosen": chosen,
        "defaulted": defaulted or 0,
        "rate": round(chosen / issued, 4) if issued else None,
        "by_item": [{"id": i["id"], "name": i.get("name"), "n": by_item.get(i["id"], 0)} for i in m.get("items", [])],
        "ship": ship,
    }


def export_orders(eng, mall_id: str, *, by: str) -> list[dict]:
    """발송 요청 주문을 공급사 전달용으로 (복호화) — 내보낸 것은 'exported', 기록에 건수만."""
    m = get_mall(eng, mall_id=mall_id) or {"items": []}
    names = {i["id"]: i.get("name") for i in m["items"]}
    with eng.begin() as c:
        rows = (
            c.execute(
                select(t_order)
                .where(and_(t_order.c.mall_id == mall_id, t_order.c.ship_status == "requested"))
                .order_by(t_order.c.chosen_at)
            )
            .mappings()
            .all()
        )
        out = []
        for r in rows:
            ship = _dec(r["ship_enc"]) or {}
            out.append({"order_id": r["order_id"], "item_id": r["item_id"], "item": names.get(r["item_id"]), **ship})
        if rows:
            c.execute(
                update(t_order)
                .where(t_order.c.order_id.in_([r["order_id"] for r in rows]))
                .values(ship_status="exported", updated_at=now())
            )
        _event(c, mall_id, "exported", {"n": len(rows), "by": by})
    return out


def no_address_labels(eng, mall_id: str) -> list[int]:
    """마감 뒤 주소 없이 기본 상품이 된 코드 번호 — 발주처 후속 처리용 (이름·코드 원문 없음)."""
    with eng.connect() as c:
        return list(
            c.execute(
                select(t_code.c.label)
                .join(t_order, t_order.c.code_hash == t_code.c.code_hash)
                .where(and_(t_order.c.mall_id == mall_id, t_order.c.ship_status == "no_address"))
                .order_by(t_code.c.label)
            ).scalars()
        )


def update_manual(eng, mall_id: str, raw: dict) -> dict:
    """몰 매뉴얼만 고친다 (출고 예정일·택배사·교환 조건 등)."""
    from app.services.corpmall import manual

    m = get_mall(eng, mall_id=mall_id)
    if m is None:
        raise MallError("없는 몰")
    try:
        man = manual.check_manual(raw)
    except ValueError as e:
        raise MallError(str(e)) from e
    with eng.begin() as c:
        r = c.execute(select(t_mall.c.payload).where(t_mall.c.mall_id == mall_id)).scalar()
        c.execute(update(t_mall).where(t_mall.c.mall_id == mall_id).values(payload={**r, "manual": man}))
        _event(c, mall_id, "manual", {"keys": sorted(man)})
    return man


def set_tracking(eng, mall_id: str, rows: list[dict], *, shipped: bool = False) -> dict:
    """송장 번호 넣기 [{order_id, tracking}].

    송장 발급 ≠ 출고(2026-11-24 검토). 기본은 송장만 넣고 상태는 그대로 — 직원 답은 "송장이 발급됐어요(출고되면 조회돼요)".
    shipped=True(택배사 인수·출고 확인된 주문만 올릴 때)면 '발송함' + 출고 시각.
    - 이 몰의 주문이 아니면 skipped. 배송 완료는 건드리지 않음(상태가 되돌아가지 않게).
    - 같은 송장을 다시 올리면 same(처리 안 함, 출고 시각도 그대로). 이미 다른 송장이 있으면 **덮어쓰지 않고** conflicts 로 돌려준다(사람 확인).
    """
    n, skipped, same, conflicts = 0, 0, 0, []
    t = now()
    with eng.begin() as c:
        for r in rows[:5000]:
            oid = str(r.get("order_id") or "").strip()
            tr = re.sub(r"[^0-9A-Za-z-]", "", str(r.get("tracking") or ""))[:40]
            cur = (
                c.execute(
                    select(t_order.c.tracking, t_order.c.ship_status).where(
                        and_(t_order.c.mall_id == mall_id, t_order.c.order_id == oid)
                    )
                ).first()
                if oid
                else None
            )
            if not oid or not tr or cur is None or cur.ship_status == "delivered":
                skipped += 1
                continue
            if cur.tracking and cur.tracking != tr:
                conflicts.append({"order_id": oid, "now": cur.tracking, "file": tr})
                continue
            if cur.tracking == tr and (not shipped or cur.ship_status == "shipped"):
                same += 1
                continue
            vals = {"tracking": tr, "updated_at": t}
            if shipped and cur.ship_status != "shipped":
                vals.update(ship_status="shipped", shipped_at=t)
            n += c.execute(update(t_order).where(t_order.c.order_id == oid).values(**vals)).rowcount
        _event(
            c,
            mall_id,
            "tracking",
            {"n": n, "skipped": skipped, "same": same, "conflicts": len(conflicts), "shipped": shipped},
        )
    return {"n": n, "skipped": skipped, "same": same, "conflicts": conflicts}


def mark(eng, mall_id: str, order_ids: list[str], status: str) -> int:
    if status not in ("shipped", "delivered"):
        raise MallError("shipped · delivered 만")
    vals = {"ship_status": status, "updated_at": now()}
    if status == "shipped":
        vals["shipped_at"] = now()
    if status == "delivered":
        vals["delivered_at"] = now()
    with eng.begin() as c:
        n = c.execute(
            update(t_order).where(and_(t_order.c.mall_id == mall_id, t_order.c.order_id.in_(order_ids))).values(**vals)
        ).rowcount
        _event(c, mall_id, status, {"n": n})
    return n


def purge(eng, at: datetime | None = None) -> int:
    """배송 완료 뒤 보존 기간이 지난 배송 정보를 지운다 (몰마다 retention_days). 매일 보존 작업이 부른다."""
    at = at or now()
    n = 0
    with eng.begin() as c:
        malls = {r["mall_id"]: r["payload"] for r in c.execute(select(t_mall.c.mall_id, t_mall.c.payload)).mappings()}
        for r in c.execute(
            select(t_order.c.order_id, t_order.c.mall_id, t_order.c.delivered_at).where(
                and_(t_order.c.ship_enc.is_not(None), t_order.c.delivered_at.is_not(None))
            )
        ).mappings():
            keep = int((malls.get(r["mall_id"]) or {}).get("retention_days") or 30)
            d = r["delivered_at"] if r["delivered_at"].tzinfo else r["delivered_at"].replace(tzinfo=KST)
            if d + timedelta(days=keep) <= at:
                c.execute(
                    update(t_order).where(t_order.c.order_id == r["order_id"]).values(ship_enc=None, purged_at=at)
                )
                n += 1
        if n:
            _event(c, None, "purged", {"n": n})
    return n


def orders(eng, mall_id: str) -> list[dict]:
    """주문 목록 — 배송 정보 없이 (번호·상품·상태). 배송 정보는 내보내기에서만."""
    with eng.connect() as c:
        rows = (
            c.execute(
                select(
                    t_order.c.order_id,
                    t_order.c.item_id,
                    t_order.c.defaulted,
                    t_order.c.ship_status,
                    t_order.c.chosen_at,
                    t_order.c.purged_at,
                    t_order.c.tracking,
                    t_order.c.ship_enc.is_not(None).label("has_ship"),
                )
                .where(t_order.c.mall_id == mall_id)
                .order_by(t_order.c.chosen_at)
            )
            .mappings()
            .all()
        )
    return [
        {
            "order_id": r["order_id"],
            "item_id": r["item_id"],
            "defaulted": bool(r["defaulted"]),
            "ship_status": r["ship_status"],
            "has_shipping": bool(r["has_ship"]),
            "purged": r["purged_at"] is not None,
            "tracking": r["tracking"],
            "chosen_at": r["chosen_at"].isoformat() if r["chosen_at"] else None,
        }
        for r in rows
    ]


def events(eng, mall_id: str, limit: int = 50) -> list[dict]:
    with eng.connect() as c:
        rows = c.execute(
            select(t_event).where(t_event.c.mall_id == mall_id).order_by(t_event.c.at.desc()).limit(limit)
        ).mappings()
        return [
            {"kind": r["kind"], "detail": r["detail"], "at": r["at"].isoformat() if r["at"] else None} for r in rows
        ]


__all__ = [
    "update_manual",
    "set_tracking",
    "ask",
    "asker",
    "orders",
    "MallError",
    "engine",
    "create_mall",
    "get_mall",
    "list_malls",
    "set_status",
    "issue_codes",
    "void_and_reissue",
    "enter",
    "choose",
    "close_mall",
    "stats",
    "export_orders",
    "mark",
    "purge",
    "events",
    "public_mall",
    "reset_limits",
    "no_address_labels",
    "link_hash",
]
