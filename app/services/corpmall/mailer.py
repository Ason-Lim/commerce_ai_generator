"""발주서 메일 (2026-11-24) — 설계 claude/b2b_po_mail_2026-11-24.md.

흐름: 발주서마다 '메일 준비' → 운영자가 받는 사람·제목·본문을 확인(고칠 수 있음) → '보내기'.
* 받는 사람: 공급 거래처의 발주 담당 메일(거래처 목록, 암호화 보관). 거래처가 '이름만'이면 준비할 수 없다.
* 정식 발주서(미확정 아님, 취소·취소 요청 아님)만 준비·보내기·.eml 이 된다. 처음 링크를 넣는 순간 발주서는 '전달됨'.
* 본문: 발주 번호·발주일·출고 기한·도착 요청일·결제 조건·품목·수량·합계(면세 따로) + **확인 링크**. 링크는 보낼 때마다 새로 만들어 넣고(옛 링크 막힘)
  원문은 저장하지 않는다(본문에는 `{ACK_LINK}` 자리 표시만).
* **배송 정보는 기본적으로 메일에 넣지 않는다.** 공급사는 확인 링크 화면에서 배송 목록 파일을 받는다(발주 뒤 30일까지, 받을 때마다 기록).
  운영자가 '첨부도 넣기'를 고르면 공급사 전달용 엑셀을 첨부한다(그 공급사 것만).
* 보내기: SMTP 설정(`MAIL_SMTP_HOST`·`MAIL_SMTP_PORT`·`MAIL_SMTP_USER`·`MAIL_SMTP_PASSWORD`·`MAIL_FROM`)이 있을 때만.
  사업자등록 뒤 회사 발신 메일을 연결하기 전에는 **.eml 파일**로 내려받아 메일 프로그램에서 열어 직접 보낸 뒤 '보냄 표시'.
* 기록: 준비·보냄·실패·.eml 내려받기(받는 사람 주소는 기록에 남기지 않음).
"""

from __future__ import annotations

import os
import secrets
import smtplib
import ssl
from email.message import EmailMessage
from email.utils import formataddr, make_msgid

from sqlalchemy import and_, select, update

from app.services.corpmall import store

ACK = "{ACK_LINK}"


def smtp_config() -> dict | None:
    host = os.getenv("MAIL_SMTP_HOST", "").strip()
    sender = os.getenv("MAIL_FROM", "").strip()
    if not host or not sender:
        return None
    return {
        "host": host,
        "port": int(os.getenv("MAIL_SMTP_PORT", "587") or 587),
        "user": os.getenv("MAIL_SMTP_USER", ""),
        "password": os.getenv("MAIL_SMTP_PASSWORD", ""),
        "sender": sender,
        "name": os.getenv("MAIL_FROM_NAME", ""),
    }


def _won(v) -> str:
    return "단가 확인 필요" if v is None else f"{v:,}원"


def compose(p: dict, orderer: str | None) -> tuple[str, str]:
    """(제목, 본문) — 본문에는 확인 링크 자리 표시."""
    who = orderer or "발주사"
    subject = f"[발주] {p['po_no']} {who} → {p['supplier']}"
    lines = [
        f"- {ln.get('name') or ln.get('item_id')}" + (f" ({ln['sku']})" if ln.get("sku") else "") + f" × {ln['qty']}"
        for ln in p["lines"]
    ]
    body = "\n".join(
        [
            f"{p['supplier']} 발주 담당자님께,",
            "",
            f"{who}에서 아래와 같이 발주드립니다.",
            "",
            f"발주 번호: {p['po_no']}",
            f"발주일: {(p['issued_at'] or '')[:10]}",
            f"출고 기한: {p.get('ship_by') or p['due_date'] or '협의'}",
            f"도착 요청일: {p.get('arrive_by') or '따로 없음'}",
            f"결제 조건: {p['payment_terms'] or '협의'}",
            "단가 기준: " + ("부가세 포함" if p["vat_mode"] == "included" else "부가세 별도"),
            "",
            "품목:",
            *lines,
            "",
            f"공급가액 {_won(p['supply_amount'])}"
            + (f"(그중 면세 {_won(p['exempt_amount'])})" if p.get("exempt_amount") else "")
            + f" · 부가세 {_won(p['vat'])} · 합계 {_won(p['total'])}",
            "",
            "아래 링크에서 수량·단가·금액·출고 기한을 확인하시고 '발주 수락'을 눌러 주세요.",
            "일부 품목이 안 되거나 기한을 바꿔야 하면 수락하지 마시고 '변경 요청'으로 알려 주세요.",
            "배송 목록 파일도 이 링크에서 받으실 수 있어요(발주일부터 30일).",
            ACK,
            "",
            "배송 정보는 이 발주의 배송에만 쓰시고, 배송이 끝나면 파기해 주세요. 링크는 다른 분과 나누지 말아 주세요.",
            "",
            "감사합니다.",
            who,
        ]
    )
    return subject, body


def prepare(eng, mall_id: str, po_no: str, *, by: str = "operator") -> dict:
    """발주서 메일 준비(초안). 같은 발주서에 보내지 않은 초안이 있으면 새로 만들지 않고 그것을 돌려준다."""
    from app.admin.b2b.proposal import load_profile
    from app.services.corpmall import podoc, suppliers

    p = podoc.get(eng, po_no)
    if p is None or p["mall_id"] != mall_id:
        raise store.MallError("없는 발주서예요")
    if p["status"] not in podoc.LIVE:
        raise store.MallError(
            "미확정·취소(요청)된 발주서는 메일을 준비할 수 없어요"
            + (" — 빈 곳: " + ", ".join(p["gaps"]) + " → 채운 뒤 '확정'" if p["status"] == "draft" else "")
        )
    if not p["supplier_id"]:
        raise store.MallError(
            "거래처 목록에 없는 공급사('이름만')라 받는 메일을 몰라요 — 공급 거래처를 먼저 연결해 주세요"
        )
    sup = suppliers.get(eng, p["supplier_id"], full=True) or {}
    to = ((sup.get("contact") or {}).get("email") or "").strip()
    if not to:
        raise store.MallError("거래처에 발주 받을 메일 주소가 없어요")
    with eng.connect() as c:
        ex = (
            c.execute(
                select(store.t_po_mail).where(
                    and_(store.t_po_mail.c.po_no == po_no, store.t_po_mail.c.status == "draft")
                )
            )
            .mappings()
            .first()
        )
    if ex:
        return _row(ex)
    subject, body = compose(p, load_profile().get("company_name"))
    mid = "ML" + secrets.token_hex(4).upper()
    with eng.begin() as c:
        c.execute(
            store.t_po_mail.insert().values(
                mail_id=mid,
                po_no=po_no,
                mall_id=mall_id,
                to_enc=store._enc({"to": to}),
                subject=subject,
                body=body,
                status="draft",
                attach=False,
                created_at=store.now(),
                by=by,
            )
        )
        store._event(c, mall_id, "po_mail_draft", {"po_no": po_no, "mail_id": mid, "by": by})
    return get(eng, mid)


def _row(r) -> dict:
    to = (store._dec(r["to_enc"]) or {}).get("to") if r["to_enc"] else None
    return {
        "mail_id": r["mail_id"],
        "po_no": r["po_no"],
        "to": to,
        "subject": r["subject"],
        "body": r["body"],
        "status": r["status"],
        "attach": bool(r["attach"]),
        "created_at": r["created_at"].isoformat() if r["created_at"] else None,
        "sent_at": r["sent_at"].isoformat() if r["sent_at"] else None,
        "error": r["error"],
    }


def get(eng, mail_id: str) -> dict | None:
    with eng.connect() as c:
        r = c.execute(select(store.t_po_mail).where(store.t_po_mail.c.mail_id == mail_id)).mappings().first()
    return _row(r) | {"mall_id": r["mall_id"]} if r else None


def list_mails(eng, mall_id: str) -> list[dict]:
    with eng.connect() as c:
        rows = (
            c.execute(
                select(store.t_po_mail)
                .where(store.t_po_mail.c.mall_id == mall_id)
                .order_by(store.t_po_mail.c.created_at.desc())
            )
            .mappings()
            .all()
        )
    return [_row(r) for r in rows]


def edit(eng, mall_id: str, mail_id: str, *, subject: str, body: str, attach: bool) -> dict:
    """보내기 전 고치기. 확인 링크 자리({ACK_LINK})는 지울 수 없다."""
    subject = " ".join((subject or "").split())[:200]
    body = (body or "")[:6000]
    if not subject:
        raise store.MallError("제목을 넣어 주세요")
    if ACK not in body:
        raise store.MallError("본문에 확인 링크 자리 {ACK_LINK} 가 있어야 해요")
    with eng.begin() as c:
        n = c.execute(
            update(store.t_po_mail)
            .where(
                and_(
                    store.t_po_mail.c.mail_id == mail_id,
                    store.t_po_mail.c.mall_id == mall_id,
                    store.t_po_mail.c.status == "draft",
                )
            )
            .values(subject=subject, body=body, attach=bool(attach))
        ).rowcount
    if not n:
        raise store.MallError("보내지 않은 메일만 고칠 수 있어요")
    return get(eng, mail_id)


def _build(eng, d: dict, *, sender: str, sender_name: str = "", base_url: str = "") -> EmailMessage:
    """보낼 메일 — 확인 링크를 새로 만들어 넣고, 고른 경우에만 그 공급사 전달용 엑셀을 첨부."""
    from app.services.corpmall import po, podoc

    p = podoc.get(eng, d["po_no"])
    if p is None or p["status"] not in podoc.LIVE:
        raise store.MallError("정식 발주서가 아니게 됐어요(미확정·취소·취소 요청) — 이 메일은 보낼 수 없어요")
    link = base_url.rstrip("/") + podoc.ack_link(eng, d["mall_id"], d["po_no"], by="mail")
    msg = EmailMessage()
    msg["Subject"] = d["subject"]
    msg["From"] = formataddr((sender_name, sender)) if sender_name else sender
    msg["To"] = d["to"]
    msg["Message-ID"] = make_msgid(domain=sender.split("@")[-1] if "@" in sender else None)
    msg.set_content(d["body"].replace(ACK, link))
    if d["attach"]:
        data, name = po.render(eng, d["mall_id"], p["batch_id"], supplier=p["supplier"], by="mail")
        msg.add_attachment(
            data, maintype="application", subtype="vnd.openxmlformats-officedocument.spreadsheetml.sheet", filename=name
        )
    return msg


def _mark(eng, d: dict, status: str, *, by: str, error: str | None = None) -> None:
    with eng.begin() as c:
        c.execute(
            update(store.t_po_mail)
            .where(store.t_po_mail.c.mail_id == d["mail_id"])
            .values(status=status, sent_at=store.now() if status in ("sent", "manual") else None, error=error)
        )
        store._event(
            c,
            d["mall_id"],
            f"po_mail_{status}",
            {"po_no": d["po_no"], "mail_id": d["mail_id"], "by": by, "attach": d["attach"]},
        )


def send(eng, mall_id: str, mail_id: str, *, base_url: str, by: str = "operator") -> dict:
    """SMTP 로 보내기 — 설정이 없으면 거부(.eml 로 직접 보내기). 실패하면 'failed' + 이유, 다시 보낼 수 있다."""
    d = get(eng, mail_id)
    if d is None or d["mall_id"] != mall_id:
        raise store.MallError("없는 메일이에요")
    if d["status"] not in ("draft", "failed"):
        raise store.MallError("이미 보낸 메일이에요")
    cfg = smtp_config()
    if cfg is None:
        raise store.MallError(
            "발신 메일이 아직 연결되지 않았어요 — '.eml 내려받기'로 메일 프로그램에서 직접 보내 주세요"
        )
    msg = _build(eng, d, sender=cfg["sender"], sender_name=cfg["name"], base_url=base_url)
    try:
        with smtplib.SMTP(cfg["host"], cfg["port"], timeout=20) as s:
            s.starttls(context=ssl.create_default_context())
            if cfg["user"]:
                s.login(cfg["user"], cfg["password"])
            s.send_message(msg)
    except (smtplib.SMTPException, OSError) as e:
        _mark(eng, d, "failed", by=by, error=type(e).__name__ + ": " + str(e)[:200])
        raise store.MallError("메일을 보내지 못했어요 — 잠시 뒤 다시 보내거나 .eml 로 직접 보내 주세요") from e
    _mark(eng, d, "sent", by=by)
    return get(eng, mail_id)


def eml(eng, mall_id: str, mail_id: str, *, base_url: str, by: str = "operator") -> tuple[bytes, str]:
    """발신 메일 연결 전: .eml 파일(확인 링크 포함)로 내려받아 메일 프로그램에서 직접 보낸다. 받을 때마다 확인 링크가 새로 바뀐다."""
    d = get(eng, mail_id)
    if d is None or d["mall_id"] != mall_id:
        raise store.MallError("없는 메일이에요")
    if d["status"] not in ("draft", "failed"):
        raise store.MallError("이미 보낸 메일이에요")
    cfg = smtp_config() or {}
    msg = _build(eng, d, sender=cfg.get("sender") or "", sender_name=cfg.get("name") or "", base_url=base_url)
    if not cfg.get("sender"):
        del msg["From"]
    msg["X-Unsent"] = "1"  # 메일 프로그램이 '보낼 메일'로 연다
    with eng.begin() as c:
        store._event(c, mall_id, "po_mail_eml", {"po_no": d["po_no"], "mail_id": mail_id, "by": by})
    return bytes(msg), f"{d['po_no']}.eml"


def mark_sent(eng, mall_id: str, mail_id: str, *, by: str = "operator") -> dict:
    """.eml 로 직접 보낸 뒤 '보냄' 표시."""
    d = get(eng, mail_id)
    if d is None or d["mall_id"] != mall_id or d["status"] not in ("draft", "failed"):
        raise store.MallError("보내지 않은 메일만 '보냄'으로 표시할 수 있어요")
    _mark(eng, d, "manual", by=by)
    return get(eng, mail_id)


__all__ = ["ACK", "smtp_config", "compose", "prepare", "get", "list_mails", "edit", "send", "eml", "mark_sent"]
