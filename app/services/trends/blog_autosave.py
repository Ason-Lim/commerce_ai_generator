"""블로그 초안 승인 → 네이버 블로그(applesodda) 자동 임시저장 (2026-11-20).

관리자가 '확인 완료 → 네이버 임시저장'을 누르면:
  1) 승인 전 검사(check) — 하나라도 걸리면 시작하지 않는다.
  2) (선택) gpt-image 로 보조 그림 1장 — naver_blog_mcp 의 image_worker. 캡션 앞에 'AI로 만든 그림' 자동.
  3) naver_blog_mcp 의 post_worker 로 **임시저장만** (publish=False 고정). 발행은 사람이 블로그에서 직접.
같은 맥에서 돈다 — 앱 서버(8001)가 naver_blog_mcp 폴더의 가상환경 파이썬으로 워커를 띄운다.
결과는 초안 파일 옆 `<초안 이름>.approval.json` 에 남는다 (승인 시각·그림 여부·상태·메시지).

.env
  BLOG_AUTODRAFT=1            켜야 동작 (기본 꺼짐)
  NAVER_BLOG_MCP_DIR          기본 ~/naver_blog_mcp
  NAVER_BLOG_ID               기본 applesodda
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import threading
import uuid
from collections.abc import Callable
from datetime import datetime, timezone
from pathlib import Path

PLACEHOLDER = "▶ [여기에"
IMAGE_MARK = "[[이미지1]]"
IMAGE_CAPTION_KW = "관련 일러스트"
_LOCK = threading.Lock()
_RUNNING: set[str] = set()


def enabled(env=None) -> bool:
    return ((env if env is not None else os.environ).get("BLOG_AUTODRAFT") or "0").strip() == "1"


def mcp_dir(env=None) -> Path:
    src = env if env is not None else os.environ
    return Path(src.get("NAVER_BLOG_MCP_DIR") or (Path.home() / "naver_blog_mcp")).expanduser()


def mcp_python(env=None) -> Path:
    return mcp_dir(env) / ".venv" / "bin" / "python"


def approval_path(draft_path: Path) -> Path:
    return draft_path.with_name(draft_path.name[:-len(".txt")] + ".approval.json")


def read_approval(draft_path: Path) -> dict | None:
    p = approval_path(draft_path)
    try:
        return json.loads(p.read_text(encoding="utf-8")) if p.is_file() else None
    except (OSError, ValueError):
        return None


def _write(draft_path: Path, data: dict) -> dict:
    data = {**data, "updated_at": datetime.now(timezone.utc).isoformat(timespec="seconds")}
    approval_path(draft_path).write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
    return data


# ── 승인 전 검사 (프레임 0.4 + 기존 경고) ─────────────────────────────────
def check(variant: str, title: str, body: str, warnings: list[str], coupang_disclosure: str,
          connect_disclosure_mark: str = "쇼핑 커넥트 활동") -> list[str]:
    issues = []
    for w in warnings:
        # 네이버 블로그용의 쇼핑커넥트 삽입 자리는 임시저장 글에서 사람이 스마트에디터로 상품을 넣는 자리 — 막지 않는다
        if variant == "naver" and "삽입 자리" in w:
            continue
        issues.append(w)
    if not title.strip() or not body.strip():
        issues.append("제목과 본문이 있어야 해요.")
    ad = coupang_disclosure in body or connect_disclosure_mark in body
    if ad and not title.lstrip().startswith("[광고]"):
        issues.append("광고 고지가 있는 글은 제목 맨 앞에 [광고]를 붙여 주세요.")
    if ad:
        first = body.lstrip().split("\n", 1)[0]
        if coupang_disclosure not in first and connect_disclosure_mark not in first:
            issues.append("광고 고지는 본문 첫 줄에 있어야 해요 (상품 링크보다 먼저).")
    # 55종 템플릿 '작성 완료 확인': [입력]·[상품] 같은 빈칸이 남지 않았는가 ([광고]·[트렌드 리포트]·[[이미지1]]·쇼핑커넥트 자리 제외)
    # 2026-11-20 실제 초안 검증: 링크가 있는 줄(쿠팡 상품명 '[로켓프레시] …: https://…')의 대괄호는 상품명이라 빈칸이 아니다
    text = "\n".join(ln for ln in (title + "\n" + body).split("\n") if "http://" not in ln and "https://" not in ln)
    left = [m for m in re.findall(r"(?<!\[)\[([^\[\]\n]{1,20})\](?!\])", text)
            if m not in ("광고", "트렌드 리포트") and not m.startswith("여기에")]
    if left:
        issues.append("채우지 않은 빈칸이 있어요: " + ", ".join(f"[{m}]" for m in left[:5]))
    if variant == "coupang" and re.search(r"내돈내산|직접\s*(?:먹어|써|사용해)\s*봤", body):
        issues.append("직접 사용 기록이 없는 글에 사용 후기 표현이 있어요.")
    return issues


def with_image_mark(body: str) -> str:
    """그림 자리: '먼저 답부터' 문단 뒤(없으면 고지 문단 뒤). 이미 표시가 있으면 그대로."""
    if IMAGE_MARK in body:
        return body
    blocks = body.split("\n\n")
    at = next((i + 1 for i, b in enumerate(blocks) if b.startswith("먼저 답부터")), 1 if len(blocks) > 1 else len(blocks))
    return "\n\n".join(blocks[:at] + [IMAGE_MARK] + blocks[at:])


def image_prompt(keywords: list[str]) -> str:
    names = ", ".join(keywords[:3])
    # 2026-11-20: 키워드가 상품·브랜드 이름이어도 상표가 그려지지 않게
    return (f"A warm, friendly illustration of Korean food ingredients for a shopping guide blog: {names}. "
            "Draw generic, unbranded food on a simple kitchen table. No text, no letters, no logos, "
            "no brand packaging, no real product designs. Soft natural colors.")


SELLER_IMAGE_MAX = 5 * 1024 * 1024


def download_seller_image(url: str, dest_dir: Path, name: str, opener=None) -> Path | None:
    """대표 그림용 쿠팡 상품 사진 받기 (2026-11-20). 쿠팡 https 사진 주소만, 5MB 이하, jpg/png/webp. 실패하면 None."""
    from urllib.request import Request, urlopen

    from app.services.trend_posts import policy

    if not url or not policy.coupang_image(url):
        return None
    ext = {"image/jpeg": ".jpg", "image/png": ".png", "image/webp": ".webp"}
    try:
        req = Request(url, headers={"User-Agent": "Mozilla/5.0 (commerce_ai blog cover)"})
        with (opener or urlopen)(req, timeout=20) as res:
            kind = (res.headers.get("Content-Type") or "").split(";")[0].strip().lower()
            data = res.read(SELLER_IMAGE_MAX + 1)
        if kind not in ext or len(data) > SELLER_IMAGE_MAX or not data:
            return None
        dest_dir.mkdir(parents=True, exist_ok=True)
        out = dest_dir / (re.sub(r"[^0-9A-Za-z가-힣_-]+", "_", name)[:80] + ext[kind])
        out.write_bytes(data)
        return out
    except Exception:  # noqa: BLE001 — 사진이 없어도 글은 임시저장한다
        return None


# ── 실행 ───────────────────────────────────────────────────────────────
Runner = Callable[[list[str], Path], dict]


def _run_worker(module: str, payload: dict, env=None, timeout: int = 420) -> dict:
    jobs = mcp_dir(env).joinpath("jobs_app")
    jobs.mkdir(parents=True, exist_ok=True)
    job = uuid.uuid4().hex[:12]
    inp, out = jobs / f"{job}.in.json", jobs / f"{job}.out.json"
    inp.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    try:
        subprocess.run([str(mcp_python(env)), "-m", module, str(inp), str(out)], cwd=str(mcp_dir(env)),
                       timeout=timeout, check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except subprocess.TimeoutExpired:
        return {"status": "error", "message": f"작업 시간이 {timeout}초를 넘었어요."}
    try:
        return json.loads(out.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {"status": "error", "message": "작업 결과 파일이 없어요 (워커가 시작되지 않았을 수 있어요)."}


def start(draft_path: Path, *, variant: str, title: str, tags: list[str], body: str, keywords: list[str],
          with_image: bool, env=None, worker: Callable[[str, dict], dict] | None = None,
          background: bool = True, cover: dict | None = None,
          fetch_image: Callable[[str, Path, str], Path | None] | None = None, extra: dict | None = None) -> dict:
    """승인 기록을 남기고 임시저장 작업을 시작한다. 같은 초안이 이미 진행 중이면 그 기록을 돌려준다.
    2026-11-20 대표 그림(cover, 초안 만들 때 정함): {'kind': 'ai'} = 보류 글 → AI 그림,
    {'kind': 'seller', 'url', 'caption'} = 구매 글 → 쿠팡 상품 사진(판매처 이미지). with_image=True 면 늘 AI 그림.
    사진을 못 받으면 그림 없이 임시저장하고 기록에 남긴다."""
    cover = cover or {}
    use_ai = with_image or cover.get("kind") == "ai"
    use_seller = not use_ai and cover.get("kind") == "seller" and bool(cover.get("url"))
    key = str(draft_path)
    with _LOCK:
        if key in _RUNNING:
            return read_approval(draft_path) or {"status": "running"}
        _RUNNING.add(key)
    src = env if env is not None else os.environ
    run = worker or (lambda module, payload: _run_worker(module, payload, src))
    rec = _write(draft_path, {"file": draft_path.name, "variant": variant, "approved_at":
                              datetime.now(timezone.utc).isoformat(timespec="seconds"),
                              "with_image": use_ai, "cover": "ai" if use_ai else ("seller" if use_seller else None),
                              "status": "running", "step": "그림 만들기" if use_ai else
                              ("상품 사진 받기" if use_seller else "네이버 임시저장"), "message": "",
                              **(extra or {})})   # 2026-11-21 승인 때 남길 것 (제목 유사도·확인 여부)

    def work():
        try:
            images, content, note = [], body, ""
            if use_seller:
                got = (fetch_image or (lambda u, d, n: download_seller_image(u, d, n)))(
                    cover["url"], draft_path.parent.parent / "blog_images", draft_path.name[:-len(".txt")])
                if got:
                    images = [{"path": str(got), "source": "seller",
                               "caption": cover.get("caption") or "쿠팡 상품 사진 (판매처 이미지)"}]
                    content = with_image_mark(body)
                else:
                    note = "상품 사진을 받지 못해 그림 없이 저장했어요. "
                _write(draft_path, {**rec, "step": "네이버 임시저장", **({"image_path": str(got)} if got else {})})
            if use_ai:
                res = run("naver_blog_mcp.image_worker", {"prompt": image_prompt(keywords), "name": "blog_" + "_".join(keywords[:2]),
                                                          "size": "1536x1024", "quality": "medium"})
                if res.get("status") != "done":
                    _write(draft_path, {**rec, "status": "error", "step": "그림 만들기",
                                        "message": res.get("message") or "그림을 만들지 못했어요."})
                    return
                images = [{"path": res["image_path"], "source": "ai",
                           "caption": f"{', '.join(keywords[:2])} {IMAGE_CAPTION_KW}"}]
                content = with_image_mark(body)
                _write(draft_path, {**rec, "step": "네이버 임시저장", "image_path": res["image_path"]})
            res = run("naver_blog_mcp.post_worker", {
                "blog_id": (src.get("NAVER_BLOG_ID") or "applesodda").strip(), "title": title, "content": content,
                "tags": tags[:10], "category": "", "publish": False, "images": images})
            ok = res.get("status") == "done"
            _write(draft_path, {**rec, "status": "done" if ok else "error", "step": "끝" if ok else "네이버 임시저장",
                                "message": note + (res.get("message") or ""),
                                **({"image_path": images[0]["path"]} if images else {})})
        except Exception as exc:  # noqa: BLE001 — 기록만 남기고 앱은 계속
            _write(draft_path, {**rec, "status": "error", "message": f"{type(exc).__name__}: {str(exc)[:200]}"})
        finally:
            with _LOCK:
                _RUNNING.discard(key)

    if background:
        threading.Thread(target=work, daemon=True, name="blog-autosave").start()
    else:
        work()
    return read_approval(draft_path) or rec
