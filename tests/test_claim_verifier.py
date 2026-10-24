from dataclasses import replace

import pytest

from src.claim_spans import alias_spans, date_spans, phrase_spans, split_clauses
from src.claim_verifier import ClaimVerifier
from src.models import CONTRADICTED, INSUFFICIENT, SUPPORTED, UNDETERMINED


@pytest.fixture(scope="module")
def engine(facts, retriever):
    return ClaimVerifier(facts, retriever)


def test_character_offsets_survive_accents_and_numeric_dots():
    text = "Hồ Chí Minh đọc ngày 02.09.1945. Ngày 7 tháng 5 năm 1954."
    assert len(split_clauses(text)) == 2
    for value in date_spans(text)[0]:
        assert text[value.span.start:value.span.end] == value.span.text
    assert phrase_spans(text, "Ho Chi Minh")[0].text == "Hồ Chí Minh"
    assert alias_spans(text, {"hcm": ["Hồ Chí Minh"]}, "person")[0].canonical == "hcm"


def test_three_values_are_separately_checked_with_offsets(engine):
    text = "Hồ Chí Minh đọc Tuyên ngôn Độc lập ngày 2/9/1945 tại Quảng trường Ba Đình."
    result = engine.verify("Kiểm chứng thông tin lịch sử sau.", text)
    assert result.label == SUPPORTED
    assert {check.fact_id for check in result.checks} == {"F001", "F002", "F003"}
    for check in result.checks:
        assert text[check.span_start:check.span_end] == check.observed
        assert check.reference and check.source_id


def test_one_wrong_value_makes_mixed_answer_contradicted(engine):
    result = engine.verify("Kiểm chứng các thông tin sau.",
                           "Võ Nguyên Giáp đọc Tuyên ngôn Độc lập ngày 2/9/1945 tại Quảng trường Ba Đình.")
    assert result.label == CONTRADICTED
    assert [c.fact_id for c in result.checks if c.label == CONTRADICTED] == ["F002"]
    assert len([c for c in result.checks if c.label == SUPPORTED]) == 2


def test_two_events_in_two_clauses_are_bound_separately(engine):
    text = "Chiến dịch Điện Biên Phủ bắt đầu ngày 13/3/1954; Chiến dịch Điện Biên Phủ kết thúc ngày 7/5/1954."
    result = engine.verify("Kiểm chứng các mốc thời gian.", text)
    assert result.label == SUPPORTED
    assert {c.relation for c in result.checks} == {"dbp.start", "dbp.end"}


@pytest.mark.parametrize("answer,expected", [
    ("Không phải ngày 2/9/1945.", CONTRADICTED),
    ("Không phải ngày 3/9/1945 mà là ngày 2/9/1945.", SUPPORTED),
    ("Không phải ngày 2/9/1945 mà là ngày 3/9/1945.", CONTRADICTED),
    ("Có lẽ ngày 2/9/1945.", INSUFFICIENT),
    ("Vào năm 1945.", INSUFFICIENT),
])
def test_negation_and_precision(engine, answer, expected):
    assert engine.verify("Chủ tịch Hồ Chí Minh đọc Tuyên ngôn Độc lập vào ngày nào?", answer).label == expected


@pytest.mark.parametrize("question", [
    "Ai đọc Tuyên ngôn Độc lập tại Him Lam năm 1945?",
    "Ai đọc Tuyên ngôn Độc lập tại Sao Hỏa năm 1945?",
    "Ai đọc Tuyên ngôn Độc lập năm 1946?",
])
def test_bad_question_premises_are_not_inherited(engine, question):
    result = engine.verify(question, "Hồ Chí Minh")
    assert result.label == UNDETERMINED
    assert any("premise" in issue["reason"] for issue in result.metadata["issues"])


def test_extra_fabricated_clause_is_accounted_for(engine):
    answer = "Hồ Chí Minh đọc Tuyên ngôn Độc lập ngày 2/9/1945. Người ngoài hành tinh tạo ra sự kiện này."
    result = engine.verify("Kiểm chứng câu trả lời.", answer)
    assert result.label == INSUFFICIENT
    assert result.checks and result.metadata["unresolved_count"] > 0


def test_source_disagreement_forces_review(engine, facts, retriever):
    conflict = replace(facts[0], id="CONFLICT", canonical="1945-09-03", answer="3/9/1945")
    result = ClaimVerifier([*facts, conflict], retriever).verify(
        "Chủ tịch Hồ Chí Minh đọc Tuyên ngôn Độc lập vào ngày nào?", "2/9/1945")
    assert result.label == UNDETERMINED
    assert any(i["reason"] == "source_conflict" for i in result.metadata["issues"])


def test_ablation_really_disables_uncovered_content_guard(facts, retriever):
    answer = "2/9/1945. Người ngoài hành tinh tạo ra sự kiện này."
    question = "Chủ tịch Hồ Chí Minh đọc Tuyên ngôn Độc lập vào ngày nào?"
    assert ClaimVerifier(facts, retriever, guarded=False).verify(question, answer).label == SUPPORTED
    assert ClaimVerifier(facts, retriever).verify(question, answer).label == INSUFFICIENT


def test_unverified_and_missing_values_never_supported(facts, retriever):
    engine = ClaimVerifier([replace(f, verified=False) for f in facts], retriever)
    assert engine.verify("Tuyên ngôn Độc lập được đọc ngày nào?", "2/9/1945").label != SUPPORTED
    assert engine.verify("", "2/9/1945").label == INSUFFICIENT


def test_correct_names_with_swapped_roles_not_supported(engine):
    result = engine.verify("Kiểm chứng câu trả lời.",
                           "Quảng trường Ba Đình đọc Tuyên ngôn Độc lập tại Hồ Chí Minh ngày 2/9/1945.")
    assert result.label != SUPPORTED
    assert any(i["reason"] == "wrong_role" for i in result.metadata["issues"])
