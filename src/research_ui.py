"""Research workspace: measured experiments, independent review and source workflow."""
import json
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

from src.evaluator import csv_bytes
from src.loader import DataError
from src.models import GOLD_LABELS, LABELS_VI
from src.research_evaluator import (
    METHODS,
    load_challenge,
    report_markdown,
    run_research,
    save_research,
    validate_freeze,
)
from src.research_statistics import rating_agreement
from src.review import ReviewRepository, content_hash
from src.utils import PROJECT_ROOT, digest_bytes

METHOD_LABELS = {"lexical_3way": "Đối chứng từ vựng 3 nhãn", "rules_single_v1": "Luật một dữ kiện v1",
                 "claims_no_guard": "Mệnh đề bỏ chốt phạm vi", "claims_guarded": "Mệnh đề đầy đủ chốt"}


def research_results(frame: pd.DataFrame, summary: dict) -> None:
    rows = [{"Phương pháp": METHOD_LABELS[method], "Accuracy": metrics["accuracy"], "F1 macro": metrics["f1_macro"],
             "Số hỗ trợ sai": metrics["false_support_count"], "Tỷ lệ hỗ trợ sai": metrics["false_support_rate"],
             "Có kết luận đúng/sai": metrics["decisive_coverage"], "Rủi ro trên ca có kết luận": metrics["decisive_risk"],
             "Đúng nhãn + đủ bằng chứng": metrics["evidence_complete_accuracy"]}
            for method, metrics in summary["metrics"].items()]
    st.dataframe(pd.DataFrame(rows), hide_index=True, width="stretch")
    st.caption("Tỷ lệ hỗ trợ sai lấy mẫu số là ca nhãn chuẩn không phải supported. Kết luận đúng/sai chỉ gồm supported và contradicted. Undetermined vẫn tính sai trong Accuracy.")
    chart = pd.DataFrame([{"Phương pháp": METHOD_LABELS[method], "Chỉ số": name, "Giá trị": metrics[key]}
                          for method, metrics in summary["metrics"].items()
                          for key, name in [("accuracy", "Accuracy"), ("f1_macro", "F1 macro"),
                                            ("evidence_complete_accuracy", "Đúng nhãn và đủ bằng chứng")]])
    figure = px.bar(chart, x="Chỉ số", y="Giá trị", color="Phương pháp", barmode="group", range_y=[0, 1],
                    color_discrete_sequence=["#9BAFC9", "#65768C", "#82ADA4", "#2158B0"])
    figure.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="white", legend_title_text="")
    st.plotly_chart(figure, width="stretch")
    st.subheader("Mức bao phủ và rủi ro")
    risk_rows = [{"Phương pháp": METHOD_LABELS[m], "Mức bao phủ": v["decisive_coverage"], "Rủi ro": v["decisive_risk"]}
                 for m, v in summary["metrics"].items() if v["decisive_risk"] is not None]
    figure = px.scatter(pd.DataFrame(risk_rows), x="Mức bao phủ", y="Rủi ro", color="Phương pháp", range_x=[0, 1.05], range_y=[-.03, 1], size_max=18)
    figure.update_traces(marker_size=14)
    st.plotly_chart(figure, width="stretch")
    st.caption("Mỗi điểm là một cấu hình thực sự đã chạy, không phải đường cong xác suất được hiệu chỉnh. Không có lỗi quan sát được trên bộ nhỏ không có nghĩa rủi ro thực tế bằng 0.")
    interval = summary["paired_event_interval"]
    with st.expander("Khoảng biến thiên theo cụm sự kiện và quy tắc tính"):
        st.json(interval)
        st.write("Bootstrap cặp theo sự kiện, mỗi sự kiện có cùng trọng số. Khoảng 95% này chỉ mô tả sự biến thiên trên bộ tổng hợp được chọn; không suy rộng hiệu quả học tập.")
    st.subheader("Các bước xử lý có hoạt động không?")
    st.dataframe(pd.DataFrame([{"Phương pháp": METHOD_LABELS[m], "Recall trích dữ kiện": v["claim_detection_recall"],
                               "Recall đúng nhãn mệnh đề": v["claim_label_recall"], "Precision trích dữ kiện": v["claim_precision"],
                               "TB (ms)": v["mean_ms"], "Median (ms)": v["median_ms"], "P95 (ms)": v["p95_ms"]}
                              for m, v in summary["metrics"].items()]), hide_index=True, width="stretch")
    st.caption("Đối chứng không trích mệnh đề được ghi khả năng đó bằng 0/không xác định; không dùng điểm trích để thay thế Accuracy phân loại.")
    method = st.selectbox("Xem chi tiết phương pháp", METHODS, format_func=lambda m: METHOD_LABELS[m])
    selected = frame.loc[frame["method"] == method]
    st.dataframe(selected.groupby("group")["correct"].agg(["count", "mean"]).reset_index().rename(columns={"group": "Nhóm", "count": "Số ca", "mean": "Accuracy"}), hide_index=True, width="stretch")
    with st.expander("Chỉ số theo nhãn và ma trận nhầm lẫn"):
        metric = summary["metrics"][method]
        st.json({"per_label": metric["per_label"], "labels": metric["labels"], "confusion_matrix": metric["confusion_matrix"]})
    failed = selected.loc[~selected["correct"].astype(bool)]
    st.markdown(f"**{len(failed)} ca sai hoặc từ chối so với nhãn chuẩn**")
    st.dataframe(failed[["id", "question", "answer", "gold", "prediction", "explanation"]], hide_index=True, width="stretch")
    with st.expander("Toàn bộ dự đoán, mệnh đề và phần chưa xử lý"):
        st.dataframe(selected, hide_index=True, width="stretch")
    left, middle, right = st.columns(3)
    left.download_button("Xuất CSV nghiên cứu", csv_bytes(frame), "factguard-nghien-cuu-v2.csv", "text/csv")
    middle.download_button("Xuất báo cáo nghiên cứu", report_markdown(frame, summary), "bao-cao-nghien-cuu-v2.md", "text/markdown")
    right.download_button("Xuất thông số và dấu vân tay", json.dumps(summary, ensure_ascii=False, indent=2), "research-manifest.json", "application/json")


def independent_review(repository: ReviewRepository, facts, sources, development, runtime) -> None:
    st.subheader("Thẩm định nhãn bằng dữ liệu thật")
    st.info("Màn hình này ẩn nhãn tạo sẵn và dự đoán của hệ thống. Người gán nhãn cần đọc nguồn, tự chọn nhãn và ghi ID bằng chứng. Danh tính ở đây do người dùng tự khai, chưa xác thực.")
    with st.expander("Thu thập câu trả lời mới từ người dùng"):
        with st.form("collect_case_form"):
            new_question = st.text_area("Câu hỏi được thu thập", max_chars=12000)
            new_answer = st.text_area("Câu trả lời nguyên bản được thu thập", max_chars=12000)
            origin = st.text_input("Nguồn gốc câu trả lời: công cụ/phiên bản/ngày lấy, hoặc tự xây dựng")
            submitter = st.text_input("Mã người thu thập")
            dev_events = set(development["event_id"])
            event = st.selectbox("Sự kiện của ca mới", sorted({f.event_id for f in facts} - dev_events) + ["outside"])
            add = st.form_submit_button("Lưu ca mới chưa gán nhãn")
        if add:
            try:
                identifier = repository.add_case(question=new_question, answer=new_answer, origin=origin,
                                                 submitter=submitter, event_id=event or "")
                st.success(f"Đã lưu {identifier}; chưa có nhãn hay dự đoán được tự điền.")
            except DataError as error:
                st.error(str(error))
    path = PROJECT_ROOT / "data" / "research" / "blind_review.csv"
    queue = pd.read_csv(path, keep_default_na=False).to_dict("records")
    collected = repository.collected_cases()
    queue += [{**{k: row[k] for k in ["id", "question", "answer"]}, "exclude_event": ""} for row in collected]
    annotations = repository.annotations()
    st.metric("Nhãn người dùng đã lưu", len(annotations))
    if not annotations:
        st.caption("Chưa có nhãn người thật được lưu. Chưa tính độ đồng thuận và chưa gọi đây là bộ kiểm thử độc lập.")
    row = st.selectbox("Chọn ca cần tự gán nhãn", queue, format_func=lambda r: r["id"])
    if row.get("exclude_event"):
        st.warning(f"Điều kiện kho của ca này: không chứa dữ kiện thuộc sự kiện {row['exclude_event']}. Hãy gán nhãn theo kho khả dụng, không bổ sung tri thức bên ngoài vào điều kiện đo.")
    else:
        st.caption("Điều kiện: kho tham chiếu gốc đi kèm dự án, không dùng tài liệu người dùng tải thêm.")
    visible_facts = [fact for fact in facts if fact.event_id != row.get("exclude_event", "")]
    with st.expander("Dữ kiện khả dụng để người gán nhãn tự đọc"):
        st.dataframe(pd.DataFrame([{"ID": f.id, "Câu hỏi chuẩn": f.question, "Bằng chứng": f.reference,
                                     "Nguồn": f.source_id, "Vị trí": f.location} for f in visible_facts]), hide_index=True, width="stretch")
    st.markdown("**Câu hỏi**")
    st.text(row["question"])
    st.markdown("**Câu trả lời**")
    st.text(row["answer"])
    with st.form("annotation_form_" + row["id"]):
        reviewer = st.text_input("Tên hoặc mã người gán nhãn")
        label = st.selectbox("Nhãn do bạn xác định", GOLD_LABELS, index=None, format_func=lambda label: LABELS_VI[label])
        evidence_ids = st.multiselect("ID dữ kiện đã đọc để làm bằng chứng", [f.id for f in visible_facts])
        note = st.text_area("Giải thích và vị trí nguồn bạn đã kiểm tra")
        confirmed = st.checkbox("Tôi đã tự đọc nguồn và gán nhãn; đây không phải nhãn tự động sao chép.")
        save = st.form_submit_button("Lưu nhãn của tôi", type="primary")
    if save:
        try:
            repository.annotate(case_id=row["id"], question=row["question"], answer=row["answer"], reviewer=reviewer,
                                label=label or "", evidence_ids=evidence_ids, note=note, confirmed=confirmed)
            st.success("Đã lưu nhãn, thời điểm và nhật ký thay đổi. Thống kê được cập nhật ở lần xem tiếp theo.")
        except DataError as error:
            st.error(str(error))
    current_hashes = {r["id"]: content_hash(r["question"], r["answer"]) for r in queue}
    eligible = [r for r in annotations if current_hashes.get(r["case_id"]) == r["content_hash"]]
    agreement = rating_agreement(eligible)
    if agreement:
        st.dataframe(pd.DataFrame(agreement), hide_index=True, width="stretch")
        st.caption("Chỉ tính trên các ca cùng nội dung được ít nhất hai tên người khác nhau gán nhãn. Một nhãn duy nhất ở cả hai người có thể làm kappa không xác định.")
    else:
        st.caption("Chưa có đủ hai người gán nhãn trên cùng ca để tính độ đồng thuận.")
    if annotations:
        st.download_button("Xuất nhãn đã gán thực tế", csv_bytes(pd.DataFrame(annotations)), "nhan-nguoi-dung.csv", "text/csv")
    st.download_button("Tải phiếu gán nhãn ẩn kết quả", csv_bytes(pd.DataFrame(queue)), "phieu-gan-nhan.csv", "text/csv")
    st.divider()
    st.subheader("Đánh giá trên các ca người dùng thực sự đã nhập")
    from src.annotation_study import consensus_cases, evaluate_collected

    accepted, pending = consensus_cases(collected, repository.annotations())
    st.write(f"Đã nhập {len(collected)} ca; {len(accepted)} ca có ít nhất hai tên gán nhãn đồng thuận; {len(pending)} ca còn chờ hoặc bất đồng.")
    st.caption("Các tên tự khai không chứng minh người duyệt độc lập. Kết quả này tách khỏi bộ tổng hợp 46 ca; không trộn số liệu để tăng quy mô mẫu.")
    if st.button("Đánh giá các ca đã có hai nhãn đồng thuận", disabled=not accepted):
        try:
            from src.loader import source_documents

            documents = source_documents(PROJECT_ROOT / "data", sources, facts)
            frame, summary = evaluate_collected(facts, documents, development, accepted)
            output = runtime / "collected_study"
            output.mkdir(parents=True, exist_ok=True)
            (output / "results.csv").write_bytes(csv_bytes(frame))
            (output / "latest.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
            st.success("Đã đo trên các ca người dùng nhập, với nhãn đồng thuận được lưu thật.")
        except ValueError as error:
            st.error(str(error))
    output = runtime / "collected_study"
    if (output / "latest.json").exists():
        summary = json.loads((output / "latest.json").read_text(encoding="utf-8"))
        st.caption(f"Lần đo lưu: {summary['created_at']} (UTC), {summary['cases']} ca. Thêm/sửa nhãn cần chạy lại.")
        st.dataframe(pd.DataFrame([{"Phương pháp": METHOD_LABELS[m], "Accuracy": metric["accuracy"],
                                   "F1 macro": metric["f1_macro"], "Số hỗ trợ sai": metric["false_support_count"]}
                                  for m, metric in summary["metrics"].items()]), hide_index=True, width="stretch")
        st.download_button("Xuất kết quả ca người dùng", (output / "results.csv").read_bytes(), "ket-qua-ca-nguoi-dung.csv", "text/csv")


def review_sources(repository: ReviewRepository, store, facts) -> None:
    st.info("Tạo bản nháp từ đoạn văn có trong tài liệu, rồi người thật đọc nguồn và duyệt. Chỉ dữ kiện đã duyệt mới tham gia kiểm chứng tương tác; thực nghiệm chuẩn không dùng dữ kiện tải thêm.")
    documents = store.uploaded_documents()
    if not documents:
        st.caption("Hãy tải một tài liệu trong tab Bổ sung tài liệu để bắt đầu lập dữ kiện có nguồn.")
    else:
        document = st.selectbox("Chọn đoạn nguồn để lập dữ kiện", documents, format_func=lambda d: f"{d.title} / {d.location}")
        st.text(document.text)
        with st.form("fact_draft_form"):
            question = st.text_input("Câu hỏi chuẩn của dữ kiện mới")
            answer = st.text_input("Đáp án hiển thị")
            kind = st.selectbox("Loại dữ kiện", ["date", "person", "place"], format_func=lambda k: {"date": "Ngày tháng năm", "person": "Nhân vật", "place": "Địa điểm"}[k])
            canonical = st.text_input("Giá trị chuẩn: YYYY-MM-DD cho ngày; tên đầy đủ cho nhân vật/địa điểm")
            event_id = st.text_input("Mã sự kiện", placeholder="Ví dụ: bien_gioi_1950")
            anchors = st.text_area("Neo nhận diện: mỗi dòng một nhóm; dùng | giữa các cách viết tương đương", placeholder="chiến dịch Biên giới\nkết thúc|toàn thắng")
            excerpt = st.text_area("Đoạn bằng chứng nguyên văn", value=document.text)
            url = st.text_input("URL nguồn gốc nếu có", value=document.url)
            author = st.text_input("Người lập dữ kiện")
            submit = st.form_submit_button("Lưu bản nháp dữ kiện", type="primary")
        if submit:
            try:
                identifier = repository.create_draft(question=question, answer=answer, kind=kind, canonical=canonical,
                                                      anchors=[[s.strip() for s in line.split("|")] for line in anchors.splitlines() if line.strip()],
                                                      document=document, excerpt=excerpt or "", author=author, event_id=event_id, url=url or "")
                st.success(f"Đã lưu bản nháp {identifier}. Cần duyệt ở phần bên dưới.")
            except DataError as error:
                st.error(str(error))
    rows = repository.records()
    if rows:
        st.subheader("Duyệt hoặc thu hồi dữ kiện")
        record = st.selectbox("Chọn bản ghi", rows, format_func=lambda r: f"{r['id']} / {r['state']} / {r['question']}")
        st.json({k: record[k] for k in ["question", "answer", "canonical", "reference", "location", "document_title", "document_sha256", "state", "revision"]})
        if record["state"] in {"draft", "approved"}:
            with st.form(f"source_review_form_{record['id']}_{record['revision']}"):
                action = st.selectbox("Quyết định", ["approved", "rejected"] if record["state"] == "draft" else ["withdrawn"],
                                      format_func=lambda a: {"approved": "Duyệt để dùng đối chiếu", "rejected": "Từ chối bản nháp", "withdrawn": "Thu hồi khỏi kho đối chiếu"}[a])
                reviewer = st.text_input("Người trực tiếp duyệt nguồn")
                reason = st.text_area("Căn cứ quyết định")
                confirmed = st.checkbox("Tôi đã đọc nguồn gốc, kiểm tra giá trị và chịu trách nhiệm về quyết định thẩm định này.")
                submit_review = st.form_submit_button("Ghi quyết định thẩm định", type="primary")
            if submit_review:
                try:
                    repository.transition(record["id"], state=action, reviewer=reviewer, reason=reason,
                                          confirmed=confirmed, existing_facts=facts)
                    st.success("Đã ghi quyết định. Nạp lại trang hoặc sang Kiểm chứng để dùng trạng thái mới.")
                except DataError as error:
                    st.error(str(error))
    st.caption("Chuỗi hash cục bộ giúp phát hiện thay đổi ngoài luồng trong nhật ký/bản ghi; không phải chữ ký số, xác thực danh tính hoặc bằng chứng chống sửa toàn bộ cơ sở dữ liệu.")
    if repository.audit_export():
        st.download_button("Xuất nhật ký thẩm định", json.dumps(repository.audit_export(), ensure_ascii=False, indent=2), "nhat-ky-tham-dinh.json", "application/json")


def research_page(facts, sources, development, runtime: Path, repository: ReviewRepository) -> None:
    st.caption("FactGuard EDU / Nghiên cứu kiểm chứng mệnh đề")
    st.title("Phòng nghiên cứu")
    st.write("Đo khả năng kiểm chứng nhiều dữ kiện, phân tích lỗi và thu thập thẩm định có nguồn gốc rõ ràng.")
    tabs = st.tabs(["Thực nghiệm v2", "Gán nhãn độc lập", "Thiết kế và đóng băng"])
    with tabs[0]:
        challenge = PROJECT_ROOT / "data" / "research" / "challenge.jsonl"
        cases = load_challenge(challenge, facts)
        st.write(f"**{len(cases)} ca thử thách / {len({r['event_id'] for r in cases})} cụm sự kiện / 4 phương pháp**")
        st.warning("Bộ thử thách do trợ lý tạo sau khi đóng băng mã, chưa phải đánh giá độc lập. V1 evaluation đã được xem và chỉ dùng hồi quy. Không chỉnh quy tắc hoặc nhãn theo điểm thử thách này.")
        directory = runtime / "research_v2"
        if st.button("Chạy nghiên cứu bốn phương pháp", type="primary"):
            with st.spinner("Đang chạy cùng dữ liệu, đối chứng, ablation và bootstrap theo sự kiện…"):
                frame, summary = run_research(facts, sources, development, cases)
                summary["challenge_sha256"] = digest_bytes(challenge.read_bytes())
                save_research(frame, summary, directory)
            st.success("Đã đo và lưu kết quả nghiên cứu thực tế.")
        if not (directory / "latest.json").exists():
            directory = PROJECT_ROOT / "reports" / "research_v2"
        if (directory / "latest.json").exists():
            summary = json.loads((directory / "latest.json").read_text(encoding="utf-8"))
            frame = pd.read_csv(directory / "results.csv", keep_default_na=False)
            frame["retrieval_recall_at_4"] = pd.to_numeric(frame["retrieval_recall_at_4"], errors="coerce")
            st.caption(f"Lần đo: {summary['created_at']} (UTC). Phiên bản {summary['version']}.")
            if not validate_freeze() or summary.get("challenge_sha256") != digest_bytes(challenge.read_bytes()):
                st.warning("Mã hoặc dữ liệu khác lần đóng băng/đo; kết quả cũ cần được xem đúng phiên bản. Không ghi đè bộ đã chấm để tăng điểm.")
            research_results(frame, summary)
    with tabs[1]:
        independent_review(repository, facts, sources, development, runtime)
    with tabs[2]:
        st.json(json.loads((PROJECT_ROOT / "reports" / "research_protocol_v2.json").read_text(encoding="utf-8")))
        st.caption(f"Mã hiện tại khớp bản đóng băng: {validate_freeze()}. Tài liệu thiết kế và giới hạn nằm trong reports/nghien_cuu_v2.md.")
        path = PROJECT_ROOT / "reports" / "nghien_cuu_v2.md"
        if path.exists():
            st.markdown(path.read_text(encoding="utf-8"))
