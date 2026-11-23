"""머리줄 겹침 (2026-11-23 사용자 PDF): 대화 중 진행 표시 '3/5 후보 비교'가 로고를 덮어 'AI 식품 추'까지만 보였다.

여러 화면 폭에서 로고 · 진행 표시 · 메뉴의 상자가 서로 겹치지 않는지 잰다.
"""
from __future__ import annotations

import threading
import time

import pytest

pw = pytest.importorskip("playwright.sync_api")

from tests.e2e.test_site_browser import DIST, _free_port  # noqa: E402

BOX_JS = """() => {
  const r = (el) => el && el.getBoundingClientRect();
  const head = document.querySelector('header');
  const logo = r([...head.querySelectorAll('a')].find(a => a.textContent.includes('AI 식품 추천')));
  const step = r(head.querySelector('[aria-label^="진행 단계"]'));
  const right = r(head.querySelector('nav[aria-label="주요 메뉴"]') || head.querySelector('button'));
  const logoText = [...head.querySelectorAll('a span')].find(s => s.textContent === 'AI 식품 추천');
  return {logo: logo && [logo.left, logo.right], step: step && [step.left, step.right],
          right: right && [right.left, right.right], logoVisible: !!(logoText && logoText.offsetWidth),
          clipped: logoText ? logoText.scrollWidth > logoText.clientWidth + 1 : null};
}"""


@pytest.fixture(scope="module")
def site():
    if not (DIST / "index.html").is_file():
        pytest.skip("화면 빌드(frontend/dist)가 없어요 — npm --prefix frontend run build")
    import uvicorn
    from fastapi import FastAPI

    from app.web_frontend import mount_frontend

    app = FastAPI()

    @app.get("/api/trend-examples")
    def _examples():
        return {"items": []}

    mount_frontend(app, DIST)
    port = _free_port()
    server = uvicorn.Server(uvicorn.Config(app, host="127.0.0.1", port=port, log_level="warning"))
    th = threading.Thread(target=server.run, daemon=True)
    th.start()
    for _ in range(100):
        if server.started:
            break
        time.sleep(0.05)
    yield f"http://127.0.0.1:{port}"
    server.should_exit = True
    th.join(timeout=5)


@pytest.fixture(scope="module")
def browser():
    with pw.sync_playwright() as p:
        try:
            b = p.chromium.launch()
        except Exception as e:  # noqa: BLE001
            pytest.skip(f"Chromium 을 띄우지 못했어요 ({type(e).__name__})")
        yield b
        b.close()


@pytest.mark.parametrize("width", [1280, 1024, 900, 820, 768, 700, 640])
def test_stepper_never_covers_logo_or_menu(site, browser, width):
    ctx = browser.new_context(viewport={"width": width, "height": 800}, locale="ko-KR")
    page = ctx.new_page()
    page.route("**/api/chat", lambda route: route.fulfill(status=200, content_type="application/json",
               body='{"session_id":"s","stage":"shopping","blocks":[{"type":"text","data":{"text":"좋아요"}}]}'))
    page.goto(site + "/#")
    page.get_by_label("쇼핑 질문").fill("사과추천해줘")
    page.keyboard.press("Enter")
    page.get_by_text("좋아요").wait_for()
    page.locator('header [aria-label^="진행 단계 3/5"]').wait_for()
    box = page.evaluate(BOX_JS)
    assert box["step"] and box["logo"]
    if box["logoVisible"]:
        assert box["logo"][1] <= box["step"][0] + 0.5, box            # 로고 오른쪽 끝 ≤ 진행 표시 왼쪽
        assert box["clipped"] is False, box
    if box["right"] and box["right"][0] > box["step"][0]:
        assert box["step"][1] <= box["right"][0] + 0.5, box           # 진행 표시 오른쪽 끝 ≤ 메뉴 왼쪽
    ctx.close()
