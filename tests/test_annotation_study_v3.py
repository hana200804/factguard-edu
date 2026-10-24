"""Synthetic metric fixtures only; these are not real answers or human annotations."""
import json

import pytest

from src import annotation_study_v3 as study
from src.nli import NliScore


class FakeNli:
    def __init__(self):
        self.calls = []

    def score(self, pairs):
        self.calls.extend(pairs)
        return [NliScore(.95, .03, .02) for _ in pairs]


@pytest.mark.parametrize("freeze_matches", [False, True])
def test_evaluate_collected_v3_keeps_five_methods_and_actual_metrics(corpus, cases, monkeypatch, freeze_matches):
    _, facts, documents = corpus
    development = cases.loc[cases["split"] == "development"]
    # The second gold label deliberately exercises a false support count, not a history judgement.
    accepted = [dict(id=f"software-test-{index}", question=question, answer=answer, event_id=event, label=label,
                     reviewers=["Software test rater 1", "Software test rater 2"], origin="Software metric fixture")
                for index, (question, answer, event, label) in enumerate([
                    ("Tuyên ngôn Độc lập được đọc vào ngày nào?", "Ngày 2/9/1945.", "independence1945", "supported"),
                    ("Kiểm chứng câu trả lời.", "Chiến dịch Điện Biên Phủ diễn ra tại Điện Biên Phủ.", "dbp1954", "contradicted"),
                    ("Sự kiện kiểm thử ngoài kho là gì?", "Dữ liệu kiểm thử ngoài kho.", "outside", "insufficient"),
                ])]
    monkeypatch.setattr(study, "validate_v3_freeze", lambda: freeze_matches)
    fake = FakeNli()
    frame, summary = study.evaluate_collected_v3(facts, documents, development, accepted, fake)
    assert len(frame) == 15 and summary["cases"] == 3
    assert set(frame["method"]) == {"lexical_3way", "rules_single_v1", "claims_no_guard", "claims_guarded", "hybrid_v3"}
    assert summary["v3_engine_matches_freeze"] is freeze_matches and summary["engine_matches_freeze"]
    hybrid = frame.loc[frame["method"] == "hybrid_v3"]
    metrics = summary["metrics"]["hybrid_v3"]
    assert metrics["n"] == 3 and metrics["accuracy"] == pytest.approx(float(hybrid["correct"].mean()))
    assert metrics["false_support_count"] == 1 and metrics["non_supported_gold_count"] == 2
    assert metrics["decisive_coverage"] == pytest.approx(2 / 3) and metrics["decisive_risk"] == .5
    assert "claim_detection_recall" not in metrics
    assert fake.calls and any(json.loads(value) for value in hybrid["nli_trace"])
    assert all(json.loads(value) == accepted[0]["reviewers"] for value in frame["reviewers"])
    assert summary["hybrid_vs_rules_interval"]["first"] == "hybrid_v3"


def test_evaluate_collected_v3_requires_cases_before_using_nli(corpus, cases):
    _, facts, documents = corpus
    fake = FakeNli()
    with pytest.raises(ValueError, match="Chưa có ca"):
        study.evaluate_collected_v3(facts, documents, cases.loc[cases["split"] == "development"], [], fake)
    assert fake.calls == []


def test_evaluate_collected_v3_rejects_development_event_before_using_nli(corpus, cases):
    _, facts, documents = corpus
    development = cases.loc[cases["split"] == "development"]
    fake = FakeNli()
    with pytest.raises(ValueError, match="trùng development"):
        study.evaluate_collected_v3(facts, documents, development, [{"event_id": development.iloc[0]["event_id"]}], fake)
    assert fake.calls == []
