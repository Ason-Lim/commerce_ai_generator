# capture_mcp_raw.py — 실제 MCP 프로토콜(stdio)로 서버를 띄워 도구를 부르고, 응답 원본을 그대로 저장한다. (2026-11-03 p39)
# Claude 앱과 같은 서버 코드(python -m app.mcp_adapter.server)를 쓴다.  읽기 전용 도구만 부른다 (판매처 검색 API 호출 있음).
# 결과: Claude outputs/mcp_raw_p39/*.json  — 저장 전에 제휴 링크·키처럼 보이는 문자열이 없는지 검사한다.
# 사용: 저장소 폴더에서  python capture_mcp_raw.py
import asyncio
import datetime as dt
import json
import os
import re
import sys
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

CALLS = [
    ("search_국산_삼겹살", "food_search_products", {"text": "국산 삼겹살", "limit": 5}),
    ("search_5만원_한우_등심", "food_search_products", {"text": "5만원 이하 한우 등심", "limit": 5}),
    ("search_빈_검색어", "food_search_products", {"text": "   ", "limit": 5}),
    ("recipe_파스타", "food_get_recipe", {"dish_name": "파스타"}),
    ("recipe_epis-318", "food_get_recipe", {"recipe_id": "epis-318"}),
]
# 저장하면 안 되는 것: 제휴 링크(쿠팡 파트너스·쇼핑커넥트), API 키·토큰 모양 문자열
BLOCK = re.compile(r"link\.coupang\.com|coupa\.ng|naver\.me/|brandconnect|(?:api[_-]?key|secret|access[_-]?key|token)\"?\s*[:=]",
                   re.IGNORECASE)
OUT = Path("Claude outputs") / "mcp_raw_p39"


def _get(obj, *names):
    """mcp 1.x(camelCase)·2.x(snake_case) 모두 지원."""
    for n in names:
        try:
            return getattr(obj, n)
        except AttributeError:
            continue
    return None


async def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    params = StdioServerParameters(command=sys.executable, args=["-m", "app.mcp_adapter.server"],
                                   cwd=str(Path.cwd()), env=dict(os.environ))
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            init = await session.initialize()
            tools = await session.list_tools()
            meta = {"captured_at": dt.datetime.now().isoformat(timespec="seconds"),
                    "server": getattr(_get(init, "server_info", "serverInfo"), "name", None),
                    "protocol": _get(init, "protocol_version", "protocolVersion"),
                    "tools": [t.name for t in tools.tools]}
            for name, tool, args in CALLS:
                res = await session.call_tool(tool, args)
                texts = [c.text for c in res.content if getattr(c, "type", "") == "text"]
                raw = texts[0] if len(texts) == 1 else json.dumps(texts, ensure_ascii=False)
                if BLOCK.search(raw):
                    print(f"[건너뜀] {name}: 제휴 링크·키 모양 문자열이 있어 저장하지 않았어요")
                    continue
                try:
                    body = json.loads(raw)
                except ValueError:
                    body = raw
                record = {"call": {"tool": tool, "arguments": args}, "is_error": bool(_get(res, "is_error", "isError")), "response": body}
                (OUT / f"{name}.json").write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")
                status = body.get("status") if isinstance(body, dict) else "?"
                print(f"저장: {name}.json  status={status}")
            (OUT / "_meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"완료: {OUT}")


asyncio.run(main())
