// node --test extensions/bc-to-registry/test
const test = require('node:test');
const assert = require('node:assert/strict');
const R = require('../lib/registry_row.js');

const P = { id: 123, productName: ' 김명월 태안구운감태 1봉 ', storeName: '김명월', salePrice: 11000, discountedSalePrice: 9900,
  discountedRate: 10, commissionRate: 16, shortenUrl: 'https://naver.me/AbC12', reviewInfo: { totalReviewCount: 5 } };

test('검색·발급 주소를 구분하고, 발급은 POST 만 본다', () => {
  const s = 'https://gw-brandconnect.naver.com/affiliate/query/affiliate-products/search-by-query?query=감태&limit=20';
  const i = 'https://gw-brandconnect.naver.com/affiliate/command/affiliate-urls?affiliateProductId=123';
  assert.equal(R.kindOf(s, 'GET'), 'search');
  assert.equal(R.kindOf(i, 'post'), 'issue');
  assert.equal(R.kindOf(i, 'GET'), null);
  assert.equal(R.kindOf('https://gw-brandconnect.naver.com/ping', 'GET'), null);
  assert.equal(R.productIdOfIssueUrl(i), '123');
});

test('검색 응답 {data, paging} 에서 상품만 꺼낸다', () => {
  assert.deepEqual(R.productsOf({ data: [P, { id: 9 }, null], paging: { nextCursor: 'x' } }).map((p) => p.id), [123]);
  assert.deepEqual(R.productsOf({ data: { data: [P] } }).length, 1);
  assert.deepEqual(R.productsOf({ error: 'x' }), []);
  assert.deepEqual(R.productsOf(null), []);
});

test('발급 응답의 여러 모양에서 링크를 찾고, 쇼핑커넥트 링크가 아니면 버린다', () => {
  assert.equal(R.issuedUrlOf({ shortenUrl: 'https://naver.me/x1' }), 'https://naver.me/x1');
  assert.equal(R.issuedUrlOf({ data: { shortenUrl: 'https://naver.me/x2' } }), 'https://naver.me/x2');
  assert.equal(R.issuedUrlOf({ data: 'https://naver.me/x3' }), 'https://naver.me/x3');
  assert.equal(R.issuedUrlOf({ url: 'https://smartstore.naver.com/a/products/1' }), null);
  assert.equal(R.issuedUrlOf({}), null);
});

test('등록부 행: 판매가=할인 전, 할인가=할인가, 수수료=응답 값 그대로', () => {
  assert.deepEqual(R.toRegistryRow(P, ' 감태 '), {
    keyword: '감태', product_name: '김명월 태안구운감태 1봉', store_name: '김명월', price: 11000, discount_price: 9900,
    commission_rate: 16, link: 'https://naver.me/AbC12', memo: '' });
});

test('할인이 없거나 할인가가 판매가와 같으면 discount_price 는 비운다', () => {
  assert.equal(R.toRegistryRow({ ...P, discountedSalePrice: null }, 'k').discount_price, null);
  assert.equal(R.toRegistryRow({ ...P, discountedSalePrice: 11000 }, 'k').discount_price, null);
  const onlyDisc = R.toRegistryRow({ ...P, salePrice: null }, 'k');
  assert.equal(onlyDisc.price, 9900);
  assert.equal(onlyDisc.discount_price, null);
});

test('검색 화면 주소의 검색어', () => {
  assert.equal(R.keywordFromPageUrl('https://brandconnect.naver.com/971564859961248/affiliate/products/search?keyword=%EA%B0%90%ED%83%9C'), '감태');
  assert.equal(R.keywordFromPageUrl('not a url'), '');
});

test('서버 주소는 이 컴퓨터만', () => {
  assert.ok(R.serverOk('http://localhost:8001'));
  assert.ok(R.serverOk('http://127.0.0.1:8001'));
  assert.ok(!R.serverOk('https://my-tunnel.trycloudflare.com'));
  assert.ok(!R.serverOk('http://localhost.evil.com:8001'));
  assert.ok(!R.serverOk('javascript:alert(1)'));
});
