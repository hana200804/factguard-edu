import pandas as pd

from src.research_evaluator import METHODS, run_research


def test_same_inputs_all_methods_and_evidence_metrics(corpus, cases):
    sources, facts, _ = corpus
    challenge = [{"id": "unit", "question": "Kiểm chứng các thông tin sau.",
                  "answer": "Hồ Chí Minh đọc Tuyên ngôn Độc lập ngày 2/9/1945 tại Quảng trường Ba Đình.",
                  "label": "supported", "event_id": "independence1945", "group": "unit_regression", "exclude_event": "",
                  "gold_claims": [{"fact_id": "F001", "value": "2/9/1945", "label": "supported"},
                                  {"fact_id": "F002", "value": "Hồ Chí Minh", "label": "supported"},
                                  {"fact_id": "F003", "value": "Quảng trường Ba Đình", "label": "supported"}]}]
    development = cases.loc[cases["split"] == "development"].copy()
    frame, summary = run_research(facts, sources, development, challenge)
    assert len(frame) == 4 and set(frame["method"]) == set(METHODS)
    guarded = summary["metrics"]["claims_guarded"]
    assert guarded["claim_detection_recall"] == 1
    assert guarded["claim_label_recall"] == 1
    assert guarded["evidence_complete_accuracy"] == 1
    assert guarded["false_support_rate"] is None
    first, _ = run_research(facts, sources, development, challenge)
    pd.testing.assert_frame_equal(first.drop(columns="elapsed_ms"), frame.drop(columns="elapsed_ms"))
