# make_ucp_profile.py — 우리 UCP 플랫폼 프로필을 정적 파일로 만든다 (업로드용). (2026-11-04 p40)
# UCP 판매자는 요청마다 우리 프로필 주소(예: https://trendguide.kr/.well-known/ucp)를 직접 가져와 검증한다.
# 결과: Claude outputs/ucp_site/  ─ .well-known/ucp (JSON) · ucp-profile.json + _redirects(200 재작성, 숨김 폴더 대비)
#       · _headers (Cloudflare Pages·Netlify 용 Content-Type 지정)
#       · .nojekyll (GitHub Pages 가 .well-known 폴더를 숨기지 않게) · index.html (안내 한 줄)
# 내용은 app/services/ucp/platform.py 의 platform_profile() — 카탈로그 읽기만 광고, 결제 없음. 비밀값 없음.
# 사용: python make_ucp_profile.py
import json
from pathlib import Path

from app.services.ucp.platform import platform_profile

out = Path("Claude outputs") / "ucp_site"
(out / ".well-known").mkdir(parents=True, exist_ok=True)
body = json.dumps(platform_profile(), ensure_ascii=False, indent=2) + "\n"
(out / ".well-known" / "ucp").write_text(body, encoding="utf-8")
# p42: 맥 Finder 는 점(.)으로 시작하는 폴더를 숨겨 끌어다 놓기 업로드에서 빠질 수 있다 → 숨김 없는 사본 + 내부 재작성.
#      _redirects 의 상태 200 은 리다이렉트(3xx)가 아니라 같은 주소에서 내용을 바로 주는 재작성(rewrite)이다.
(out / "ucp-profile.json").write_text(body, encoding="utf-8")
(out / "_redirects").write_text("/.well-known/ucp /ucp-profile.json 200\n", encoding="utf-8")
(out / "_headers").write_text("/.well-known/ucp\n  Content-Type: application/json; charset=utf-8\n"
                              "  Cache-Control: public, max-age=3600\n  Access-Control-Allow-Origin: *\n", encoding="utf-8")
(out / ".nojekyll").write_text("", encoding="utf-8")
(out / "index.html").write_text('<!doctype html><meta charset="utf-8"><title>trendguide</title>'
                                '<p>trendguide — UCP platform profile: <a href="/.well-known/ucp">/.well-known/ucp</a></p>\n',
                                encoding="utf-8")
print(f"만듦: {out}/.well-known/ucp — 이 폴더를 https://trendguide.kr 루트에 올린 뒤 .env 에\n"
      "  UCP_PLATFORM_PROFILE_URL=https://trendguide.kr/.well-known/ucp")
