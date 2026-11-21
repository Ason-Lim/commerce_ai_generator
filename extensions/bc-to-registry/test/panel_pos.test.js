// node --test extensions/bc-to-registry/test
const test = require('node:test');
const assert = require('node:assert/strict');
const P = require('../lib/panel_pos.js');

test('창은 화면 안에 머문다 (머리줄은 늘 보이게)', () => {
  const view = { width: 1200, height: 800 }, size = { width: 380, height: 500 };
  assert.deepEqual(P.clamp({ left: 100, top: 100 }, size, view), { left: 100, top: 100 });
  assert.deepEqual(P.clamp({ left: -50, top: -20 }, size, view), { left: 8, top: 8 });
  assert.deepEqual(P.clamp({ left: 5000, top: 5000 }, size, view), { left: 1200 - 380 - 8, top: 800 - 48 - 8 });
});

test('짧게 움직이면 옮기기가 아니다 · 저장 값 검사', () => {
  assert.equal(P.moved({ x: 0, y: 0 }, { x: 3, y: 4 }), false);
  assert.equal(P.moved({ x: 0, y: 0 }, { x: 10, y: 0 }), true);
  assert.equal(P.valid({ left: 1, top: 2 }), true);
  assert.equal(P.valid({ left: 'a', top: 2 }), false);
  assert.equal(P.valid(null), false);
});
