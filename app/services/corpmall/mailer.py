"""발주서 메일 (2026-11-24, 검토 반영) — 설계 claude/b2b_po_mail_2026-11-24.md.

흐름: 발주서마다 '메일 준비' → 운영자가 받는 사람·제목·본문을 확인(고칠 수 있음) → '보내기'(SMTP) 또는 '.eml'.
* 받는 사람: 공급 거래처의 발주 담당 메일(암호화 보관). 거래처가 '이름만'이면 준비할 수 없다.
* **정식 발주·수락 상태만**(미확정·변경 요청·취소 요청·취소는 안 됨 — 변경 요청 중 기존 조건을 다시 보내면 확정된 발주로 오해).
* 본문의 `{ACK_LINK}` 에는 그 판의 **같은 확인 링크**를 넣는다. 재발송·.eml 재다운로드로 공급사가 받은 링크가 끊기지 않는다.
  새 링크는 운영자가 '링크 재발급'을 따로 눌렀을 때만.
* 상태: draft → sending → sent(SMTP 접수 완료) / failed(안 간 게 확실) / unknown(결과 불명) · manual(직접 발송 확인).
  - 연결·로그인 단계 실패, 서버가 받는 사람·보내는 사람·본문을 명시적으로 거부 → failed(다시 보낼 수 있음).
  - 본문을 넘기는 중 연결이 끊김·시간 초과 → **unknown**: 실제로 갔을 수 있어 **자동·버튼 재발송을 막는다**.
    운영자가 공급사에 확인하고 '보냄으로 확인' 또는 '안 감 확인(다시 보낼 수 있게)'으로 정리.
  - 'sending' 이 남아 있으면(처리 중 서버 중단 등) 역시 재발송 막음 — 같은 정리 절차.
* 발주서 기록에는 '전달 가능(취소 잠금)'과 따로 실제 사건(SMTP 접수 완료·결과 불명·직접 발송 확인·.eml 내려받기)을 남긴다.
* **배송 정보는 기본적으로 메일에 넣지 않는다.** 공급사는 확인 링크 화면에서 그 공급사 배송 목록만 받는다(정식 발주이고 배송 정보가
  남아 있는 동안). 운영자가 '첨부도 넣기'를 고르면 그 공급사 전달용 엑셀을 첨부한다.
* SMTP 설정(`MAIL_SMTP_HOST`·`MAIL_SMTP_PORT`·`MAIL_SMTP_USER`·`MAIL_SMTP_PASSWORD`·`MAIL_FROM`)이 없으면 .eml 로 직접.
* 기록: 받는 사람 주소는 남기지 않는다.
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
            "배송 목록 파일도 이 링크에서 받으실 수 있어요(배송 정보는 이 발주의 배송에만 쓰고 끝나면 파기해 주세요).",
            ACK,
            "",
            "배송 정보는 이 발주의 배송에만 쓰시고, 배송이 끝나면 파기해 주세요. 링크는 다른 분과 나누지 말아 주세요.",
            "",
            "감사합니다.",
            who,
        ]
    )
    return subject, body


def _check_po(p: dict | None) -> None:
    from app.services.corpmall import podoc

    if p is None:
        raise store.MallError("없는 발주서예요")
    if p["status"] == "change_requested":
        raise store.MallError(
            "공급사 변경 요청을 먼저 처리해 주세요 — 검토 끝 수락 표시, 또는 취소 후 바뀐 조건으로 다시 발주"
        )
    if p["status"] not in podoc.MAILABLE:
        raise store.MallError(
            "미확정·취소(요청)된 발주서는 메일을 보낼 수 없어요"
            + (" — 빈 곳: " + ", ".join(p["gaps"]) + " → 채운 뒤 '확정'" if p["status"] == "draft" else "")
        )


def prepare(eng, mall_id: str, po_no: str, *, by: str = "operator") -> dict:
    """발주서 메일 준비(초안). 같은 발주서에 아직 안 보냈거나 결과를 모르는 메일이 있으면 새로 만들지 않고 그것을 돌려준다
    (결과 불명 메일을 두고 새 메일로 다시 보내는 것을 막음)."""
    from app.admin.b2b.proposal import load_profile
    from app.services.corpmall import podoc, suppliers

    p = podoc.get(eng, po_no)
    if p is None or p["mall_id"] != mall_id:
        raise store.MallError("없는 발주서예요")
    _check_po(p)
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
                    and_(
                        store.t_po_mail.c.po_no == po_no,
                        store.t_po_mail.c.status.in_(("draft", "failed", "sending", "unknown")),
                    )
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
                    store.t_po_mail.c.status.in_(OPEN),
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
    _check_po(p)
    link = base_url.rstrip("/") + podoc.ack_link(eng, d["mall_id"], d["po_no"], by="mail")  # 같은 판이면 같은 링크
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


OPEN = ("draft", "failed")  # 보낼 수 있는 상태
STUCK = ("sending", "unknown")  # 결과를 모름 — 운영자가 정리하기 전엔 재발송 금지


def _mark(eng, d: dict, status: str, *, by: str, error: str | None = None, po_what: str | None = None) -> None:
    from app.services.corpmall import podoc

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
    if po_what:
        podoc.record_send(eng, d["mall_id"], d["po_no"], po_what, by=by)


def _claim(eng, d: dict) -> None:
    """draft·failed → sending (한 번에 하나만 — 두 번 눌러도 한 통)."""
    with eng.begin() as c:
        n = c.execute(
            update(store.t_po_mail)
            .where(and_(store.t_po_mail.c.mail_id == d["mail_id"], store.t_po_mail.c.status.in_(OPEN)))
            .values(status="sending", error=None)
        ).rowcount
    if not n:
        raise store.MallError("이미 보내는 중이거나 보낸 메일이에요")


def _load_open(eng, mall_id: str, mail_id: str) -> dict:
    d = get(eng, mail_id)
    if d is None or d["mall_id"] != mall_id:
        raise store.MallError("없는 메일이에요")
    if d["status"] in STUCK:
        raise store.MallError(
            "보낸 결과를 모르는 메일이에요 — 공급사에 받았는지 확인한 뒤 '보냄으로 확인' 또는 '안 감 확인'을 눌러 주세요"
        )
    if d["status"] not in OPEN:
        raise store.MallError("이미 보낸 메일이에요")
    return d


def send(eng, mall_id: str, mail_id: str, *, base_url: str, by: str = "operator") -> dict:
    """SMTP 로 보내기. 실패가 확실하면 failed(다시 보낼 수 있음), 갔을 수도 있으면 unknown(재발송 막음)."""
    d = _load_open(eng, mall_id, mail_id)
    cfg = smtp_config()
    if cfg is None:
        raise store.MallError(
            "발신 메일이 아직 연결되지 않았어요 — '.eml 내려받기'로 메일 프로그램에서 직접 보내 주세요"
        )
    msg = _build(eng, d, sender=cfg["sender"], sender_name=cfg["name"], base_url=base_url)
    _claim(eng, d)
    stage = "connect"
    try:
        s = smtplib.SMTP(cfg["host"], cfg["port"], timeout=20)
        try:
            s.starttls(context=ssl.create_default_context())
            if cfg["user"]:
                s.login(cfg["user"], cfg["password"])
            stage = "data"
            s.send_message(msg)
            stage = "done"
        finally:
            try:
                s.quit()
            except smtplib.SMTPException, OSError:
                pass  # 접수 뒤 종료 오류는 결과와 무관
    except (smtplib.SMTPRecipientsRefused, smtplib.SMTPSenderRefused, smtplib.SMTPDataError) as e:
        _mark(eng, d, "failed", by=by, error=type(e).__name__ + ": " + str(e)[:200])  # 서버가 명시적으로 거부
        raise store.MallError("메일 서버가 받지 않았어요(주소·내용 거부) — 확인 뒤 다시 보내 주세요") from e
    except (smtplib.SMTPException, OSError) as e:
        why = type(e).__name__ + ": " + str(e)[:200]
        if stage == "data":
            _mark(eng, d, "unknown", by=by, error=why, po_what="smtp_unknown")
            raise store.MallError(
                "보내는 중 연결이 끊겨 실제로 갔는지 몰라요 — 다시 보내지 말고 공급사에 받았는지 확인해 주세요"
            ) from e
        _mark(eng, d, "failed", by=by, error=why)
        raise store.MallError("메일 서버에 연결하지 못했어요 — 잠시 뒤 다시 보내거나 .eml 로 직접 보내 주세요") from e
    _mark(eng, d, "sent", by=by, po_what="smtp_accepted")
    return get(eng, mail_id)


def eml(eng, mall_id: str, mail_id: str, *, base_url: str, by: str = "operator") -> tuple[bytes, str]:
    """발신 메일 연결 전: .eml 파일로 내려받아 메일 프로그램에서 직접 보낸다. 같은 판이면 확인 링크도 같다(다시 받아도 안 끊김)."""
    d = _load_open(eng, mall_id, mail_id)
    cfg = smtp_config() or {}
    msg = _build(eng, d, sender=cfg.get("sender") or "", sender_name=cfg.get("name") or "", base_url=base_url)
    if not cfg.get("sender"):
        del msg["From"]
    msg["X-Unsent"] = "1"  # 메일 프로그램이 '보낼 메일'로 연다
    with eng.begin() as c:
        store._event(c, mall_id, "po_mail_eml", {"po_no": d["po_no"], "mail_id": mail_id, "by": by})
    from app.services.corpmall import podoc

    podoc.record_send(eng, mall_id, d["po_no"], "eml_downloaded", by=by)
    return bytes(msg), f"{d['po_no']}.eml"


def mark_sent(eng, mall_id: str, mail_id: str, *, by: str = "operator") -> dict:
    """.eml 로 직접 보낸 뒤, 또는 결과 불명 메일을 공급사가 받았다고 확인한 뒤 '직접 발송 확인'."""
    d = get(eng, mail_id)
    if d is None or d["mall_id"] != mall_id or d["status"] not in (*OPEN, *STUCK):
        raise store.MallError("보내지 않았거나 결과를 모르는 메일만 '보냄'으로 표시할 수 있어요")
    _mark(eng, d, "manual", by=by, po_what="manual_sent")
    return get(eng, mail_id)


def mark_not_sent(eng, mall_id: str, mail_id: str, *, by: str, note: str) -> dict:
    """결과 불명·보내는 중으로 남은 메일을 '안 감'으로 정리(공급사가 못 받았다고 확인) — 근거 메모 필수, 다시 보낼 수 있게."""
    note = " ".join((note or "").split())[:200]
    if not note:
        raise store.MallError("공급사가 못 받았다는 걸 어떻게 확인했는지 적어 주세요")
    d = get(eng, mail_id)
    if d is None or d["mall_id"] != mall_id or d["status"] not in STUCK:
        raise store.MallError("결과를 모르는 메일만 정리할 수 있어요")
    _mark(eng, d, "failed", by=by, error=f"안 감 확인: {note}")
    return get(eng, mail_id)


__all__ = [
    "ACK",
    "OPEN",
    "STUCK",
    "smtp_config",
    "compose",
    "prepare",
    "get",
    "list_mails",
    "edit",
    "send",
    "eml",
    "mark_sent",
    "mark_not_sent",
]
