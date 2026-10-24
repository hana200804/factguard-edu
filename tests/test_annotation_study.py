import pytest

from src.annotation_study import consensus_cases, evaluate_collected
from src.review import ReviewRepository


def test_collected_cases_need_two_actual_ratings_and_keep_disagreements(tmp_path):
    repository = ReviewRepository(tmp_path)
    identifier = repository.add_case(question="Q", answer="A", origin="Software test fixture", submitter="Tester", event_id="outside")
    assert consensus_cases(repository.collected_cases(), repository.annotations())[0] == []
    repository.annotate(case_id=identifier, question="Q", answer="A", reviewer="Rater 1", label="insufficient", evidence_ids=[], note="Nguồn chưa đủ.", confirmed=True)
    assert not consensus_cases(repository.collected_cases(), repository.annotations())[0]
    repository.annotate(case_id=identifier, question="Q", answer="A", reviewer="Rater 2", label="supported", evidence_ids=["F001"], note="Ghi nhãn thử nghiệm.", confirmed=True)
    accepted, pending = consensus_cases(repository.collected_cases(), repository.annotations())
    assert not accepted and pending[0]["raters"] == 2
    repository.annotate(case_id=identifier, question="Q", answer="A", reviewer="Rater 2", label="insufficient", evidence_ids=[], note="Đã đối chiếu lại.", confirmed=True)
    accepted, _ = consensus_cases(repository.collected_cases(), repository.annotations())
    assert len(accepted) == 1 and accepted[0]["label"] == "insufficient"
    with pytest.raises(ValueError):
        repository.add_case(question="Q", answer="A", origin="test", submitter="Tester", event_id="outside")


def test_actual_label_evaluation_is_separate_and_not_fabricated(corpus, cases):
    sources, facts, documents = corpus
    development = cases.loc[cases["split"] == "development"].copy()
    accepted = [dict(id="human-test", event_id="independence1945", question="Tuyên ngôn Độc lập được đọc vào ngày nào?",
                     answer="Ngày 2 tháng 9 năm 1945.", label="supported", reviewers=["Test rater 1", "Test rater 2"], origin="Software unit test")]
    frame, summary = evaluate_collected(facts, documents, development, accepted)
    assert len(frame) == 4 and summary["cases"] == 1
    assert "claim_detection_recall" not in summary["metrics"]["claims_guarded"]
    with pytest.raises(ValueError):
        evaluate_collected(facts, documents, development, [])
