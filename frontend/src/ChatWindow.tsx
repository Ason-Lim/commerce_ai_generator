import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { ArrowUp, ArrowRight, Plus, Sparkles, ShoppingBag, Utensils, Square, Gift, Cookie, Leaf, TrendingUp, Heart, type LucideIcon } from 'lucide-react';
import { SavedPanel } from './components/SavedPanel';
import { SavedProvider, useSaved } from './state/saved';
import { PENDING_ASK } from './components/TrendsPage';
import { BlockRenderer } from './components/BlockRenderer';
import { ProductDetail } from './components/ProductDetail';
import { FlowStepper } from './components/FlowStepper';
import { ChatActions, type ChatActionsValue } from './components/ChatActions';
import type { FlowStep, SendPayload } from './state/useConversation';
import type { Message } from './types';
import type { Candidate } from './types/blocks';
import { API_MODE, sendChat } from './api/client';
import { pageTitle } from './lib/pageTitle';
import { BusyStatus } from './components/BusyStatus';
import { BUSY_TIMEOUT_MS, TIMEOUT_MESSAGE, busyKind, type BusyKind } from './lib/busyStages';

// ── 홈 화면 예시 질문: src/data/trend_examples_YYYY-MM-DD.json 중 최신 파일을 읽는다 ──
// 파일은 commerce_ai_generator/scripts/update_trend_examples.py가 매일 10시에 만든다.
// 2026-11-04: 운영 화면은 빌드 때 넣은 파일에 머물지 않도록, 열릴 때 /api/trend-examples 로 그날 파일을 다시 받는다
// (받지 못하면 빌드 때 넣은 최신 파일 → 기본 예시 순으로 쓴다)
type TrendExample = { category: string; icon?: string; keyword?: string; question: string };
type Example = { icon: LucideIcon; label: string; text: string; note: string };

const ICONS: Record<string, LucideIcon> = { Gift, Cookie, Utensils, Leaf, ShoppingBag };

const FALLBACK_EXAMPLES: Example[] = [
    { icon: Gift, label: '선물용', text: '부모님 선물로 좋은 식품 추천해줘', note: '받는 분 취향까지 고려해서' },
    { icon: Cookie, label: '간식/디저트', text: '두바이 쫀득쿠키 추천해줘', note: '가격부터 배송까지 한 번에' },
    { icon: Utensils, label: '레시피/요리', text: '파스타 레시피로 장보기', note: '있는 재료는 빼고, 필요한 만큼' },
    { icon: Leaf, label: '캠핑', text: '캠핑 갈 때 챙길 먹거리 추천해줘', note: '보관·조리 편의까지 함께' }
];

const trendFiles = import.meta.glob<TrendExample[]>('./data/trend_examples_*.json', { eager: true, import: 'default' });

// 정상 파일: 질문이 3개 이상이고 키워드가 서로 겹치지 않는 파일 (같은 키워드만 반복된 파일은 건너뜀)
function isUsable(rows: unknown): rows is TrendExample[] {
    if (!Array.isArray(rows) || rows.length < 3) return false;
    const ok = rows.filter(r => r && typeof r.question === 'string' && r.question.trim() && typeof r.category === 'string');
    const keys = new Set(ok.map(r => (r.keyword || r.question).trim()));
    return ok.length >= 3 && keys.size === ok.length;
}

type ExampleSet = { examples: Example[]; date: string | null };

function toExamples(rows: TrendExample[], day: string | null): ExampleSet {
    const date = day?.match(/(\d{4})-(\d{2})-(\d{2})/);
    const mmdd = date ? `${Number(date[2])}/${Number(date[3])}` : '';
    return {
        date: date ? date[0] : null,
        examples: rows.slice(0, 4).map(r => ({
            icon: ICONS[r.icon ?? ''] ?? ShoppingBag,
            label: r.category,
            text: r.question.trim(),
            note: r.keyword ? `${mmdd} 급상승 키워드 · ${r.keyword}` : `${mmdd} 트렌드`,
        })),
    };
}

function loadExamples(): ExampleSet {
    const paths = Object.keys(trendFiles).sort().reverse(); // 파일명 날짜 기준 최신순
    for (const path of paths) {
        const rows = trendFiles[path];
        if (isUsable(rows)) return toExamples(rows, path);
    }
    return { examples: FALLBACK_EXAMPLES, date: null };
}

const BUILT_EXAMPLES = loadExamples();

/** 서버의 그날 예시 (빌드 없이 매일 바뀜). 형식이 맞을 때만 쓴다 */
function useLiveExamples(): ExampleSet {
    const [set, setSet] = useState<ExampleSet>(BUILT_EXAMPLES);
    useEffect(() => {
        if (API_MODE === 'mock') return;
        const ctl = new AbortController();
        fetch('/api/trend-examples', { signal: ctl.signal })
            .then(r => (r.ok ? r.json() : null))
            .then((d: { date?: string; items?: unknown } | null) => {
                if (d && typeof d.date === 'string' && isUsable(d.items) && (!BUILT_EXAMPLES.date || d.date >= BUILT_EXAMPLES.date)) {
                    setSet(toExamples(d.items, d.date));
                }
            })
            .catch(() => { /* 빌드 때 넣은 예시 그대로 */ });
        return () => ctl.abort();
    }, []);
    return set;
}


// 화면 안에서만 쓰는 메시지 key. crypto.randomUUID 는 HTTPS·localhost(보안 컨텍스트)에서만 있어서
// 같은 Wi‑Fi의 http://192.168.x.x 접속이나 오래된 인앱 브라우저에서는 없다 → 렌더 중 오류로 화면 전체가 비었다.
let idSeq = 0;
const newId = (): string =>
    typeof crypto !== 'undefined' && typeof crypto.randomUUID === 'function'
        ? crypto.randomUUID()
        : `m${Date.now().toString(36)}-${(idSeq += 1)}-${Math.random().toString(36).slice(2, 8)}`;

// 대화 세션 id 를 이 브라우저에 기억해 새로고침·재접속해도 서버에 저장된 레시피 기록(남은 양·부족 답변)을 이어 쓴다.
// 화면의 지난 메시지는 다시 그리지 않는다(첫 화면 그대로). '새 대화'를 누르면 지운다. 저장소가 막힌 브라우저에서는 그냥 새 세션.
const SESSION_KEY = 'ai-food-chat-session';
const loadSession = (): string | null => { try { return window.localStorage.getItem(SESSION_KEY); } catch { return null; } };
const saveSession = (sid: string | null) => {
    try { if (sid) window.localStorage.setItem(SESSION_KEY, sid); else window.localStorage.removeItem(SESSION_KEY); } catch { /* 기억 못 해도 동작에는 지장 없음 */ }
};

export default function ChatWindow() {
    const { examples, date: examplesDate } = useLiveExamples();
    const [messages, setMessages] = useState<Message[]>([]);
    // 2026-11-04: 네이버 쇼핑커넥트 상품이 실제로 보였을 때만 하단 고지에 네이버 수수료 문구를 붙인다
    const hasConnect = useMemo(() => messages.some(m => (m.blocks ?? []).some(b =>
        b.type === 'product_list' && b.data.items.some(it => it.affiliate_program === '네이버 쇼핑커넥트'))), [messages]);
    const [input, setInput] = useState('');
    const [sessionId, setSessionIdState] = useState<string | null>(loadSession);
    const setSessionId = (sid: string | null) => { setSessionIdState(sid); saveSession(sid); };
    const [busy, setBusy] = useState(false);
    const [waitKind, setWaitKind] = useState<BusyKind>('shopping');
    const [error, setError] = useState('');
    const [detail, setDetail] = useState<Candidate | null>(null);
    const [purchasing, setPurchasing] = useState(false);
    const controller = useRef<AbortController | null>(null);
    const locked = useRef(false);
    // 레시피 대화 중에는 입력 안내를 레시피 질문으로 (첫 화면·쇼핑 대화는 그대로)
    const lastStage = [...messages].reverse().find(m => m.role === 'assistant')?.stage ?? '';
    const inRecipe = lastStage.startsWith('recipe');
    const header = useRef<HTMLElement>(null);
    const footer = useRef<HTMLElement>(null);
    const answer = useRef<HTMLElement>(null);

    // 대화 진행 상태로 현재 단계 추정: 입력 → 조건 확인 → 후보 비교 → 상품 판단 → 구매 연결
    const step: FlowStep = (() => {
        if (detail) return purchasing ? 5 : 4;
        if (!messages.length) return 1;
        if (busy) return 2;
        const assistantTurns = messages.filter(m => m.role === 'assistant').length;
        if (assistantTurns <= 1) return 3;
        if (assistantTurns === 2) return 4;
        return 5;
    })();

    // 사용자가 (응답을 기다리는 동안) 위로 올라가 읽고 있는지 — 스크롤할 때만 갱신
    const following = useRef(true);
    const autoUntil = useRef(0);   // 자동 스크롤(부드러운 이동) 중에 생기는 scroll 이벤트는 사용자 동작으로 보지 않는다
    const scrollToY = (top: number, smooth = true) => {
        autoUntil.current = Date.now() + 1000;
        window.scrollTo(smooth ? { top, behavior: 'smooth' } : { top });
    };
    useEffect(() => {
        const onScroll = () => {
            if (Date.now() < autoUntil.current) return;
            following.current = document.documentElement.scrollHeight - window.innerHeight - window.scrollY < 120;
        };
        // 휠·터치·스크롤 키는 사용자 동작 — 진행 중인 자동 스크롤보다 우선한다.
        // 입력창에서 누른 키(Enter 전송 포함)는 스크롤 동작이 아니므로 제외한다.
        const userMoved = () => { autoUntil.current = 0; };
        const SCROLL_KEYS = new Set(['PageUp', 'PageDown', 'ArrowUp', 'ArrowDown', 'Home', 'End', ' ']);
        const onKey = (e: KeyboardEvent) => {
            const el = e.target as HTMLElement | null;
            const editing = !!el && (el.tagName === 'TEXTAREA' || el.tagName === 'INPUT' || el.isContentEditable);
            if (!editing && SCROLL_KEYS.has(e.key)) userMoved();
        };
        window.addEventListener('scroll', onScroll, { passive: true });
        window.addEventListener('wheel', userMoved, { passive: true });
        window.addEventListener('touchmove', userMoved, { passive: true });
        window.addEventListener('keydown', onKey);
        return () => {
            window.removeEventListener('scroll', onScroll);
            window.removeEventListener('wheel', userMoved);
            window.removeEventListener('touchmove', userMoved);
            window.removeEventListener('keydown', onKey);
        };
    }, []);

    // 자동 스크롤 — 문서(window) 스크롤 하나만 기준으로 삼는다.
    // · 첫 화면/새 대화: 맨 위
    // · 질문 전송·응답 대기·오류: 문서 맨 끝 (sticky 입력창은 문서 흐름 안에 있어 맨 끝이면 아무것도 가리지 않는다)
    // · 새 답변: 헤더~입력창 사이에 다 들어오면 맨 끝, 길면 답변 시작을 헤더 바로 아래에 맞춰 처음부터 읽게 한다
    // · 단, 기다리는 동안 사용자가 위로 올라가 읽고 있었으면 새 답변이 와도 위치를 옮기지 않는다
    useEffect(() => {
        if (!messages.length) { scrollToY(0, false); return; }
        const end = () => document.documentElement.scrollHeight - window.innerHeight;
        const last = messages[messages.length - 1];
        const el = answer.current;
        if (last.role === 'user') following.current = true;   // 방금 보낸 질문은 늘 보여 준다
        else if (!following.current) return;
        if (last.role === 'assistant' && !busy && !error && el) {
            const headerH = header.current?.offsetHeight ?? 0;
            const footerH = footer.current?.offsetHeight ?? 0;
            const rect = el.getBoundingClientRect();
            if (rect.height > window.innerHeight - headerH - footerH) {
                scrollToY(Math.min(rect.top + window.scrollY - headerH - 16, end()));
                return;
            }
        }
        scrollToY(end());
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [messages, busy, error]);
    useEffect(() => () => controller.current?.abort(), []);
    // '지금 뜨는 식품'에서 '추천 상품 보기'를 누르고 돌아왔을 때 — 그 상품을 한 번만 물어본다 (2026-10-31)
    useEffect(() => {
        let ask: string | null = null;
        try { ask = sessionStorage.getItem(PENDING_ASK); sessionStorage.removeItem(PENDING_ASK); } catch { /* 저장소 막힘 */ }
        if (ask) void send({ message: ask });
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, []);

    // 브라우저 탭 제목: 첫 화면은 'AI 식품 추천', 세부 화면은 영어 화면명을 앞에 붙인다
    useEffect(() => {
        const last = [...messages].reverse().find(m => m.role === 'assistant');
        const asked = [...messages].reverse().find(m => m.role === 'user');
        document.title = pageTitle({ hasMessages: messages.length > 0, detailOpen: !!detail, purchasing, stage: last?.stage, blocks: last?.blocks,
                                     question: asked?.text });
    }, [messages, detail, purchasing]);

    // 자연어 메시지 · 칩 · 조건 선택(answers) 모두 이 함수로 서버에 보낸다
    async function send(payload: SendPayload, userText?: string) {
        if (locked.current) return;
        if (!payload.message?.trim() && !payload.chip && !payload.answers) return;
        locked.current = true;
        setBusy(true);
        setError('');
        // 첫 화면에서 보낸 질문은 손님이 볼 수 없는 지난 레시피에 이어 읽히지 않게 (2026-11-12 '4인분' → 지난 레시피 인분 답변)
        const fresh = messages.length === 0;
        const shown = userText ?? payload.message?.trim();
        if (shown) setMessages(prev => [...prev, { id: newId(), role: 'user', text: shown }]);
        // 2026-11-12: 레시피는 작성 + 다른 AI 검토로 30초를 넘길 수 있다 — 종류별 안내 문구와 기다리는 시간
        const kind = busyKind(shown ?? payload.message ?? payload.chip);
        setWaitKind(kind);
        const current = new AbortController();
        controller.current = current;
        const timeout = window.setTimeout(() => current.abort('timeout'), BUSY_TIMEOUT_MS[kind]);
        try {
            const response = await sendChat({ session_id: sessionId, ...payload, ...(fresh ? { fresh: true } : {}) }, current.signal);
            if (current.signal.aborted) return;
            setSessionId(response.session_id);
            setMessages(prev => [...prev, { id: newId(), role: 'assistant', blocks: response.blocks, stage: response.stage }]);
        } catch (e) {
            if (current.signal.reason !== 'cancelled')
                setError(current.signal.aborted ? TIMEOUT_MESSAGE[kind] : e instanceof Error ? e.message : '응답 오류');
        } finally {
            clearTimeout(timeout);
            locked.current = false;
            setBusy(false);
            controller.current = null;
        }
    }

    function submit(value: string) {
        const text = value.trim();
        if (!text || locked.current) return;
        setInput('');
        void send({ message: text }, text);
    }

    const closeDetail = useCallback(() => { setDetail(null); setPurchasing(false); }, []);

    // 블록 컴포넌트(칩·조건 선택·상품 카드)가 쓰는 동작
    const actions: ChatActionsValue = useMemo(() => ({
        send: (payload, userText) => void send(payload, userText),
        openDetail: c => { setDetail(c); setPurchasing(false); },
        busy,
        sessionId,
    }), [busy, sessionId]);

    return (
        <ChatActions.Provider value={actions}>
        <SavedProvider sessionId={sessionId}>
        <div className="min-h-dvh bg-paper text-ink">
            <header ref={header} className="sticky top-0 z-10 border-b border-stone-200/70 bg-paper/95 backdrop-blur">
                <div className="mx-auto flex h-[72px] max-w-6xl items-center justify-between px-5 sm:px-8">
                    <a href="./" className="flex items-center gap-2 text-lg font-semibold tracking-tight">
                        <span className="flex h-8 w-8 items-center justify-center rounded-xl bg-ink text-white"><Sparkles size={17} /></span>
                        AI 식품 추천
                    </a>
                    <div className="flex items-center gap-3">
                        <span className="hidden rounded-full border border-stone-200 bg-white px-3 py-1 text-[11px] text-stone-500 md:inline">API 연결 준비 중</span>
                        <div className="hidden sm:flex">
                            <FlowStepper step={step} />
                        </div>
                        {messages.length > 0 && <SavedButton />}
                        <a href="#/trends" className="flex items-center gap-1 rounded-lg p-2 text-xs hover:bg-stone-100" aria-label="지금 뜨는 식품">
                            <TrendingUp size={16} /><span className="hidden sm:inline">지금 뜨는 식품</span>
                        </a>
                        <button className="flex items-center gap-1 rounded-lg p-2 text-xs hover:bg-stone-100" disabled={busy} onClick={() => { setMessages([]); setSessionId(null); setError(''); setInput(''); closeDetail(); }}>
                            <Plus size={16} /><span className="hidden sm:inline">새 대화</span>
                        </button>
                    </div>
                </div>
            </header>

            <main className="mx-auto w-full max-w-[900px] px-4 pb-8 pt-8 sm:px-8">
                {!messages.length ? (
                    <section className="pb-12 pt-8 sm:pt-16">
                        <div className="mb-5 inline-flex items-center gap-2 rounded-full border border-stone-200 bg-white px-4 py-2.5 text-sm text-accent">
                            <Sparkles size={18} />더 쉬운 선택의 시작
                        </div>
                        <h1 className="text-3xl font-medium leading-[1.35] tracking-tight sm:text-4xl">
                            식품 구매, <span className="text-accent">무엇이든 물어보세요!</span>
                        </h1>
                        <p className="mt-5 text-sm leading-7 text-stone-500 sm:text-base">
                            원하는 상품이나 만들고 싶은 요리를 말해 주세요.<br />중요한 조건을 확인하고, 비교하기 쉽게 정리해 드려요.
                        </p>
                        {/* 제휴 수수료 고지 — 첫 화면 첫 부분 (공정위 추천·보증 심사지침, 쿠팡 파트너스 정책) */}
                        <p className="mt-4 rounded-xl border border-stone-200 bg-white px-4 py-3 text-sm leading-7 text-stone-600">
                            <strong className="font-semibold text-ink">광고 · 제휴 링크 안내</strong>{' '}
                            이 사이트는 쿠팡 파트너스 활동의 일환으로, 이에 따른 일정액의 수수료를 제공받습니다.
                            수수료는 본 사이트 운영과 무료 서비스 유지에 도움이 되며, 추천 순위에는 반영하지 않습니다.
                        </p>

                        {/* 예시 질문 버튼 렌더링 영역 (모바일 1열, PC 2x2 그리드) */}
                        <div className="mt-9 grid gap-3 grid-cols-1 sm:grid-cols-2">
                            {examples.map(({ icon: Icon, ...item }) => {
                                return (
                                    <button key={item.text} type="button" disabled={busy} onClick={() => submit(item.text)} className="group flex flex-col justify-between rounded-2xl border border-stone-200 bg-white p-5 text-left transition hover:-translate-y-1 hover:border-accent/40 hover:shadow-sm">
                                        <div>
                                            <div className="mb-4 flex items-center gap-2">
                                                <span className="flex h-9 w-9 items-center justify-center rounded-full bg-accent/10 text-accent">
                                                    <Icon size={20} />
                                                </span>
                                                <span className="rounded-full bg-stone-100 px-2.5 py-1 text-xs font-semibold text-stone-600">
                                                    {item.label}
                                                </span>
                                            </div>
                                            <p className="text-lg font-medium leading-relaxed text-ink break-keep">
                                                "{item.text}"
                                            </p>
                                        </div>
                                        <div className="mt-5 flex w-full items-center justify-between text-sm text-stone-400">
                                            <span>{item.note}</span>
                                            <ArrowRight size={16} className="transition group-hover:text-accent group-hover:translate-x-1" />
                                        </div>
                                    </button>
                                );
                            })}
                        </div>
                        {examplesDate && <p className="mt-3 text-right text-[11px] text-stone-400">예시 질문 기준일 {examplesDate} · 네이버 식품 키워드 순위</p>}
                        <p className="mt-7 text-center text-xs text-stone-400">조건 확인 → 후보 비교 → 근거 확인 → 판매처 연결</p>
                    </section>
                ) : (
                    <div className="space-y-8">
                        {messages.map((message, i) => (
                            <section key={message.id} ref={i === messages.length - 1 ? answer : undefined} className={message.role === 'user' ? 'flex justify-end' : 'min-w-0'} aria-label={message.role === 'user' ? '내 질문' : 'AI 응답'}>
                                {message.role === 'user' ? (
                                    <p className="max-w-[88%] whitespace-pre-wrap break-words rounded-3xl rounded-tr-md bg-[#eaece5] px-5 py-3 text-sm leading-7">{message.text}</p>
                                ) : (
                                    <>
                                        <div className="mb-4 flex items-center gap-2 text-xs font-semibold"><Sparkles size={16} className="text-accent" />AI 식품 추천</div>
                                        <BlockRenderer blocks={message.blocks ?? []} />
                                    </>
                                )}
                            </section>
                        ))}
                        <div role="status">{busy && <BusyStatus kind={waitKind} />}</div>
                    </div>
                )}
                {error && <div role="alert" className="mt-4 rounded-xl bg-red-50 p-4 text-sm text-red-700">{error}</div>}
            </main>

            <footer ref={footer} className="sticky bottom-0 mx-auto w-full max-w-[900px] bg-gradient-to-t from-paper via-paper to-paper/90 px-4 pb-[max(1rem,env(safe-area-inset-bottom))] pt-4 sm:px-8">
                <form onSubmit={e => { e.preventDefault(); submit(input); }} className="rounded-3xl border border-stone-200 bg-white p-3 shadow-[0_4px_24px_#00000006] transition focus-within:border-stone-300 focus-within:shadow-[0_4px_24px_#0000000f]">
                    <label htmlFor="prompt" className="sr-only">쇼핑 질문</label>
                    <textarea id="prompt" value={input} onChange={e => setInput(e.target.value)} rows={2} maxLength={4000} placeholder={inRecipe ? '재료나 만드는 방법을 물어보세요' : '어떤 상품을 찾으세요? 예산과 원하는 조건을 알려주세요.'} className="max-h-40 min-h-14 w-full resize-y bg-transparent px-2 py-1 text-sm leading-6 outline-none placeholder:text-stone-400" onKeyDown={e => { if (e.key === 'Enter' && !e.shiftKey && !e.nativeEvent.isComposing) { e.preventDefault(); submit(input); } }} />
                    <div className="flex items-center justify-between px-1">
                        <span className="text-[11px] text-stone-400">추천 정보는 판매처에서 최종 확인해 주세요</span>
                        {busy ? (
                            <button type="button" aria-label="응답 중단" className="send" onClick={() => controller.current?.abort('cancelled')}><Square size={15} /></button>
                        ) : (
                            <button type="submit" className="send" aria-label="질문 보내기" disabled={!input.trim()}><ArrowUp size={18} /></button>
                        )}
                    </div>
                </form>
                <p className="mt-3 text-center text-[10px] text-stone-400">쿠팡 파트너스 활동의 일환으로 일정액의 수수료를 제공받습니다.{hasConnect && ' 네이버 쇼핑커넥트 링크로 구매하셔도 수수료를 제공받습니다.'} 수수료는 본 사이트 운영에 도움이 됩니다. 가격·배송·리뷰는 확인 시점에 따라 달라질 수 있어요.</p>
            </footer>

            <SavedPanel />
            {detail && <ProductDetail key={detail.key} c={detail} sessionId={sessionId} purchasing={purchasing} onPurchasing={setPurchasing} onClose={closeDetail} />}
        </div>
        </SavedProvider>
        </ChatActions.Provider>
    );
}

// 관심 상품 버튼 — 대화를 시작한 뒤에만 보인다 (첫 화면 디자인은 그대로, 2026-11-01)
function SavedButton() {
    const { view, setOpen } = useSaved();
    return (
        <button type="button" onClick={() => setOpen(true)} className="flex items-center gap-1 rounded-lg p-2 text-xs hover:bg-stone-100" aria-label={`관심 상품 ${view.saved.length}개`}>
            <Heart size={16} className={view.saved.length ? 'text-[#c62828]' : ''} fill={view.saved.length ? 'currentColor' : 'none'} />
            <span className="hidden sm:inline">관심 상품</span>
            {view.saved.length > 0 && <span className="rounded-full bg-ink px-1.5 text-[10px] font-bold text-white">{view.saved.length}</span>}
        </button>
    );
}
