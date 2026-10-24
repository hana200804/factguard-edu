"""Regression run: v2 rules vs v3 hybrid on the already-seen synthetic sets.

These sets were all inspected while developing v2, so the numbers are regression checks only,
never evidence of generalisation. The primary v3 evaluation is the collected real-answer study.
"""
import json
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.claim_verifier import ClaimVerifier
from src.evaluator import calculate_metrics, csv_bytes
from src.hybrid_verifier import HYBRID_VERSION, HybridVerifier
from src.loader import load_evaluation, load_facts, load_sources, source_documents
from src.models import SUPPORTED
from src.nli import MODEL_REVISION, shared_model
from src.research_evaluator import load_challenge, validate_freeze
from src.retriever import Retriever
from src.utils import PROJECT_ROOT, atomic_json, utc_now


def main():
    base = PROJECT_ROOT / "data"
    sources = load_sources(base / "sources.json")
    facts = load_facts(base / "facts.csv", sources)
    v1 = load_evaluation(base / "evaluation.csv", facts)
    challenge = load_challenge(base / "research" / "challenge.jsonl", facts)
    sets = [("v1_development", "", row) for row in v1.loc[v1["split"] == "development"].to_dict("records")]
    sets += [("v1_evaluation", "", row) for row in v1.loc[v1["split"] == "evaluation"].to_dict("records")]
    sets += [("v2_challenge", row["exclude_event"], row) for row in challenge]
    nli, engines, rows = shared_model(), {}, []
    for name, excluded, case in sets:
        if excluded not in engines:
            visible = [f for f in facts if f.event_id != excluded]
            retriever = Retriever([d for d in source_documents(base, sources, visible) if d.id in {f.id for f in visible}])
            engines[excluded] = {"claims_guarded": ClaimVerifier(visible, retriever), "hybrid_v3": HybridVerifier(visible, retriever, nli)}
        for method, engine in engines[excluded].items():
            verdict = engine.verify(case["question"], case["answer"])
            rows.append({"set": name, "id": case["id"], "event_id": case["event_id"], "question": case["question"],
                         "answer": case["answer"], "gold": case["label"], "method": method, "prediction": verdict.label,
                         "correct": verdict.label == case["label"], "elapsed_ms": verdict.elapsed_ms,
                         "nli_trace": json.dumps(verdict.metadata.get("nli_trace", []), ensure_ascii=False)})
    frame = pd.DataFrame(rows)
    metrics = {}
    for (name, method), part in frame.groupby(["set", "method"]):
        metric = calculate_metrics(part)
        negative = part["gold"] != SUPPORTED
        metric["false_support_count"] = int(((part["prediction"] == SUPPORTED) & negative).sum())
        metric["non_supported_gold_count"] = int(negative.sum())
        metric["correct"] = int(part["correct"].sum())
        metrics.setdefault(name, {})[method] = metric
    paired = frame.pivot_table(index=["set", "id"], columns="method", values="prediction", aggfunc="first").reset_index()
    changed = paired.loc[paired["claims_guarded"] != paired["hybrid_v3"]]
    output = PROJECT_ROOT / "reports" / "research_v3"
    output.mkdir(parents=True, exist_ok=True)
    (output / "regression_results.csv").write_bytes(csv_bytes(frame))
    summary = {"created_at": utc_now(), "version": HYBRID_VERSION, "model_revision": MODEL_REVISION,
               "v2_engine_matches_freeze": validate_freeze(), "metrics": metrics, "changed_predictions": len(changed),
               "data_origin": "Bộ tổng hợp đã xem khi phát triển v2; chỉ là kiểm tra hồi quy."}
    atomic_json(output / "regression.json", summary)
    for name, by_method in metrics.items():
        line = " | ".join(f"{m}: {v['correct']}/{v['n']} đúng, hỗ trợ sai {v['false_support_count']}/{v['non_supported_gold_count']}, "
                          f"{v['mean_ms']:.0f} ms" for m, v in by_method.items())
        print(f"{name:15s} {line}")
    print(f"Số ca v3 đổi nhãn so với v2: {len(changed)}")


if __name__ == "__main__":
    main()
