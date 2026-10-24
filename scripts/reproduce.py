"""Verify deterministic predictions twice without changing the published report."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.evaluator import data_fingerprints, run_experiment
from src.loader import load_evaluation, load_facts, load_sources, source_documents
from src.retriever import Retriever
from src.utils import PROJECT_ROOT, atomic_json, utc_now


def main():
    base = PROJECT_ROOT / "data"
    sources = load_sources(base / "sources.json")
    facts = load_facts(base / "facts.csv", sources)
    cases = load_evaluation(base / "evaluation.csv", facts)
    retriever = Retriever(source_documents(base, sources, facts))
    first, _ = run_experiment(facts, retriever, cases)
    second, _ = run_experiment(facts, retriever, cases)
    columns = ["id", "method", "gold", "prediction", "explanation"]
    same = first[columns].equals(second[columns])
    result = {"created_at": utc_now(), "identical_predictions": same, "rows_per_run": len(first),
              "data_sha256": data_fingerprints(base), "timing_compared": False}
    atomic_json(PROJECT_ROOT / "reports" / "reproducibility.json", result)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if not same:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
