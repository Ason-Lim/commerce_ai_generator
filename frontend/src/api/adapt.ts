/**
 * 백엔드 응답 → 화면 블록 정규화.
 *
 * 1) 같은 블록의 형식 차이를 흡수한다 (text.md / text.text, chips 문자열 / 객체 …)
 * 2) 주 추천 결과(카드 3장 이상)는 ③ 후보 비교(candidate_compare)로 묶는다.
 *    카드 2장짜리 comparison_pair(후속 1:1 비교)는 split view 그대로 둔다.
 * 3) is_sponsored 카드는 일반 추천에서 빼서 sponsored_list 로 분리한다.
 */
import type {
  ApiCard, Block, Candidate, ChatResponse, ChipItem, ClarifyFormBlock, ClarifyQuestion,
} from "../types/blocks";
import { parseWeightFromTitle, per100g, volumeLabel, weightLabel, won } from "../lib/format";

export const toChip = (c: string | ChipItem): ChipItem => (typeof c === "string" ? { label: c } : c);

export function cardToCandidate(c: ApiCard): Candidate {
  // 2026-11-13: 서버가 배송비 상태를 주면 총액은 'confirmed' 일 때만. 무료 표시·적힌 배송비는 총액으로 합치지 않는다.
  const status = c.shipping_status ?? null;
  const ship = c.shipping_fee ?? null;
  const total = status ? (status === "confirmed" ? c.total ?? null : null) : c.total ?? (ship != null ? c.price + ship : null);
  // 2026-11-11: 서버가 중량·100g당을 내려 주면(값이 null 이어도) 그대로 쓴다 — 옵션 목록·증정분처럼 서버가 일부러
  // 비운 값을 화면이 상품명 첫 중량으로 다시 채우지 않게. 필드가 아예 없는 예전 응답에만 상품명 추정을 쓴다.
  const serverWeighed = c.weight_g !== undefined || c.weight_note != null;
  const g = serverWeighed ? (c.weight_g ?? null) : parseWeightFromTitle(c.title);
  const reasons = c.why?.length ? c.why.map((w) => w.text) : [c.reasoning || c.reason].filter((x): x is string => !!x);
  return {
    rank: c.rank,
    key: c.key ? `k:${c.key}` : `${c.mall ?? "m"}:${c.pid ?? c.title}`,
    title: c.title,
    image: c.image ?? c.image_url ?? null,
    source: c.source ?? c.mall ?? "판매처",
    mall: c.mall,
    price: c.price,
    shippingFee: ship,
    total,
    shippingStatus: status,
    weightLabel: weightLabel(g) ?? volumeLabel(c.volume_ml),
    per100g: c.per100g !== undefined ? c.per100g : serverWeighed ? null : per100g(total ?? c.price, g),
    per100ml: c.per100ml ?? null,
    weightNote: c.weight_note ?? null,
    varietyMix: c.variety_mix ?? null,
    unitLabel: c.unit_price && c.unit_count ? `${c.unit_count}개 · 개당 약 ${won(c.unit_price)}` : null,
    delivery: c.delivery_terms ? { label: c.delivery_terms, verified: true }
      : c.rocket ? { label: "로켓배송 표시", verified: true } : null,
    reasons,
    evidence: c.evidence ?? [],
    unverified: [
      ...(c.unverified ?? []),
      ...(ship == null ? ["배송비"] : []),
      // 도착 예정일은 판매처 API가 주지 않는 경우가 많아 '미확인' 경고 대신 카드의 안내 문구로 보여준다
      ...(c.delivery_terms || c.check_at_mall ? [] : ["도착 예정일"]),
    ].filter((v, i, a) => a.indexOf(v) === i),
    badges: c.badges ?? [],
    observed: c.observed,
    stale: c.stale,
    url: c.url,
    isSample: c.is_sample,
    isSponsored: c.is_sponsored,
    affiliate: c.affiliate,
    affiliateProgram: c.affiliate_program,
    direct: c.direct === true,
    checkAtMall: c.check_at_mall,
    deliveryHint: c.delivery_hint,
    followUp: c.follow_up,
    cardKey: c.key ?? null,
    goPath: c.go ?? null,
    role: c.role ?? null,
    roleLabel: c.role_label ?? null,
    why: c.why ?? [],
    sellerClaims: c.seller_claims ?? [],
    saved: c.saved,
    seenAt: c.seen_at ?? null,
    detail: c.detail ?? {
      sellerFacts: [
        ...(c.spec ? [{ label: "규격", value: c.spec, source: { label: c.source ?? "판매처", url: c.url } }] : []),
        { label: "상품가", value: won(c.price), source: { label: c.source ?? "판매처", url: c.url } },
        { label: "배송비", value: ship == null ? "판매자 표기 확인 필요" : won(ship), source: { label: c.source ?? "판매처", url: c.url } },
        ...(c.rocket || c.free_shipping ? [{ label: "배송 표시", value: [c.rocket && "로켓배송", c.free_shipping && "무료배송"].filter(Boolean).join(" · ") + " (판매처 검색 결과 표시 · 도착일 약속 아님)", source: { label: c.source ?? "판매처", url: c.url } }] : []),
        ...(c.seller_claims?.length ? [{ label: "상품명 문구", value: `${c.seller_claims.join(" · ")} — 판매자가 상품명에 적은 내용이라 확인되지 않았고, 추천 순서에 쓰지 않았어요`, source: { label: c.source ?? "판매처", url: c.url } }] : []),
        // 식약처 품목제조보고 (식품정보24) — 제조사·품목명이 맞는 경우에만 백엔드가 내려준다
        ...(c.public_info ? [
          { label: "신고 제품", value: `${c.public_info.name} · ${c.public_info.company}`, source: { label: "식약처 품목제조보고" } },
          { label: "원재료", value: c.public_info.raw, source: { label: "식약처 품목제조보고" } },
          ...(c.public_info.expiry ? [{ label: "소비기한", value: c.public_info.expiry, source: { label: "식약처 품목제조보고" } }] : []),
          ...(c.public_info.allergens.length ? [{ label: "알레르기", value: `원재료에 ${c.public_info.allergens.join(", ")} 포함`, source: { label: "식약처 품목제조보고" } }] : []),
        ] : []),
      ],
      reviews: null,
      notes: [c.check_at_mall
        ? `평점·후기·도착일은 판매처 검색 API가 제공하지 않아요. ${c.source ?? "판매처"} 상품 페이지에서 확인해 주세요.`
        : "리뷰 요약은 상품 상세 API 연결 후 표시됩니다."],
    },
  };
}

function normalizeClarify(b: ClarifyFormBlock): ClarifyFormBlock {
  const d = b.data;
  let questions: ClarifyQuestion[] = d.questions ?? [];
  if (!questions.length && d.title && d.options) {
    questions = [{ id: "budget", label: d.title, options: d.options }];
  }
  return { type: "clarify_form", data: { ...d, questions, layout: d.layout ?? "sequential" } };
}

export function normalize(res: ChatResponse): ChatResponse {
  const out: Block[] = [];
  const sponsored: Candidate[] = [];
  const seen = new Set<string>();
  const cardKey = (c: ApiCard) => `${c.mall ?? ""}:${c.pid ?? c.title}`;

  for (const b of res.blocks) {
    switch (b.type) {
      case "text":
        out.push({ type: "text", data: { md: b.data.md ?? b.data.text ?? "" } });
        break;
      case "chips":
        out.push({ type: "chips", data: { mode: b.data.mode ?? "message", items: b.data.items.map(toChip) } });
        break;
      case "clarify_form":
        out.push(normalizeClarify(b));
        break;
      case "comparison_pair": {
        const cards = b.data.pairs.flatMap((p) => p.cards);
        const general = cards.filter((c) => !c.is_sponsored);
        general.forEach((c) => seen.add(cardKey(c)));
        sponsored.push(...cards.filter((c) => c.is_sponsored).map(cardToCandidate));
        if (general.length >= 3) {
          out.push({ type: "candidate_compare", data: { candidates: general.map(cardToCandidate) } });
        } else if (general.length) {
          out.push({ type: "comparison_pair", data: { pairs: [{ pair_index: 0, cards: general, compare: general.length === 2, chips: b.data.pairs[0]?.chips }] } });
        }
        break;
      }
      case "product_list": {
        // 같은 응답 안에서 이미 보여 준 카드는 다시 그리지 않는다
        // (presenter 가 rankable 후보가 0개일 때 같은 목록을 두 번 내려주는 경우 대응)
        const general = b.data.items.filter((c) => !c.is_sponsored && !seen.has(cardKey(c)));
        sponsored.push(...b.data.items.filter((c) => c.is_sponsored).map(cardToCandidate));
        general.forEach((c) => seen.add(cardKey(c)));
        if (general.length) out.push({ type: "product_list", data: { ...b.data, items: general } });
        break;
      }
      case "candidate_compare": {
        const general = b.data.candidates.filter((c) => !c.isSponsored);
        sponsored.push(...b.data.candidates.filter((c) => c.isSponsored));
        out.push({ type: "candidate_compare", data: { ...b.data, candidates: general } });
        break;
      }
      case "sponsored_list":
        sponsored.push(...b.data.items);
        break;
      default:
        out.push(b);
    }
  }
  if (sponsored.length) {
    // 유료 소개는 항상 일반 추천 '뒤', 별도 영역
    const at = out.findIndex((b) => b.type === "chips");
    const block: Block = { type: "sponsored_list", data: { items: sponsored.map((s) => ({ ...s, isSponsored: true })) } };
    if (at >= 0) out.splice(at, 0, block); else out.push(block);
  }
  return { ...res, blocks: out };
}
