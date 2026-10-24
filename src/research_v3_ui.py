"""Interactive v3 demonstration and collected-study reporting; never tunes the engine."""
import json

import pandas as pd
import streamlit as st

from src.annotation_study import consensus_cases
from src.claim_verifier import ClaimVerifier
from src.collected_workspace_v3 import (
    METHOD_NAMES,
    load_latest_study_v3,
    run_collected_study_v3,
    save_collected_study_v3,
    study_input_digest,
)
from src.hybrid_verifier import HybridVerifier
from src.loader import DataError, source_documents
from src.models import LABELS_VI
from src.nli import shared_model
from src.retriever import Retriever
from src.utils import PROJECT_ROOT
from src.v3_freeze import validate_v3_freeze

DECISIONS = {"entailment": "Đạt ngưỡng hỗ trợ và qua chốt giá trị", "contradiction": "Đạt ngưỡng mâu thuẫn",
             "blocked_by_value_guard": "Bị chặn vì giá trị không có trong bằng chứng",
             "unresolved": "Chưa đạt ngưỡng kết luận", "no_premise": "Chưa chọn được bằng chứng cùng sự kiện"}


def v3_comparison(facts, sources) -> None:
    st.subheader("Cùng đầu vào: luật v2 và luật kết hợp NLI v3")
    st.caption("Minh họa trên kho gốc. Ca thử tại đây không tự vào dữ liệu nghiên cứu. Người gán nhãn cần hoàn tất phiếu trước khi xem dự đoán.")
    with st.form("v3_comparison_form"):
        question = st.text_area("Câu hỏi so sánh v3", value="Kiểm chứng câu trả lời.", max_chars=12000)
        answer = st.text_area("Câu trả lời so sánh v3", max_chars=12000)
        compare = st.form_submit_button("So sánh v2 và v3", type="primary")
    if compare:
        if not question.strip() or not answer.strip():
            st.error("Điền cả câu hỏi và câu trả lời để so sánh.")
        else:
            try:
                with st.spinner("Kiểm tra bản đóng băng và chạy mô hình trên CPU…"):
                    if not validate_v3_freeze():
                        raise DataError("V3 chưa khớp bản đóng băng. Kiểm tra mã và bốn tệp mô hình cục bộ.")
                    retriever = Retriever(source_documents(PROJECT_ROOT / "data", sources, facts))
                    v2 = ClaimVerifier(facts, retriever).verify(question, answer)
                    v3 = HybridVerifier(facts, retriever, shared_model()).verify(question, answer)
                st.session_state["v3_comparison_result"] = {"question": question, "answer": answer, "v2": v2, "v3": v3}
            except (ValueError, OSError, ImportError, RuntimeError) as error:
                st.error(f"Chưa so sánh được: {error}")
    previous = st.session_state.get("v3_comparison_result")
    if not previous:
        st.info("Mô hình chỉ được nạp khi bấm so sánh; mở trang không tải trọng số hay gọi mạng.")
        return
    if previous["question"] != question or previous["answer"] != answer:
        st.info("Đầu vào đã đổi. Kết quả dưới đây thuộc lần so sánh trước; bấm so sánh để cập nhật.")
    st.text(previous["question"])
    st.text(previous["answer"])
    for column, name in zip(st.columns(2), ["v2", "v3"], strict=True):
        result = previous[name]
        with column:
            st.markdown(f"**{'Luật v2' if name == 'v2' else 'Luật và NLI v3'}**")
            status = {"supported": st.success, "contradicted": st.error, "insufficient": st.warning, "undetermined": st.info}[result.label]
            status(LABELS_VI[result.label])
            st.write(result.explanation)
            st.caption(f"Thời gian kiểm chứng: {result.elapsed_ms:.2f} ms; chưa tính thời gian nạp mô hình.")
    trace = previous["v3"].metadata.get("nli_trace", [])
    if trace:
        st.markdown("**NLI đã xử lý những đoạn nào?**")
        st.dataframe(pd.DataFrame([{"Đoạn": row["text"], "Quyết định": DECISIONS[row["decision"]],
                                    "Entailment": row.get("entailment"), "Contradiction": row.get("contradiction"),
                                    "Qua chốt giá trị": row.get("guard"), "ID bằng chứng": ", ".join(row.get("fact_ids", []))}
                                   for row in trace]), hide_index=True, width="stretch")
        st.caption("Điểm NLI chưa được hiệu chuẩn thành xác suất câu trả lời đúng. Chốt giá trị áp dụng cho nhánh hỗ trợ.")
    else:
        st.info("NLI không tham gia: luật v2 đã kết luận hoặc có điều kiện chủ động dừng. Xem các phần chưa xác minh bên dưới.")
    for issue in previous["v3"].metadata.get("issues", []):
        st.text(issue["text"])
        st.caption(issue["explanation"])
    identifiers = {check.fact_id for check in previous["v3"].checks}
    identifiers |= {identifier for row in trace for identifier in row.get("fact_ids", [])}
    with st.expander("Đọc bằng chứng dùng trong đối chiếu"):
        for fact in facts:
            if fact.id in identifiers:
                st.markdown(f"**{fact.id} · {fact.location}**")
                st.text(fact.reference)
                if sources[fact.source_id].get("url"):
                    st.link_button(f"Mở nguồn {fact.id}", sources[fact.source_id]["url"])
    export = {"question": previous["question"], "answer": previous["answer"],
              "v2": previous["v2"].to_dict(), "v3": previous["v3"].to_dict(), "purpose": "Interactive demonstration; not study data"}
    st.download_button("Tải đối chiếu v2-v3 JSON", json.dumps(export, ensure_ascii=False, indent=2), "doi-chieu-v2-v3.json", "application/json")


def v3_collected_study(facts, sources, development, runtime, repository) -> None:
    st.subheader("Đánh giá năm phương pháp trên ca thu thập")
    collected, annotations = repository.collected_cases(), repository.annotations()
    accepted, pending = consensus_cases(collected, annotations)
    st.write(f"Đã nhập {len(collected)} ca; {len(accepted)} ca có nhãn đồng thuận; {len(pending)} ca còn chờ hoặc bất đồng.")
    st.caption("Nguồn dữ liệu: hàng đợi nhập CSV/nhập tay và phiếu đã lưu. Hai tên tự khai không chứng minh tính độc lập. Ca minh họa và bộ tổng hợp không tự được đưa vào phép đo.")
    if not accepted:
        st.info("Chưa có dữ liệu đủ điều kiện. Nhập câu trả lời thật trong Gán nhãn độc lập và hoàn tất ít nhất hai phiếu đồng thuận trên cùng nội dung.")
    if st.button("Đánh giá v3 và xuất báo cáo", disabled=not accepted, key="evaluate_collected_v3"):
        try:
            with st.spinner("Kiểm tra phiên bản, đo năm phương pháp và lưu một lần chạy riêng…"):
                if not validate_v3_freeze():
                    raise DataError("V3 chưa khớp bản đóng băng; chưa thể chạy đánh giá chính.")
                documents = source_documents(PROJECT_ROOT / "data", sources, facts)
                frame, summary = run_collected_study_v3(facts, documents, development, collected, annotations, shared_model())
                save_collected_study_v3(frame, summary, runtime)
            st.success("Đã lưu kết quả thật của lần chạy; các lần trước được giữ riêng.")
        except (ValueError, OSError, ImportError, RuntimeError) as error:
            st.error(f"Chưa hoàn tất đánh giá: {error}")
    try:
        latest = load_latest_study_v3(runtime)
    except DataError as error:
        st.error(str(error))
        return
    if latest is None:
        return
    directory, frame, summary = latest
    st.caption(f"Lần đo lưu: {summary['created_at']} UTC · {summary['cases']} ca · {summary['unique_question_count']} câu hỏi · {summary['event_code_count']} mã sự kiện.")
    if summary["input_sha256"] != study_input_digest(collected, annotations):
        st.warning("Dữ liệu hoặc phiếu gán nhãn đã thay đổi. Bảng này thuộc lần đo cũ; cần chạy lại để cập nhật.")
    st.dataframe(pd.DataFrame([{"Phương pháp": METHOD_NAMES[name], "Accuracy": m["accuracy"], "Macro F1": m["f1_macro"],
                               "Số hỗ trợ sai": m["false_support_count"], "Ca gold không hỗ trợ": m["non_supported_gold_count"],
                               "Có kết luận đúng-sai": m["decisive_coverage"], "Rủi ro trên kết luận": m["decisive_risk"]}
                              for name, m in summary["metrics"].items()]), hide_index=True, width="stretch")
    st.caption("Tỷ lệ và thời gian được đo trên ca có đồng thuận; cần đọc cả ca chờ/bất đồng để tránh diễn giải quá mức. Không suy ra hiệu quả học tập.")
    with st.expander("Ca sai hoặc từ chối so với nhãn chuẩn"):
        st.dataframe(frame.loc[~frame["correct"].astype(bool), ["id", "event_id", "method", "gold", "prediction"]], hide_index=True, width="stretch")
    for label, name, mime in [("Tải báo cáo v3 Markdown", "report.md", "text/markdown"),
                              ("Tải kết quả v3 CSV", "results.csv", "text/csv"),
                              ("Tải thông số lần đo v3 JSON", "summary.json", "application/json")]:
        st.download_button(label, (directory / name).read_bytes(), name, mime)
    st.caption("CSV chi tiết có nội dung, xuất xứ và mã người gán nhãn. Kiểm tra thông tin cá nhân trước khi chia sẻ.")
