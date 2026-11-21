// 등록부 창 위치 (0.7.0, 2026-11-21 사용자 요청: 머리줄을 길게 누르면 옮길 수 있게) — 계산만, 화면은 content.js
(function (root) {
  'use strict';
  const HOLD_MS = 350;     // 이만큼 누르고 있으면 옮기기 시작
  const SLOP = 6;          // 그 전에 이만큼 움직이면 옮기기가 아니라 보통 누르기(스크롤·선택)
  const MARGIN = 8;        // 화면 가장자리 여백

  // 창이 화면 밖으로 나가지 않게: 왼쪽 위 좌표를 화면 안으로
  function clamp(pos, size, view) {
    const maxX = Math.max(MARGIN, view.width - size.width - MARGIN);
    const maxY = Math.max(MARGIN, view.height - Math.min(size.height, 48) - MARGIN);   // 머리줄만은 늘 보이게
    return { left: Math.round(Math.min(Math.max(pos.left, MARGIN), maxX)),
             top: Math.round(Math.min(Math.max(pos.top, MARGIN), maxY)) };
  }

  function moved(a, b) { return Math.abs(a.x - b.x) > SLOP || Math.abs(a.y - b.y) > SLOP; }

  // 저장된 값 검사 (숫자 두 개만)
  function valid(p) { return !!p && Number.isFinite(p.left) && Number.isFinite(p.top); }

  const api = { HOLD_MS, SLOP, MARGIN, clamp, moved, valid };
  if (typeof module !== 'undefined' && module.exports) module.exports = api;
  else root.BcPanelPos = api;
})(typeof self !== 'undefined' ? self : this);
