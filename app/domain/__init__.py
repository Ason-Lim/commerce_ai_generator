"""Protocol-neutral domain contracts (2026-11-02, 설계서 '프로토콜 연계 설계서 (UCP·MCP)' 1단계).

이 패키지는 FastAPI · mcp · UCP 를 import 하지 않는다.  웹(/api/chat)·MCP·UCP 어댑터는 모두
여기 모델만 주고받고, 형식 변환은 각 어댑터 안에서만 한다.
"""
