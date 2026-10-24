"""Workspace tests use labelled software fixtures and temporary storage only."""
import copy
import json

import pytest
from streamlit.testing.v1 import AppTest

from src import annotation_study_v3, collected_workspace_v3, research_v3_ui
from src.loader import DataError
from src.nli import NliScore
from src.review import ReviewRepository
from src.ui import PAGE_NAMES
from src.utils import PROJECT_ROOT


class FakeNli:
    def __init__(self):
        self.calls = []

    def score(self, pairs):
        self.calls.extend(pairs)
        return [NliScore(.95, .03, .02) for _ in pairs]


def seed_software_cases(repository):
    identifiers = []
    for question, answer, event in [
        ("Kiểm chứng câu trả lời.", "Chiến dịch Điện Biên Phủ diễn ra tại Điện Biên Phủ.", "dbp1954"),
        ("Tuyên ngôn Độc lập được đọc vào ngày nào?", "Ngày 2/9/1945.", "independence1945"),
        ("Câu hỏi kiểm thử ngoài kho?", "Câu trả lời kiểm thử ngoài kho.", "outside"),
    ]:
        identifier = repository.add_case(question=question, answer=answer, event_id=event,
                                         origin="Software test fixture; not a real chatbot response", submitter="Software tester")
        identifiers.append(identifier)
        if event != "outside":
            for reviewer in ["Software test rater 1", "Software test rater 2"]:
                repository.annotate(case_id=identifier, question=question, answer=answer, reviewer=reviewer,
                                    label="supported", evidence_ids=["F015" if event == "dbp1954" else "F001"],
                                    note="Software annotation fixture, not a human study.", confirmed=True)
    return identifiers


@pytest.fixture
def workspace(tmp_path, monkeypatch, corpus, cases):
    repository = ReviewRepository(tmp_path)
    identifiers = seed_software_cases(repository)
    monkeypatch.setattr(collected_workspace_v3, "validate_v3_freeze", lambda: True)
    monkeypatch.setattr(annotation_study_v3, "validate_v3_freeze", lambda: True)
    development = cases.loc[cases["split"] == "development"]
    return repository, identifiers, corpus, development, FakeNli()


def run_fixture(workspace):
    repository, _, (_, facts, documents), development, fake = workspace
    return collected_workspace_v3.run_collected_study_v3(
        facts, documents, development, repository.collected_cases(), repository.annotations(), fake)


def test_report_exports_real_computed_counts_and_preserves_previous_runs(workspace, tmp_path):
    repository, _, _, _, fake = workspace
    frame, summary = run_fixture(workspace)
    assert summary["cases"] == 2 and summary["collected_count"] == 3 and summary["pending_count"] == 1
    assert summary["unique_question_count"] == 2 and summary["event_code_count"] == 2
    assert len(frame) == 10 and fake.calls
    first = collected_workspace_v3.save_collected_study_v3(frame, summary, tmp_path)
    second = collected_workspace_v3.save_collected_study_v3(frame, summary, tmp_path)
    assert first != second and first.is_dir() and second.is_dir()
    directory, loaded, record = collected_workspace_v3.load_latest_study_v3(tmp_path)
    assert directory == second and record == summary and len(loaded) == 10
    report = (directory / "report.md").read_text(encoding="utf-8")
    assert "đánh giá 2 ca đồng thuận" in report and "còn 1 ca chờ hoặc bất đồng" in report
    assert all(name in report for name in collected_workspace_v3.METHOD_NAMES.values())
    assert summary["input_sha256"] in report and "không xác thực danh tính" in report
    assert repository.verify_audit()


def test_input_digest_ignores_order_but_changes_with_actual_labels(workspace):
    repository = workspace[0]
    collected, annotations = repository.collected_cases(), repository.annotations()
    original = collected_workspace_v3.study_input_digest(collected, annotations)
    assert original == collected_workspace_v3.study_input_digest(list(reversed(collected)), list(reversed(annotations)))
    assert original == collected_workspace_v3.study_input_digest(collected, [*annotations, {"case_id": "unrelated"}])
    changed = copy.deepcopy(annotations)
    changed[0]["label"] = "insufficient"
    assert original != collected_workspace_v3.study_input_digest(collected, changed)


def test_study_requires_actual_consensus_and_a_matching_freeze(workspace, monkeypatch):
    repository, _, (_, facts, documents), development, fake = workspace
    with pytest.raises(DataError, match="Chưa có ca"):
        collected_workspace_v3.run_collected_study_v3(facts, documents, development, [], [], fake)
    monkeypatch.setattr(collected_workspace_v3, "validate_v3_freeze", lambda: False)
    with pytest.raises(DataError, match="chưa khớp"):
        run_fixture(workspace)
    assert fake.calls == [] and len(repository.collected_cases()) == 3


def test_changed_freeze_after_evaluation_is_not_saved_as_primary(workspace, monkeypatch):
    monkeypatch.setattr(annotation_study_v3, "validate_v3_freeze", lambda: False)
    with pytest.raises(DataError, match="sau lần chạy"):
        run_fixture(workspace)


@pytest.mark.parametrize("name", ["results.csv", "summary.json", "report.md"])
def test_changed_saved_results_are_detected(workspace, tmp_path, name):
    frame, summary = run_fixture(workspace)
    directory = collected_workspace_v3.save_collected_study_v3(frame, summary, tmp_path)
    (directory / name).write_bytes(b"changed software test fixture")
    with pytest.raises(DataError, match="Không đọc được"):
        collected_workspace_v3.load_latest_study_v3(tmp_path)


def test_latest_pointer_cannot_escape_runtime(tmp_path):
    base = tmp_path / "collected_study_v3"
    base.mkdir()
    (base / "latest.json").write_text(json.dumps({"run_id": "../../outside"}), encoding="utf-8")
    with pytest.raises(DataError, match="Không đọc được"):
        collected_workspace_v3.load_latest_study_v3(tmp_path)


def widget(nodes, label):
    return next(node for node in nodes if node.label == label)


@pytest.fixture
def app(tmp_path, monkeypatch):
    monkeypatch.setenv("FACTGUARD_RUNTIME_DIR", str(tmp_path))
    return AppTest.from_file(str(PROJECT_ROOT / "app.py"), default_timeout=30).run()


def test_opening_research_workspace_does_not_load_model_or_create_results(app, tmp_path, monkeypatch):
    def forbidden():
        pytest.fail("Browsing must not load the optional NLI model")

    monkeypatch.setattr(research_v3_ui, "shared_model", forbidden)
    app.radio(key="navigation").set_value(PAGE_NAMES[6]).run()
    assert not app.exception
    assert widget(app.button, "Đánh giá v3 và xuất báo cáo").disabled
    assert not (tmp_path / "collected_study_v3").exists()
    assert ReviewRepository(tmp_path).collected_cases() == []


def test_comparison_explains_nli_without_adding_study_cases(app, tmp_path, monkeypatch):
    fake = FakeNli()
    monkeypatch.setattr(research_v3_ui, "shared_model", lambda: fake)
    monkeypatch.setattr(research_v3_ui, "validate_v3_freeze", lambda: True)
    app.radio(key="navigation").set_value(PAGE_NAMES[6]).run()
    widget(app.text_area, "Câu trả lời so sánh v3").set_value("Chiến dịch Điện Biên Phủ diễn ra tại Điện Biên Phủ.")
    widget(app.button, "So sánh v2 và v3").click().run()
    assert not app.exception and fake.calls
    result = app.session_state["v3_comparison_result"]
    assert result["v2"].label == "insufficient" and result["v3"].label == "supported"
    assert any("Quyết định" in frame.value.columns for frame in app.dataframe)
    repository = ReviewRepository(tmp_path)
    assert repository.collected_cases() == [] and repository.annotations() == []
    widget(app.text_area, "Câu trả lời so sánh v3").set_value("Câu trả lời kiểm thử đã sửa.")
    widget(app.button, "So sánh v2 và v3").click().run()
    assert not app.exception
    assert app.session_state["v3_comparison_result"]["answer"] == "Câu trả lời kiểm thử đã sửa."


def test_comparison_blocks_invalid_freeze_without_model_inference(app, monkeypatch):
    fake = FakeNli()
    monkeypatch.setattr(research_v3_ui, "shared_model", lambda: fake)
    monkeypatch.setattr(research_v3_ui, "validate_v3_freeze", lambda: False)
    app.radio(key="navigation").set_value(PAGE_NAMES[6]).run()
    widget(app.text_area, "Câu trả lời so sánh v3").set_value("Câu trả lời kiểm thử.")
    widget(app.button, "So sánh v2 và v3").click().run()
    assert not app.exception and any("chưa khớp" in error.value for error in app.error)
    assert fake.calls == []


def test_consensus_to_v3_report_and_stale_label_warning_through_ui(app, tmp_path, monkeypatch):
    repository = ReviewRepository(tmp_path)
    identifiers = seed_software_cases(repository)
    fake = FakeNli()
    monkeypatch.setattr(research_v3_ui, "shared_model", lambda: fake)
    monkeypatch.setattr(research_v3_ui, "validate_v3_freeze", lambda: True)
    monkeypatch.setattr(collected_workspace_v3, "validate_v3_freeze", lambda: True)
    monkeypatch.setattr(annotation_study_v3, "validate_v3_freeze", lambda: True)
    app.radio(key="navigation").set_value(PAGE_NAMES[6]).run()
    assert not widget(app.button, "Đánh giá v3 và xuất báo cáo").disabled
    widget(app.button, "Đánh giá v3 và xuất báo cáo").click().run()
    assert not app.exception and not app.error
    directory, frame, summary = collected_workspace_v3.load_latest_study_v3(tmp_path)
    assert summary["cases"] == 2 and len(frame) == 10 and (directory / "report.md").is_file()
    case = next(row for row in repository.collected_cases() if row["id"] == identifiers[0])
    repository.annotate(case_id=case["id"], question=case["question"], answer=case["answer"], reviewer="Software test rater 2",
                        label="insufficient", evidence_ids=[], note="Software fixture edited to create disagreement.", confirmed=True)
    app.run()
    assert not app.exception and any("Dữ liệu hoặc phiếu gán nhãn đã thay đổi" in warning.value for warning in app.warning)
