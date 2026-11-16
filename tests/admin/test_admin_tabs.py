"""관리자 화면 어디서든 위쪽 탭 5개(운영·트렌드·근거·AI·B2B)가 똑같이 보여야 한다."""
import re
from pathlib import Path

PAGES = sorted(Path("app/admin").rglob("*.html"))
TABS = ["/admin", "/admin/trends", "/admin/evidence", "/admin/ai", "/admin/b2b"]


def test_every_admin_page_has_all_top_tabs():
    seen = 0
    for p in PAGES:
        m = re.search(r'<nav class="tabs-top"[^>]*>(.*?)</nav>', p.read_text(encoding="utf-8"), re.S)
        if not m:
            continue
        seen += 1
        assert re.findall(r'href="([^"]+)"', m.group(1)) == TABS, p
    assert seen >= 8
