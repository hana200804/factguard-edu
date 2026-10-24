"""Label-only evaluation on collected cases already accepted by the consensus workflow.

This function does not collect answers, invent ratings, or authenticate reviewers.
"""
import json

import pandas as pd

from src.claim_verifier import ClaimVerifier
from src.evaluator import calculate_metrics
from src.hybrid_verifier import HYBRID_VERSION, HybridVerifier
from src.models import CONTRADICTED, SUPPORTED
from src.research_baseline import LexicalThreeWay
from src.research_evaluator import validate_freeze
from src.research_statistics import paired_cluster_interval
from src.retriever import Retriever
from src.utils import utc_now
from src.v3_freeze import validate_v3_freeze
from src.verifier import ProposedVerifier


def evaluate_collected_v3(facts, documents, development, accepted: list[dict], nli) -> tuple[pd.DataFrame, dict]:
    if not accepted:
        raise ValueError("Chưa có ca người dùng thu thập với hai nhãn đồng thuận.")
    if set(development["event_id"]) & {row["event_id"] for row in accepted}:
        raise ValueError("Có sự kiện trùng development; chưa thể gọi là đánh giá giữ riêng theo sự kiện.")
    retriever = Retriever(documents)
    methods = {"lexical_3way": LexicalThreeWay(facts, development), "rules_single_v1": ProposedVerifier(facts, retriever),
               "claims_no_guard": ClaimVerifier(facts, retriever, guarded=False), "claims_guarded": ClaimVerifier(facts, retriever),
               "hybrid_v3": HybridVerifier(facts, retriever, nli)}
    rows = []
    for case in accepted:
        for name, method in methods.items():
            verdict = method.verify(case["question"], case["answer"])
            rows.append({"id": case["id"], "event_id": case["event_id"], "question": case["question"],
                         "answer": case["answer"], "gold": case["label"], "method": name, "prediction": verdict.label,
                         "correct": verdict.label == case["label"], "elapsed_ms": verdict.elapsed_ms,
                         "reviewers": json.dumps(case["reviewers"], ensure_ascii=False), "origin": case["origin"],
                         "rules_label": verdict.metadata.get("rules_label", ""),
                         "nli_trace": json.dumps(verdict.metadata.get("nli_trace", []), ensure_ascii=False)})
    frame = pd.DataFrame(rows)
    metrics = {}
    for method in methods:
        subset = frame.loc[frame["method"] == method].copy()
        metric = calculate_metrics(subset)
        negative = subset["gold"] != SUPPORTED
        decisive = subset.loc[subset["prediction"].isin([SUPPORTED, CONTRADICTED])]
        metric["false_support_count"] = int(((subset["prediction"] == SUPPORTED) & negative).sum())
        metric["non_supported_gold_count"] = int(negative.sum())
        metric["decisive_coverage"] = len(decisive) / len(subset)
        metric["decisive_risk"] = float((~decisive["correct"].astype(bool)).mean()) if len(decisive) else None
        metrics[method] = metric
    return frame, {"created_at": utc_now(), "version": HYBRID_VERSION, "cases": len(accepted), "metrics": metrics,
                   "paired_event_interval": paired_cluster_interval(rows, "claims_guarded", "lexical_3way"),
                   "hybrid_vs_rules_interval": paired_cluster_interval(rows, "hybrid_v3", "claims_guarded"),
                   "engine_matches_freeze": validate_freeze(), "v3_engine_matches_freeze": validate_v3_freeze(),
                   "data_origin": "User-collected; at least two distinct self-declared names agree; identities not authenticated",
                   "limitations": "Chỉ đo phân loại trên ca đồng thuận được truyền vào; chưa có chuẩn mệnh đề/bằng chứng chi tiết. Không xác thực người gán nhãn hoặc suy ra hiệu quả học tập. Chưa đóng băng thì chỉ là chạy thăm dò."}
