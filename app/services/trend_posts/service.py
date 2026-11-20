"""트렌드 글 상태 바꾸기.  사람(운영자)만 승인한다 — 자동 게시 없음.

  초안 draft ──검토 요청 submit──▶ 검토 대기 pending ──승인 approve(정책 검사 통과 시)──▶ 게시됨 approved
     ▲  고치기 update · 가격 다시 확인 refresh      └──반려 reject(사유 필수)──▶ 반려 rejected ──고치기──▶ 초안
     └──────────────────────────── 내림 withdraw (게시됨 → 내림, 다시 고쳐 검토 요청 가능) ◀─────────┘
같은 주제 글이 최근 30일 안에 있으면 새로 만들지 않고 그 글을 돌려준다(게시 중이면 내림 후 갱신하도록 안내).
"""
from __future__ import annotations

from collections.abc import Callable
from datetime import datetime, timedelta, timezone

from app.services.trend_posts import draft, policy
from app.services.trend_posts.model import EDITABLE, VALID_ID, HistoryEntry, Post, now_iso, parse_time
from app.services.trend_posts.store import FilePostStore


class PostError(ValueError):
    def __init__(self, message: str, code: str = "bad_request", issues: list | None = None):
        super().__init__(message)
        self.code, self.issues = code, issues or []


EDIT_FIELDS = {"title", "summary", "why", "price_note", "products", "recipe",
               "question", "answer", "criteria", "constraints", "checklist"}   # 2026-11-20 프레임 0.4 칸


class TrendPosts:
    def __init__(self, store: FilePostStore | None = None, clock: Callable[[], datetime] | None = None):
        self.store = store or FilePostStore()
        self.clock = clock or (lambda: datetime.now(timezone.utc))

    # ── 읽기 ──
    def get(self, post_id: str) -> Post:
        post = self.store.get(post_id) if VALID_ID.match(post_id or "") else None
        if post is None:
            raise PostError("글을 찾을 수 없어요.", "not_found")
        return post

    def public(self, post_id: str) -> Post | None:
        """공개 쪽은 이 함수만 쓴다 — 승인된 글이 아니면 None."""
        post = self.store.get(post_id) if VALID_ID.match(post_id or "") else None
        return post if post is not None and post.status == "approved" else None

    def published(self) -> list[Post]:
        return sorted(self.store.by_status("approved"), key=lambda p: p.approved_at or "", reverse=True)

    def check(self, post: Post) -> list[dict]:
        return policy.check(post, self.store.all(), self.clock())

    # ── 만들기 ──
    def recent_same_topic(self, topic: str, days: int = policy.DUPLICATE_DAYS) -> Post | None:
        now = self.clock()
        for p in self.store.all():
            t = parse_time(p.created_at)
            if p.topic == topic and p.status != "withdrawn" and t and now - t <= timedelta(days=days):
                return p
        return None

    def create_from_surge(self, report: dict, keyword: str, *, find_products: Callable[[str], dict] | None = None,
                          find_recipe: Callable[[str], dict] | None = None) -> tuple[Post, bool]:
        """(글, 새로 만들었는지).  리포트에 없는 단어는 만들지 않는다."""
        item = next((it for it in report.get("items") or [] if it.get("keyword") == keyword), None)
        if item is None:
            raise PostError("리포트에 없는 단어예요.", "not_in_report")
        same = self.recent_same_topic(keyword)
        if same is not None:
            return same, False
        now = self.clock()
        products = draft.products_from_result(find_products(keyword), now, keyword) if find_products else []
        recipe = draft.recipe_from_result(find_recipe(keyword), keyword) if find_recipe else None
        post = draft.build(item, report.get("data_until"), products=products, recipe=recipe, now=now,
                           sources=_used_sources(report))
        if self.store.get(post.id) is not None:                 # 같은 날짜·주제 id (내린 글) → 덮어쓰지 않음
            raise PostError(f"같은 주소의 글({post.id})이 이미 있어요. 그 글을 고쳐 다시 검토 요청해 주세요.", "exists")
        return self.store.save(post), True

    # ── 고치기 ──
    def _log(self, post: Post, action: str, note: str | None = None) -> Post:
        stamp = now_iso(self.clock())
        return post.model_copy(update={"updated_at": stamp,
                                       "history": post.history + [HistoryEntry(at=stamp, action=action, note=note)]})

    def update(self, post_id: str, fields: dict) -> Post:
        post = self.get(post_id)
        if post.status not in EDITABLE:
            raise PostError("초안·반려 글만 고칠 수 있어요 (게시된 글은 내린 뒤 고쳐요).", "not_editable")
        unknown = set(fields) - EDIT_FIELDS
        if unknown:
            raise PostError(f"고칠 수 없는 칸이에요: {', '.join(sorted(unknown))}")
        merged = Post.model_validate({**post.model_dump(mode="json"), **fields, "status": "draft"})
        # 제휴 상품이 생기거나 없어지면 [광고]·고지를 그에 맞춘다 (사람이 빼먹지 않게)
        aff = policy.has_affiliate(merged)
        title = merged.title.removeprefix(policy.AD_PREFIX).strip()
        merged = merged.model_copy(update={"title": f"{policy.AD_PREFIX} {title}" if aff else title,
                                           "disclosure": policy.disclosure_text() if aff else None})
        return self.store.save(self._log(merged, "update", ", ".join(sorted(fields))))

    def refresh_products(self, post_id: str, find_products: Callable[[str], dict]) -> Post:
        post = self.get(post_id)
        if post.status not in EDITABLE:
            raise PostError("초안·반려 글만 가격을 다시 확인할 수 있어요.", "not_editable")
        products = draft.products_from_result(find_products(post.topic), self.clock(), post.topic)
        return self.update(post_id, {"products": [p.model_dump(mode="json") for p in products]})

    # ── 상태 ──
    def submit(self, post_id: str) -> Post:
        post = self.get(post_id)
        if post.status not in EDITABLE:
            raise PostError("초안·반려 글만 검토 요청할 수 있어요.", "bad_status")
        post = post.model_copy(update={"status": "pending", "submitted_at": now_iso(self.clock())})
        return self.store.save(self._log(post, "submit"))

    def approve(self, post_id: str, note: str | None = None) -> Post:
        post = self.get(post_id)
        if post.status != "pending":
            raise PostError("검토 대기 글만 승인할 수 있어요.", "bad_status")
        issues = self.check(post)
        if issues:
            raise PostError("정책 검사를 통과하지 못해 승인할 수 없어요.", "policy", issues)
        post = post.model_copy(update={"status": "approved", "approved_at": now_iso(self.clock()),
                                       "reviewer_note": note})
        return self.store.save(self._log(post, "approve", note))

    def reject(self, post_id: str, reason: str) -> Post:
        post = self.get(post_id)
        if post.status != "pending":
            raise PostError("검토 대기 글만 반려할 수 있어요.", "bad_status")
        if not (reason or "").strip():
            raise PostError("반려 사유를 적어 주세요.")
        post = post.model_copy(update={"status": "rejected", "reviewer_note": reason.strip()})
        return self.store.save(self._log(post, "reject", reason.strip()))

    def withdraw(self, post_id: str, reason: str | None = None) -> Post:
        post = self.get(post_id)
        if post.status != "approved":
            raise PostError("게시된 글만 내릴 수 있어요.", "bad_status")
        post = post.model_copy(update={"status": "withdrawn"})
        return self.store.save(self._log(post, "withdraw", reason))

    def reopen(self, post_id: str) -> Post:
        """내린 글을 다시 초안으로 (고쳐서 다시 검토 요청)."""
        post = self.get(post_id)
        if post.status != "withdrawn":
            raise PostError("내린 글만 다시 초안으로 돌릴 수 있어요.", "bad_status")
        return self.store.save(self._log(post.model_copy(update={"status": "draft"}), "reopen"))


def _used_sources(report: dict) -> dict:
    try:
        from app.services.trends.surge import used_sources

        return used_sources(report)
    except Exception:  # noqa: BLE001 — 출처 표시만 줄어든다
        return {}
