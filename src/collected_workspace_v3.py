"""Application wrapper and exports around the frozen v3 evaluation function."""
import json
import re
from pathlib import Path
from uuid import uuid4

import pandas as pd

from src.annotation_study import consensus_cases
from src.annotation_study_v3 import evaluate_collected_v3
from src.evaluator import csv_bytes
from src.loader import DataError
from src.nli import MODEL_ID, MODEL_REVISION
from src.utils import PROJECT_ROOT, atomic_json, digest_bytes
from src.v3_freeze import validate_v3_freeze

METHOD_NAMES = {"lexical_3way": "Đối chứng từ vựng 3 nhãn", "rules_single_v1": "Luật một dữ kiện v1",
                "claims_no_guard": "Mệnh đề bỏ chốt phạm vi", "claims_guarded": "Luật mệnh đề v2",
                "hybrid_v3": "Luật và NLI v3"}


def study_input_digest(collected: list[dict], annotations: list[dict]) -> str:
    identifiers = {row["id"] for row in collected}
    ratings = [row for row in annotations if row["case_id"] in identifiers]
    def serialise(row):
        return json.dumps(row, ensure_ascii=False, sort_keys=True)

    payload = {"collected": sorted(map(serialise, collected)), "annotations": sorted(map(serialise, ratings))}
    return digest_bytes(json.dumps(payload, ensure_ascii=False, sort_keys=True).encode("utf-8"))


def run_collected_study_v3(facts, documents, development, collected: list[dict], annotations: list[dict], nli):
    accepted, pending = consensus_cases(collected, annotations)
    if not accepted:
        raise DataError("Chưa có ca thu thập với ít nhất hai tên gán nhãn đồng thuận.")
    if not validate_v3_freeze():
        raise DataError("V3 chưa khớp bản đóng băng. Kiểm tra mã, kho dữ kiện và mô hình trước khi đo.")
    frame, summary = evaluate_collected_v3(facts, documents, development, accepted, nli)
    if not summary["v3_engine_matches_freeze"]:
        raise DataError("Bản đóng băng không còn khớp sau lần chạy; chưa lưu như kết quả nghiên cứu.")
    identifiers = {row["id"] for row in collected}
    summary.update(collected_count=len(collected), pending_count=len(pending),
                   annotation_count=sum(row["case_id"] in identifiers for row in annotations),
                   unique_question_count=len({" ".join(row["question"].split()) for row in accepted}),
                   event_code_count=len({row["event_id"] for row in accepted}),
                   input_sha256=study_input_digest(collected, annotations),
                   model_id=MODEL_ID, model_revision=MODEL_REVISION,
                   freeze_manifest_sha256=digest_bytes((PROJECT_ROOT / "reports/research_v3/engine_freeze.json").read_bytes()),
                   presentation_code_sha256=digest_bytes(Path(__file__).read_bytes()))
    return frame, summary


def _cell(value) -> str:
    return str(value).replace("|", "\\|").replace("\n", " ")


def study_report_markdown(frame: pd.DataFrame, summary: dict) -> str:
    lines = ["# Đánh giá v3 trên ca thu thập có nhãn đồng thuận", "",
             f"Thời điểm chạy (UTC): {summary['created_at']}. Phiên bản: {summary['version']}.", "",
             f"Đã nhập {summary['collected_count']} ca; đánh giá {summary['cases']} ca đồng thuận; "
             f"còn {summary['pending_count']} ca chờ hoặc bất đồng.",
             f"Tập được đo có {summary['unique_question_count']} câu hỏi phân biệt và {summary['event_code_count']} mã sự kiện.", "",
             "Các câu trả lời cho cùng câu hỏi hoặc cùng sự kiện phụ thuộc nhau. Số ca không phải số người tham gia; "
             "mã outside không chứng minh các câu ngoài kho thuộc cùng một sự kiện thực tế.", "",
             "| Phương pháp | Đúng/tổng | Accuracy | Macro F1 | Hỗ trợ sai/ca gold không hỗ trợ | Có kết luận đúng-sai | Rủi ro trên kết luận đúng-sai |",
             "| --- | ---: | ---: | ---: | ---: | ---: | ---: |"]
    for method, metrics in summary["metrics"].items():
        part = frame.loc[frame["method"] == method]
        risk = metrics["decisive_risk"]
        risk_text = f"{risk:.2%}" if risk is not None else "Không xác định"
        lines.append(f"| {METHOD_NAMES[method]} | {int(part['correct'].sum())}/{metrics['n']} | "
                     f"{metrics['accuracy']:.2%} | {metrics['f1_macro']:.4f} | "
                     f"{metrics['false_support_count']}/{metrics['non_supported_gold_count']} | "
                     f"{metrics['decisive_coverage']:.2%} | {risk_text} |")
    interval = summary["hybrid_vs_rules_interval"]
    lines += ["", "## So sánh v3 với luật v2", ""]
    if interval["estimate"] is None:
        lines.append(f"Chưa đủ cụm để tính khoảng bootstrap: {interval.get('reason', 'Chưa đủ dữ liệu')}.")
    else:
        lines.append(f"Chênh lệch Accuracy cặp, mỗi mã sự kiện cùng trọng số: {interval['estimate']:.4f}; "
                     f"khoảng bootstrap 95% [{interval['lower']:.4f}, {interval['upper']:.4f}], "
                     f"{interval['n_clusters']} cụm. Đây là mô tả thăm dò, không chứng minh cải thiện học tập.")
    failed = frame.loc[~frame["correct"].astype(bool)]
    lines += ["", "## Ca sai hoặc từ chối so với nhãn chuẩn", ""]
    if failed.empty:
        lines.append("Không quan sát ca sai trong tập này; không suy ra rủi ro thực tế bằng 0.")
    else:
        lines += ["| ID | Mã sự kiện | Phương pháp | Nhãn chuẩn | Dự đoán |", "| --- | --- | --- | --- | --- |"]
        for row in failed.to_dict("records"):
            lines.append("| " + " | ".join(_cell(row[key]) for key in ["id", "event_id", "method", "gold", "prediction"]) + " |")
    lines += ["", "## Nguồn gốc và giới hạn", "",
              f"- Mô hình: {summary['model_id']}, revision {summary['model_revision']}.",
              f"- V3 khớp bản đóng băng sau đo: {summary['v3_engine_matches_freeze']}.",
              f"- SHA-256 đầu vào/nhãn: {summary['input_sha256']}.",
              f"- SHA-256 manifest v3: {summary['freeze_manifest_sha256']}.",
              "- Người gán nhãn dùng tên tự khai; phần mềm không xác thực danh tính hoặc tính độc lập.",
              "- Chỉ các ca nhập và có đồng thuận được đo. Việc loại ca còn bất đồng có thể gây thiên lệch; cần báo cả số ca còn chờ.",
              "- Không trộn bộ tổng hợp/hồi quy vào số ca thu thập. Chưa có chuẩn mệnh đề chi tiết hoặc nghiên cứu tác động học tập.",
              "- Mã giao diện/xuất báo cáo được bổ sung sau đóng băng; thuật toán, ngưỡng và hàm đánh giá v3 giữ nguyên.",
              "- CSV chi tiết chứa nội dung và xuất xứ đã nhập; kiểm tra thông tin cá nhân trước khi chia sẻ."]
    return "\n".join(lines) + "\n"


def save_collected_study_v3(frame: pd.DataFrame, summary: dict, runtime: Path) -> Path:
    base = runtime / "collected_study_v3"
    run_id = uuid4().hex
    destination = base / run_id
    destination.mkdir(parents=True)
    (destination / "results.csv").write_bytes(csv_bytes(frame))
    atomic_json(destination / "summary.json", summary)
    (destination / "report.md").write_text(study_report_markdown(frame, summary), encoding="utf-8")
    hashes = {name: digest_bytes((destination / name).read_bytes()) for name in ["results.csv", "summary.json", "report.md"]}
    atomic_json(base / "latest.json", {"run_id": run_id, "files": hashes})
    return destination


def load_latest_study_v3(runtime: Path):
    base = runtime / "collected_study_v3"
    pointer = base / "latest.json"
    if not pointer.exists():
        return None
    try:
        record = json.loads(pointer.read_text(encoding="utf-8"))
        run_id = record["run_id"]
        if not isinstance(run_id, str) or not re.fullmatch(r"[0-9a-f]{32}", run_id):
            raise ValueError("Mã lần chạy không hợp lệ")
        directory = base / run_id
        for name in ["results.csv", "summary.json", "report.md"]:
            if digest_bytes((directory / name).read_bytes()) != record["files"][name]:
                raise ValueError("Tệp kết quả đã thay đổi ngoài lần lưu")
        summary = json.loads((directory / "summary.json").read_text(encoding="utf-8"))
        frame = pd.read_csv(directory / "results.csv", keep_default_na=False)
        if len(frame) != summary["cases"] * 5 or set(frame["method"]) != set(METHOD_NAMES):
            raise ValueError("Kết quả thiếu ca hoặc phương pháp")
        return directory, frame, summary
    except (OSError, ValueError, KeyError, TypeError) as error:
        raise DataError("Không đọc được lần đánh giá v3 đã lưu; kiểm tra các tệp trong collected_study_v3.") from error
