import html
import json
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from src.evaluator import csv_bytes, data_fingerprints, markdown_report, run_experiment, save_experiment
from src.loader import DataError
from src.models import GOLD_LABELS, LABELS_VI, Verdict
from src.retriever import Retriever
from src.utils import PROJECT_ROOT, normalize

COLORS = {"baseline": "#94A8C7", "proposed": "#2158B0"}
PAGE_NAMES = ["Tổng quan", "Kiểm chứng câu trả lời", "Kho kiến thức", "So sánh phương pháp",
              "Thực nghiệm và đánh giá", "Phương pháp nghiên cứu", "Phòng nghiên cứu"]


def load_style() -> None:
    st.markdown((PROJECT_ROOT / "assets" / "style.css").read_text(encoding="utf-8"), unsafe_allow_html=True)


def page_header(title: str, subtitle: str) -> None:
    st.caption("FactGuard EDU / Lịch sử Việt Nam THPT")
    st.title(title)
    st.markdown(subtitle)


def evidence_view(result: Verdict) -> None:
    status = {"supported": st.success, "contradicted": st.error,
              "insufficient": st.warning, "undetermined": st.info}[result.label]
    status(f"**{LABELS_VI[result.label]}**\n\n{result.explanation}")
    st.caption("Kết luận chỉ trong phạm vi các quan hệ được nhận dạng. Điểm truy xuất văn bản không phải xác suất đúng.")
    if result.checks:
        st.subheader("Dữ kiện đã đối chiếu")
        for check in result.checks:
            with st.container(border=True):
                st.markdown(f"**{LABELS_VI[check.label]}**")
                if check.claim_text:
                    st.text(check.claim_text)
                st.markdown(f"**{check.question}**")
                left, right = st.columns(2)
                left.markdown("Giá trị nhận dạng")
                left.write(check.observed)
                right.markdown("Đáp án có nguồn")
                right.write(check.expected)
                st.caption(f"{check.fact_id} · {check.location}" + (f" · {check.relation}" if check.relation else ""))
                st.caption(check.explanation)
    issues = result.metadata.get("issues", [])
    if issues:
        with st.expander(f"Phần chưa thể xác minh ({len(issues)})", expanded=True):
            for issue in issues:
                st.text(issue["text"])
                st.caption(issue["explanation"])
    st.subheader("Bằng chứng để bạn kiểm tra")
    if not result.evidence:
        st.info("Chưa tìm được đoạn liên quan. Hãy bổ sung nguồn hoặc nêu rõ sự kiện.")
    for item in result.evidence:
        doc = item.document
        with st.container(border=True):
            st.markdown(f"**{html.escape(doc.title)}**")
            st.text(doc.text)
            st.caption(f"{doc.location} · {'Đã đối chiếu nguồn trực tuyến' if doc.verified else 'Chưa xác minh nguồn'}")
            if doc.url:
                st.link_button("Mở nguồn gốc", doc.url)
            with st.expander("Thông tin truy xuất"):
                st.write(f"Điểm tương đồng TF-IDF: {item.similarity:.3f}")
                st.caption("Dùng để xếp hạng đoạn liên quan. 0 có thể là bằng chứng được thêm bằng quy tắc tra cứu dữ kiện.")


def read_latest(directory: Path) -> tuple[pd.DataFrame | None, dict | None]:
    try:
        summary = json.loads((directory / "latest.json").read_text(encoding="utf-8"))
        frame = pd.read_csv(directory / "results.csv", keep_default_na=False)
        expected = summary["cases"] * len(summary["metrics"])
        if len(frame) != expected or not {"method", "prediction", "gold", "correct"} <= set(frame.columns):
            return None, None
        return frame, summary
    except (OSError, ValueError, KeyError, TypeError):
        return None, None


def overview(facts, sources, cases, store, report_dir) -> None:
    st.html("""<section class="hero"><div><span class="hero-tag">Kiểm chứng để hiểu đúng</span>
    <h1>Đọc câu trả lời AI.<br>Đi tìm bằng chứng.</h1>
    <p>Một không gian thực hành tư duy phản biện dành cho học sinh THPT.<br>
    Đối chiếu dữ kiện lịch sử, đọc nguồn và tự đưa ra kết luận.</p>
    </div><div class="hero-seal" aria-hidden="true"><svg viewBox="0 0 120 140" width="112">
    <path d="M60 8 106 26v42c0 30-19 49-46 64C33 117 14 98 14 68V26Z" fill="none" stroke="#AFCBF5" stroke-width="3"/>
    <path d="m36 68 16 16 34-37" fill="none" stroke="white" stroke-width="7" stroke-linecap="round" stroke-linejoin="round"/>
    </svg><span>FactGuard EDU</span><small>Bằng chứng dẫn đường</small></div></section>""")
    st.write("")
    def start_verification() -> None:
        st.session_state["navigation"] = PAGE_NAMES[1]

    st.button("Bắt đầu kiểm chứng", type="primary", on_click=start_verification)
    test = cases[cases["split"] == "evaluation"]
    columns = st.columns(4)
    research_card = PROJECT_ROOT / "data" / "research" / "dataset_card.json"
    if research_card.exists():
        challenge_count = json.loads(research_card.read_text(encoding="utf-8"))["cases"]
        columns[0].metric("Ca thử thách nghiên cứu v2", challenge_count)
    else:
        columns[0].metric("Câu hỏi đánh giá", test["question"].nunique())
    columns[1].metric("Nguồn tham chiếu", len(sources))
    columns[2].metric("Dữ kiện có nguồn", sum(f.verified for f in facts))
    columns[3].metric("Lượt kiểm chứng thực tế", store.count())
    st.caption(f"{len(test)} ca v1 được giữ để hồi quy; bộ thử thách v2 đo riêng bốn phương pháp. Ca thực nghiệm và kiểm thử phần mềm được tính riêng với lượt sử dụng thực tế.")
    st.divider()
    st.subheader("Từ câu trả lời đến căn cứ")
    for column, heading, body in zip(st.columns(3), ["Nhập câu trả lời", "Đối chiếu dữ kiện", "Đọc lại nguồn"],
                                    ["Dán câu hỏi và câu trả lời từ AI bạn đang dùng.",
                                     "Kiểm tra mốc thời gian, nhân vật hoặc địa điểm trong phạm vi kho.",
                                     "Xem đoạn bằng chứng, vị trí đối chiếu và giới hạn của kết luận."], strict=True):
        column.markdown(f"### {heading}")
        column.write(body)
    _, summary = read_latest(report_dir)
    st.subheader("Thực nghiệm gần nhất")
    if summary:
        st.caption(f"Tập {summary.get('split', 'thử thách v2')} · {summary['cases']} ca/phương pháp · {summary['created_at']} (UTC)")
        st.dataframe(pd.DataFrame([{"Phương pháp": k, "Accuracy": v["accuracy"], "F1 macro": v["f1_macro"]}
                                   for k, v in summary["metrics"].items()]), hide_index=True, width="stretch")
        if "data_sha256" in summary and summary["data_sha256"] != data_fingerprints(PROJECT_ROOT / "data"):
            st.warning("Dữ liệu đã thay đổi so với lần chạy này. Hãy chạy lại thực nghiệm.")
    else:
        st.info("Chưa chạy thực nghiệm. Mở ‘Thực nghiệm và đánh giá’ để đo kết quả thật.")
    st.info("Kho hiện tại là bộ dữ kiện nhỏ được đối chiếu với nguồn trực tuyến. Giáo viên và học sinh cần rà soát nguồn, nhãn kiểm thử trước khi sử dụng trong báo cáo dự thi.")


def verify_page(facts, verifier, store) -> None:
    page_header("Kiểm chứng câu trả lời", "Đối chiếu từng mệnh đề. Xem riêng dữ kiện đúng, dữ kiện sai và phần chưa được kiểm tra.")
    samples = {
        "Tự nhập": ("", ""),
        "Mốc thời gian đúng": ("Chủ tịch Hồ Chí Minh đọc Tuyên ngôn Độc lập vào ngày nào?", "Ngày 2 tháng 9 năm 1945."),
        "Mốc thời gian sai": ("Chiến dịch Điện Biên Phủ kết thúc vào ngày nào?", "Ngày 7/5/1955."),
        "Chưa đủ thông tin": ("Chủ tịch Hồ Chí Minh đọc Tuyên ngôn Độc lập vào ngày nào?", "Vào năm 1945."),
        "Câu hỏi ngoài kho": ("Trận Bạch Đằng năm 938 diễn ra vào ngày nào?", "Ngày 1/1/938."),
        "Câu hỏi cần tự phân tích": ("Vì sao chiến thắng Điện Biên Phủ có ý nghĩa quốc tế?", "Đây là bước ngoặt quan trọng trong lịch sử."),
        "Nhiều dữ kiện cùng đúng": ("Kiểm chứng các dữ kiện lịch sử sau.", "Hồ Chí Minh đọc Tuyên ngôn Độc lập ngày 2/9/1945 tại Quảng trường Ba Đình."),
        "Đúng ngày nhưng sai nhân vật": ("Kiểm chứng các dữ kiện lịch sử sau.", "Trần Phú đọc Tuyên ngôn Độc lập ngày 2/9/1945 tại Quảng trường Ba Đình."),
        "Hai quan hệ thời gian": ("Kiểm chứng các mốc thời gian.", "Chiến dịch Điện Biên Phủ bắt đầu ngày 13/3/1954; Chiến dịch Điện Biên Phủ kết thúc ngày 7/5/1954."),
        "Tiền đề câu hỏi sai": ("Ai đọc Tuyên ngôn Độc lập tại Sao Hỏa năm 1945?", "Hồ Chí Minh."),
    }

    def load_sample() -> None:
        question, answer = samples[st.session_state["sample"]]
        st.session_state["question_input"] = question
        st.session_state["answer_input"] = answer
        st.session_state.pop("last_result", None)

    st.selectbox("Tình huống để thử", list(samples), key="sample", on_change=load_sample)
    left, right = st.columns([1.05, 1], gap="large")
    with left:
        with st.form("verify_form"):
            question = st.text_area("Câu hỏi Lịch sử", key="question_input", height=110,
                                    placeholder="Ví dụ: Chiến dịch Điện Biên Phủ kết thúc vào ngày nào?", max_chars=4000)
            answer = st.text_area("Câu trả lời do AI cung cấp", key="answer_input", height=200,
                                  placeholder="Dán câu trả lời cần kiểm tra tại đây…", max_chars=12000)
            submit = st.form_submit_button("Kiểm chứng", type="primary", width="stretch")
        st.caption("Nội dung và lịch sử được lưu trên máy này. Ứng dụng không gửi câu trả lời lên dịch vụ AI.")
        if submit:
            if not question.strip() or not answer.strip():
                st.warning("Hãy nhập cả câu hỏi và câu trả lời.")
            else:
                result = verifier.verify(question, answer)
                store.log(question, answer, result)
                st.session_state["last_result"] = {"question": question, "answer": answer, "verdict": result}
    with right:
        saved = st.session_state.get("last_result")
        if saved and saved["question"] == question and saved["answer"] == answer:
            result = saved["verdict"]
            st.subheader("Kết quả đối chiếu")
            highlight_answer(answer, result)
            evidence_view(result)
            st.caption(f"Thời gian xử lý: {result.elapsed_ms:.2f} ms (không gồm giao diện).")
            st.download_button("Tải kết quả JSON", json.dumps(saved, default=lambda v: v.to_dict(), ensure_ascii=False, indent=2),
                               "factguard-ket-qua.json", "application/json")
        else:
            st.markdown("### Một kết luận cần có căn cứ")
            st.write("Sau khi kiểm chứng, bạn sẽ thấy dữ kiện được đối chiếu, đáp án tham chiếu và các đoạn liên quan.")
            with st.container(border=True):
                for label in LABELS_VI.values():
                    st.markdown(f"• {label}")
            st.caption("Đã hỗ trợ nhiều mệnh đề và phủ định đơn trong các quan hệ có mẫu. Suy luận hoặc quan hệ chưa rõ vẫn cần người kiểm tra.")
    with st.expander("Lịch sử kiểm chứng trên máy"):
        history = store.history()
        if history:
            view = [{"Thời gian (UTC)": r["created_at"], "Câu hỏi": r["question"],
                     "Kết quả": LABELS_VI[json.loads(r["verdict"])["label"]]} for r in history]
            st.dataframe(pd.DataFrame(view), hide_index=True, width="stretch")
        else:
            st.caption("Chưa có lượt kiểm chứng.")


def highlight_answer(answer: str, verdict: Verdict) -> None:
    palette = {"supported": "#dff2e8", "contradicted": "#fbe1df", "insufficient": "#fff0c8", "undetermined": "#e1eafa"}
    parts, offset = [], 0
    for check in sorted(verdict.checks, key=lambda c: (c.span_start, -c.span_end)):
        if check.span_start < offset or check.span_start < 0 or check.span_end > len(answer):
            continue
        parts.append(html.escape(answer[offset:check.span_start]))
        tooltip = html.escape(f"{LABELS_VI[check.label]} / {check.fact_id} / {check.expected}", quote=True)
        parts.append(f'<mark title="{tooltip}" style="background:{palette[check.label]};padding:1px 3px">{html.escape(answer[check.span_start:check.span_end])}</mark>')
        offset = check.span_end
    parts.append(html.escape(answer[offset:]))
    st.html('<div style="background:white;border:1px solid #ccd9eb;border-radius:7px;padding:14px;line-height:1.9;white-space:pre-wrap">' + "".join(parts) + '</div>')
    st.caption("Tô màu các giá trị được nhận dạng; đọc nhãn từng mệnh đề bên dưới. Phần không tô màu chưa mặc nhiên được xác nhận.")


def knowledge_page(facts, sources, store, repository=None) -> None:
    page_header("Kho kiến thức", "Mỗi dữ kiện đều cần một nguồn và một vị trí có thể đọc lại.")
    tabs = st.tabs(["Dữ kiện tham chiếu", "Tài liệu và nguồn", "Bổ sung tài liệu", "Thẩm định dữ kiện"])
    with tabs[0]:
        query = st.text_input("Tìm dữ kiện", placeholder="Tìm theo sự kiện, câu hỏi, đáp án hoặc nguồn…")
        rows = [{"ID": f.id, "Chủ đề": f.topic, "Câu hỏi": f.question, "Đáp án chuẩn": f.answer,
                 "Bằng chứng tóm lược": f.reference, "Nguồn": sources[f.source_id]["title"],
                 "URL": sources[f.source_id]["url"], "Vị trí": f.location,
                 "Trạng thái": "Đã đối chiếu nguồn" if f.verified else "Chưa xác minh"} for f in facts]
        if query:
            rows = [r for r in rows if normalize(query) in normalize(" ".join(r.values()))]
        st.caption(f"{len(rows)} dữ kiện phù hợp. Đã đối chiếu trực tuyến không đồng nghĩa đã được giáo viên thẩm định.")
        st.dataframe(pd.DataFrame(rows), hide_index=True, width="stretch", column_config={"URL": st.column_config.LinkColumn("Nguồn gốc")})
        st.download_button("Tải bộ dữ kiện CSV", (PROJECT_ROOT / "data" / "facts.csv").read_bytes(), "facts.csv", "text/csv")
    with tabs[1]:
        for source in sources.values():
            with st.expander(f"{source['id']} · {source['title']}"):
                st.caption(f"{source['publisher']} · kiểm tra ngày {source['checked_at']} · {source['verification_method']}")
                if source["url"]:
                    st.link_button("Đọc nguồn gốc", source["url"])
                if source.get("runtime"):
                    st.caption(f"Người tự khai thẩm định: {source['reviewer']}")
                    st.text(source["text"])
                else:
                    st.text((PROJECT_ROOT / "data" / "sources" / source["file"]).read_text(encoding="utf-8"))
        uploaded = store.uploaded_documents()
        if uploaded:
            st.subheader("Tài liệu bổ sung chưa xác minh")
            for document in uploaded:
                with st.expander(f"{document.title} / {document.location}"):
                    st.text(document.text)
    with tabs[2]:
        st.info("Tài liệu mới dùng để tìm bằng chứng liên quan, có nhãn ‘Chưa xác minh’. Dùng tab Thẩm định dữ kiện để tạo bản nháp, duyệt nguồn và đưa dữ kiện đã duyệt vào kiểm chứng.")
        file = st.file_uploader("Chọn TXT, Markdown hoặc PDF dạng văn bản", type=["txt", "md", "markdown", "pdf"])
        st.caption("Tối đa 5 MB, PDF tối đa 100 trang. PDF scan cần OCR bên ngoài. Chỉ tải nội dung bạn được phép sử dụng.")
        if st.button("Thêm vào kho và tái lập chỉ mục", disabled=file is None, type="primary"):
            if file is not None:
                try:
                    count = store.import_document(file.name, file.getvalue())
                    st.success(f"Đã thêm {count} đoạn. Chỉ mục sẽ dùng tài liệu mới ở lần kiểm chứng tiếp theo.")
                except DataError as error:
                    st.error(str(error))
        if st.button("Tái lập chỉ mục"):
            documents = store.uploaded_documents()
            st.success(f"Đã đọc lại {len(facts)} dữ kiện chuẩn và {len(documents)} đoạn bổ sung. Chỉ mục được dựng lại ở mỗi lượt xử lý.")
    with tabs[3]:
        if repository is not None:
            from src.research_ui import review_sources

            review_sources(repository, store, facts)


def results_view(frame: pd.DataFrame, summary: dict) -> None:
    rows = [{"Phương pháp": method, "Accuracy": m["accuracy"], "Precision macro": m["precision_macro"],
             "Recall macro": m["recall_macro"], "F1 macro": m["f1_macro"], "Từ chối tự kết luận": m["abstention_rate"],
             "Chưa kết luận đúng/sai": m["no_conclusive_rate"], "TB (ms)": m["mean_ms"]}
            for method, m in summary["metrics"].items()]
    st.dataframe(pd.DataFrame(rows), hide_index=True, width="stretch")
    chart_frame = pd.DataFrame([{"Phương pháp": method, "Chỉ số": metric, "Giá trị": values[metric]}
                               for method, values in summary["metrics"].items()
                               for metric in ["accuracy", "precision_macro", "recall_macro", "f1_macro"]])
    fig = px.bar(chart_frame, x="Chỉ số", y="Giá trị", color="Phương pháp", barmode="group",
                 color_discrete_map=COLORS, range_y=[0, 1], text_auto=True)
    fig.update_traces(texttemplate="%{y:.3f}")
    fig.update_layout(plot_bgcolor="white", paper_bgcolor="rgba(0,0,0,0)", font_family="Segoe UI",
                      legend_title_text="", margin=dict(l=0, r=0, t=20, b=0))
    st.plotly_chart(fig, width="stretch")
    st.caption("Hai phương pháp kiểm chứng dùng cùng ca kiểm thử. Chưa tích hợp mô hình AI tạo sinh. Số liệu được tính bằng code từ lần chạy này.")
    st.subheader("Ma trận nhầm lẫn")
    for column, (method, metrics) in zip(st.columns(2), summary["metrics"].items(), strict=True):
        labels = [LABELS_VI[k] for k in metrics["labels"]]
        fig = go.Figure(go.Heatmap(z=metrics["confusion_matrix"], x=labels, y=labels, colorscale="Blues",
                                  text=metrics["confusion_matrix"], texttemplate="%{text}", showscale=False))
        fig.update_layout(title=method, xaxis_title="Dự đoán", yaxis_title="Nhãn chuẩn", height=400,
                          margin=dict(l=0, r=0, t=45, b=0), paper_bgcolor="rgba(0,0,0,0)")
        column.plotly_chart(fig, width="stretch")
    st.subheader("Kết quả theo nhãn")
    st.dataframe(pd.DataFrame([{"Phương pháp": method, "Nhãn": LABELS_VI[label], **values["per_label"][label]}
                               for method, values in summary["metrics"].items() for label in GOLD_LABELS]), hide_index=True, width="stretch")
    st.subheader("Theo nhóm dữ liệu")
    st.dataframe(frame.groupby(["method", "group"])["correct"].agg(["count", "mean"]).reset_index().rename(
        columns={"method": "Phương pháp", "group": "Nhóm", "count": "Số ca", "mean": "Accuracy"}), hide_index=True, width="stretch")
    failures = frame[~frame["correct"].astype(bool)]
    with st.expander(f"Các trường hợp chưa đạt nhãn chuẩn ({len(failures)})", expanded=bool(len(failures))):
        st.dataframe(failures, hide_index=True, width="stretch")
    with st.expander("Toàn bộ kết quả từng ca"):
        st.dataframe(frame, hide_index=True, width="stretch")
    left, right = st.columns(2)
    left.download_button("Xuất CSV kết quả", csv_bytes(frame), "factguard-results.csv", "text/csv")
    right.download_button("Xuất báo cáo Markdown", markdown_report(frame, summary), "ket-qua-thuc-nghiem.md", "text/markdown")
    st.caption("Accuracy gồm mọi ca. Nhãn không thể tự động kết luận được tính sai so với ba nhãn chuẩn. Thời gian không gồm dựng chỉ mục hay giao diện.")


def experiment_page(facts, documents, cases, runtime) -> None:
    page_header("Thực nghiệm và đánh giá v1", "Bộ đo gốc được giữ để hồi quy. Mở Phòng nghiên cứu để chạy bộ thử thách v2 với đối chứng ba nhãn và ablation.")
    split = st.selectbox("Tập thực nghiệm", ["evaluation", "development"],
                         format_func=lambda x: "Tập đánh giá" if x == "evaluation" else "Tập phát triển")
    selected = cases[cases["split"] == split]
    st.write(f"**{len(selected)} ca** · **{selected['question'].nunique()} câu hỏi** · **{selected['event_id'].nunique()} nhóm sự kiện**")
    st.warning("Đây là dữ liệu kiểm thử được xây dựng có chủ đích, chưa phải bộ đánh giá độc lập. Không điều chỉnh quy tắc theo kết quả tập đánh giá rồi báo cáo lại trên chính tập đó.")
    st.caption("Thực nghiệm luôn dùng kho tham chiếu đi kèm để tái lập, không dùng tài liệu tải thêm. Tách tập theo sự kiện; đáp án tham chiếu của sự kiện vẫn nằm trong kho tri thức.")
    directory = runtime / "experiments" / split
    if st.button("Chạy thực nghiệm", type="primary"):
        with st.spinner("Đang chạy từng ca và tính chỉ số…"):
            frame, summary = run_experiment(facts, Retriever(documents), cases, split)
            summary["data_sha256"] = data_fingerprints(PROJECT_ROOT / "data")
            save_experiment(frame, summary, directory)
        st.success("Đã chạy xong. Kết quả và thời gian dưới đây được đo trong lần chạy này.")
    frame, summary = read_latest(directory)
    if summary is None and split == "evaluation":
        frame, summary = read_latest(PROJECT_ROOT / "reports" / "experiment")
    if summary is not None and frame is not None:
        st.caption(f"Lần chạy: {summary['created_at']} (UTC) · phiên bản {summary['algorithm_version']}")
        if summary.get("data_sha256") != data_fingerprints(PROJECT_ROOT / "data"):
            st.warning("Dữ liệu hiện tại khác dấu vân tay của lần đo này. Hãy chạy lại.")
        results_view(frame, summary)
    else:
        st.info("Bấm ‘Chạy thực nghiệm’ để sinh bảng, biểu đồ và báo cáo từ dữ liệu thực tế.")


def comparison_page(facts, verifier) -> None:
    from src.baseline import BaselineVerifier

    page_header("So sánh phương pháp", "Cùng một câu hỏi, cùng một câu trả lời, hai cách đối chiếu.")
    st.info("Đây là minh họa đối chứng khớp từ v1 và kiểm chứng mệnh đề v2. Mở Phòng nghiên cứu để xem đối chứng học máy ba nhãn và ablation trên cùng bộ thử thách.")
    fact = st.selectbox("Chọn câu hỏi chuẩn", facts, format_func=lambda f: f.question)
    answer = st.text_area("Câu trả lời dùng chung", value=fact.answer, key=f"comparison_{fact.id}")
    if st.button("So sánh hai phương pháp", type="primary"):
        baseline = BaselineVerifier(facts).verify(fact.question, answer or "")
        proposed = verifier.verify(fact.question, answer or "")
        left, right = st.columns(2)
        left.subheader("Baseline: khớp từ")
        left.write(LABELS_VI[baseline.label])
        left.write(baseline.explanation)
        left.caption(f"{baseline.elapsed_ms:.3f} ms")
        with right:
            st.subheader("Đối chiếu mệnh đề v2")
            evidence_view(proposed)
    st.divider()
    st.subheader("Khác nhau ở đâu?")
    st.dataframe(pd.DataFrame([
        {"Bước": "Tìm câu hỏi", "Baseline": "Tương đồng từ", "Đề xuất": "TF-IDF tìm đoạn + ý định và neo sự kiện tìm dữ kiện"},
        {"Bước": "Đối chiếu đáp án", "Baseline": "Tỷ lệ khớp tập từ", "Đề xuất": "Chuẩn hóa ngày, tên riêng có alias đã kiểm tra"},
        {"Bước": "Mâu thuẫn", "Baseline": "Không nhận diện", "Đề xuất": "Mốc thời gian hoặc tên riêng thay thế có thể xác minh"},
        {"Bước": "Câu phức tạp", "Baseline": "Có thể khớp từ sai", "Đề xuất": "Tách các mệnh đề có mẫu, ghi phần chưa xác minh"},
    ]), hide_index=True, width="stretch")


def methodology_page() -> None:
    page_header("Phương pháp nghiên cứu", "Một công cụ hỗ trợ đọc nguồn và một thực nghiệm có thể kiểm tra lại.")
    st.html('<div class="pipeline"><span>Kho có nguồn</span><b>›</b><span>Truy xuất đoạn</span><b>›</b><span>Chuẩn hóa dữ kiện</span><b>›</b><span>Đối chiếu / từ chối</span><b>›</b><span>Học sinh đọc lại</span></div>')
    for filename, title in [("de_cuong.md", "Vấn đề và giả thuyết"), ("phuong_phap.md", "Thuật toán và thiết kế thực nghiệm"),
                             ("gioi_han_nghien_cuu.md", "Giới hạn và hướng phát triển"), ("phan_bien.md", "15 câu hỏi phản biện")]:
        path = PROJECT_ROOT / "reports" / filename
        if path.exists():
            with st.expander(title, expanded=filename == "de_cuong.md"):
                st.markdown(path.read_text(encoding="utf-8"))
    st.caption("Không có LLM, API trả phí, GPU hay kết nối mạng trong luồng kiểm chứng. Mở Phòng nghiên cứu để xem thiết kế nghiên cứu v2, thẩm định nhãn và các kết quả đo riêng.")
