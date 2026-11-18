"""파일 저장소 — 글 한 편 = JSON 파일 한 개 (TREND_POSTS_DIR, 기본 var/trends/posts, git 에 넣지 않음).

파일 이름은 글 id 의 해시(맥의 한글 파일 이름 정규화 차이를 피함), 글 id 는 파일 안에 둔다.
쓰기는 임시 파일에 쓴 뒤 바꿔 끼운다(쓰다 끊겨도 반쯤 쓴 글이 남지 않음).
"""
from __future__ import annotations

import hashlib
import json
import os
import unicodedata
from pathlib import Path

from app.services.trend_posts.model import Post

ROOT = Path(__file__).resolve().parents[3]


def default_dir(env=None) -> Path:
    source = os.environ if env is None else env
    raw = (source.get("TREND_POSTS_DIR") or "").strip()
    path = Path(raw).expanduser() if raw else ROOT / "var" / "trends" / "posts"
    return path if path.is_absolute() else ROOT / path


class FilePostStore:
    def __init__(self, root: Path | str | None = None):
        self.root = Path(root) if root else default_dir()

    def _path(self, post_id: str) -> Path:
        key = hashlib.sha1(unicodedata.normalize("NFC", post_id).encode()).hexdigest()[:20]
        return self.root / f"post_{key}.json"

    def get(self, post_id: str) -> Post | None:
        path = self._path(post_id)
        if not path.is_file():
            return None
        post = Post.model_validate_json(path.read_text(encoding="utf-8"))
        return post if post.id == unicodedata.normalize("NFC", post_id) else None

    def save(self, post: Post) -> Post:
        self.root.mkdir(parents=True, exist_ok=True)
        path = self._path(post.id)
        tmp = path.with_suffix(".tmp")
        tmp.write_text(json.dumps(post.model_dump(mode="json"), ensure_ascii=False, indent=1), encoding="utf-8")
        os.replace(tmp, path)
        return post

    def all(self) -> list[Post]:
        if not self.root.is_dir():
            return []
        out = []
        for path in sorted(self.root.glob("post_*.json")):
            try:
                out.append(Post.model_validate_json(path.read_text(encoding="utf-8")))
            except ValueError:
                continue                         # 깨진 파일은 건너뛴다 (공개 쪽에 나가지 않음)
        return sorted(out, key=lambda p: p.created_at, reverse=True)

    def by_status(self, *statuses: str) -> list[Post]:
        return [p for p in self.all() if not statuses or p.status in statuses]
