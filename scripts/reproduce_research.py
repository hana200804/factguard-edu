"""Run v2 twice; verify predictions, traces, event intervals and frozen files."""
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.loader import load_evaluation, load_facts, load_sources
from src.research_evaluator import load_challenge, run_research, validate_freeze
from src.utils import PROJECT_ROOT, atomic_json, digest_bytes, utc_now


def main():
    base = PROJECT_ROOT / "data"
    sources = load_sources(base / "sources.json")
    facts = load_facts(base / "facts.csv", sources)
    old_cases = load_evaluation(base / "evaluation.csv", facts)
    development = old_cases.loc[old_cases["split"] == "development"].copy()
    path = base / "research" / "challenge.jsonl"
    cases = load_challenge(path, facts)
    before = digest_bytes(path.read_bytes())
    first, first_summary = run_research(facts, sources, development, cases)
    second, second_summary = run_research(facts, sources, development, cases)
    pd.testing.assert_frame_equal(first.drop(columns="elapsed_ms"), second.drop(columns="elapsed_ms"))
    if first_summary["paired_event_interval"] != second_summary["paired_event_interval"]:
        raise AssertionError("Event bootstrap was not reproducible")
    result = {"created_at": utc_now(), "identical_predictions_and_traces": True,
              "identical_event_intervals": True, "rows_per_run": len(first), "challenge_sha256": before,
              "challenge_unchanged": before == digest_bytes(path.read_bytes()), "engine_matches_freeze": validate_freeze(),
              "timing_compared": False}
    atomic_json(PROJECT_ROOT / "reports" / "research_v2" / "reproducibility.json", result)
    if not result["challenge_unchanged"] or not result["engine_matches_freeze"]:
        raise AssertionError("Frozen engine or challenge was modified")
    print("V2 reproducibility PASS:", len(first), "predictions/traces each run; cluster interval identical.")


if __name__ == "__main__":
    main()
