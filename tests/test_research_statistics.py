import pytest

from src.research_baseline import LexicalThreeWay
from src.research_statistics import paired_cluster_interval, rating_agreement


def test_baseline_can_predict_all_three_classes_and_has_no_test_fit(facts, cases):
    development = cases[cases["split"] == "development"]
    baseline = LexicalThreeWay(facts, development)
    assert set(baseline.manifest()["classes"]) == {"supported", "contradicted", "insufficient"}
    assert set(baseline.training_ids) == set(development["id"])
    assert baseline.verify("Ai chỉ huy chiến dịch Điện Biên Phủ?", "Võ Nguyên Giáp").method == "lexical_3way"
    with pytest.raises(ValueError):
        LexicalThreeWay(facts, cases)


def test_cluster_bootstrap_equal_event_weight_and_reproducibility():
    rows = []
    for i, event, difference in [(1, "e1", 1), (2, "e1", 1), (3, "e2", -1)]:
        for method, correct in [("a", difference == 1), ("b", difference != 1)]:
            rows.append(dict(id=str(i), event_id=event, gold="supported", method=method, correct=correct))
    first = paired_cluster_interval(rows, "a", "b", replicates=100)
    assert first == paired_cluster_interval(rows, "a", "b", replicates=100)
    assert first["estimate"] == 0  # Event e1 has two related cases, but one event vote.
    assert first["n_clusters"] == 2
    assert first["lower"] <= 0 <= first["upper"]


def test_agreement_requires_real_overlapping_reviewers():
    assert rating_agreement([]) == []
    annotations = [dict(case_id=str(i), content_hash="same", reviewer=reviewer, label=label)
                   for i, label in enumerate(["supported", "contradicted"])
                   for reviewer in ["Reviewer A", "Reviewer B"]]
    assert rating_agreement(annotations)[0]["cohen_kappa"] == 1
    assert rating_agreement(annotations)[0]["overlap"] == 2
    assert rating_agreement(annotations[:1]) == []
