import { StrictMode, useEffect, useState } from "react";
import { createRoot } from "react-dom/client";
import ChatWindow from "./ChatWindow"; // App 대신 ChatWindow를 불러옵니다.
import { TrendsPage } from "./components/TrendsPage";
import "./index.css";

/** '#/trends' → 지금 뜨는 식품 탭, 그 밖에는 기존 대화 화면 (2026-10-31) */
function Root() {
  const [hash, setHash] = useState(window.location.hash);
  useEffect(() => {
    const on = () => { setHash(window.location.hash); window.scrollTo(0, 0); };
    window.addEventListener("hashchange", on);
    return () => window.removeEventListener("hashchange", on);
  }, []);
  return hash === "#/trends" ? <TrendsPage /> : <ChatWindow />;
}

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <Root />
  </StrictMode>,
);
