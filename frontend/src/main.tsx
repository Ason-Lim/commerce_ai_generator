import { StrictMode, useEffect, useState } from "react";
import { createRoot } from "react-dom/client";
import ChatWindow from "./ChatWindow"; // App 대신 ChatWindow를 불러옵니다.
import { TrendsPage } from "./components/TrendsPage";
import { AI_NOTICE_HASH, TERMS_HASH, HOT_HASH, ME_HASH, POLICY_HASH, PRIVACY_HASH } from "./components/SiteNav";
import { PrivacyPage } from "./components/PrivacyPage";
import { PolicyPage } from "./components/PolicyPage";
import { AiNoticePage } from "./components/AiNoticePage";
import { TermsPage } from "./components/TermsPage";
import { DIRECT_HASH, DirectBuyPage } from "./components/DirectBuy";
import { MyShelf } from "./components/MyShelf";
import "./index.css";

/** '#/hot' → 지금 뜨는 식품, 그 밖에는 대화 화면 (2026-10-31 · 2026-11-17 주소 '#/trends' → '#/hot').
 *  옛 주소 '#/trends' 는 '#/hot' 으로 바꿔 준다 (서버의 트렌드 글 '/trends' 와 헷갈리지 않게). */
const normalize = () => {
  if (window.location.hash === "#/trends") window.history.replaceState(null, "", window.location.pathname + window.location.search + HOT_HASH);
  return window.location.hash;
};

function Root() {
  const [hash, setHash] = useState(normalize);
  useEffect(() => {
    const on = () => { setHash(normalize()); window.scrollTo(0, 0); };
    window.addEventListener("hashchange", on);
    return () => window.removeEventListener("hashchange", on);
  }, []);
  if (hash === ME_HASH) return <MyShelf />;          // 2026-11-22 창 3-B 내 보관함
  if (hash === PRIVACY_HASH) return <PrivacyPage />; // 2026-11-23 개인정보처리방침 (한 곳으로 모음)
  if (hash === DIRECT_HASH) return <DirectBuyPage />;      // 2026-11-26 해외 직구 찾기
  if (hash === TERMS_HASH) return <TermsPage />;          // 2026-11-26 이용약관
  if (hash === AI_NOTICE_HASH) return <AiNoticePage />;   // 2026-11-26 AI 기본법에 따른 고지
  if (hash === POLICY_HASH) return <PolicyPage />;   // 2026-11-23 운영정책 (순위·추천 기준·갱신·가격 표시)
  return hash === HOT_HASH ? <TrendsPage /> : <ChatWindow />;
}

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <Root />
  </StrictMode>,
);
