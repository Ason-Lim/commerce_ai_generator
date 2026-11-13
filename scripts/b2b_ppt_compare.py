"""모델별 파워포인트 제작 수준 비교 (2026-11-11).

같은 사실(가상 공고 N1 · 회사 정보 빈칸 · 후보 상품 · 비용 가정)을 주고 각 모델이 python-pptx 코드를 쓴다.
코드는 이 스크립트에서 실행하지 않는다 — 격리된 곳에서 실행·이미지로 바꿔 블라인드 비교한다.
  uv run python scripts/b2b_ppt_compare.py gen                      # var/b2b_compare/ppt/<model>.py
  uv run python scripts/b2b_ppt_compare.py repair errors.json       # 실행 오류를 알려 주고 한 번 고치게
"""
from __future__ import annotations

import json
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

import b2b_llm_compare  # noqa: E402
from b2b_llm_compare import BENCH, CANDIDATES, PROFILE, call  # noqa: E402

b2b_llm_compare.MAX_TOKENS = 32000
# 2026-11-11: Claude 5.5 기본 생각 모드가 16,000 토큰 중 13,935 를 추론에 써서 코드가 잘렸다 → 생각 강도 medium
b2b_llm_compare.CLAUDE_EXTRA = {"output_config": {"effort": "medium"}}

OUT = ROOT / "var" / "b2b_compare" / "ppt"
MODELS = ["deepseek-flash", "claude-sonnet", "claude-opus", "gpt-sol", "gpt-astra"]
COST = {"1인 예산": "50,000원 (VAT 포함) → 공급가액 45,455원",
        "비용 가정 (1인, VAT 별도)": {"상품 매입": "[확인 필요: 공급사 견적]", "포장": "1,000원 (가정)", "물류창고 입고·보관·출고": "700원 (가정)",
                                 "택배": "3,500원 (가정, 협력 택배사 미정)", "교환·반품 예비": "300원 (가정)", "운영·CS": "800원 (가정)",
                                 "폐쇄몰 구축비 배분": "1,667원 (구축비 200만원 ÷ 1,200명, 가정)", "일반관리비": "공급가액의 5% = 2,273원 (가정)"},
        "목표 이익률": "10% → 최대 매입가 30,670원 (가정값 기준)"}

PROMPT = """너는 공공기관 입찰 제안 발표 자료를 만드는 프레젠테이션 디자이너다. JSON 하나만 출력한다: {"code": "파이썬 코드"}
- python-pptx 1.0 으로 16:9(13.333×7.5in) 발표 자료 10~12장을 만들어 현재 폴더의 out.pptx 로 저장하는 완결된 스크립트.
- 외부 파일·이미지·네트워크를 쓰지 않는다 (도형·표·차트·아이콘 대신 도형으로). 글꼴은 'Noto Sans CJK KR'.
- 평가위원이 한눈에 보도록: 장마다 핵심 메시지 한 줄 제목, 표·도식·숫자 강조, 일관된 색·여백, 표지와 목차 포함.
- 내용은 입력의 사실만 쓴다. 회사 정보가 비어 있으면 "[확인 필요: 항목]". 가정값은 '가정'이라고 표시한다.
- 제출본이므로 내부 이익·마진 숫자는 넣지 않는다 (단가 구성 항목은 넣되 금액은 견적 확정 후)."""


def facts() -> str:
    n1 = next(n for n in json.loads(BENCH.read_text(encoding="utf-8"))["notices"] if n["id"] == "N1")
    return json.dumps({"공고 원문": n1["text"], "공고 조건": n1["key"], "회사 정보": PROFILE,
                       "후보 상품 (관측 가격 — 확정 단가 아님)": CANDIDATES["N1"], "비용 구조 (내부 참고)": COST},
                      ensure_ascii=False)


def gen(models: list[str], extra: dict[str, str] | None = None) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    meta_p = OUT / "meta.json"
    meta = json.loads(meta_p.read_text(encoding="utf-8")) if meta_p.exists() else {}

    def one(m):
        user = facts()
        if extra and m in extra:
            prev = (OUT / f"{m}.py").read_text(encoding="utf-8")
            user += "\n\n이전 코드가 실행 중 오류가 났다. 고친 전체 코드를 다시 출력하라.\n오류:\n" + extra[m][:1500] + "\n\n이전 코드:\n" + prev[:20000]
        try:
            res = call(m, PROMPT, user)
            code = (res["json"] or {}).get("code") or ""
            (OUT / f"{m}.py").write_text(code, encoding="utf-8")
            meta.setdefault(m, []).append({k: res[k] for k in ("seconds", "tokens_in", "tokens_out", "usd", "served")}
                                          | {"repair": bool(extra and m in extra), "chars": len(code)})
            print(m, "OK", res["seconds"], "초", len(code), "자", flush=True)
        except Exception as e:  # noqa: BLE001
            print(m, "ERR", type(e).__name__, str(e)[:200], flush=True)

    with ThreadPoolExecutor(max_workers=len(models)) as ex:
        list(ex.map(one, models))
    meta_p.write_text(json.dumps(meta, ensure_ascii=False, indent=1), encoding="utf-8")


if __name__ == "__main__":
    if sys.argv[1] == "gen":
        gen(sys.argv[2].split(",") if len(sys.argv) > 2 else MODELS)
    elif sys.argv[1] == "repair":
        errs = json.loads(Path(sys.argv[2]).read_text(encoding="utf-8"))
        gen(list(errs), errs)
