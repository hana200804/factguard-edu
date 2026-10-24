"""Evaluate actual user-collected cases only after two self-declared raters agree.

This workflow does not authenticate identities or establish statistical independence.
It computes label metrics only: source IDs selected by a rater are not atomic gold claims.
"""
import json

import pandas as pd

from src.claim_verifier import ClaimVerifier
from src.evaluator import calculate_metrics
from src.models import SUPPORTED
from src.research_baseline import LexicalThreeWay
from src.research_evaluator import validate_freeze
from src.research_statistics import paired_cluster_interval
from src.retriever import Retriever
from src.review import content_hash
from src.utils import normalize, utc_now
from src.verifier import ProposedVerifier


def consensus_cases(collected: list[dict], annotations: list[dict]) -> tuple[list[dict], list[dict]]:
    accepted, pending = [], []
    for case in collected:
        signature = content_hash(case["question"], case["answer"])
        # One vote per distinct normalized name; editing a rating cannot add votes.
        votes = {normalize(row["reviewer"]): row for row in annotations
                 if row["case_id"] == case["id"] and row["content_hash"] == signature}
        if len(votes) < 2 or len({r["label"] for r in votes.values()}) != 1:
            pending.append({"id": case["id"], "raters": len(votes), "reason": "Thiếu hai nhãn đồng thuận hoặc đang bất đồng."})
            continue
        accepted.append({**case, "label": next(iter(votes.values()))["label"],
                         "reviewers": [r["reviewer"] for r in votes.values()],
                         "evidence_ids": sorted({fid for r in votes.values() for fid in r["evidence_ids"]})})
    return accepted, pending


def evaluate_collected(facts, documents, development, accepted: list[dict]) -> tuple[pd.DataFrame, dict]:
    if not accepted:
        raise ValueError("Chưa có ca người dùng thu thập với hai nhãn đồng thuận.")
    if set(development["event_id"]) & {row["event_id"] for row in accepted}:
        raise ValueError("Có sự kiện trùng development; chưa thể gọi là đánh giá giữ riêng theo sự kiện.")
    retriever = Retriever(documents)
    methods = {"lexical_3way": LexicalThreeWay(facts, development), "rules_single_v1": ProposedVerifier(facts, retriever),
               "claims_no_guard": ClaimVerifier(facts, retriever, guarded=False), "claims_guarded": ClaimVerifier(facts, retriever)}
    rows = []
    for case in accepted:
        for name, method in methods.items():
            verdict = method.verify(case["question"], case["answer"])
            rows.append({"id": case["id"], "event_id": case["event_id"], "question": case["question"],
                         "answer": case["answer"], "gold": case["label"], "method": name, "prediction": verdict.label,
                         "correct": verdict.label == case["label"], "elapsed_ms": verdict.elapsed_ms,
                         "reviewers": json.dumps(case["reviewers"], ensure_ascii=False), "origin": case["origin"]})
    frame = pd.DataFrame(rows)
    metrics = {}
    for method in methods:
        subset = frame.loc[frame["method"] == method].copy()
        metric = calculate_metrics(subset)
        negative = subset["gold"] != SUPPORTED
        metric["false_support_count"] = int(((subset["prediction"] == SUPPORTED) & negative).sum())
        metric["non_supported_gold_count"] = int(negative.sum())
        metrics[method] = metric
    return frame, {"created_at": utc_now(), "cases": len(accepted), "metrics": metrics,
                   "paired_event_interval": paired_cluster_interval(rows, "claims_guarded", "lexical_3way"),
                   "engine_matches_freeze": validate_freeze(),
                   "data_origin": "User-collected; at least two distinct self-declared names agree; identities not authenticated",
                   "limitations": "Chưa có chuẩn mệnh đề và bằng chứng chi tiết nên chỉ đo phân loại; không suy ra hiệu quả học tập."}
