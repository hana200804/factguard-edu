"""Explicitly POST HOC sensitivity analysis of question-format shift.

Keep the original scored challenge unchanged. This analysis was added after
observing its scores; it is exploratory and must not replace the primary result.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.loader import load_evaluation, load_facts, load_sources
from src.research_evaluator import load_challenge, run_research, save_research
from src.utils import PROJECT_ROOT, digest_bytes, utc_now


def main():
    base = PROJECT_ROOT / "data"
    sources = load_sources(base / "sources.json")
    facts = load_facts(base / "facts.csv", sources)
    cases = load_challenge(base / "research" / "challenge.jsonl", facts)
    fact_map = {fact.id: fact for fact in facts}
    # Only change the task instruction for cases that originally used the generic
    # instruction. Leave explicit question premises and their labels unchanged.
    controls = []
    for case in cases:
        alternate = dict(case)
        if case["question"] == "Kiểm chứng các dữ kiện lịch sử sau." and case["gold_claims"]:
            alternate["question"] = fact_map[case["gold_claims"][0]["fact_id"]].question
        alternate["paired_to"] = case["id"]
        alternate["analysis_type"] = "post_hoc_question_format_sensitivity"
        controls.append(alternate)
    all_cases = load_evaluation(base / "evaluation.csv", facts)
    development = all_cases.loc[all_cases["split"] == "development"].copy()
    frame, summary = run_research(facts, sources, development, controls)
    summary["analysis_type"] = "POST HOC; not preregistered; do not replace primary challenge score"
    summary["question_changes"] = sum(a["question"] != b["question"] for a, b in zip(cases, controls, strict=True))
    summary["original_challenge_sha256"] = digest_bytes((base / "research" / "challenge.jsonl").read_bytes())
    summary["created_at"] = utc_now()
    output = PROJECT_ROOT / "reports" / "research_v2" / "format_control"
    save_research(frame, summary, output)
    path = output / "bao_cao_nghien_cuu.md"
    path.write_text("# Phân tích hậu nghiệm về dạng câu hỏi\n\n"
                    "Phân tích này được bổ sung SAU khi xem kết quả bộ chính. Thay chỉ dẫn chung bằng câu hỏi chuẩn cho những ca phù hợp, giữ nguyên đáp án và nhãn. "
                    "Mục đích: kiểm tra mức phụ thuộc vào dạng đầu vào của đối chứng. Không coi là một bộ độc lập hoặc thay kết quả chính.\n\n" + path.read_text(encoding="utf-8"), encoding="utf-8")
    (output / "cases.jsonl").write_text("".join(json.dumps(c, ensure_ascii=False) + "\n" for c in controls), encoding="utf-8")
    print(json.dumps({"question_changes": summary["question_changes"], "accuracy": {m: v["accuracy"] for m, v in summary["metrics"].items()}, "frozen_core": summary["engine_matches_freeze"]}))


if __name__ == "__main__":
    main()
