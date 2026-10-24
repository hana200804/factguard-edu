import os
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from src.review import ReviewRepository
from src.storage import Store
from src.ui import PAGE_NAMES
from src.utils import PROJECT_ROOT


def widget(nodes, label):
    return next(node for node in nodes if node.label == label)


@pytest.fixture
def app(monkeypatch, tmp_path):
    monkeypatch.setenv("FACTGUARD_RUNTIME_DIR", str(tmp_path))
    return AppTest.from_file(str(PROJECT_ROOT / "app.py"), default_timeout=30).run()


def test_multiple_claim_demo_exposes_per_claim_labels(app):
    app.radio(key="navigation").set_value(PAGE_NAMES[1]).run()
    app.selectbox(key="sample").set_value("Đúng ngày nhưng sai nhân vật").run()
    widget(app.button, "Kiểm chứng").click().run()
    result = app.session_state["last_result"]["verdict"]
    assert result.label == "contradicted" and len(result.checks) == 3
    assert not app.exception


def test_research_workspace_runs_four_methods_and_starts_without_human_labels(app):
    app.radio(key="navigation").set_value(PAGE_NAMES[6]).run()
    assert not app.exception
    widget(app.button, "Chạy nghiên cứu bốn phương pháp").click().run()
    assert not app.exception
    repository = ReviewRepository(Path(os.environ["FACTGUARD_RUNTIME_DIR"]))
    assert repository.annotations() == [] and repository.collected_cases() == []
    assert widget(app.button, "Đánh giá các ca đã có hai nhãn đồng thuận").disabled
    widget(app.button, "Lưu nhãn của tôi").click().run()
    assert app.error and repository.annotations() == []


def test_draft_approve_verify_and_withdraw_through_ui(app):
    runtime = Path(os.environ["FACTGUARD_RUNTIME_DIR"])
    source = "Sự kiện kiểm thử diễn ra vào ngày 7/5/1954 tại một địa điểm minh họa."
    Store(runtime).import_document("software-test.txt", source.encode())
    app.radio(key="navigation").set_value(PAGE_NAMES[2]).run()
    for label, value in [("Câu hỏi chuẩn của dữ kiện mới", "Sự kiện kiểm thử diễn ra vào ngày nào?"),
                         ("Đáp án hiển thị", "7/5/1954"),
                         ("Giá trị chuẩn: YYYY-MM-DD cho ngày; tên đầy đủ cho nhân vật/địa điểm", "1954-05-07"),
                         ("Mã sự kiện", "software_test"), ("Người lập dữ kiện", "Software tester")]:
        widget(app.text_input, label).set_value(value)
    widget(app.text_area, "Neo nhận diện: mỗi dòng một nhóm; dùng | giữa các cách viết tương đương").set_value("sự kiện kiểm thử")
    widget(app.button, "Lưu bản nháp dữ kiện").click().run()
    assert not app.exception
    repository = ReviewRepository(runtime)
    assert repository.records()[0]["state"] == "draft"
    widget(app.text_input, "Người trực tiếp duyệt nguồn").set_value("Test reviewer")
    widget(app.text_area, "Căn cứ quyết định").set_value("Đã đọc và đối chiếu đoạn thử nghiệm.")
    widget(app.checkbox, "Tôi đã đọc nguồn gốc, kiểm tra giá trị và chịu trách nhiệm về quyết định thẩm định này.").check()
    widget(app.button, "Ghi quyết định thẩm định").click().run()
    assert not app.exception and repository.records()[0]["state"] == "approved"
    app.radio(key="navigation").set_value(PAGE_NAMES[1]).run()
    app.text_area(key="question_input").set_value("Sự kiện kiểm thử diễn ra vào ngày nào?")
    app.text_area(key="answer_input").set_value("Ngày 7/5/1954.")
    widget(app.button, "Kiểm chứng").click().run()
    assert not app.exception
    assert app.session_state["last_result"]["verdict"].label == "supported"
    app.radio(key="navigation").set_value(PAGE_NAMES[2]).run()
    widget(app.text_input, "Người trực tiếp duyệt nguồn").set_value("Test reviewer")
    widget(app.text_area, "Căn cứ quyết định").set_value("Thu hồi dữ kiện dùng để kiểm thử phần mềm.")
    widget(app.checkbox, "Tôi đã đọc nguồn gốc, kiểm tra giá trị và chịu trách nhiệm về quyết định thẩm định này.").check()
    widget(app.button, "Ghi quyết định thẩm định").click().run()
    assert not app.exception and repository.records()[0]["state"] == "withdrawn"
