from dataclasses import replace

import pytest

from src.baseline import BaselineVerifier
from src.models import CONTRADICTED, INSUFFICIENT, SUPPORTED, UNDETERMINED
from src.retriever import Retriever
from src.verifier import ProposedVerifier, extract_dates

QUESTION = "Chủ tịch Hồ Chí Minh đọc Tuyên ngôn Độc lập vào ngày nào?"


@pytest.mark.parametrize("answer", ["2/9/1945", "02-09-1945", "2.9.1945", "Ngày 2 tháng 9 năm 1945."])
def test_supported_dates_have_citation(verifier, answer):
    result = verifier.verify(QUESTION, answer)
    assert result.label == SUPPORTED
    assert result.checks[0].source_id == "S01"
    assert result.evidence and result.elapsed_ms > 0


@pytest.mark.parametrize("answer", ["Ngày 2/9/1946.", "3/9/1945", "Năm 1946."])
def test_date_contradictions(verifier, answer):
    assert verifier.verify(QUESTION, answer).label == CONTRADICTED


@pytest.mark.parametrize("answer", ["1945", "Tôi không biết.", "Có lẽ ngày 2/9/1945.", "", "Một ngày mùa thu."])
def test_incomplete_answer_abstains(verifier, answer):
    assert verifier.verify(QUESTION, answer).label == INSUFFICIENT


@pytest.mark.parametrize("answer", ["Không phải 2/9/1945.", "3/9/1945 hoặc 2/9/1945.",
                                  "2/9/1945 và 3/9/1945.", "31/2/1945.",
                                  "2/9/1945. Người ngoài hành tinh đã đến.",
                                  "Ngày 2/9/1945 tại Sao Hỏa.", "Ngày 2/9/1945, năm 1946."])
def test_complex_answers_never_supported(verifier, answer):
    assert verifier.verify(QUESTION, answer).label in {UNDETERMINED, INSUFFICIENT}


def test_wrong_entity_and_correct_entity(verifier):
    question = "Ai chỉ huy chiến dịch Điện Biên Phủ?"
    assert verifier.verify(question, "Đại tướng Võ Nguyên Giáp.").label == SUPPORTED
    assert verifier.verify(question, "Trần Phú.").label == CONTRADICTED
    assert verifier.verify(question, "Một vị tướng.").label == INSUFFICIENT
    assert verifier.verify(question, "Võ Nguyên Giáp đến từ Sao Hỏa.").label == UNDETERMINED


def test_place_precision_and_unknown_event(verifier):
    q = "Chủ tịch Hồ Chí Minh đọc Tuyên ngôn Độc lập ở đâu?"
    assert verifier.verify(q, "Quảng trường Ba Đình, Hà Nội").label == SUPPORTED
    assert verifier.verify(q, "Hà Nội").label != CONTRADICTED
    assert verifier.verify(q, "Him Lam").label == CONTRADICTED
    assert verifier.verify("Trận Bạch Đằng diễn ra ngày nào?", "7/5/1954").label == INSUFFICIENT


def test_open_question_and_long_answer(verifier):
    assert verifier.verify("Vì sao Điện Biên Phủ có ý nghĩa quốc tế?", "Chiến thắng lớn.").label == UNDETERMINED
    assert verifier.verify(QUESTION, "a" * 12001).label == UNDETERMINED
    assert verifier.verify("", "2/9/1945").label == INSUFFICIENT


def test_unverified_fact_or_ambiguous_fact_cannot_adjudicate(facts, retriever):
    unverified = [replace(f, verified=False) for f in facts]
    assert ProposedVerifier(unverified, retriever).verify(QUESTION, "2/9/1945").label == INSUFFICIENT
    duplicate = replace(facts[0], id="duplicate")
    assert ProposedVerifier([*facts, duplicate], retriever).verify(QUESTION, "2/9/1945").label == UNDETERMINED


def test_exact_evidence_added_without_index(facts):
    result = ProposedVerifier(facts, Retriever([])).verify(QUESTION, "2/9/1945")
    assert result.checks and result.evidence[0].document.text == facts[0].reference


def test_year_question_and_multiple_dates(verifier):
    assert verifier.verify("Tuyên ngôn Độc lập được đọc năm nào?", "1945").label == SUPPORTED
    assert verifier.verify("Tuyên ngôn Độc lập được đọc năm nào?", "1946").label == CONTRADICTED
    assert verifier.verify(QUESTION, "2/9/1945, 3/9/1945").label == UNDETERMINED
    assert extract_dates("ngày 31 tháng 2 năm 1945")[1]


def test_baseline_weakness_is_visible(facts):
    baseline = BaselineVerifier(facts)
    assert baseline.verify(QUESTION, "Không phải ngày 2/9/1945.").label == SUPPORTED
    assert BaselineVerifier([]).verify(QUESTION, "1945").label == INSUFFICIENT
