"""트렌드 글 대표 그림 (2026-11-20 사용자 결정 '트렌드 글에도 이미지').

* 구매 글: 따로 만들지 않는다 — render.cover 가 상품 비교의 첫 쿠팡 사진을 대표로 그린다 (비용 없음).
* 보류 글: 상품 사진은 구매를 이끌어 쓰지 않고, gpt-image 그림 1장 (유료). 브랜드·로고·글자·포장 없이 일반 식재료 그림,
  캡션 'AI로 만든 그림 · 실제 상품 사진이 아니에요'. 결론을 보류로 바꿀 때 한 번 자동으로, 관리자 '그림 다시'로 다시.
같은 맥에서 돈다 — 블로그 자동 임시저장과 같은 naver_blog_mcp image_worker 를 쓴다 (.env OPENAI 키는 그쪽).
.env TREND_AI_COVER=0 이면 끈다.
"""

from __future__ import annotations

import os
import shutil
import threading
from collections.abc import Callable
from pathlib import Path

from app.services.trend_posts.model import HistoryEntry, PostImage, now_iso

_LOCK = threading.Lock()
_RUNNING: set[str] = set()


def image_dir() -> Path:
    from app.services.trends.surge import ROOT

    return ROOT / "var" / "trend_images"


def enabled(env=None) -> bool:
    from app.services.trends import blog_autosave as bas

    src = env if env is not None else os.environ
    return (src.get("TREND_AI_COVER") or "1").strip() != "0" and bas.mcp_python(src).is_file()


def prompt(topic: str) -> str:
    """브랜드·상표가 그려지지 않게 — 키워드가 상품명이어도 '이런 종류의 음식'의 일반 그림."""
    return (
        f"A warm, friendly illustration for a Korean food trend article about '{topic}'. "
        "Draw a generic, unbranded example of this kind of food on a simple kitchen table. "
        "No text, no letters, no logos, no brand packaging, no real product designs. Soft natural colors."
    )


def start(
    svc, post_id: str, *, env=None, run: Callable[[str, dict], dict] | None = None, background: bool = True
) -> bool:
    """보류 글의 AI 대표 그림 만들기. 시작했으면 True (이미 진행 중이거나 꺼져 있으면 False)."""
    from app.services.trends import blog_autosave as bas

    src = env if env is not None else os.environ
    if run is None and not enabled(src):
        return False
    with _LOCK:
        if post_id in _RUNNING:
            return False
        _RUNNING.add(post_id)
    runner = run or (lambda module, payload: bas._run_worker(module, payload, src, timeout=300))

    def work():
        try:
            post = svc.get(post_id)
            res = runner(
                "naver_blog_mcp.image_worker",
                {"prompt": prompt(post.topic), "name": "trend_" + post.id, "size": "1536x1024", "quality": "medium"},
            )
            post = svc.get(post_id)  # 그사이 바뀌었을 수 있어 다시 읽는다
            stamp = now_iso(svc.clock())
            if res.get("status") != "done" or not res.get("image_path"):
                note = "AI 대표 그림 실패: " + str(res.get("message") or "알 수 없음")[:150]
                svc.store.save(
                    post.model_copy(
                        update={"history": post.history + [HistoryEntry(at=stamp, action="cover", note=note)]}
                    )
                )
                return
            if post.conclusion != "hold":  # 그사이 구매 글로 바뀌었으면 붙이지 않는다
                return
            folder = image_dir()
            folder.mkdir(parents=True, exist_ok=True)
            n = sum(1 for f in folder.glob(post.id + "*") if f.suffix in (".png", ".webp"))
            stem = post.id if n == 0 else f"{post.id}-{n + 1}"
            name = save_image(Path(res["image_path"]), folder, stem)
            svc.store.save(
                post.model_copy(
                    update={
                        "cover": PostImage(file=name, created_at=stamp),
                        "history": post.history + [HistoryEntry(at=stamp, action="cover", note=f"AI 대표 그림 {name}")],
                    }
                )
            )
        except Exception:  # noqa: BLE001 — 그림이 없어도 글은 그대로
            pass
        finally:
            with _LOCK:
                _RUNNING.discard(post_id)

    if background:
        threading.Thread(target=work, daemon=True, name="trend-cover").start()
    else:
        work()
    return True


MAX_WIDTH = 1024


def save_image(src: Path, folder: Path, stem: str) -> str:
    """2026-11-21 report v1.1: 1536px PNG(약 2MB) 그대로 두지 않고 폭 1024 WebP 로 줄여 저장 (보통 100KB 안팎).
    Pillow 가 없거나 변환이 실패하면 원본 PNG 를 그대로 복사한다. 저장한 파일 이름을 돌려준다."""
    try:
        from PIL import Image

        with Image.open(src) as im:
            im = im.convert("RGB")
            if im.width > MAX_WIDTH:
                im = im.resize((MAX_WIDTH, round(im.height * MAX_WIDTH / im.width)), Image.LANCZOS)
            name = stem + ".webp"
            im.save(folder / name, "WEBP", quality=82, method=6)
            return name
    except Exception:  # noqa: BLE001 — 줄이지 못해도 그림은 붙인다
        name = stem + ".png"
        shutil.copyfile(src, folder / name)
        return name


def running(post_id: str) -> bool:
    return post_id in _RUNNING
