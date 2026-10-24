"""Collection fixtures are software test data, never real chatbot responses or study labels."""

import csv
import os
import subprocess
import sys
from datetime import date

import pytest

from src.collection import (
    BANK_COLUMNS,
    QUESTION_BANK,
    TEMPLATE_COLUMNS,
    eligible_events,
    import_cases,
    load_question_bank,
    parse_answers,
    read_table,
    template_rows,
    write_template,
)
from src.loader import DataError
from src.review import ReviewRepository
from src.utils import PROJECT_ROOT

TODAY = date(2026, 10, 24)
TEST_NOTE = "Dữ liệu kiểm thử phần mềm, không phải câu trả lời chatbot thật."


@pytest.fixture(scope="session")
def question_bank(facts, cases):
    development = cases.loc[cases["split"] == "development"]
    return load_question_bank(QUESTION_BANK, eligible_events(facts, development))


@pytest.fixture
def filled_row(question_bank):
    question = question_bank["Q01"]
    return {
        "ma_cau_hoi": question["ma_cau_hoi"], "ma_su_kien": question["ma_su_kien"],
        "cau_hoi": question["cau_hoi"], "cong_cu": "Công cụ kiểm thử",
        "phien_ban": "Phiên bản kiểm thử", "ngay_lay": TODAY.isoformat(),
        "kieu_lenh": "ngan_gon", "nguoi_thu_thap": "Người thu thập kiểm thử",
        "cau_tra_loi": "Ngày 2/9/1945.", "ghi_chu": TEST_NOTE,
    }


def write_csv(path, rows, columns=TEMPLATE_COLUMNS, delimiter=","):
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, columns, delimiter=delimiter)
        writer.writeheader()
        writer.writerows(rows)


def run_script(script, arguments, tmp_path):
    environment = os.environ.copy()
    environment["FACTGUARD_RUNTIME_DIR"] = str(tmp_path / "isolated-runtime")
    environment["PYTHONIOENCODING"] = "utf-8"
    return subprocess.run(
        [sys.executable, str(PROJECT_ROOT / "scripts" / script), *map(str, arguments)],
        cwd=PROJECT_ROOT, env=environment, capture_output=True, text=True, encoding="utf-8", timeout=30,
        check=False,
    )


def test_real_question_bank_contains_only_events_eligible_for_collection(question_bank, facts, cases):
    development = cases.loc[cases["split"] == "development"]
    events = {question["ma_su_kien"] for question in question_bank.values()}
    assert len(question_bank) == 50
    assert events <= eligible_events(facts, development)
    assert events.isdisjoint({"departure1911", "return1941", "conference1941"})


@pytest.mark.parametrize("identifier", ["Q1", "q01", "Q00001", "unknown"])
def test_question_bank_rejects_malformed_identifiers(tmp_path, question_bank, identifier):
    row = {**question_bank["Q01"], "ma_cau_hoi": identifier}
    path = tmp_path / "test-bank.csv"
    write_csv(path, [row], BANK_COLUMNS)
    with pytest.raises(DataError, match="Mã câu hỏi không hợp lệ"):
        load_question_bank(path, {row["ma_su_kien"]})


def test_question_bank_rejects_duplicate_identifiers(tmp_path, question_bank):
    row = question_bank["Q01"]
    path = tmp_path / "test-bank.csv"
    write_csv(path, [row, row], BANK_COLUMNS)
    with pytest.raises(DataError, match="bị trùng"):
        load_question_bank(path, {row["ma_su_kien"]})


@pytest.mark.parametrize("event", ["departure1911", "return1941", "conference1941"])
def test_question_bank_rejects_development_events(tmp_path, question_bank, facts, cases, event):
    path = tmp_path / "test-bank.csv"
    write_csv(path, [{**question_bank["Q01"], "ma_su_kien": event}], BANK_COLUMNS)
    development = cases.loc[cases["split"] == "development"]
    with pytest.raises(DataError, match="thuộc development"):
        load_question_bank(path, eligible_events(facts, development))


def test_question_bank_rejects_invalid_question_type(tmp_path, question_bank):
    path = tmp_path / "test-bank.csv"
    row = {**question_bank["Q01"], "loai": "supported"}
    write_csv(path, [row], BANK_COLUMNS)
    with pytest.raises(DataError, match="loại không hợp lệ"):
        load_question_bank(path, {row["ma_su_kien"]})


def test_question_bank_rejects_missing_column(tmp_path, question_bank):
    path = tmp_path / "test-bank.csv"
    columns = [column for column in BANK_COLUMNS if column != "nguon_cau_hoi"]
    write_csv(path, [{key: value for key, value in question_bank["Q01"].items() if key in columns}], columns)
    with pytest.raises(DataError, match="thiếu cột: nguon_cau_hoi"):
        load_question_bank(path, {question_bank["Q01"]["ma_su_kien"]})


@pytest.mark.parametrize("delimiter", [",", ";"])
def test_read_table_accepts_utf8_bom_excel_delimiters_and_quoted_newlines(tmp_path, filled_row, delimiter):
    path = tmp_path / "test-answers.csv"
    row = {**filled_row, "cau_tra_loi": 'Dữ liệu kiểm thử: "một, hai; ba".\nDòng thứ hai.'}
    write_csv(path, [row], delimiter=delimiter)
    assert path.read_bytes().startswith(b"\xef\xbb\xbf")
    assert read_table(path) == [row]


@pytest.mark.parametrize("encoding", ["cp1258", "cp1252"])
def test_read_table_rejects_legacy_excel_encodings(tmp_path, encoding):
    path = tmp_path / "test-legacy.csv"
    path.write_bytes("cau_tra_loi\nDonnée de test: café\n".encode(encoding))
    with pytest.raises(DataError, match="Tệp không phải UTF-8"):
        read_table(path)


def test_parse_answers_counts_blank_rows_without_validating_unfilled_metadata(question_bank, filled_row):
    blank_row = {column: "" for column in TEMPLATE_COLUMNS}
    parsed, errors, blank = parse_answers([blank_row, filled_row], question_bank, today=TODAY)
    assert not errors and blank == 1
    assert len(parsed) == 1 and parsed[0]["row"] == 3


@pytest.mark.parametrize("value", ["2026-10-24", "24/10/2026", "24-10-2026"])
def test_parse_answers_accepts_collection_date_formats(question_bank, filled_row, value):
    parsed, errors, blank = parse_answers([{**filled_row, "ngay_lay": value}], question_bank, today=TODAY)
    assert not errors and blank == 0
    assert len(parsed) == 1 and "lấy ngày 2026-10-24" in parsed[0]["origin"]


@pytest.mark.parametrize("value", ["2026-10-25", "2022-11-29", "10/24/2026", "not-a-date", "2026-02-30"])
def test_parse_answers_rejects_out_of_range_or_malformed_dates(question_bank, filled_row, value):
    parsed, errors, blank = parse_answers([{**filled_row, "ngay_lay": value}], question_bank, today=TODAY)
    assert parsed == [] and blank == 0
    assert len(errors) == 1 and "Dòng 2 (Q01)" in errors[0] and "ngay_lay" in errors[0]


@pytest.mark.parametrize(("column", "value", "message"), [
    ("ma_cau_hoi", "Q9999", "không có trong ngân hàng"),
    ("cau_hoi", "Câu hỏi sửa để kiểm thử?", "câu hỏi khác ngân hàng"),
    ("ma_su_kien", "outside", "ma_su_kien khác ngân hàng"),
    ("cong_cu", "", "thiếu cong_cu"),
    ("phien_ban", "", "thiếu phien_ban"),
    ("nguoi_thu_thap", "", "thiếu nguoi_thu_thap"),
    ("kieu_lenh", "invalid_test_mode", "kieu_lenh chỉ nhận"),
    ("cau_tra_loi", "x" * 12001, "vượt 12.000 ký tự"),
    ("cau_tra_loi", "45000", "Excel đã đổi thành số/ngày/lỗi công thức"),
    ("cau_tra_loi", "1945-09-02", "Excel đã đổi thành số/ngày/lỗi công thức"),
    ("cau_tra_loi", "#NAME?", "Excel đã đổi thành số/ngày/lỗi công thức"),
])
def test_parse_answers_rejects_invalid_filled_rows(question_bank, filled_row, column, value, message):
    parsed, errors, blank = parse_answers([{**filled_row, column: value}], question_bank, today=TODAY)
    assert parsed == [] and blank == 0
    assert len(errors) == 1 and "Dòng 2" in errors[0] and message in errors[0]


def test_parse_answers_rejects_duplicate_question_answer_even_from_another_tool(question_bank, filled_row):
    rows = [filled_row, {**filled_row, "cong_cu": "Công cụ kiểm thử khác"}]
    parsed, errors, blank = parse_answers(rows, question_bank, today=TODAY)
    assert len(parsed) == 1 and blank == 0
    assert len(errors) == 1 and "Dòng 3" in errors[0] and "trùng nguyên văn với dòng 2" in errors[0]


def test_parse_answers_accepts_whitespace_only_question_changes(question_bank, filled_row):
    row = {**filled_row, "cau_hoi": "  \t" + filled_row["cau_hoi"].replace(" ", " \t ") + "\n"}
    parsed, errors, blank = parse_answers([row], question_bank, today=TODAY)
    assert not errors and blank == 0
    assert len(parsed) == 1 and parsed[0]["question"] == row["cau_hoi"]


def test_parse_answers_preserves_legitimate_date_answer_and_origin(question_bank, filled_row):
    parsed, errors, blank = parse_answers([filled_row], question_bank, today=TODAY)
    assert not errors and blank == 0
    case = parsed[0]
    assert case["answer"] == "Ngày 2/9/1945."
    for value in [filled_row["cong_cu"], filled_row["phien_ban"], "2026-10-24", "ngan_gon", "Q01",
                  question_bank["Q01"]["loai"], question_bank["Q01"]["nguon_cau_hoi"], TEST_NOTE]:
        assert value in case["origin"]


def test_parse_answers_allows_optional_note_and_free_prompt_mode(question_bank, filled_row):
    row = {key: value for key, value in filled_row.items() if key != "ghi_chu"}
    row["kieu_lenh"] = "tu_do"
    parsed, errors, blank = parse_answers([row], question_bank, today=TODAY)
    assert not errors and blank == 0
    assert len(parsed) == 1 and "lệnh tu_do" in parsed[0]["origin"] and "ghi chú" not in parsed[0]["origin"]


def test_parse_answers_reports_missing_required_column(question_bank, filled_row):
    row = {key: value for key, value in filled_row.items() if key != "phien_ban"}
    parsed, errors, blank = parse_answers([row], question_bank, today=TODAY)
    assert parsed == [] and blank == 0
    assert errors == ["Thiếu cột: phien_ban."]


def test_import_cases_is_idempotent_and_keeps_cases_unlabelled(tmp_path, question_bank, filled_row):
    second_question = question_bank["Q02"]
    second = {**filled_row, **{key: second_question[key] for key in ["ma_cau_hoi", "ma_su_kien", "cau_hoi"]},
              "cau_tra_loi": "Câu trả lời dùng để kiểm thử phần mềm, không phải dữ liệu nghiên cứu."}
    parsed, errors, blank = parse_answers([filled_row, second], question_bank, today=TODAY)
    assert not errors and blank == 0
    repository = ReviewRepository(tmp_path)
    first_log = import_cases(repository, parsed)
    stored = repository.collected_cases()
    assert len(stored) == 2 and [entry["status"] for entry in first_log] == ["đã nhập", "đã nhập"]
    for actual, expected in zip(stored, parsed, strict=True):
        for key in ["question", "answer", "event_id", "submitter", "origin"]:
            assert actual[key] == expected[key]
    assert repository.annotations() == [] and repository.verify_audit()
    audit_before = repository.audit_export()
    repeated_log = import_cases(repository, parsed)
    assert [entry["status"] for entry in repeated_log] == ["đã có, bỏ qua", "đã có, bỏ qua"]
    assert [entry["case_id"] for entry in repeated_log] == [entry["case_id"] for entry in first_log]
    assert repository.collected_cases() == stored and repository.audit_export() == audit_before
    assert repository.annotations() == [] and repository.verify_audit()


def test_write_template_creates_expected_columns_and_tool_rows(tmp_path, question_bank):
    tools = ["Công cụ kiểm thử A", "Công cụ kiểm thử B", "Công cụ kiểm thử C"]
    path = tmp_path / "nested" / "test-template.csv"
    write_template(path, template_rows(question_bank, tools))
    rows = read_table(path)
    assert list(rows[0]) == TEMPLATE_COLUMNS and len(rows) == 50 * len(tools)
    assert all(not row["cau_tra_loi"] for row in rows)
    assert {(row["ma_cau_hoi"], row["cong_cu"]) for row in rows} == {
        (identifier, tool) for identifier in question_bank for tool in tools
    }


def test_write_template_refuses_to_overwrite_any_answer(tmp_path, question_bank, filled_row):
    path = tmp_path / "test-filled.csv"
    rows = template_rows(question_bank, ["Công cụ kiểm thử"])
    rows[-1] = filled_row
    write_csv(path, rows)
    before = path.read_bytes()
    with pytest.raises(DataError, match="đã có câu trả lời được điền; không ghi đè"):
        write_template(path, template_rows(question_bank, ["Công cụ kiểm thử khác"]))
    assert path.read_bytes() == before


def test_write_template_can_replace_a_blank_template(tmp_path, question_bank):
    path = tmp_path / "test-blank.csv"
    write_template(path, template_rows(question_bank, ["Công cụ kiểm thử A"]))
    replacement = template_rows(question_bank, ["Công cụ kiểm thử B", "Công cụ kiểm thử C"])
    write_template(path, replacement)
    assert read_table(path) == replacement


def test_build_collection_script_creates_template_and_protects_filled_sheet(tmp_path, filled_row):
    path = tmp_path / "test-template.csv"
    arguments = ["--tools", "TestToolA", "TestToolB", "TestToolC", "--output", path]
    result = run_script("build_collection_kit.py", arguments, tmp_path)
    assert result.returncode == 0, result.stdout + result.stderr
    assert len(read_table(path)) == 150
    write_csv(path, [filled_row])
    before = path.read_bytes()
    result = run_script("build_collection_kit.py", arguments, tmp_path)
    assert result.returncode != 0 and "không ghi đè" in result.stderr
    assert path.read_bytes() == before
    assert not (tmp_path / "isolated-runtime" / "research.sqlite3").exists()


def test_import_script_dry_run_validates_without_creating_database(tmp_path, filled_row):
    path = tmp_path / "test-valid.csv"
    write_csv(path, [filled_row])
    result = run_script("import_collected.py", [path, "--dry-run"], tmp_path)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "1 dòng hợp lệ, 0 dòng lỗi" in result.stdout
    assert not (tmp_path / "isolated-runtime" / "research.sqlite3").exists()
    assert not (tmp_path / "isolated-runtime" / "collection_imports").exists()


def test_import_script_rejects_entire_sheet_with_one_invalid_row(tmp_path, filled_row, question_bank):
    path = tmp_path / "test-invalid.csv"
    question = question_bank["Q02"]
    invalid = {**filled_row, **{key: question[key] for key in ["ma_cau_hoi", "ma_su_kien", "cau_hoi"]},
               "phien_ban": ""}
    write_csv(path, [filled_row, invalid])
    result = run_script("import_collected.py", [path], tmp_path)
    assert result.returncode != 0
    assert "1 dòng hợp lệ, 1 dòng lỗi" in result.stdout and "Dòng 3" in result.stdout
    assert "Chưa nhập gì" in result.stderr
    assert not (tmp_path / "isolated-runtime" / "research.sqlite3").exists()
    assert not (tmp_path / "isolated-runtime" / "collection_imports").exists()
