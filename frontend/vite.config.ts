import { defineConfig, loadEnv } from "vite";
import react from "@vitejs/plugin-react";

// 개발 서버: /api, /go, /admin 요청을 commerce_ai_generator 백엔드(:8001)로 넘긴다 (2026-11-02 통합).
// 운영에서는 `npm run build` 결과(dist)를 백엔드가 같은 주소(:8001)에서 함께 보여 준다 — 프록시 불필요.
export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, ".", "");
  const target = env.VITE_API_TARGET || "http://127.0.0.1:8001";
  return {
    plugins: [react()],
    server: {
      port: 5173,
      proxy: {
        "/api": { target, changeOrigin: true },
        "/go": { target, changeOrigin: true },
        "/admin": { target, changeOrigin: true },
      },
    },
  };
});
