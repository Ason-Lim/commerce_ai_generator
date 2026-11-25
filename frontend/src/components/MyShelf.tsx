/**
 * 내 보관함 /#/me (2026-11-22, 창 3-B — roadmap '고객 화면 상세: 내 보관함').
 * 칸 넷: 최근 검색 · 관심 상품 · 장보기 목록 · 설정.  로그인 없음(4단계), 판매·결제를 하지 않으므로 구매 버튼은 '판매처에서 보기'.
 * - 관심 상품·최근 검색: 서버(브라우저별 보관함 주인 값 · 이 브라우저가 쓴 대화 세션)
 * - 장보기 목록·설정: 브라우저 안에만. 설정은 서버로 보내지 않는다(화면 표시·숨기기에만, 순위 불변).
 */
import { useCallback, useEffect, useMemo, useState } from "react";
import { Brand } from "./Brand";
import { ArrowLeftRight, Eye, Heart, History, MessageSquare, Settings2, ShoppingBasket, Trash2, X } from "lucide-react";
import type { ApiCard, SavedView, ShelfTicket } from "../types/blocks";
import { cardToCandidate } from "../api/adapt";
import { claimTransferCode, fetchShelf, forgetShelf, goHref, issueTransferCode, logDirectClick, resetSavedOwner, sendChat } from "../api/client";
import { cx, won } from "../lib/format";
import { clearLocalShelf, knownSessions, useBasket, usePrefs, type BasketEntry, type Prefs } from "../state/shelf";
import { BlockRenderer } from "./BlockRenderer";
import { RecentViewed } from "./RecentViewed";
import { BasketControls } from "./ShoppingPanel";
import { ChatActions, type ChatActionsValue } from "./ChatActions";
import { MobileTabBar, MOBILE_TAB_H, PrivacyLink, ShelfLink, SiteNav } from "./SiteNav";
import { PENDING_ASK } from "./TrendsPage";
import { Thumb } from "./ui";

function ask(text: string) {
  try { sessionStorage.setItem(PENDING_ASK, text); } catch { /* 막혀도 대화 화면으로는 간다 */ }
  window.location.hash = "";
}

function Item({ card, note }: { card: ApiCard; note?: string | null }) {
  const c = cardToCandidate(card);
  const href = goHref(c, null);
  return (
    <li className="flex items-start gap-3 py-3">
      <Thumb c={c} size="sm" />
      <div className="min-w-0 flex-1 space-y-1">
        <p className="line-clamp-2 text-sm font-semibold leading-snug">{c.title}</p>
        <p className="text-sm font-bold">{won(c.total ?? c.price)}
          <span className="ml-1 text-[11px] font-normal text-ink3">{c.total != null ? "배송비 포함" : "상품가"}{note ? ` · ${note}` : ""}</span>
        </p>
        {href && (
          <a href={href} target="_blank" rel={c.affiliate ? "sponsored noopener" : "noopener"} onClick={() => logDirectClick(c, null)}
            className="text-xs font-semibold text-ink2 underline underline-offset-2">{c.source}에서 보기 ↗</a>
        )}
      </div>
    </li>
  );
}

const TICKET_STATUS: Record<ShelfTicket["status"], string> = { open: "확인 중", answered: "답변 있음", closed: "끝남" };

function md(d: string) {
  return d.length >= 16 ? `${Number(d.slice(5, 7))}/${Number(d.slice(8, 10))} ${d.slice(11, 16)}` : d;
}

/** 2026-11-23 창 4 ③: 자동 접수된 문의와 회신 (식품 안전 신고·개인정보 요청·분쟁) */
function Tickets({ items }: { items: ShelfTicket[] }) {
  return (
    <ul className="divide-y divide-line">
      {items.map((t) => (
        <li key={t.id} className="space-y-1 py-2.5">
          <p className="flex flex-wrap items-center gap-2">
            <span className="font-semibold">{t.label}</span>
            <span className={cx("rounded-full px-2 py-0.5 text-xs", t.status === "open" ? "bg-chip" : "bg-accent/10 text-accent")}>
              {TICKET_STATUS[t.status]}
            </span>
            <span className="text-xs text-ink3">접수 {t.id} · {md(t.created_at)}</span>
          </p>
          {t.summary && <p className="text-sm text-ink3">“{t.summary}”</p>}
          {t.messages.map((m) => (
            <p key={`${m.kind}-${m.at}`} className="rounded-xl bg-chip px-3 py-2 text-sm">
              <span className="text-xs text-ink3">{m.kind === "reply" ? "운영팀 답변" : "자동 안내"} · {md(m.at)}</span><br />{m.text}
            </p>
          ))}
        </li>
      ))}
    </ul>
  );
}

function Section({ id, icon: Icon, title, count, children }: {
  id: string; icon: typeof Heart; title: string; count?: number; children: React.ReactNode;
}) {
  return (
    <section aria-labelledby={id} className="rounded-3xl border border-stone-200 bg-white px-5 py-4">
      <h2 id={id} className="flex items-center gap-2 text-base font-bold">
        <Icon size={18} aria-hidden />{title}{count != null && count > 0 && <span className="text-sm font-semibold text-accent">{count}</span>}
      </h2>
      <div className="mt-2">{children}</div>
    </section>
  );
}

const HOUSEHOLD: { v: Prefs["household"]; label: string }[] = [
  { v: "", label: "정하지 않음" }, { v: "1", label: "1인" }, { v: "2", label: "2인" }, { v: "3-4", label: "3~4인" }, { v: "5+", label: "5인 이상" },
];

function PrefsForm() {
  const [prefs, setPrefs] = usePrefs();
  const [word, setWord] = useState("");
  const add = () => {
    const w = word.trim().slice(0, 20);
    if (w && !prefs.avoid.includes(w)) setPrefs({ ...prefs, avoid: [...prefs.avoid, w].slice(0, 20) });
    setWord("");
  };
  return (
    <div className="space-y-4 text-sm">
      <p className="text-xs leading-relaxed text-ink3">
        이 기기 안에만 저장되고, 대화에서 보이는 상품에 표시하거나 숨기는 데만 써요(추천 순서는 그대로).
      </p>
      <fieldset className="space-y-2">
        <legend className="font-semibold">선호 조건</legend>
        <label className="flex items-center gap-2"><input type="checkbox" checked={prefs.vegetarian}
          onChange={(e) => setPrefs({ ...prefs, vegetarian: e.target.checked })} />채식 (고기 상품 표시)</label>
        <label className="flex items-center gap-2"><input type="checkbox" checked={prefs.mild}
          onChange={(e) => setPrefs({ ...prefs, mild: e.target.checked })} />맵지 않은 것 (매운 상품 표시)</label>
        <label className="flex flex-wrap items-center gap-2">가구 인원
          <select value={prefs.household} onChange={(e) => setPrefs({ ...prefs, household: e.target.value as Prefs["household"] })}
            className="rounded-lg border border-line px-2 py-1">
            {HOUSEHOLD.map((h) => <option key={h.v} value={h.v}>{h.label}</option>)}
          </select>
          <span className="text-xs text-ink3">저장만 해요 — 추천에는 아직 쓰지 않아요</span>
        </label>
        <p className="text-xs text-ink3">채식·맵기는 <b>상품명</b>에 든 말로만 표시해요. 상품명에 없으면 표시되지 않으니 판매처 정보를 확인해 주세요.</p>
      </fieldset>
      <fieldset className="space-y-2">
        <legend className="font-semibold">피하고 싶은 재료</legend>
        <div className="flex gap-2">
          <label htmlFor="avoid-word" className="sr-only">피하고 싶은 재료 입력</label>
          <input id="avoid-word" value={word} onChange={(e) => setWord(e.target.value)} maxLength={20}
            onKeyDown={(e) => { if (e.key === "Enter") { e.preventDefault(); add(); } }}
            placeholder="예: 땅콩, 새우" className="min-w-0 flex-1 rounded-lg border border-line px-3 py-1.5" />
          <button type="button" onClick={add} className="rounded-lg border border-line px-3 py-1.5 font-semibold">추가</button>
        </div>
        {prefs.avoid.length > 0 && (
          <ul className="flex flex-wrap gap-1.5">
            {prefs.avoid.map((w) => (
              <li key={w} className="flex items-center gap-1 rounded-full bg-chip px-2.5 py-1 text-xs">
                {w}
                <button type="button" aria-label={`${w} 빼기`} onClick={() => setPrefs({ ...prefs, avoid: prefs.avoid.filter((x) => x !== w) })}>
                  <X size={12} aria-hidden />
                </button>
              </li>
            ))}
          </ul>
        )}
        <label className="flex items-center gap-2"><input type="checkbox" checked={prefs.hideAvoided}
          onChange={(e) => setPrefs({ ...prefs, hideAvoided: e.target.checked })} />표시 대신 목록에서 숨기기</label>
        <p className="text-xs text-ink3">숨기면 대화 목록 아래에 숨긴 개수가 보이고, 여기서 체크를 끄면 다시 보여요.</p>
        <p className="text-xs text-warn">상품명으로만 찾아 표시해요. 알레르기는 판매처 상품 정보(원재료·알레르기 표시)를 꼭 확인하세요.</p>
      </fieldset>
    </div>
  );
}

/** 2026-11-24 다른 기기로 옮기기 — 로그인 없이 한 번 쓰고 버리는 코드 (10분). 관심 상품·장보기 목록만, 문의·설정은 옮기지 않음. */
const TRANSFER_ERR: Record<string, string> = {
  bad_code: "코드가 맞지 않거나 10분이 지났어요. 원래 기기에서 코드를 다시 만들어 주세요.",
  same_device: "이 기기에서 만든 코드예요. 옮겨 갈 다른 기기에서 입력해 주세요.",
  too_many: "잘못 입력한 횟수가 많아 잠시 막았어요. 10분 뒤에 다시 해 주세요.",
};
function TransferBox({ basket, onClaimed }: { basket: BasketEntry[]; onClaimed: (moved: number, incoming: BasketEntry[]) => void }) {
  const [code, setCode] = useState<{ code: string; until: number } | null>(null);
  const [input, setInput] = useState("");
  const [msg, setMsg] = useState("");
  const [now, setNow] = useState(() => Date.now());
  useEffect(() => {
    if (!code) return;
    const t = window.setInterval(() => setNow(Date.now()), 1000);
    return () => window.clearInterval(t);
  }, [code]);
  const left = code ? Math.max(0, Math.round((code.until - now) / 1000)) : 0;
  async function make() {
    setMsg("");
    try {
      const r = await issueTransferCode(basket);
      if (r.ok && r.code) setCode({ code: r.code, until: Date.now() + (r.expires_in ?? 600) * 1000 });
      else setMsg("코드를 만들지 못했어요. 잠시 후 다시 해 주세요.");
    } catch { setMsg("코드를 만들지 못했어요. 잠시 후 다시 해 주세요."); }
  }
  async function claim() {
    if (input.replace(/[^0-9a-z]/gi, "").length < 8) { setMsg("코드 8글자를 입력해 주세요."); return; }
    try {
      const r = await claimTransferCode(input);
      if (!r.ok) { setMsg(TRANSFER_ERR[r.error ?? ""] ?? "불러오지 못했어요. 잠시 후 다시 해 주세요."); return; }
      const incoming = (r.basket ?? []) as BasketEntry[];
      onClaimed(r.saved_moved ?? 0, incoming);
      setInput("");
      setMsg(`관심 상품 ${r.saved_moved ?? 0}개, 장보기 ${incoming.length}개를 불러왔어요. 원래 기기의 보관함은 그대로예요.`);
    } catch { setMsg("불러오지 못했어요. 잠시 후 다시 해 주세요."); }
  }
  return (
    <div className="grid gap-4 sm:grid-cols-2">
      <div>
        <p className="text-sm font-semibold">이 기기에서 보내기</p>
        <p className="mt-1 text-xs leading-relaxed text-ink3">코드를 만들어 다른 기기의 '내 보관함 → 코드로 불러오기'에 넣으세요. 10분 동안 한 번만 쓸 수 있어요.</p>
        {code && left > 0 ? (
          <p className="mt-2 flex items-baseline gap-2"><b aria-label="옮기기 코드" className="font-mono text-2xl tracking-widest">{code.code}</b>
            <span className="text-xs text-ink3">{Math.floor(left / 60)}:{String(left % 60).padStart(2, "0")} 남음</span></p>
        ) : null}
        <button type="button" onClick={() => void make()} className="mt-2 rounded-full border border-line px-4 py-1.5 text-sm font-semibold">
          {code ? "코드 다시 만들기" : "옮기기 코드 만들기"}</button>
      </div>
      <div>
        <label htmlFor="transfer-code" className="text-sm font-semibold">코드로 불러오기</label>
        <p className="mt-1 text-xs leading-relaxed text-ink3">다른 기기에서 만든 코드를 넣으면 관심 상품과 장보기 목록을 이 기기에 합쳐요.</p>
        <div className="mt-2 flex gap-2">
          <input id="transfer-code" value={input} onChange={(e) => setInput(e.target.value)} placeholder="ABCD-EFGH" maxLength={12}
            autoComplete="off" spellCheck={false} className="w-36 rounded-xl border border-line px-3 py-1.5 font-mono uppercase tracking-widest" />
          <button type="button" onClick={() => void claim()} className="rounded-full bg-ink px-4 py-1.5 text-sm font-semibold text-white">불러오기</button>
        </div>
      </div>
      {msg && <p role="status" className="text-sm sm:col-span-2">{msg}</p>}
      <p className="text-[11px] leading-relaxed text-ink3 sm:col-span-2">로그인·전화번호 없이 쓰는 방식이에요. 문의 내역과 설정(피하고 싶은 재료 등)은 옮기지 않아요.</p>
    </div>
  );
}

export function MyShelf() {
  const [view, setView] = useState<SavedView>({ saved: [], recent: [] });
  const [loaded, setLoaded] = useState(false);
  const [basket, setBasket] = useBasket();
  const [cleared, setCleared] = useState("");
  const [busyName, setBusyName] = useState("");
  const load = useCallback(async (signal?: AbortSignal) => {
    try { setView(await fetchShelf(knownSessions(), signal)); } catch { /* 못 읽어도 장보기·설정은 보인다 */ }
    setLoaded(true);
  }, []);
  useEffect(() => {
    const ctrl = new AbortController();
    void load(ctrl.signal);
    document.title = "내 보관함 | AI 식품 추천";
    return () => ctrl.abort();
  }, [load]);

  // 보관함 안의 장보기 상품 카드는 대화 동작 없이 보여 준다 (상세·담기 버튼은 대화 화면에서)
  const actions: ChatActionsValue = useMemo(() => ({
    send: () => {}, shop: () => {}, basket: basket.map((e) => e.ingredient), openDetail: () => {}, openTrendPost: () => {},
    busy: false, sessionId: null, askFeedback: () => {},
  }), [basket]);

  const groups = new Map<string, ApiCard[]>();
  for (const c of view.saved) groups.set(c.query ?? "기타", [...(groups.get(c.query ?? "기타") ?? []), c]);
  const comparable = [...groups.values()].some((g) => g.length >= 2);

  async function forget() {
    if (!window.confirm("관심 상품, 이 브라우저의 최근 대화 기록(최근 검색 포함), 최근 본 상품, 장보기 목록, 설정을 모두 지울까요? 되돌릴 수 없어요.")) return;
    let ok = false;
    try { ok = await forgetShelf(knownSessions()); } catch { ok = false; }
    if (!ok) {
      // 서버를 못 지웠으면 아무것도 지우지 않는다 — 세션 값을 남겨 다시 시도할 수 있게
      setCleared("서버 기록을 지우지 못했어요. 이 기기의 기록도 그대로 두었으니 잠시 후 다시 눌러 주세요.");
      return;
    }
    clearLocalShelf();
    resetSavedOwner();
    setView({ saved: [], recent: [] });
    setCleared("기록을 모두 지웠어요. 다른 탭에 열린 대화는 새로고침해 주세요.");
  }

  // '가지고 있어요' — 그 재료의 레시피 대화에 '충분해요'를 보내고 목록에서 뺀다 (대화 칸과 같은 뜻)
  async function have(name: string, sessionId?: string | null) {
    setBusyName(name);
    try {
      if (sessionId) await sendChat({ session_id: sessionId, message: `${name} 충분해요` });
      setBasket((prev) => prev.filter((x) => x.ingredient !== name));
    } catch {
      setCleared(`'${name}'를 레시피에 반영하지 못했어요. 목록에서만 빼려면 '목록에서 빼기'를 눌러 주세요.`);
    } finally {
      setBusyName("");
    }
  }

  return (
    <ChatActions.Provider value={actions}>
      <div className="min-h-screen bg-paper text-ink">
        <header className="sticky top-0 z-10 border-b border-stone-200/70 bg-paper/95 backdrop-blur">
          <div className="mx-auto flex h-[64px] w-full max-w-[900px] items-center justify-between gap-3 px-4 sm:px-8">
            <Brand />
            <div className="flex items-center gap-2"><SiteNav current="me" /><ShelfLink current count={view.saved.length} /></div>
          </div>
        </header>
        <main className="mx-auto w-full max-w-[900px] space-y-4 px-4 pt-8 sm:px-8 sm:!pb-12" style={{ paddingBottom: MOBILE_TAB_H + 32 }}>
          <h1 className="text-2xl font-semibold tracking-tight sm:text-3xl">내 보관함</h1>
          <p className="text-sm leading-7 text-stone-600">이 브라우저에만 모아 두는 곳이에요. 로그인 없이 쓰고, 다른 기기로는 아래 '다른 기기로 옮기기' 코드로 옮겨요.</p>
          {cleared && <p role="status" className="rounded-xl bg-chip px-4 py-3 text-sm">{cleared}</p>}

          {view.tickets && view.tickets.length > 0 && (
            <Section id="shelf-tickets" icon={MessageSquare} title="문의" count={view.tickets.length}>
              <Tickets items={view.tickets} />
            </Section>
          )}
          <Section id="shelf-recent" icon={History} title="최근 검색" count={view.recent.length}>
            {view.recent.length ? (
              <ul className="divide-y divide-line">
                {view.recent.map((r) => (
                  <li key={`${r.session_id}-${r.query}`} className="flex items-center gap-3 py-2.5">
                    <div className="min-w-0 flex-1">
                      <p className="truncate font-semibold">{r.query}</p>
                      <p className="text-xs text-ink3">{r.at}{r.budget ? ` · 예산 ${r.budget}` : ""} · 후보 {r.cards.length}개</p>
                    </div>
                    <button type="button" onClick={() => ask(`${r.query} 추천해 줘`)}
                      className="shrink-0 rounded-full border border-line px-3 py-1.5 text-xs font-semibold">다시 묻기</button>
                  </li>
                ))}
              </ul>
            ) : <p className="py-3 text-sm text-ink3">{loaded ? "아직 검색한 상품이 없어요." : "불러오는 중…"}</p>}
          </Section>

          <Section id="shelf-viewed" icon={Eye} title="최근 본 상품">
            <RecentViewed variant="shelf" />
          </Section>
          <Section id="shelf-saved" icon={Heart} title="관심 상품" count={view.saved.length}>
            {view.saved.length ? (
              <>
                {[...groups.entries()].map(([q, cards]) => (
                  <div key={q} className="border-b border-line py-1 last:border-0">
                    <h3 className="pt-2 text-xs font-bold text-ink3">'{q}' 에서 담은 상품 {cards.length}개</h3>
                    <ul className="divide-y divide-line">
                      {cards.map((c) => <Item key={c.key} card={c} note={c.seen_at ? `${c.seen_at} 확인 가격` : null} />)}
                    </ul>
                  </div>
                ))}
                <button type="button" disabled={!comparable} onClick={() => ask("관심 상품 비교해줘")}
                  className={cx("primary-btn mt-3 w-full", !comparable && "opacity-50")}>관심 상품 비교하기</button>
                <p className="mt-1.5 text-center text-[11px] text-ink3">
                  {comparable ? "대화 화면에서 같은 검색에서 담은 상품끼리 비교해요" : "같은 검색에서 2개 이상 담으면 비교할 수 있어요"}
                </p>
              </>
            ) : (
              <p className="py-3 text-sm leading-relaxed text-ink3">
                아직 담은 상품이 없어요. 대화에서 상품 카드의 <Heart size={13} className="inline" aria-hidden /> 관심 을 누르면 여기에 모여요.
              </p>
            )}
          </Section>

          <Section id="shelf-basket" icon={ShoppingBasket} title="장보기 목록" count={basket.length}>
            {basket.length ? (
              <div className="space-y-4">
                <p className="text-xs leading-relaxed text-ink3">
                  레시피에서 '부족해요'·'없어요'를 누른 재료예요. '목록에서 빼기'는 이 목록에서만, '가지고 있어요'는 레시피 대화에도 알려요.
                  도착일은 판매처에서 확인해 주세요.
                </p>
                {basket.map((e) => (
                  <div key={e.ingredient} className="rounded-2xl bg-stone-50 p-3">
                    <div className="mb-2 flex items-center gap-2">
                      <span className="text-sm font-bold">{e.ingredient}</span>
                      <span className="tag bg-chip text-ink2">{e.mode === "absent" ? "없음" : "부족"}</span>
                      <BasketControls name={e.ingredient} busy={busyName === e.ingredient}
                        onDrop={() => setBasket((prev) => prev.filter((x) => x.ingredient !== e.ingredient))}
                        onHave={e.sessionId ? () => void have(e.ingredient, e.sessionId) : undefined} />
                    </div>
                    <BlockRenderer blocks={e.blocks} />
                  </div>
                ))}
              </div>
            ) : <p className="py-3 text-sm text-ink3">레시피 대화에서 부족한 재료를 고르면 여기에 모여요.</p>}
          </Section>

          <Section id="shelf-transfer" icon={ArrowLeftRight} title="다른 기기로 옮기기">
            <TransferBox basket={basket} onClaimed={(_moved, incoming) => {
              setBasket((prev) => [...prev, ...incoming.filter((x) => x && x.ingredient && !prev.some((p) => p.ingredient === x.ingredient))]);
              void load();
            }} />
          </Section>

          <Section id="shelf-prefs" icon={Settings2} title="설정">
            <PrefsForm />
          </Section>

          <div className="pt-2">
            <button type="button" onClick={() => void forget()}
              className="inline-flex items-center gap-1.5 rounded-full border border-red-200 px-4 py-2 text-sm font-semibold text-red-700">
              <Trash2 size={15} aria-hidden />보관함·최근 대화 기록 지우기
            </button>
            <p className="mt-1.5 text-xs leading-relaxed text-ink3">
              지우는 것: 관심 상품, 이 브라우저의 최근 대화 5개(최근 검색·대화 기록), 장보기 목록, 설정, 최근 누른 품목(맞춤 추천).
              서비스 운영 기록의 보존 기간은 <PrivacyLink />에 있어요.
            </p>
          </div>
        </main>
        <MobileTabBar current="me" />
      </div>
    </ChatActions.Provider>
  );
}
