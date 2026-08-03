# Context Intelligence 문서 패키지

프로젝트 루트에서 아래 구조로 복사하세요.

```text
docs/AI/CONTEXT_INTELLIGENCE.md
app/design/context_intelligence_design.py
scripts/sync_context_intelligence_docs.py
```

검사:

```bash
python -m py_compile   app/design/context_intelligence_design.py   scripts/sync_context_intelligence_docs.py
```

동기화:

```bash
python scripts/sync_context_intelligence_docs.py
```

권장 운영 방식:

1. 구조·상수·모델 변경은 Python 파일에서 먼저 수행
2. 동기화 스크립트 실행
3. Markdown 문서 검토
4. 두 파일을 같은 커밋에 포함
