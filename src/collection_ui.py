"""Preview and explicitly import answer sheets into the unlabelled review queue."""
import csv
import sqlite3
from pathlib import Path
from uuid import uuid4

import pandas as pd
import streamlit as st

from src.collection import (
    QUESTION_BANK,
    TEMPLATE,
    eligible_events,
    import_cases,
    load_question_bank,
    parse_answers,
    read_table,
)
from src.loader import DataError
from src.review import ReviewRepository
from src.utils import digest_bytes, utc_now

MAX_UPLOAD_BYTES = 5 * 1024 * 1024
LOG_COLUMNS = ["row", "qid", "case_id", "status"]


def _new_path(directory: Path, prefix: str) -> Path:
    timestamp = utc_now().replace(":", "").replace("+", "_")
    return directory / f"{prefix}_{timestamp}_{uuid4().hex}.csv"


def _save_snapshot(payload: bytes, runtime: Path) -> Path:
    signature = f"{runtime.resolve()}:{digest_bytes(payload)}"
    snapshot = st.session_state.get("collection_csv_snapshot")
    if snapshot and snapshot["signature"] == signature:
        previous = Path(snapshot["path"])
        if previous.is_file():
            return previous
    directory = runtime / "collection_imports"
    directory.mkdir(parents=True, exist_ok=True)
    path = _new_path(directory, "upload")
    path.write_bytes(payload)
    st.session_state["collection_csv_snapshot"] = {"signature": signature, "path": str(path)}
    return path


def collection_upload(repository: ReviewRepository, facts, development, runtime: Path) -> None:
    with st.expander("Nhập nhiều câu trả lời từ tệp CSV"):
        st.caption("Tải mẫu, điền nguyên văn câu trả lời rồi tải CSV UTF-8 lên. Tệp gốc được lưu cục bộ; chỉ bấm Nhập mới thêm ca chưa gán nhãn.")
        try:
            st.download_button("Tải mẫu ghi câu trả lời CSV", TEMPLATE.read_bytes(), TEMPLATE.name,
                               "text/csv", key="collection_csv_template")
        except OSError:
            st.error("Không đọc được tệp mẫu CSV. Kiểm tra data/collection/mau_ghi_cau_tra_loi.csv.")
            return
        uploaded = st.file_uploader("Chọn tệp CSV đã điền (tối đa 5 MB)", type=["csv"], key="collection_csv")
        if uploaded is None:
            st.session_state.pop("collection_csv_snapshot", None)
            return
        payload = uploaded.getvalue()
        if len(payload) > MAX_UPLOAD_BYTES:
            st.error("Tệp CSV vượt giới hạn 5 MB. Hãy chia thành các tệp nhỏ hơn rồi tải lại.")
            return
        try:
            bank = load_question_bank(QUESTION_BANK, eligible_events(facts, development))
            path = _save_snapshot(payload, runtime)
            cases, errors, blank = parse_answers(read_table(path), bank)
        except DataError as error:
            st.error(str(error))
            return
        except (OSError, csv.Error):
            st.error("Không đọc hoặc lưu được CSV. Kiểm tra cấu trúc tệp và quyền ghi thư mục dữ liệu.")
            return
        st.write(f"{len(cases)} dòng hợp lệ, {len(errors)} dòng lỗi, {blank} dòng chưa điền câu trả lời.")
        if errors:
            st.error("\n\n".join(errors))
            st.caption("Chưa nhập dòng nào từ tệp này. Sửa tất cả dòng lỗi rồi tải lại.")
            return
        if cases:
            preview = pd.DataFrame([{"Dòng CSV": row["row"], "Mã câu hỏi": row["qid"],
                                     "Câu hỏi": row["question"], "Câu trả lời": row["answer"]} for row in cases])
            st.dataframe(preview, hide_index=True, width="stretch")
        else:
            st.caption("Tệp chưa có câu trả lời để nhập.")
        if not st.button("Nhập vào hàng đợi gán nhãn", disabled=not cases, key="collection_csv_import"):
            return
        try:
            log = import_cases(repository, cases)
        except (DataError, sqlite3.Error) as error:
            st.error(f"Nhập chưa hoàn tất: {error}. Kiểm tra hàng đợi trước khi chạy lại; ca đã có sẽ được bỏ qua.")
            return
        added = sum(entry["status"] == "đã nhập" for entry in log)
        try:
            destination = _new_path(runtime / "collection_imports", "import")
            with destination.open("w", encoding="utf-8-sig", newline="") as handle:
                writer = csv.DictWriter(handle, LOG_COLUMNS)
                writer.writeheader()
                writer.writerows(log)
        except OSError:
            st.error("Đã xử lý các ca trong hàng đợi nhưng chưa lưu được nhật ký CSV. Kiểm tra quyền ghi và sao lưu hàng đợi trước khi chạy lại.")
            return
        st.success(f"Đã nhập {added} ca mới, bỏ qua {len(log) - added} ca đã có. Các ca mới chưa có nhãn.")
        st.caption(f"Nhật ký lần nhập: {destination.name}, trong thư mục collection_imports của dữ liệu cục bộ.")
