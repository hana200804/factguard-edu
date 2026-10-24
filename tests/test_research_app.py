import csv
import io
import os
from datetime import date
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from src.collection import QUESTION_BANK, TEMPLATE_COLUMNS, read_table
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


@pytest.fixture
def collection_row():
    question = read_table(QUESTION_BANK)[0]
    return {
        "ma_cau_hoi": question["ma_cau_hoi"], "ma_su_kien": question["ma_su_kien"],
        "cau_hoi": question["cau_hoi"], "cong_cu": "Công cụ kiểm thử tải CSV",
        "phien_ban": "Phiên bản kiểm thử phần mềm", "ngay_lay": date.today().isoformat(),
        "kieu_lenh": "ngan_gon", "nguoi_thu_thap": "Người thu thập kiểm thử tải CSV",
        "cau_tra_loi": "Ngày 2/9/1945.",
        "ghi_chu": "Dữ liệu kiểm thử phần mềm, không phải câu trả lời chatbot thật.",
    }


def answer_sheet(rows):
    handle = io.StringIO(newline="")
    writer = csv.DictWriter(handle, TEMPLATE_COLUMNS)
    writer.writeheader()
    writer.writerows(rows)
    return handle.getvalue().encode("utf-8-sig")


def upload_answer_sheet(app, payload):
    app.radio(key="navigation").set_value(PAGE_NAMES[6]).run()
    app.file_uploader(key="collection_csv").set_value(("software-test.csv", payload, "text/csv")).run()


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


def test_csv_upload_previews_blindly_then_imports_unlabelled_cases_idempotently(app, tmp_path, collection_row):
    payload = answer_sheet([collection_row])
    upload_answer_sheet(app, payload)
    assert not app.exception and not app.error
    assert any(expander.label == "Nhập nhiều câu trả lời từ tệp CSV" for expander in app.expander)
    expected_columns = ["Dòng CSV", "Mã câu hỏi", "Câu hỏi", "Câu trả lời"]
    preview = next(frame.value for frame in app.dataframe if list(frame.value.columns) == expected_columns)
    assert preview.to_dict("records") == [{
        "Dòng CSV": 2, "Mã câu hỏi": collection_row["ma_cau_hoi"],
        "Câu hỏi": collection_row["cau_hoi"], "Câu trả lời": collection_row["cau_tra_loi"],
    }]
    for value in [collection_row["cong_cu"], collection_row["phien_ban"],
                  collection_row["nguoi_thu_thap"], collection_row["ghi_chu"]]:
        assert value not in preview.to_string(index=False)
    repository = ReviewRepository(tmp_path)
    assert repository.collected_cases() == [] and repository.annotations() == []
    directory = tmp_path / "collection_imports"
    snapshots = list(directory.glob("upload_*.csv"))
    assert len(snapshots) == 1 and snapshots[0].read_bytes() == payload
    assert not list(directory.glob("import_*.csv"))
    app.run()
    assert not app.exception and list(directory.glob("upload_*.csv")) == snapshots
    widget(app.button, "Nhập vào hàng đợi gán nhãn").click().run()
    assert not app.exception and not app.error
    stored = repository.collected_cases()
    assert len(stored) == 1
    for stored_key, sheet_key in [("question", "cau_hoi"), ("answer", "cau_tra_loi"),
                                  ("event_id", "ma_su_kien"), ("submitter", "nguoi_thu_thap")]:
        assert stored[0][stored_key] == collection_row[sheet_key]
    assert collection_row["cong_cu"] in stored[0]["origin"]
    assert repository.annotations() == [] and repository.verify_audit()
    first_logs = list(directory.glob("import_*.csv"))
    assert len(first_logs) == 1
    first_log = read_table(first_logs[0])
    assert list(first_log[0]) == ["row", "qid", "case_id", "status"]
    assert first_log == [{"row": "2", "qid": collection_row["ma_cau_hoi"],
                          "case_id": stored[0]["id"], "status": "đã nhập"}]
    audit_before = repository.audit_export()
    widget(app.button, "Nhập vào hàng đợi gán nhãn").click().run()
    assert not app.exception and not app.error
    new_logs = set(directory.glob("import_*.csv")) - set(first_logs)
    assert len(new_logs) == 1 and read_table(new_logs.pop())[0]["status"] == "đã có, bỏ qua"
    assert repository.collected_cases() == stored and repository.audit_export() == audit_before
    assert repository.annotations() == [] and repository.verify_audit()
    assert list(directory.glob("upload_*.csv")) == snapshots


def test_csv_upload_with_one_invalid_row_blocks_the_whole_sheet(app, tmp_path, collection_row):
    upload_answer_sheet(app, answer_sheet([collection_row]))
    assert not app.exception and not app.error
    assert not widget(app.button, "Nhập vào hàng đợi gán nhãn").disabled
    repository = ReviewRepository(tmp_path)
    assert repository.collected_cases() == []
    invalid = {**collection_row, "phien_ban": "", "cau_tra_loi": "Câu trả lời kiểm thử khác."}
    upload_answer_sheet(app, answer_sheet([collection_row, invalid]))
    app.run()
    assert not app.exception
    assert any("Dòng 3" in error.value and "thiếu phien_ban" in error.value for error in app.error)
    assert not any(button.label == "Nhập vào hàng đợi gán nhãn" for button in app.button)
    assert repository.collected_cases() == [] and repository.annotations() == []
    assert repository.audit_export() == [] and repository.verify_audit()
    assert not list((tmp_path / "collection_imports").glob("import_*.csv"))


def test_csv_upload_with_only_blank_answers_disables_import(app, tmp_path, collection_row):
    upload_answer_sheet(app, answer_sheet([{**collection_row, "cau_tra_loi": ""}]))
    assert not app.exception and not app.error
    assert widget(app.button, "Nhập vào hàng đợi gán nhãn").disabled
    repository = ReviewRepository(tmp_path)
    assert repository.collected_cases() == [] and repository.annotations() == []
    assert not list((tmp_path / "collection_imports").glob("import_*.csv"))


def test_csv_import_log_write_failure_reports_already_processed_cases(app, tmp_path, collection_row, monkeypatch):
    original_open = Path.open

    def fail_import_log(path, mode="r", *args, **kwargs):
        if path.name.startswith("import_") and mode == "w":
            raise OSError("Simulated software-test log write failure")
        return original_open(path, mode, *args, **kwargs)

    monkeypatch.setattr(Path, "open", fail_import_log)
    upload_answer_sheet(app, answer_sheet([collection_row]))
    widget(app.button, "Nhập vào hàng đợi gán nhãn").click().run()
    assert not app.exception
    errors = [error.value for error in app.error]
    assert any("Đã xử lý các ca trong hàng đợi nhưng chưa lưu được nhật ký CSV" in error for error in errors)
    assert not any("chưa nhập dòng nào" in error.casefold() for error in errors)
    repository = ReviewRepository(tmp_path)
    stored = repository.collected_cases()
    assert len(stored) == 1
    assert stored[0]["question"] == collection_row["cau_hoi"]
    assert stored[0]["answer"] == collection_row["cau_tra_loi"]
    assert repository.annotations() == [] and repository.verify_audit()
    assert not list((tmp_path / "collection_imports").glob("import_*.csv"))


def test_csv_upload_over_five_mib_is_rejected_before_saving_or_importing(app, tmp_path):
    upload_answer_sheet(app, b"x" * (5 * 1024 * 1024 + 1))
    assert not app.exception
    assert any("vượt giới hạn 5 MB" in error.value for error in app.error)
    assert not any(button.label == "Nhập vào hàng đợi gán nhãn" for button in app.button)
    assert not (tmp_path / "collection_imports").exists()
    repository = ReviewRepository(tmp_path)
    assert repository.collected_cases() == [] and repository.annotations() == []


def test_csv_upload_with_legacy_encoding_shows_data_error_without_crashing(app, tmp_path):
    payload = "cau_tra_loi\nDonnée de test: café\n".encode("cp1252")
    upload_answer_sheet(app, payload)
    assert not app.exception
    assert any("Tệp không phải UTF-8" in error.value for error in app.error)
    assert not any(button.label == "Nhập vào hàng đợi gán nhãn" for button in app.button)
    repository = ReviewRepository(tmp_path)
    assert repository.collected_cases() == [] and repository.annotations() == []
    assert not list((tmp_path / "collection_imports").glob("import_*.csv"))
