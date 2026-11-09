#!/usr/bin/env bash
# 백엔드(:8001)와 화면 개발 서버(:5173)를 끈다 (2026-11-02).
# 'Address already in use' 가 나올 때 — 자동 재시작 모드는 프로그램이 둘이라 Ctrl+C 를 놓치면 남는다.
for port in "${API_PORT:-8001}" 5173; do
  pids=$(lsof -tiTCP:"$port" -sTCP:LISTEN 2>/dev/null || true)
  [ -z "$pids" ] && continue
  echo "포트 $port 종료: $pids"
  kill $pids 2>/dev/null || true
  sleep 1
  left=$(lsof -tiTCP:"$port" -sTCP:LISTEN 2>/dev/null || true)
  [ -n "$left" ] && kill -9 $left 2>/dev/null || true
done
echo "완료"
