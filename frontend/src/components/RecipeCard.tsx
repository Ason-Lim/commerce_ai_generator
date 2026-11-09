import { useEffect, useState } from "react";
import { AlertTriangle, BookOpen, Check, CheckCircle2, ChefHat, Clock, Flame, Lightbulb, ListChecks, Loader2, ShoppingBasket, Wrench } from "lucide-react";
import type { RecipeCardBlock, RecipeEasyStep, RecipeEasyView, RecipeGeneralTips, RecipeHero, RecipeStockStatus, RecipeSupplement } from "../types/blocks";
import { fetchRecipeEasy } from "../api/client";
import { useChatActions } from "./ChatActions";
import { cx } from "../lib/format";

/**
 * 레시피 카드 (commerce /api/chat 의 recipe_card 블록). 순서: 완성 사진 → 특징·전체 진행 → 재료 → 부족한 재료 → 만드는 순서 → 팁 → 출처.
 * - 사진: 공공데이터 사진(이용 조건 확인한 출처만), 없으면 'AI 생성 예시 이미지' 표시를 단 AI 이미지.
 * - 만드는 순서(easy-v2): 번호 목록. 단계마다 할 일 + 완료 신호(원문 구절이면 '원문', 아니면 '일반 제안'),
 *   원문 신호는 원문 구절 그대로 보여 준다(바꿔 쓴 문장은 쓰지 않음, easy-v3).
 *   2026-10-30: 단계마다 '원문/일반 제안' 배지를 반복하지 않는다. 원문이 기본이고, 일반 제안에만 작은 * 를 붙여
 *   맨 아래에서 한 번 설명한다. 주의(caution)만 강조하고 '잘 안 되면'은 흐리게.
 *   필요한 단계에만 주의·잘 안 되면(항상 '일반 제안'). 서버가 원문과 대조해 순서·재료 투입·분량·숫자를 검사한 것만 온다.
 *   준비 중이거나 다듬지 못했으면 공공데이터 문장을 번호 목록으로 그대로 보여 준다. 단계를 큰 카드로 감싸지 않는다.
 * - 재료: 원문 기준 인분 + 원문 분량. 컵 용량을 원문이 정하지 않으므로 기본 표에는 mL 환산을 넣지 않는다
 *   (고객이 기준을 고른 경우에만 서버가 reference 를 보낸다).
 * - 인분·시간·난이도·열량은 원문 표기 그대로이며 그렇게 표시한다.
 * - 출처는 맨 아래에서 원문과 일반 조리 제안을 구분해 밝힌다.
 * - '부족해요'·'없어요'는 버튼이다(누르면 대화 메시지로 전송·기록). 누르지 않은 재료는 부족으로 보지 않는다.
 *   답한 뒤에는 '내 답변: 부족' 태그로 상태를 보여 준다. 남은 양만으로 부족을 정하지 않는다.
 * - 재료 행은 재료명·현재 인분 분량·'부족해요'만 (2026-10-30). '원문 분량 보기'·'눈대중으로 보기'를 켤 때만
 *   원문 분량(인분 변경 시)과 눈대중 참고를 펼친다. 눈대중은 대략적인 참고이고 계산에 쓰지 않는다.
 * - 상품 검색은 '부족한 재료 상품 보기'를 눌렀을 때만.
 * - 재료 체크(준비)는 이 화면에서만 쓰는 표시다(서버에 저장하지 않음).
 */

const POLL_MS = 2500;
const POLL_MAX = 36; // 약 1분 30초 (이미지 생성은 쉽게 보기보다 오래 걸린다)

const STATUS_STYLE: Record<RecipeStockStatus, string> = {
  short: "bg-warnSoft text-warn",
  absent: "bg-warnSoft text-warn",
  enough: "bg-accentSoft text-accent",
  have: "bg-chip text-ink2",
};

function metaIcon(m: string) {
  if (/분$|시간/.test(m)) return <Clock size={13} aria-hidden />;
  if (/kcal/i.test(m)) return <Flame size={13} aria-hidden />;
  if (/^난이도/.test(m)) return <ChefHat size={13} aria-hidden />;
  return null;
}

/** 이미지가 없거나 불러오지 못하면 영역 자체를 숨긴다 (빈 상자를 남기지 않음) */
function Photo({ src, alt, className }: { src: string | null | undefined; alt: string; className: string }) {
  const [failed, setFailed] = useState(false);
  if (!src || failed) return null;
  return <img src={src} alt={alt} loading="lazy" referrerPolicy="no-referrer" onError={() => setFailed(true)} className={className} />;
}

function Hero({ hero, title }: { hero: RecipeHero; title: string }) {
  const [failed, setFailed] = useState(false);
  if (failed) return null;
  return (
    <figure className="relative">
      <img src={hero.src} alt={hero.kind === "ai" ? `${title} AI 생성 예시 이미지` : `${title} 완성 사진`}
        referrerPolicy="no-referrer" onError={() => setFailed(true)}
        className="h-44 w-full bg-chip object-cover sm:h-64" />
      {hero.kind === "ai" && hero.label && (
        <figcaption className="absolute bottom-2 left-2 rounded-full bg-black/55 px-2.5 py-1 text-[11px] font-medium text-white backdrop-blur-sm">
          {hero.label}
        </figcaption>
      )}
    </figure>
  );
}

/** "약 300mL (1컵=200mL 기준 · 참고)" → "약 300mL" (기준 설명은 재료 아래 한 번만) */
const shortRef = (r: string) => r.split(" (")[0];


/** 원문에 없는 일반 조리 제안 표시 — 반복 배지 대신 작은 * (뜻은 카드 맨 아래 한 번만 설명) */
function Suggested() {
  return (
    <sup className="ml-0.5 text-[11px] font-semibold text-ink3" title="일반 조리 제안 (원문에 없음)">
      *<span className="sr-only">일반 조리 제안</span>
    </sup>
  );
}

function EasyStep({ s, last }: { s: RecipeEasyStep; last: boolean }) {
  return (
    <li className="flex gap-3 py-3 first:pt-1 last:pb-1">
      <span className="mt-0.5 grid h-6 w-6 shrink-0 place-items-center rounded-full bg-accent text-xs font-bold text-surface">{s.no}</span>
      <div className="min-w-0 flex-1 space-y-1">
        <p className="font-semibold">{s.title}</p>
        <p className="text-[15px] leading-relaxed text-ink2">{s.text}</p>
        {s.done && (
          <p className="flex gap-1.5 text-sm leading-relaxed text-ink2">
            <CheckCircle2 size={15} className="mt-[3px] shrink-0 text-accent" aria-hidden />
            <span><span className="text-ink3">{last ? "완성" : "다음으로"}</span>{" "}
              {s.done.basis === "source" ? (s.done.quote ?? s.done.text) : s.done.text}
              {s.done.basis !== "source" && <Suggested />}</span>
          </p>
        )}
        {(s.notes ?? []).map((n) => (
          n.kind === "caution" ? (
            <p key={n.text} className="flex gap-1.5 text-sm leading-relaxed text-ink">
              <AlertTriangle size={15} className="mt-[3px] shrink-0 text-warn" aria-label="주의" />
              <span>{n.text}<Suggested /></span>
            </p>
          ) : (
            <p key={n.text} className="flex gap-1.5 text-sm leading-relaxed text-ink3">
              <Wrench size={14} className="mt-[3px] shrink-0" aria-label="잘 안 되면" />
              <span>{n.text}<Suggested /></span>
            </p>
          )
        ))}
      </div>
      <Photo src={s.image} alt={`${s.title} 사진`} className="h-16 w-24 shrink-0 rounded-xl object-cover sm:h-20 sm:w-28" />
    </li>
  );
}

export function RecipeCard({ block }: { block: RecipeCardBlock }) {
  const d = block.data;
  const { send, busy } = useChatActions();
  const [easy, setEasy] = useState<RecipeEasyView | null>(d.easy ?? null);
  const [tips, setTips] = useState<RecipeGeneralTips | null>(d.general_tips ?? null);
  const [hero, setHero] = useState<RecipeHero | null>(d.hero ?? null);
  const [easyPending, setEasyPending] = useState(d.easy_status === "pending" && !d.easy);
  const [heroPending, setHeroPending] = useState(d.hero_status === "pending" && !d.hero);
  // 원문에 빠진 핵심 단계를 AI가 보충한 것 (원문 아님 표시)
  const [supp, setSupp] = useState<RecipeSupplement | null>(d.supplement ?? null);
  const [suppPending, setSuppPending] = useState(d.supplement_status === "pending" && !d.supplement);
  const pending = easyPending || heroPending || suppPending;

  // 쉽게 보기 / AI 사진이 준비 중이면 잠깐 물어본다 (서버는 새 작업을 시작하지 않음)
  useEffect(() => {
    if (!pending || !d.easy_key) return;
    const ctrl = new AbortController();
    let tries = 0;
    let timer = 0;
    const stop = () => { setEasyPending(false); setHeroPending(false); setSuppPending(false); };
    const tick = async () => {
      tries += 1;
      try {
        const r = await fetchRecipeEasy(d.recipe_id, d.easy_key!, ctrl.signal);
        let waiting = false;
        if (r.status === "ready" && r.easy) {
          setEasy(r.easy);
          if (r.general_tips) setTips(r.general_tips);
          setEasyPending(false);
        } else if (r.status === "pending") waiting = true; else setEasyPending(false);
        if (r.hero_status === "ready" && r.hero) { setHero(r.hero); setHeroPending(false); }
        else if (r.hero_status === "pending") waiting = true; else setHeroPending(false);
        if (r.supplement) { setSupp(r.supplement); setSuppPending(false); }
        else if (r.supplement_status === "pending") waiting = true; else setSuppPending(false);
        if (!waiting || tries >= POLL_MAX) { stop(); return; }
      } catch {
        if (ctrl.signal.aborted || tries >= 3) { stop(); return; }
      }
      timer = window.setTimeout(tick, POLL_MS);
    };
    timer = window.setTimeout(tick, POLL_MS);
    return () => { ctrl.abort(); clearTimeout(timer); };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [pending, d.recipe_id, d.easy_key]);

  const [checked, setChecked] = useState<Set<string>>(() => new Set());
  // 이 화면에서 '부족/없음'을 눌러 보낸 재료 (서버 응답 전에도 바로 보이게)
  const [marked, setMarked] = useState<Record<string, RecipeStockStatus>>({});
  const keyOf = (i: { id: string | null; name: string }) => i.id ?? i.name;
  const total = d.ingredients.length;
  const ready = d.ingredients.filter((i) => checked.has(keyOf(i))).length;
  const toggle = (key: string) =>
    setChecked((prev) => {
      const next = new Set(prev);
      if (next.has(key)) next.delete(key); else next.add(key);
      return next;
    });
  const statusOf = (i: { id: string | null; name: string; status?: RecipeStockStatus | null }) =>
    marked[keyOf(i)] ?? i.status ?? null;
  const markShort = (i: { id: string | null; name: string; quantity_known?: boolean }) => {
    const absent = !i.quantity_known;
    const text = absent ? `${i.name} 없어요` : `${i.name} 부족해요`;
    setMarked((m) => ({ ...m, [keyOf(i)]: absent ? "absent" : "short" }));
    send({ message: text }, text);
  };

  // 다른 인분일 때 한 '부족' 답변은 지금 부족으로 세지 않고 '다시 확인'으로 따로 보여 준다 (기록은 서버에 그대로)
  const staleOf = (i: { id: string | null; name: string; status_stale?: boolean }) => !!i.status_stale && !marked[keyOf(i)];
  const shortage = [
    ...d.ingredients.filter((i) => ["short", "absent"].includes(statusOf(i) ?? "") && !staleOf(i)).map((i) => i.name),
    ...d.extra_ingredients.filter((e) => ["short", "absent"].includes(e.status ?? "")).map((e) => e.name),
  ];
  const recheck = d.ingredients.filter((i) => statusOf(i) === "short" && staleOf(i)).map((i) => i.name);

  const showEasy = !!easy;
  const hasGauge = d.ingredients.some((i) => i.gauge);
  // 2026-10-30: 기본 행은 재료명·현재 인분 분량·부족해요만. 원문 분량과 눈대중은 펼쳐 볼 때만 (기본 접힘)
  const hasSource = !!d.servings_scaled || d.ingredients.some((i) => i.reference) || d.notes.length > 0;
  const [showSource, setShowSource] = useState(false);
  const [showGauge, setShowGauge] = useState(false);
  const summary = showEasy && (easy!.overview?.feature || easy!.summary) ? (easy!.overview?.feature || easy!.summary) : d.summary;
  const flow = showEasy ? easy!.overview?.flow : undefined;
  const provider = d.source.provider ?? d.source.name;
  // AI 제안 레시피 (원문 아님): 분량·순서가 AI 제안임을 카드 곳곳에서 밝힌다
  const isAi = d.source.level === "ai_suggestion";
  const basisWord = isAi ? "제안" : "원문";

  return (
    <article className="card my-3 overflow-hidden" aria-label={`${d.title} 레시피`}>
      {hero ? (
        <Hero hero={hero} title={d.title} />
      ) : heroPending ? (
        <div className="grid h-44 w-full animate-pulse place-items-center bg-chip text-ink3 sm:h-64">
          <span className="flex items-center gap-1.5 text-xs"><Loader2 size={14} className="animate-spin" aria-hidden />완성 사진을 준비하고 있어요</span>
        </div>
      ) : null}

      <div className="space-y-4 p-4 sm:p-5">
        <header className="flex items-start gap-4">
          {!hero && !heroPending && (
            <div className="grid h-16 w-16 shrink-0 place-items-center rounded-2xl bg-accentSoft text-accent sm:h-20 sm:w-20" aria-hidden>
              <ChefHat size={30} strokeWidth={1.6} />
            </div>
          )}
          <div className="min-w-0 flex-1 space-y-2">
            {isAi && <span className="tag bg-reviewSoft text-review">{d.source.label}</span>}
            <h3 className="text-xl font-bold leading-snug tracking-tight sm:text-2xl">{d.title}</h3>
            {summary && <p className="text-[15px] leading-relaxed text-ink2">{summary}</p>}
            {flow && <p className="text-sm leading-relaxed text-ink2"><b className="font-semibold text-ink">전체 진행</b> {flow}</p>}
            {d.meta.length > 0 && (
              <div className="flex flex-wrap items-center gap-1.5">
                {d.meta.map((m) => (
                  <span key={m} className="tag bg-chip text-ink2">{metaIcon(m)}{m}</span>
                ))}
                <span className="text-[11px] text-ink3">{basisWord} 표기</span>
              </div>
            )}
          </div>
        </header>

        <section aria-label="재료" className="rounded-2xl border border-line">
          <div className="flex items-center justify-between border-b border-line px-4 py-2.5">
            <h4 className="flex items-center gap-1.5 text-sm font-bold">
              <ListChecks size={15} className="shrink-0" aria-hidden /><span className="shrink-0">재료</span>
              <span className="font-normal text-ink3">· {d.servings ? `${d.servings} 기준` : `${basisWord} 분량`}{isAi && d.servings && " · AI 제안 분량"}</span>
            </h4>
            <span className="shrink-0 whitespace-nowrap text-xs text-ink3" aria-live="polite" title="준비했는지 표시하는 체크예요. 저장하지 않아요.">준비 체크 {ready}/{total}</span>
          </div>
          {(hasSource || hasGauge) && (
            <div className="flex flex-wrap items-center gap-1.5 border-b border-line px-4 py-2">
              {hasSource && (
                <button type="button" aria-pressed={showSource} onClick={() => setShowSource((v) => !v)}
                  className={cx("rounded-full border px-2.5 py-0.5 text-xs transition", showSource ? "border-ink3 bg-chip text-ink" : "border-line text-ink3 hover:text-ink2")}>
                  {basisWord} 분량 보기
                </button>
              )}
              {hasGauge && (
                <button type="button" aria-pressed={showGauge} onClick={() => setShowGauge((v) => !v)}
                  className={cx("rounded-full border px-2.5 py-0.5 text-xs transition", showGauge ? "border-ink3 bg-chip text-ink" : "border-line text-ink3 hover:text-ink2")}>
                  눈대중으로 보기
                </button>
              )}
              {showSource && d.servings_scaled && <span className="text-[11px] text-ink3">{basisWord} {d.servings_source}에서 계산했어요</span>}
              {showGauge && <span className="text-[11px] text-ink3">눈대중은 대략적인 참고예요 · 남은 양·부족 계산에는 쓰지 않아요</span>}
            </div>
          )}
          <ul className="divide-y divide-line">
            {d.ingredients.map((i) => {
              const key = keyOf(i);
              const on = checked.has(key);
              const st = statusOf(i);
              const label = marked[key] ? (marked[key] === "absent" ? "없음" : "부족") : i.status_label;
              const ask = i.quantity_known ? "부족해요" : "없어요";
              return (
                <li key={key} className="flex items-center gap-2 pr-3">
                  <button type="button" role="checkbox" aria-checked={on} onClick={() => toggle(key)}
                    className="flex min-w-0 flex-1 items-center gap-3 py-2.5 pl-4 text-left transition hover:bg-chip/50">
                    <span className={cx("grid h-5 w-5 shrink-0 place-items-center rounded-full border",
                      on ? "border-accent bg-accent text-surface" : "border-line bg-surface")}>
                      {on && <Check size={13} strokeWidth={3} aria-hidden />}
                    </span>
                    <span className="min-w-0 flex-1">
                      <span className={cx("whitespace-nowrap text-[15px]", on && "text-ink3 line-through")}>{i.name}</span>
                      {(st || i.stock) && (
                        <span className="ml-2 inline-flex flex-wrap gap-1 align-middle">
                          {st && label && (
                            <span className={cx("tag", i.status_stale && !marked[key] ? "bg-chip text-ink3" : STATUS_STYLE[st])}
                              title={i.status_stale ? `${i.status_servings} 기준으로 알려 주신 답변이에요. 지금 인분 기준으로는 다시 확인이 필요해요.` : "직접 알려 주신 답변"}>
                              내 답변: {label}{i.status_stale && !marked[key] ? ` · ${i.status_servings} 기준` : ""}
                            </span>
                          )}
                          {i.stock && <span className="tag bg-chip text-ink2">남은 양 {i.stock}</span>}
                        </span>
                      )}
                      {showGauge && i.gauge && <span className="mt-0.5 block text-[11px] leading-snug text-ink3">{i.gauge}</span>}
                    </span>
                    <span className="shrink-0 text-right text-[15px] font-semibold">
                      {i.amount || <span className="font-normal text-ink3">분량 표기 없음</span>}
                      {showSource && i.reference && <span className="block text-[11px] font-normal text-ink3" title={i.reference}>{shortRef(i.reference)}</span>}
                      {showSource && i.scaled && i.source_amount && <span className="block text-[11px] font-normal text-ink3">{basisWord} {i.source_amount}</span>}

                    </span>
                  </button>
                  {(!(st === "short" || st === "absent") || staleOf(i)) && (
                    <button type="button" disabled={busy} onClick={() => markShort(i)}
                      aria-label={`${i.name} ${ask}라고 알리기`}
                      className="shrink-0 rounded-full border border-line px-2.5 py-1 text-xs text-ink2 transition hover:border-ink3 hover:text-ink disabled:opacity-40">
                      {ask}
                    </button>
                  )}
                </li>
              );
            })}
          </ul>
          {d.extra_ingredients.length > 0 && (
            <p className="border-t border-line px-4 py-2.5 text-xs text-ink2">
              <b className="font-semibold">조리 과정에만 나와요</b>{" "}
              {d.extra_ingredients.map((e) => `${e.name}(${e.short ?? e.note})`).join(", ")}
            </p>
          )}
          {showSource && d.notes.map((n) => (
            <p key={n} className="border-t border-line px-4 py-2 text-xs leading-relaxed text-ink3">{n}</p>
          ))}
        </section>

        <section aria-label="부족한 재료" className={cx("rounded-2xl px-4 py-3", shortage.length ? "bg-warnSoft/50" : "bg-chip/50")}>
          <h4 className="flex items-center gap-1.5 text-sm font-bold">
            <ShoppingBasket size={15} aria-hidden />부족한 재료{shortage.length > 0 && <span className="text-warn">{shortage.length}</span>}
          </h4>
          {recheck.length > 0 && (
            <p className="mt-1 text-xs leading-relaxed text-ink2">
              다시 확인: {recheck.join(", ")} — 다른 인분일 때 '부족'이라고 하셨어요. 지금 인분에서도 부족하면 '부족해요'를 눌러 주세요.
            </p>
          )}
          {shortage.length > 0 ? (
            <div className="mt-2 flex flex-wrap items-center gap-2">
              {shortage.map((n) => <span key={n} className="tag bg-surface text-ink">{n}</span>)}
              <button type="button" disabled={busy} onClick={() => send({ message: "부족한 재료 상품 보여줘" }, "부족한 재료 상품 보여줘")}
                className="ml-auto rounded-full bg-ink px-3.5 py-1.5 text-sm font-semibold text-surface transition hover:opacity-90 disabled:opacity-30">
                부족한 재료 상품 보기
              </button>
            </div>
          ) : (
            <p className="mt-1 text-xs leading-relaxed text-ink3">
              모자라거나 없는 재료만 오른쪽 '부족해요'·'없어요'를 눌러 알려 주세요. 누르지 않은 재료는 부족으로 보지 않아요.
              왼쪽 동그라미는 준비 체크(저장 안 함)이고, 남은 양은 "생크림 100mL 있어요"처럼 말씀해 주시면 기록해요.
            </p>
          )}
        </section>

        <section aria-label="만드는 순서" className="space-y-2.5">
          <div className="flex flex-wrap items-center justify-between gap-2">
            <h4 className="flex items-center gap-1.5 text-sm font-bold">
              <BookOpen size={15} aria-hidden />만드는 순서
            </h4>
            {easyPending && (
              <span className="flex items-center gap-1.5 text-xs text-ink3" aria-live="polite">
                <Loader2 size={14} className="animate-spin" aria-hidden />읽기 쉽게 다듬고 있어요
              </span>
            )}
          </div>
          {showEasy ? (
            <ol className="divide-y divide-line">
              {easy!.steps.map((s, k) => <EasyStep key={s.no} s={s} last={k === easy!.steps.length - 1} />)}
            </ol>
          ) : (
            <ol className="divide-y divide-line">
              {d.steps.map((s) => (
                <li key={s.no} className="flex gap-3 py-3 first:pt-1 last:pb-1">
                  <span className="mt-0.5 grid h-6 w-6 shrink-0 place-items-center rounded-full bg-accent text-xs font-bold text-surface">{s.no}</span>
                  <p className="min-w-0 flex-1 text-[15px] leading-relaxed">{s.text}</p>
                  <Photo src={s.image} alt={`${s.no}단계 사진`} className="h-16 w-24 shrink-0 rounded-xl object-cover sm:h-20 sm:w-28" />
                </li>
              ))}
            </ol>
          )}
        </section>

        {d.source_gap && (
          <section aria-label="원문에 없는 단계" className="rounded-2xl border border-dashed border-line px-4 py-3">
            <p className="flex flex-wrap items-center gap-2 text-sm font-semibold text-ink">
              <AlertTriangle size={15} className="text-warn" aria-hidden />{d.source_gap}
              {supp && <span className="tag bg-reviewSoft text-review">{supp.label}</span>}
            </p>
            {supp ? (
              <>
                <p className="mt-1 text-xs leading-relaxed text-ink3">원문 단계 다음에 이어질 내용을 AI가 일반 조리 제안으로 보충했어요. 원문에는 없는 내용이에요.</p>
                <ol className="mt-1 divide-y divide-line">
                  {supp.steps.map((st, k) => (
                    <li key={st.title} className="flex gap-3 py-3 last:pb-1">
                      <span className="mt-0.5 grid h-6 w-6 shrink-0 place-items-center rounded-full border border-review text-xs font-bold text-review">{d.steps.length + k + 1}</span>
                      <p className="min-w-0 flex-1 text-[15px] leading-relaxed"><b className="font-semibold">{st.title}</b> — {st.text}</p>
                    </li>
                  ))}
                </ol>
              </>
            ) : suppPending ? (
              <p className="mt-1 flex items-center gap-1.5 text-xs text-ink3" aria-live="polite">
                <Loader2 size={14} className="animate-spin" aria-hidden />빠진 단계를 일반 조리 제안으로 보충하고 있어요
              </p>
            ) : (
              <p className="mt-1 text-xs leading-relaxed text-ink3">이 단계는 원문에 없어 안내하지 못했어요. 비슷한 다른 원문 레시피도 살펴보세요.</p>
            )}
          </section>
        )}

        {d.tips.length > 0 && (
          <section aria-label="레시피 팁" className="rounded-2xl bg-accentSoft/50 px-4 py-3">
            <h4 className="mb-1 flex items-center gap-1.5 text-sm font-bold text-accent"><Lightbulb size={15} aria-hidden />레시피 팁</h4>
            <ul className="space-y-1 text-sm leading-relaxed text-ink2">
              {d.tips.map((t) => <li key={t}>{t}</li>)}
            </ul>
          </section>
        )}

        {tips && tips.items.length > 0 && (
          <section aria-label="맛있게 만드는 팁" className="rounded-2xl border border-line px-4 py-3">
            <div className="mb-1.5 flex flex-wrap items-center gap-2">
              <h4 className="flex items-center gap-1.5 text-sm font-bold"><Lightbulb size={15} aria-hidden />맛있게 만드는 팁</h4>
              <span className={cx("tag", tips.kind === "ai" ? "bg-reviewSoft text-review" : "bg-chip text-ink3")}>{tips.label}</span>
            </div>
            <ul className="space-y-1.5 text-sm leading-relaxed text-ink2">
              {tips.items.map((t) => (
                <li key={t.title}><b className="font-semibold text-ink">{t.title}</b> — {t.text}</li>
              ))}
            </ul>
          </section>
        )}

        <footer className="text-xs leading-relaxed text-ink3">
          {isAi ? (
            <p>
              AI가 일반 조리 지식으로 만든 제안 레시피예요. 특정 블로그·유명인의 레시피를 재현한 것이 아니며, 재료 분량·조리 시간은 검증하지 않았어요.
              외부 원문의 분량을 옮긴 것이 아니에요.
              {d.generated && ` AI 생성: ${[d.generated.servings && `${d.generated.servings} 기준`, `재료 ${d.generated.ingredients}개`,
                `${d.generated.steps}단계`, d.generated.at, d.generated.model].filter(Boolean).join(" · ")}.`}
            </p>
          ) : (
          <p>
            출처: {provider} 「{d.title}」 공공데이터.
            {showEasy || supp
              ? " 재료·분량·시간·열량은 원문 그대로이고, 조리 설명은 원문을 참조해 정리한 것으로 원문 그대로가 아니에요."
              : " 재료·분량·조리 순서·시간·열량은 원문 그대로예요."}
            {showEasy ? " 조리 설명은 AI가 원문을 읽기 쉽게 다듬었고, * 표시는 원문에 없는 일반 조리 제안이에요." : ""}
            {supp ? ` '${supp.action}' 단계(${d.steps.length + 1}단계~)는 원문에 없어 AI가 보충한 일반 조리 제안이에요.` : ""}
            {hero?.kind === "ai" && " 맨 위 사진은 AI가 만든 예시 이미지예요."}
          </p>
          )}
        </footer>
      </div>
    </article>
  );
}
