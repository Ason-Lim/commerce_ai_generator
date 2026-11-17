import { StrictMode, useEffect, useState } from "react";
import { createRoot } from "react-dom/client";
import ChatWindow from "./ChatWindow"; // App 대신 ChatWindow를 불러옵니다.
import { TrendsPage } from "./components/TrendsPage";
import { HOT_HASH } from "./components/SiteNav";
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
  return hash === HOT_HASH ? <TrendsPage /> : <ChatWindow />;
}

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <Root />
  </StrictMode>,
);
