"""전화번호: 화면은 '-' 자동, DB 에는 숫자만 (2026-11-25 사용자 요청)."""

from __future__ import annotations

import os

import pytest
from cryptography.fernet import Fernet

os.environ.setdefault("CORPMALL_KEY", Fernet.generate_key().decode())

from app.services.corpmall import store as corp  # noqa: E402
from app.services.seller import store as sel  # noqa: E402


@pytest.mark.parametrize("raw, digits, shown", [
    ("010-3830-4430", "01038304430", "010-3830-4430"),
    ("01038304430", "01038304430", "010-3830-4430"),
    ("02-123-4567", "021234567", "02-123-4567"),
    ("02 1234 5678", "0212345678", "02-1234-5678"),
    ("031-123-4567", "0311234567", "031-123-4567"),
    ("1588-1234", "15881234", "1588-1234"),
    ("0505-1234-5678", "050512345678", "0505-1234-5678"),
])  # fmt: skip
def test_digits_saved_and_dashes_shown(raw, digits, shown):
    assert sel.phone_digits(raw) == digits and sel.fmt_phone(digits) == shown


@pytest.mark.parametrize("bad", ["12345", "010-12a4-5678", "0101234567890"])
def test_bad_numbers(bad):
    with pytest.raises(sel.SellerError):
        sel.phone_digits(bad)


def test_db_keeps_digits_only_and_views_format():
    corp.reset_limits()
    eng = sel.engine()
    with eng.begin() as c:
        for t in (sel.t_event, sel.t_key, sel.t_seller):
            c.execute(t.delete())
    s = sel.create_seller(eng, name="레너페인트", kind="direct",
                          contact={"name": "김", "email": "a@b.kr", "phone": "010-3830-4430"}, by="operator")  # fmt: skip
    with eng.connect() as c:
        row = c.execute(sel.t_seller.select()).mappings().first()
    assert corp._dec(row["contact_enc"])["phone"] == "01038304430"
    assert sel.detail(eng, s["seller_id"])["contact"]["phone"] == "010-3830-4430"
    assert s["contact"]["phone"] == "***-4430"
