"""Software fixtures for v3; fake scores are not observations from the NLI model."""
import importlib.util
import io

import pytest

from scripts import fetch_model
from src.claim_verifier import ClaimVerifier
from src.hybrid_verifier import HYBRID_VERSION, HybridVerifier
from src.models import CONTRADICTED, INSUFFICIENT, SUPPORTED
from src.nli import MODEL_FILES, NliModel, NliScore, model_status


class FakeNli:
    def __init__(self, score=NliScore(.95, .03, .02)):
        self.result = score
        self.calls = []

    def score(self, pairs):
        self.calls.extend(pairs)
        return [self.result for _ in pairs]


@pytest.mark.parametrize("answer,label", [("Ngày 2/9/1945.", SUPPORTED), ("Ngày 3/9/1945.", CONTRADICTED)])
def test_decisive_rules_are_preserved_without_nli(facts, retriever, answer, label):
    fake = FakeNli()
    result = HybridVerifier(facts, retriever, fake).verify("Tuyên ngôn Độc lập được đọc vào ngày nào?", answer)
    assert result.label == label and result.metadata["rules_label"] == label
    assert fake.calls == [] and result.metadata["nli_trace"] == []
    assert result.method == "hybrid_v3" and result.metadata["algorithm_version"] == HYBRID_VERSION


@pytest.mark.parametrize("question,answer,reason", [
    ("Ai đọc Tuyên ngôn Độc lập năm 1946?", "Hồ Chí Minh", "question_premise"),
    ("Vì sao Cách mạng tháng Tám thành công?", "Do nhiều yếu tố.", "open_question"),
])
def test_deliberate_rule_stops_are_not_resolved_by_nli(facts, retriever, question, answer, reason):
    base = ClaimVerifier(facts, retriever).verify(question, answer)
    assert any(issue["reason"] == reason for issue in base.metadata["issues"])
    fake = FakeNli()
    result = HybridVerifier(facts, retriever, fake).verify(question, answer)
    assert result.label == base.label and result.metadata["rules_label"] == base.label
    assert fake.calls == [] and result.metadata["nli_trace"] == []


@pytest.mark.parametrize("answer", [
    "Đại tướng Văn Tiến Dũng tham gia chiến dịch Điện Biên Phủ.",
    "Chiến dịch Điện Biên Phủ diễn ra ngày 8/5/1954.",
])
def test_high_entailment_cannot_override_unknown_names_or_wrong_dates(facts, retriever, answer):
    fake = FakeNli()
    result = HybridVerifier(facts, retriever, fake).verify("Kiểm chứng câu trả lời.", answer)
    assert fake.calls and result.label != SUPPORTED
    assert any(row["decision"] == "blocked_by_value_guard" and not row["guard"] for row in result.metadata["nli_trace"])


@pytest.mark.parametrize("entailment,label", [(.79, INSUFFICIENT), (.80, SUPPORTED)])
def test_entailment_threshold_is_inclusive_after_value_guard(facts, retriever, entailment, label):
    fake = FakeNli(NliScore(entailment, 1 - entailment, 0))
    result = HybridVerifier(facts, retriever, fake).verify(
        "Kiểm chứng câu trả lời.", "Chiến dịch Điện Biên Phủ diễn ra tại Điện Biên Phủ.")
    assert fake.calls and result.label == label
    assert all(row["guard"] for row in result.metadata["nli_trace"])
    assert result.metadata["rules_label"] == INSUFFICIENT
    assert result.method == "hybrid_v3" and result.metadata["algorithm_version"] == HYBRID_VERSION


@pytest.mark.parametrize("contradiction,label", [(.89, INSUFFICIENT), (.90, CONTRADICTED), (.95, CONTRADICTED)])
def test_contradiction_threshold_is_inclusive(facts, retriever, contradiction, label):
    fake = FakeNli(NliScore(0, 1 - contradiction, contradiction))
    result = HybridVerifier(facts, retriever, fake).verify(
        "Kiểm chứng câu trả lời.", "Chiến dịch Điện Biên Phủ diễn ra tại Điện Biên Phủ.")
    assert fake.calls and result.label == label


def test_fallback_uses_dbp_event_not_a_single_word_anchor(facts, retriever):
    fake = FakeNli()
    result = HybridVerifier(facts, retriever, fake).verify(
        "Chiến dịch Điện Biên Phủ diễn ra từ ngày nào đến ngày nào?",
        "Chiến dịch bắt đầu ngày 13/3/1954 và kết thúc ngày 7/5/1954.")
    assert fake.calls and result.metadata["nli_trace"]
    fact_map = {fact.id: fact for fact in facts}
    selected = {identifier for row in result.metadata["nli_trace"] for identifier in row["fact_ids"]}
    assert selected and {fact_map[identifier].event_id for identifier in selected} == {"dbp1954"}
    assert all("13/3/1954" in premise and "7/5/1954" in premise for premise, _ in fake.calls)


def test_model_status_missing_and_corrupt_files(tmp_path):
    assert model_status(tmp_path) == dict.fromkeys(MODEL_FILES, False)
    for name in MODEL_FILES:
        (tmp_path / name).write_bytes(b"corrupt software test fixture")
    assert model_status(tmp_path) == dict.fromkeys(MODEL_FILES, False)
    with pytest.raises(ValueError, match="SHA-256"):
        NliModel(tmp_path)


def test_fetch_model_rejects_wrong_download_without_network_or_writing(tmp_path, monkeypatch):
    monkeypatch.setattr(fetch_model, "MODEL_DIR", tmp_path)
    monkeypatch.setattr(fetch_model, "model_status", lambda: model_status(tmp_path))
    calls = []

    def wrong_download(url, timeout):
        calls.append((url, timeout))
        return io.BytesIO(b"wrong software test bytes")

    monkeypatch.setattr(fetch_model.urllib.request, "urlopen", wrong_download)
    with pytest.raises(SystemExit, match="SHA-256"):
        fetch_model.main()
    assert len(calls) == 1 and list(tmp_path.iterdir()) == []


REAL_MODEL_READY = (all(model_status().values()) and importlib.util.find_spec("onnxruntime") is not None
                    and importlib.util.find_spec("tokenizers") is not None)


@pytest.mark.skipif(not REAL_MODEL_READY, reason="Pinned model or optional NLI runtime is unavailable")
def test_real_model_negation_and_repeatability(facts):
    model = NliModel()
    premise = next(fact.reference for fact in facts if fact.id == "F001")
    pairs = [(premise, "Hồ Chí Minh không đọc Tuyên ngôn Độc lập.")]
    first = model.score(pairs)
    assert len(first) == 1 and first[0].contradiction > first[0].entailment
    assert first == model.score(pairs)
