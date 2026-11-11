/**
 * 서버 주도 UI(server-driven UI) 블록 계약.
 *
 * - 기존 블록: consumer/presenter.py 가 이미 내려주는 형태 (text · notice · verdict · product_list ·
 *   comparison_pair · clarify_form · chips · shipping_options)
 * - 제안 블록: 이번 화면 흐름을 위해 추가를 제안하는 형태 (candidate_compare · sponsored_list)
 *   → 백엔드가 아직 내려주지 않으면 api/adapt.ts 가 기존 블록에서 만들어 준다.
 */

export type ChipMode = "chip" | "message";

export interface ChipItem {
  label: string;
  /** 서버로 보낼 값. 없으면 label 을 그대로 보낸다. */
  value?: string;
}

/* ───────── 기존 블록 ───────── */

export interface TextBlock { type: "text"; data: { md?: string; text?: string } }
export interface NoticeBlock { type: "notice"; data: { md: string; tone?: "info" | "warn"; affiliate?: boolean } }
export interface VerdictBlock { type: "verdict"; data: { md: string } }
/** 네이버쇼핑 검색 링크 (2026-11-04) — 고객 편의용, 제휴 아님 · 수수료 없음. 상품이 아니라 검색 화면으로만 연결 */
export interface SearchLink { query: string; url: string; check: string }
export interface SearchLinksBlock { type: "search_links"; data: { title: string; badge?: string; links: SearchLink[]; note?: string } }

export interface ChipsBlock {
  type: "chips";
  data: { items: (string | ChipItem)[]; mode?: ChipMode };
}

export interface ClarifyOption {
  label: string; value: string; hint?: string;
  /** layout 'cards' (레시피 고르기): 원문 요약 한 줄 · 인분/시간 · 원문 사진 */
  desc?: string | null; meta?: string | null; image?: string | null;
  /** 외부 원문 링크 후보: 누르면 새 창으로 원문을 연다 (서버로 보내지 않음) */
  href?: string | null;
  /** 외부 원문 후보의 종류 (사진이 없을 때 아이콘): blog · cafearticle · video */
  source_kind?: string | null;
}
export interface ClarifyQuestion {
  id: string;
  label: string;
  /** 왜 묻는지 — 선택에 어떤 영향을 주는지 한 줄 (제안 필드) */
  why?: string;
  options: ClarifyOption[];
  /** 건너뛰기 허용 여부 (제안 필드, 기본 true) */
  skippable?: boolean;
}
export interface ClarifyFormBlock {
  type: "clarify_form";
  data: {
    questions?: ClarifyQuestion[];
    submit?: string;
    /** 첨부 예시 형식 호환: 질문 1개짜리 */
    title?: string;
    options?: ClarifyOption[];
    /** 제안 필드: 'sequential' 이면 한 번에 한 질문씩 보여 준다 */
    layout?: "sequential" | "stacked" | "cards";
  };
}

/** presenter.card() 가 만드는 카드 (필드 일부) */
export interface ApiCard {
  rank: number;
  mall?: string;
  pid?: string | null;
  title: string;
  image?: string | null;
  image_url?: string | null;
  price: number;
  shipping_fee?: number | null;
  total?: number | null;
  original_price?: number | null;
  unit_price?: number | null;
  unit_count?: number | null;
  spec?: string | null;
  reason?: string;
  reasoning?: string;
  evidence?: string[];
  unverified?: string[];
  badges?: string[];
  source?: string;
  observed?: string;
  stale?: boolean;
  url?: string | null;
  is_sample?: boolean;
  cta?: string;
  follow_up?: ChipItem[];
  rankable?: boolean;
  missing_terms?: string[];
  /* 제안 필드 (백엔드 추가 요청) */
  weight_g?: number | null;
  delivery_terms?: string | null;
  is_sponsored?: boolean;
  /** 수수료가 발생하는 제휴 링크 (쿠팡 파트너스 등) */
  affiliate?: boolean;
  affiliate_program?: string | null;
  /** true: 서버 /go 를 거치지 않고 url 로 바로 이동 (네이버 쇼핑커넥트 발급 링크) */
  direct?: boolean;
  /** 평점·후기·도착일을 판매처 API가 제공하지 않음 → 판매처에서 확인 안내 */
  check_at_mall?: boolean;
  delivery_hint?: string | null;
  /** 식약처 품목제조보고(식품정보24) — 제조사까지 맞은 경우에만 */
  public_info?: { name: string; company: string; item_type?: string; raw: string; expiry?: string | null;
                  allergens: string[]; source: string } | null;
  detail?: ProductDetail;
  /* 2026-11-01 추천 사유 (commerce /api/chat) */
  /** 카드 고유 키 — 판매처 이동(/go/…/k/{key})·관심 상품 담기에 쓴다 */
  key?: string;
  /** 서버가 정한 판매처 이동 경로 (/go/{sid}/k/{key} · 관심 상품은 /go/s/{owner}/{key}) */
  go?: string | null;
  /** 역할: value 가성비 · lowest 최저가 · fast 빠른 배송 · ample 넉넉한 양 · gift 선물용 · alt 다른 선택 */
  role?: "value" | "lowest" | "fast" | "ample" | "gift" | "alt" | null;
  role_label?: string | null;
  /** 왜 골랐는지 — basis: calc 후보끼리 계산 · mall 판매처 표시 · you 고객이 말한 조건 */
  why?: WhyLine[];
  /** 판매자가 상품명에 적은 문구 (고당도·등급·국내산 …) — 확인되지 않음, 사유·순서에 쓰지 않음 */
  seller_claims?: string[];
  per100g?: number | null;
  /** 2026-11-11: 중량 옵션·증정분 안내 — 상세페이지를 열기 전에 알 수 있게 */
  weight_note?: WeightNote | null;
  per_unit?: number | null;
  rocket?: boolean | null;
  free_shipping?: boolean | null;
  /** 관심 상품 비교 목록에서 온 카드 */
  saved?: boolean;
  query?: string | null;
  seen_at?: string | null;
  saved_at?: string | null;
}

export type WhyBasis = "calc" | "mall" | "you" | "public" | "trend";
export interface WhyLine { text: string; basis: WhyBasis }

export interface ComparisonPair {
  pair_index: number;
  cards: ApiCard[];
  compare?: boolean;
  chips?: ChipItem[];
}
export interface ComparisonPairBlock { type: "comparison_pair"; data: { pairs: ComparisonPair[] } }
export interface ProductListBlock {
  type: "product_list";
  /** title/note: 목록 머리말 · collapsed: 처음에는 접어 둠 (예: '다른 후보 6개') */
  data: { items: ApiCard[]; compare?: boolean; title?: string; note?: string; collapsed?: boolean };
}

export interface ShippingEstimate {
  agency?: string;
  total_krw?: number;
  eta_days_min?: number;
  eta_days_max?: number;
  shipping_krw?: number;
  duty_krw?: number;
  vat_krw?: number;
}
export interface ShippingOptionsBlock {
  type: "shipping_options";
  data: {
    title?: string;
    note?: string;
    options?: { id: string; label: string; desc?: string }[];
    items?: { title: string; mall?: string; estimate?: ShippingEstimate }[];
    /* 첨부 예시 형식 호환 */
    is_overseas?: boolean;
    estimated_days?: string;
    total_landed_cost?: number;
    agency?: string;
  };
}

/* ───────── 제안 블록 ───────── */

/** ③ 후보 비교 — 3개 내외 후보를 같은 기준으로 나란히 비교 */
export interface CandidateCompareBlock {
  type: "candidate_compare";
  data: {
    title?: string;
    /** 사용자가 고른 조건 요약 (예: "3~4인 · 구이용 · 이번 주 도착") */
    conditions?: string[];
    candidates: Candidate[];
  };
}

/** 유료 소개 — 일반 추천 순위와 분리해 별도 영역에 표시 */
export interface SponsoredListBlock {
  type: "sponsored_list";
  data: { note?: string; items: Candidate[] };
}

/** 레시피 카드 — 출처 레시피(원문)를 사진·재료 체크리스트·단계 카드로 보여 준다 (commerce /api/chat) */
export type RecipeSourceLevel = "source" | "source_modified" | "ai_draft" | "ai_suggestion";
export interface RecipeCardIngredient {
  id: string | null;
  name: string;
  /** 표시 분량: 원문 분량(감싼 괄호만 제거), 인분을 바꿨으면 계산한 분량 */
  amount: string;
  /** 원문 분량과, amount 가 인분 변경으로 계산된 값인지 */
  source_amount?: string;
  scaled?: boolean;
  /** 눈대중 가늠 ("500원 동전 굵기 묶음 1개") — 일반 제안, 원문 아님, 계산에 쓰지 않음 */
  gauge?: string | null;
  raw: string;
  /** 컵 분량의 mL 참고값 (기본 1컵=200mL · 원문 아님 · 보유량 계산에 쓰지 않음) */
  reference: string | null;
  /** 원문에 분량이 있는 재료인지 (없으면 '부족' 대신 '없음'으로 묻는다) */
  quantity_known?: boolean;
  /** 이 대화에서 고객이 직접 알려 준 판단 / 남은 양 (서버 기록, 추정 아님) */
  status?: RecipeStockStatus | null;
  status_label?: string | null;
  /** 충분·부족 답변을 한 때의 인분, 지금 인분과 다르면 status_stale (새 필요량의 확인 결과가 아님) */
  status_servings?: string | null;
  status_stale?: boolean;
  stock?: string | null;
}
export type RecipeStockStatus = "short" | "absent" | "enough" | "have";
export interface RecipeHero {
  src: string;
  /** source = 원문 사진, ai = AI 생성 예시 이미지 */
  kind: "source" | "ai";
  label: string | null;
}
/** 쉽게 보기 — AI가 원문을 다듬은 것 (원문 변형). 서버가 원문과 대조해 통과한 것만 내려온다 */
/** 완료 신호: source = 원문 구절(quote)에서 확인, general = 원문에 없는 일반 조리 제안 */
export interface RecipeDoneSignal { text: string; basis: "source" | "general"; quote: string | null }
/** 필요한 단계에만 붙는 보충 (항상 일반 조리 제안) */
export interface RecipeStepNote { kind: "caution" | "fix"; label: string; text: string }
export interface RecipeEasyStep {
  no: number; title: string; text: string; from: number[]; image?: string | null;
  done?: RecipeDoneSignal | null; notes?: RecipeStepNote[];
}
export interface RecipeEasyView {
  summary: string;
  /** easy-v2: feature = 요리 특징, flow = 전체 진행 한 줄 */
  overview?: { feature: string; flow: string };
  steps: RecipeEasyStep[];
  tips: RecipeTip[];
  prompt_version: string;
}
export interface RecipeTip { title: string; text: string }
export interface RecipeGeneralTips {
  /** ai = AI 제안, curated = 자체 정리한 일반 팁. 둘 다 원문 아님 */
  kind: "ai" | "curated";
  label: string;
  items: RecipeTip[];
}
export type RecipeEasyStatus = "ready" | "pending" | "unavailable";
export interface RecipeCardBlock {
  type: "recipe_card";
  data: {
    recipe_id: string;
    title: string;
    summary: string;
    image: string | null;
    source: { level: RecipeSourceLevel; label: string; name: string; ref: string; provider?: string };
    meta: string[];
    /** 인분·시간·난이도·열량의 근거. source = 원문 표기 그대로 (추정값 없음) */
    meta_basis?: "source";
    /** 원문 기준 인분 (예: "2인분"), 표기가 없으면 null */
    servings?: string | null;
    /** 원문 기준 인분, 인분을 바꿨는지 ("1인분으로 바꿔 줘") */
    servings_source?: string | null;
    servings_scaled?: boolean;
    ingredients: RecipeCardIngredient[];
    extra_ingredients: { id: string; name: string; note: string; short?: string; status?: RecipeStockStatus | null; gauge?: string | null }[];
    steps: { no: number; text: string; image: string | null }[];
    tips: string[];
    notes: string[];
    basis: { cup_ml: string | null; chosen?: boolean };
    easy?: RecipeEasyView | null;
    easy_status?: RecipeEasyStatus;
    easy_key?: string;
    general_tips?: RecipeGeneralTips | null;
    hero?: RecipeHero | null;
    hero_status?: RecipeEasyStatus;
    /** 원문에 요리의 핵심 단계가 없을 때 (예: "원문에 굽는 단계가 없어요.") */
    source_gap?: string | null;
    /** AI 제안 레시피: 무엇을 언제 어떤 모델로 만들었는지 (원문 아님) */
    generated?: { at?: string | null; model?: string | null; servings?: string | null; ingredients: number; steps: number;
      what?: string | null } | null;
    /** AI가 보충한 단계 — 원문 아님, 검증 통과분만 */
    supplement?: RecipeSupplement | null;
    supplement_status?: RecipeEasyStatus;
    /** 고객이 부족·없음이라고 알려 준 재료 */
    shortage?: { id: string; name: string; status: RecipeStockStatus }[];
  };
}

export interface RecipeSupplement {
  needed: boolean;
  action: string;
  label: string;
  steps: { title: string; text: string }[];
}

/** GET /api/recipe/easy — 쉽게 보기 준비 상태 (읽기 전용) */
export interface RecipeEasyPoll {
  status: RecipeEasyStatus | "stale" | "unknown";
  hero_status?: RecipeEasyStatus;
  hero?: RecipeHero | null;
  easy?: RecipeEasyView;
  general_tips?: RecipeGeneralTips | null;
  supplement?: RecipeSupplement | null;
  supplement_status?: RecipeEasyStatus;
}

/** 추천 상품 비교 (2026-11-06 p35) — 방금 보여 준 후보를 같은 기준으로 한 표에 (서버가 계산, 화면은 그리기만) */
export interface ProductCompareRow {
  key: string | null;
  rank: number | null;
  title: string;
  image?: string | null;
  mall?: string | null;
  /** 판매처 이동 경로 (/go/…). 쇼핑커넥트 발급 링크(direct)는 url 그대로 */
  go?: string | null;
  url?: string | null;
  direct?: boolean;
  affiliate: boolean;
  affiliate_program?: string | null;
  total: number | null;
  shipping_included: boolean;
  free_shipping?: boolean | null;
  /** 제목에 적힌 포장 용량 ('1kg', '1kg×2 (총 2kg)') — 없으면 null */
  pack: string | null;
  per100g: number | null;
  /** 2026-11-11: 포장 용량 대신 — 중량 옵션이 있어요 · 증정분이 있어요 */
  weight_note?: WeightNote | null;
  fit?: "fits" | "partial" | "unknown" | "bulk" | null;
  fit_text?: string | null;
  /** 손질 상태 표기 (굴: 깐굴 표기 · 껍질째 표기 · 손질 상태 미표기) */
  prep?: string | null;
  seller_claims: string[];
}
export interface ProductCompareBlock {
  type: "product_compare";
  data: {
    title: string;
    need?: { display?: string; basis?: string } | null;
    seen_at?: string | null;
    rows: ProductCompareRow[];
    best_total?: string | null;
    best_per100g?: string | null;
    notes: string[];
  };
}

/** 상품 목록 끝 비교 카드 (2026-11-09 A안) — 누르면 data.send 를 메시지로 보낸다 */
export interface CompareCtaBlock { type: "compare_cta"; data: { label: string; sub?: string; send: string } }

export type Block =
  | TextBlock | NoticeBlock | VerdictBlock | ChipsBlock | ClarifyFormBlock
  | ComparisonPairBlock | ProductListBlock | ShippingOptionsBlock
  | CandidateCompareBlock | SponsoredListBlock | RecipeCardBlock | SearchLinksBlock | ProductCompareBlock
  | TrendListBlock | CompareCtaBlock;

/** 지금 검색이 늘어난 식품 (2026-11-06, '요즘 뜨는 식품') — 서버 급상승 리포트의 고객용 항목 */
export interface TrendYoutube {
  recent: number; previous: number | null; saturated: boolean; rising: boolean | null; window_days: number;
  /** 검색 한 번의 상한(50개)을 채워 실제로는 더 많을 수 있음 */
  recent_more?: boolean; previous_more?: boolean;
}
export interface TrendEntry {
  keyword: string; status: "surging" | "new"; times: number | null; onset: string | null; rank: number | null;
  spark: number[]; cross: { n: number; of: number; parts: Record<string, boolean> }; clues: string[];
  cause: string | null; ask: string; youtube?: TrendYoutube | null;
}
export interface TrendListBlock {
  type: "trend_list";
  data: { title: string; data_until: string | null; items: TrendEntry[]; note?: string };
}

export interface ChatResponse {
  session_id: string;
  stage?: string;
  slots?: Record<string, unknown>;
  blocks: Block[];
}

export interface ChatRequest {
  session_id: string | null;
  /** 관심 상품 보관함 id (브라우저별) */
  owner?: string | null;
  message?: string;
  answers?: Record<string, string>;
  chip?: string;
}

/** 2026-11-11: 상품명에 중량이 여러 개(옵션 목록)이거나 증정분이 적힌 경우 — 100g당 가격은 계산하지 않는다 */
export interface WeightNote {
  kind: "options" | "bonus";
  label: string;     // "중량 옵션이 있어요" · "증정분이 있어요"
  detail: string;    // "2kg · 5kg · 10kg" · "3kg + 1kg 증정" · "1+1 구성"
}

/* ───────── 화면용 뷰 모델 ───────── */

export interface Candidate {
  rank: number;
  key: string;
  title: string;
  image?: string | null;
  source: string;          // 판매처 표시명
  mall?: string;
  price: number;
  shippingFee: number | null;   // null = 미확인 (0원과 다름)
  total: number | null;         // null = 배송비 미확인으로 확정 불가
  weightLabel?: string | null;  // "1.2kg"
  per100g?: number | null;      // 100g당 가격
  weightNote?: WeightNote | null; // 중량 옵션·증정분 안내 (2026-11-11)
  unitLabel?: string | null;    // "개당 약 4,635원"
  delivery?: { label: string; verified: boolean } | null;
  reasons: string[];            // 선택 이유
  evidence: string[];           // 확인된 근거
  unverified: string[];         // 확인되지 않은 조건
  badges: string[];
  observed?: string;
  stale?: boolean;
  url?: string | null;
  isSample?: boolean;
  isSponsored?: boolean;
  affiliate?: boolean;
  affiliateProgram?: string | null;
  direct?: boolean;            // 발급 링크로 바로 이동 (쇼핑커넥트)
  checkAtMall?: boolean;
  deliveryHint?: string | null;
  followUp?: ChipItem[];
  detail?: ProductDetail;
  /* 2026-11-01 */
  cardKey?: string | null;     // 서버 카드 키 (관심 상품)
  goPath?: string | null;      // 서버가 정한 판매처 이동 경로
  role?: ApiCard["role"];
  roleLabel?: string | null;
  why?: WhyLine[];
  sellerClaims?: string[];
  saved?: boolean;
  seenAt?: string | null;
}

/** ④ 상품 판단 — 판매자 표기와 리뷰 근거를 분리 */
export interface SourceRef { label: string; url?: string | null }

export interface SellerFact {
  label: string;        // "등급", "원산지", "중량", "배송"
  value: string;
  source?: SourceRef;   // 판매자 상세페이지 원문
}

export interface ReviewPoint {
  text: string;                   // "고기가 부드럽다는 후기가 많아요"
  tone: "positive" | "negative" | "mixed";
  mentions?: number;              // 언급 리뷰 수
  quotes?: { text: string; source?: SourceRef }[];
}

export interface ProductDetail {
  sellerFacts: SellerFact[];
  reviews?: {
    count?: number;
    rating?: number;
    analyzed?: number;            // 요약에 사용한 리뷰 수
    points: ReviewPoint[];
    source?: SourceRef;
  } | null;
  options?: { id: string; label: string; price: number; weightLabel?: string }[];
  notes?: string[];
}

/** GET/POST /api/chat/saved — 관심 상품 · 최근 본 상품 */
export interface SavedView {
  ok?: boolean;
  error?: string;
  saved: ApiCard[];
  recent: { query: string; at: string; budget?: string | null; cards: ApiCard[] }[];
}
