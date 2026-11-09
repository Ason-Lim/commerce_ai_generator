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
# p44 (2026-11-05): trendguide.kr = 안내 페이지·UCP 프로필(Pages, 항상 열림), 서비스 = app.trendguide.kr(맥 Tunnel, 맥이 켜져 있을 때만)
(out / "index.html").write_text("""<!doctype html>
<html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>trendguide</title>
<style>
:root{--bg:#fafaf7;--ink:#1d1d1b;--sub:#5f5f5a;--accent:#0f6e56}
@media (prefers-color-scheme:dark){:root{--bg:#161614;--ink:#ecece8;--sub:#a3a39c;--accent:#5fc9a6}}
body{margin:0;background:var(--bg);color:var(--ink);font:16px/1.6 -apple-system,BlinkMacSystemFont,"Apple SD Gothic Neo","Noto Sans KR",sans-serif}
main{max-width:560px;margin:0 auto;padding:72px 16px}
h1{font-size:28px;margin:0 0 8px}p{color:var(--sub);margin:0 0 20px}
a.btn{display:inline-block;background:var(--accent);color:#fff;text-decoration:none;padding:12px 20px;border-radius:10px;font-weight:600}
small{display:block;margin-top:40px;color:var(--sub)}small a{color:var(--sub)}
</style></head><body><main>
<h1>trendguide</h1>
<p>식품 장보기·레시피 추천 서비스 (시험 운영 중)</p>
<a class="btn" href="https://app.trendguide.kr/">서비스 열기</a>
<p style="margin-top:16px">시험 운영 기간에는 정해진 시간에만 열려 있어요. 연결되지 않으면 잠시 뒤 다시 와 주세요.</p>
<small>UCP platform profile: <a href="/.well-known/ucp">/.well-known/ucp</a></small>
</main></body></html>
""", encoding="utf-8")
print(f"만듦: {out} — Cloudflare Pages 'trendguide' 에 다시 배포(Create deployment)하면 trendguide.kr 에 반영.\n"
      "  .env: UCP_PLATFORM_PROFILE_URL=https://trendguide.kr/.well-known/ucp")
