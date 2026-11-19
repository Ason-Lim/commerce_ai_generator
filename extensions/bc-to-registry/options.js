// 설정: 서버 주소·관리자 토큰 (토큰은 화면에 다시 보여 주지 않는다)
const $ = (id) => document.getElementById(id);
const say = (text, cls) => { $('status').textContent = text; $('status').className = cls || ''; };

chrome.storage.local.get({ server: 'http://localhost:8001', token: '', openView: 'split' }).then((s) => {
  $('server').value = s.server;
  const v = ['split', 'tab', 'window'].includes(s.openView) ? s.openView : 'split';
  document.querySelector(`input[name=openView][value=${v}]`).checked = true;
  $('token').placeholder = s.token ? '저장된 토큰 있음 (바꿀 때만 입력)' : '토큰을 넣어 주세요';
});

$('save').onclick = async () => {
  const server = $('server').value.trim().replace(/\/+$/, '') || 'http://localhost:8001';
  if (!self.BcRegistry.serverOk(server)) return say('localhost 또는 127.0.0.1 주소만 쓸 수 있어요', 'err');
  const view = document.querySelector('input[name=openView]:checked');
  const patch = { server, openView: view ? view.value : 'split' };
  if ($('token').value.trim()) patch.token = $('token').value.trim();
  await chrome.storage.local.set(patch);
  $('token').value = '';
  $('token').placeholder = '저장된 토큰 있음 (바꿀 때만 입력)';
  say('저장했어요', 'ok');
};

$('test').onclick = async () => {
  const s = await chrome.storage.local.get({ server: 'http://localhost:8001', token: '' });
  if (!s.token) return say('토큰을 먼저 저장해 주세요', 'err');
  try {
    const r = await fetch(s.server + '/admin/api/connect/links', { headers: { 'X-Access-Token': s.token } });
    if (r.status === 401) return say('토큰이 맞지 않아요', 'err');
    if (!r.ok) return say(`서버 오류 ${r.status}`, 'err');
    const d = await r.json();
    say(`연결됐어요 — 등록부 ${d.count}건 (${d.file})`, 'ok');
  } catch (e) {
    say(`${s.server} 에 닿지 않아요 — 서버가 켜져 있는지 확인해 주세요`, 'err');
  }
};
