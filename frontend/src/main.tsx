import { StrictMode, useEffect, useState } from "react";
import { createRoot } from "react-dom/client";
import ChatWindow from "./ChatWindow"; // App 대신 ChatWindow를 불러옵니다.
import { TrendsPage } from "./components/TrendsPage";
import { HOT_HASH, ME_HASH, PRIVACY_HASH } from "./components/SiteNav";
import { PrivacyPage } from "./components/PrivacyPage";
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
  return hash === HOT_HASH ? <TrendsPage /> : <ChatWindow />;
}

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <Root />
  </StrictMode>,
);
