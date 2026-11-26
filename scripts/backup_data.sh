#!/usr/bin/env bash
# 데이터 백업 (맥미니 운영 전환 준비, 2026-11-26) — data/·var/ 의 SQLite DB 를 쓰는 중에도 안전하게(.backup) 복사.
#   bash scripts/backup_data.sh                  → ~/commerce_ai_backups/날짜_시각/ (14일 지난 백업은 지움)
#   BACKUP_DIR=/Volumes/외장/backup bash scripts/backup_data.sh
# 함께 복사: 문의·노출 중지 JSON(var/cs), 미니숍 이미지(var/shop_images), 트렌드 글(var/trends/posts).
# .env 와 암호화 키(data/admin/corpmall.key·var/measure/measure.key)는 복사하지 않는다 — 비밀번호 관리자 등 따로 보관
# (키가 없으면 백업의 암호화 칸을 못 읽으니, 키는 꼭 따로 1부 보관). 백업 폴더에는 개인정보가 들어 있으니(암호화 칸 포함) 외부 공유 금지.
set -euo pipefail
cd "$(dirname "$0")/.."
ROOT="${BACKUP_DIR:-$HOME/commerce_ai_backups}"
DEST="$ROOT/$(date +%Y-%m-%d_%H%M)"
KEEP_DAYS="${BACKUP_KEEP_DAYS:-14}"
mkdir -p "$DEST"
n=0
while IFS= read -r db; do
  out="$DEST/$db"; mkdir -p "$(dirname "$out")"
  if command -v sqlite3 >/dev/null 2>&1; then sqlite3 "$db" ".backup '$out'"; else cp "$db" "$out"; fi
  n=$((n + 1))
done < <(find data var -name '*.sqlite3' -type f 2>/dev/null | grep -v '/_to_delete/' || true)
for d in var/cs var/shop_images var/trends/posts; do
  [ -d "$d" ] && mkdir -p "$DEST/$(dirname "$d")" && cp -R "$d" "$DEST/$(dirname "$d")/"
done
chmod -R go-rwx "$DEST"
find "$ROOT" -maxdepth 1 -type d -name '20*' -mtime +"$KEEP_DAYS" -exec rm -rf {} + 2>/dev/null || true
echo "백업했어요: DB ${n}개 → $DEST ($(du -sh "$DEST" | cut -f1))"
