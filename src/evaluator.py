import argparse
import importlib.metadata
import json
import platform
from pathlib import Path
from time import perf_counter
from typing import Any, cast

import pandas as pd
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix

from src.baseline import BaselineVerifier
from src.loader import load_evaluation, load_facts, load_sources, source_documents
from src.models import ALL_LABELS, GOLD_LABELS, LABELS_VI, UNDETERMINED, Fact
from src.retriever import Retriever
from src.utils import ALGORITHM_VERSION, PROJECT_ROOT, atomic_json, csv_safe, digest_bytes, utc_now
from src.verifier import ProposedVerifier


def csv_bytes(frame: pd.DataFrame) -> bytes:
    return frame.map(csv_safe).to_csv(index=False).encode("utf-8-sig")


def calculate_metrics(frame: pd.DataFrame) -> dict:
    if frame.empty:
        raise ValueError("Không có ca thực nghiệm để đánh giá.")
    # pandas' dynamic column/boolean selection and sklearn's output_dict overload
    # are narrowed at the library boundary; validated column names are internal.
    table = cast(Any, frame)
    truth, predicted = table["gold"].tolist(), table["prediction"].tolist()
    report = cast(dict[str, Any], classification_report(truth, predicted, labels=GOLD_LABELS,
                                                       output_dict=True, zero_division=cast(Any, 0)))
    decided = table[table["prediction"] != UNDETERMINED]
    return {
        "n": len(frame),
        "accuracy": float(accuracy_score(truth, predicted)),
        "precision_macro": report["macro avg"]["precision"],
        "recall_macro": report["macro avg"]["recall"],
        "f1_macro": report["macro avg"]["f1-score"],
        "per_label": {label: report[label] for label in GOLD_LABELS},
        "confusion_matrix": confusion_matrix(truth, predicted, labels=ALL_LABELS).tolist(),
        "labels": ALL_LABELS,
        "abstention_rate": float((table["prediction"] == UNDETERMINED).mean()),
        "no_conclusive_rate": float(table["prediction"].isin(["insufficient", UNDETERMINED]).mean()),
        "selective_accuracy": float(accuracy_score(decided["gold"], decided["prediction"])) if len(decided) else None,
        "mean_ms": float(table["elapsed_ms"].mean()),
        "median_ms": float(table["elapsed_ms"].median()),
        "p95_ms": float(table["elapsed_ms"].quantile(0.95)),
    }


def run_experiment(facts: list[Fact], retriever: Retriever, cases: pd.DataFrame,
                   split: str = "evaluation") -> tuple[pd.DataFrame, dict]:
    if split not in {"development", "evaluation"}:
        raise ValueError("Tập dữ liệu không hợp lệ.")
    selected = cast(Any, cases)[cases["split"] == split]
    if selected.empty:
        raise ValueError("Tập được chọn chưa có ca kiểm thử.")
    start = perf_counter()
    methods = {"baseline": BaselineVerifier(facts), "proposed": ProposedVerifier(facts, retriever)}
    rows = []
    for case in selected.to_dict("records"):
        for method, verifier in methods.items():
            result = verifier.verify(case["question"], case["answer"])
            rows.append({"id": case["id"], "fact_id": case["fact_id"], "event_id": case["event_id"],
                         "question": case["question"], "answer": case["answer"], "gold": case["label"],
                         "group": case["group"], "split": split, "method": method,
                         "prediction": result.label, "correct": result.label == case["label"],
                         "elapsed_ms": result.elapsed_ms, "explanation": result.explanation})
    frame = pd.DataFrame(rows)
    metrics = {method: calculate_metrics(cast(Any, frame)[frame["method"] == method]) for method in methods}
    summary = {"created_at": utc_now(), "algorithm_version": ALGORITHM_VERSION, "split": split,
               "cases": len(selected), "question_count": int(selected["question"].nunique()),
               "duration_s": perf_counter() - start, "metrics": metrics,
               "environment": {"python": platform.python_version(), "platform": platform.platform(),
                               "packages": {p: importlib.metadata.version(p) for p in
                                            ["streamlit", "pandas", "scikit-learn", "rapidfuzz", "pypdf", "plotly"]}}}
    return frame, summary


def markdown_report(frame: pd.DataFrame, summary: dict) -> str:
    table = cast(Any, frame)
    lines = ["# Kết quả thực nghiệm FactGuard EDU", "", f"Thời điểm chạy (UTC): {summary['created_at']}.",
             f"Phiên bản thuật toán: {summary['algorithm_version']}. Tập: {summary['split']}.",
             f"Số ca mỗi phương pháp: {summary['cases']}; số câu hỏi phân biệt: {summary['question_count']}.", "",
             "Các câu trả lời kiểm thử do người xây dựng dự án tạo có chủ đích; không phải mẫu thu từ học sinh hay ChatGPT.",
             "Kết quả chỉ mô tả bộ kiểm thử nhỏ và kho tham chiếu hiện tại, chưa chứng minh hiệu quả trên quần thể học sinh.", "",
             "## So sánh", "", "| Phương pháp | Accuracy | Precision macro | Recall macro | F1 macro | Từ chối tự kết luận | Chưa kết luận đúng/sai | TB (ms) |",
             "|---|---:|---:|---:|---:|---:|---:|---:|"]
    for method, m in summary["metrics"].items():
        lines.append(f"| {method} | {m['accuracy']:.4f} | {m['precision_macro']:.4f} | {m['recall_macro']:.4f} | {m['f1_macro']:.4f} | {m['abstention_rate']:.4f} | {m['no_conclusive_rate']:.4f} | {m['mean_ms']:.3f} |")
    lines += ["", "Accuracy tính trên toàn bộ ca; undetermined khác cả ba nhãn chuẩn nên tính là sai.",
              "Macro lấy trung bình ba nhãn chuẩn. Precision/recall/F1 mẫu số 0 được ghi 0.",
              "Từ chối tự kết luận = undetermined/n. Chưa kết luận đúng/sai = (insufficient + undetermined)/n.",
              "Thời gian đo từng lời gọi kiểm chứng, không gồm khởi tạo chỉ mục/giao diện; không phải benchmark phần cứng."]
    for method, m in summary["metrics"].items():
        lines += ["", f"## {method}: theo nhãn", "", "| Nhãn | Precision | Recall | F1 | Support |", "|---|---:|---:|---:|---:|"]
        for label in GOLD_LABELS:
            r = m["per_label"][label]
            lines.append(f"| {LABELS_VI[label]} | {r['precision']:.4f} | {r['recall']:.4f} | {r['f1-score']:.4f} | {int(r['support'])} |")
        lines += ["", "Ma trận nhầm lẫn (hàng = nhãn chuẩn; cột = dự đoán):", "",
                  "Thứ tự: " + ", ".join(ALL_LABELS), "", "```json", json.dumps(m["confusion_matrix"]), "```"]
        groups = table[table["method"] == method].groupby("group")["correct"].agg(["count", "mean"])
        lines += ["", "### Theo nhóm", "", "| Nhóm | Số ca | Accuracy |", "|---|---:|---:|"]
        for group, row in groups.iterrows():
            lines.append(f"| {group} | {int(row['count'])} | {row['mean']:.4f} |")
        failures = table[(table["method"] == method) & ~table["correct"]]
        lines += ["", f"### Các ca thất bại: {len(failures)}", ""]
        for row in failures.to_dict("records"):
            lines.append(f"- {row['id']}: chuẩn `{row['gold']}`, dự đoán `{row['prediction']}`. {row['explanation']}")
    lines += ["", "## Khả năng tái lập", "", "Dự đoán xác định, không dùng số ngẫu nhiên. Thời gian có thể thay đổi theo máy/lần chạy.",
              "Kho tri thức chứa đáp án tham chiếu cho các sự kiện được đánh giá: đây là bài toán kiểm chứng trong kho đóng, không phải kiểm tra ghi nhớ của mô hình.",
              "Tách development/evaluation theo event_id. Quy tắc không được điều chỉnh dựa trên điểm evaluation.",
              "Baseline chỉ khớp từ, không có nhãn mâu thuẫn: đây là baseline đơn giản và yếu; chưa so với hệ thống kiểm chứng tiên tiến.",
              "Cần bộ đánh giá độc lập do giáo viên gán nhãn, mở rộng dữ liệu và nghiên cứu người dùng trước khi suy rộng.", "",
              "## Môi trường", "", "```json", json.dumps(summary.get("environment", {}), ensure_ascii=False, indent=2), "```", ""]
    return "\n".join(lines)


def save_experiment(frame: pd.DataFrame, summary: dict, directory: Path) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    # Latest JSON is the commit marker; readers never see it before matching rows.
    (directory / "results.csv").write_bytes(csv_bytes(frame))
    (directory / "ket_qua_thuc_nghiem.md").write_text(markdown_report(frame, summary), encoding="utf-8")
    atomic_json(directory / "latest.json", summary)


def data_fingerprints(base: Path) -> dict[str, str]:
    paths = [base / "facts.csv", base / "evaluation.csv", base / "sources.json"]
    paths += sorted((base / "sources").glob("*.md"))
    return {str(p.relative_to(base)): digest_bytes(p.read_bytes()) for p in paths}


def main() -> None:
    parser = argparse.ArgumentParser(description="Chạy thực nghiệm có thể tái lập, không dùng API.")
    parser.add_argument("--split", choices=["development", "evaluation"], default="evaluation")
    parser.add_argument("--output", type=Path, default=PROJECT_ROOT / "reports" / "experiment")
    args = parser.parse_args()
    base = PROJECT_ROOT / "data"
    sources = load_sources(base / "sources.json")
    facts = load_facts(base / "facts.csv", sources)
    cases = load_evaluation(base / "evaluation.csv", facts)
    retriever = Retriever(source_documents(base, sources, facts))
    frame, summary = run_experiment(facts, retriever, cases, args.split)
    summary["data_sha256"] = data_fingerprints(base)
    save_experiment(frame, summary, args.output)
    print(json.dumps({"cases": summary["cases"], "metrics": summary["metrics"]}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
