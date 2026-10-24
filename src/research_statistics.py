"""Paired event-cluster uncertainty and human agreement, without pseudo-replication."""
from itertools import combinations

import numpy as np
from sklearn.metrics import cohen_kappa_score

from src.utils import normalize


def paired_cluster_interval(rows: list[dict], first: str, second: str,
                            replicates: int = 2000, seed: int = 20261024) -> dict:
    by_case: dict[str, dict[str, dict]] = {}
    for row in rows:
        by_case.setdefault(row["id"], {})[row["method"]] = row
    clusters: dict[str, list[float]] = {}
    for methods in by_case.values():
        if first not in methods or second not in methods:
            raise ValueError("So sánh cặp cần hai phương pháp chạy trên cùng ca.")
        left, right = methods[first], methods[second]
        if left["gold"] != right["gold"] or left["event_id"] != right["event_id"]:
            raise ValueError("Nhãn hoặc sự kiện không khớp giữa phương pháp.")
        clusters.setdefault(left["event_id"], []).append(float(left["correct"]) - float(right["correct"]))
    if len(clusters) < 2:
        return {"first": first, "second": second, "n_clusters": len(clusters), "estimate": None,
                "lower": None, "upper": None, "reason": "Cần ít nhất hai cụm sự kiện."}
    means = np.asarray([np.mean(values) for values in clusters.values()])
    rng = np.random.default_rng(seed)
    samples = rng.choice(means, size=(replicates, len(means)), replace=True).mean(axis=1)
    return {"first": first, "second": second, "n_clusters": len(clusters),
            "estimate": float(means.mean()), "lower": float(np.quantile(samples, .025)),
            "upper": float(np.quantile(samples, .975)), "replicates": replicates, "seed": seed,
            "estimand": "Mean paired accuracy difference with equal weight per event cluster",
            "caution": "Mô tả thăm dò trên số ít cụm tổng hợp; không suy rộng tới người học hay mọi câu trả lời AI."}


def rating_agreement(annotations: list[dict]) -> list[dict]:
    reviewers: dict[str, dict[tuple[str, str], str]] = {}
    names = {}
    for row in annotations:
        key = normalize(row["reviewer"])
        names[key] = row["reviewer"]
        reviewers.setdefault(key, {})[(row["case_id"], row["content_hash"])] = row["label"]
    result = []
    for first, second in combinations(sorted(reviewers), 2):
        common = sorted(reviewers[first].keys() & reviewers[second].keys())
        if not common:
            continue
        left = [reviewers[first][key] for key in common]
        right = [reviewers[second][key] for key in common]
        # Kappa is undefined when both raters always choose the same single class.
        kappa = float(cohen_kappa_score(left, right)) if len(set(left + right)) > 1 else None
        result.append({"reviewer_1": names[first], "reviewer_2": names[second], "overlap": len(common),
                       "agreement": sum(a == b for a, b in zip(left, right, strict=True)) / len(common),
                       "cohen_kappa": kappa if kappa is None or np.isfinite(kappa) else None})
    return result
