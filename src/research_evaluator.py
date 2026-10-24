"""Reproducible, paired research experiment with frozen code and stage-level metrics."""
import argparse
import json
import platform
from collections import Counter
from datetime import date
from pathlib import Path

import pandas as pd

from src.claim_spans import date_spans
from src.claim_verifier import RESEARCH_VERSION, ClaimVerifier, entity_dictionary
from src.evaluator import calculate_metrics, csv_bytes
from src.loader import DataError, load_evaluation, load_facts, load_sources, source_documents
from src.models import CONTRADICTED, GOLD_LABELS, SUPPORTED
from src.research_baseline import LexicalThreeWay
from src.research_statistics import paired_cluster_interval
from src.retriever import Retriever
from src.utils import PROJECT_ROOT, atomic_json, digest_bytes, normalize, utc_now
from src.verifier import ProposedVerifier

METHODS = ["lexical_3way", "rules_single_v1", "claims_no_guard", "claims_guarded"]
FROZEN_FILES = ["src/claim_spans.py", "src/claim_verifier.py", "src/research_baseline.py",
                "src/research_statistics.py", "src/research_evaluator.py", "src/verifier.py",
                "src/retriever.py", "src/models.py", "src/loader.py", "src/utils.py",
                "data/relations.json", "data/facts.csv", "data/sources.json", "data/evaluation.csv",
                "reports/research_protocol_v2.json"]


def code_fingerprints() -> dict[str, str]:
    return {name: digest_bytes((PROJECT_ROOT / name).read_bytes()) for name in FROZEN_FILES}


def freeze_engine() -> dict:
    path = PROJECT_ROOT / "reports" / "research_v2" / "engine_freeze.json"
    if path.exists():
        raise DataError("Đã có bản đóng băng. Không ghi đè sau khi xem kết quả; tạo phiên bản nghiên cứu mới.")
    result = {"version": RESEARCH_VERSION, "frozen_at": utc_now(), "files": code_fingerprints(),
              "note": "Frozen before generating the assistant-authored challenge set; not an independent preregistration."}
    atomic_json(path, result)
    return result


def validate_freeze() -> bool:
    path = PROJECT_ROOT / "reports" / "research_v2" / "engine_freeze.json"
    if not path.exists():
        return False
    return json.loads(path.read_text(encoding="utf-8"))["files"] == code_fingerprints()


def load_challenge(path: Path, facts) -> list[dict]:
    try:
        rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    except (OSError, ValueError) as error:
        raise DataError("Không đọc được tập challenge JSONL.") from error
    if not rows:
        raise DataError("Challenge chưa có ca.")
    required = {"id", "question", "answer", "label", "event_id", "group", "gold_claims", "exclude_event"}
    seen, pairs = set(), set()
    fact_ids = {f.id for f in facts}
    for row in rows:
        if not required <= row.keys() or row["label"] not in GOLD_LABELS:
            raise DataError("Ca challenge thiếu trường hoặc nhãn sai.")
        if row["id"] in seen or (row["question"], row["answer"]) in pairs:
            raise DataError("Challenge bị trùng ca hoặc đầu vào.")
        if not row["question"].strip() or not row["answer"].strip():
            raise DataError("Đầu vào challenge không được rỗng.")
        for claim in row["gold_claims"]:
            if claim["fact_id"] not in fact_ids or claim["label"] not in GOLD_LABELS or not claim["value"]:
                raise DataError("Nhãn mệnh đề hoặc ID bằng chứng không hợp lệ.")
        seen.add(row["id"])
        pairs.add((row["question"], row["answer"]))
    return rows


def _value_key(value: str, kind: str, entity_lookup: dict) -> str:
    if kind in {"date", "year"}:
        try:
            return date.fromisoformat(value).isoformat()
        except ValueError:
            parsed, _ = date_spans(value)
            return parsed[0].canonical if parsed else normalize(value)
    return entity_lookup.get(kind, {}).get(normalize(value), normalize(value))


def run_research(facts, sources, development: pd.DataFrame, cases: list[dict]) -> tuple[pd.DataFrame, dict]:
    if set(development["event_id"]) & {row["event_id"] for row in cases}:
        raise DataError("Challenge trùng sự kiện với development.")
    base = PROJECT_ROOT / "data"
    lookup = {kind: entity_dictionary(facts, kind)[1] for kind in ["person", "place"]}
    fact_map = {f.id: f for f in facts}
    rows, models = [], {}
    for case in cases:
        excluded = case["exclude_event"]
        if excluded not in models:
            visible = [f for f in facts if f.event_id != excluded]
            documents = source_documents(base, sources, visible)
            # Excluded event sources may contain a broad summary. Only the
            # fact-level index is used in this controlled corpus perturbation.
            documents = [doc for doc in documents if doc.id in {f.id for f in visible}]
            retriever = Retriever(documents)
            models[excluded] = (retriever, {
                "lexical_3way": LexicalThreeWay(visible, development),
                "rules_single_v1": ProposedVerifier(visible, retriever),
                "claims_no_guard": ClaimVerifier(visible, retriever, guarded=False),
                "claims_guarded": ClaimVerifier(visible, retriever),
            })
        retriever, methods = models[excluded]
        hits = retriever.search(case["question"] + " " + case["answer"], 4)
        gold_ids = {c["fact_id"] for c in case["gold_claims"]}
        top_ids = {hit.document.id for hit in hits}
        retrieval_recall = len(top_ids & gold_ids) / len(gold_ids) if gold_ids else None
        gold_values = Counter((c["fact_id"], _value_key(c["value"], fact_map[c["fact_id"]].kind, lookup), bool(c.get("negated", False)))
                              for c in case["gold_claims"])
        gold_labels = Counter((*key, c["label"]) for c in case["gold_claims"]
                              for key in [(c["fact_id"], _value_key(c["value"], fact_map[c["fact_id"]].kind, lookup), bool(c.get("negated", False)))])
        for method, verifier in methods.items():
            verdict = verifier.verify(case["question"], case["answer"])
            predicted_values = Counter((c.fact_id, _value_key(c.observed, fact_map[c.fact_id].kind, lookup), c.negated) for c in verdict.checks)
            predicted_labels = Counter((c.fact_id, _value_key(c.observed, fact_map[c.fact_id].kind, lookup), c.negated, c.label) for c in verdict.checks)
            attributed = {c.fact_id for c in verdict.checks}
            if method == "lexical_3way":
                attributed = {verdict.metadata.get("nearest_fact", "")}
            correct = verdict.label == case["label"]
            rows.append({"id": case["id"], "event_id": case["event_id"], "group": case["group"],
                         "question": case["question"], "answer": case["answer"], "gold": case["label"],
                         "method": method, "prediction": verdict.label, "correct": correct,
                         "elapsed_ms": verdict.elapsed_ms, "evidence_complete_correct": correct and gold_ids <= attributed,
                         "gold_claim_count": sum(gold_values.values()), "predicted_claim_count": sum(predicted_values.values()),
                         "matched_claim_count": sum((gold_values & predicted_values).values()),
                         "matched_claim_label_count": sum((gold_labels & predicted_labels).values()),
                         "retrieval_recall_at_4": retrieval_recall,
                         "checks_json": json.dumps([c.__dict__ for c in verdict.checks], ensure_ascii=False),
                         "issues_json": json.dumps(verdict.metadata.get("issues", []), ensure_ascii=False),
                         "explanation": verdict.explanation})
    frame = pd.DataFrame(rows)
    metrics = {}
    for method in METHODS:
        selected = frame.loc[frame["method"] == method].copy()
        metric = calculate_metrics(selected)
        negative = selected["gold"] != SUPPORTED
        decisive = selected["prediction"].isin([SUPPORTED, CONTRADICTED])
        gold_count = int(selected["gold_claim_count"].sum())
        predicted_count = int(selected["predicted_claim_count"].sum())
        metric.update({"false_support_count": int(((selected["prediction"] == SUPPORTED) & negative).sum()),
                       "non_supported_gold_count": int(negative.sum()),
                       "false_support_rate": float(((selected["prediction"] == SUPPORTED) & negative).sum() / negative.sum()) if negative.any() else None,
                       "decisive_coverage": float(decisive.mean()),
                       "decisive_risk": float((~selected.loc[decisive, "correct"]).mean()) if decisive.any() else None,
                       "evidence_complete_accuracy": float(selected["evidence_complete_correct"].mean()),
                       "claim_detection_recall": float(selected["matched_claim_count"].sum() / gold_count) if gold_count else None,
                       "claim_label_recall": float(selected["matched_claim_label_count"].sum() / gold_count) if gold_count else None,
                       "claim_precision": float(selected["matched_claim_count"].sum() / predicted_count) if predicted_count else None,
                       "gold_claim_count": gold_count,
                       "predicted_claim_count": predicted_count})
        metrics[method] = metric
    summary = {"version": RESEARCH_VERSION, "created_at": utc_now(), "cases": len(cases),
               "event_clusters": len({r["event_id"] for r in cases}), "methods": METHODS, "metrics": metrics,
               "paired_event_interval": paired_cluster_interval(rows, "claims_guarded", "lexical_3way"),
               "ablation_event_interval": paired_cluster_interval(rows, "claims_guarded", "claims_no_guard"),
               "training": models[""][1]["lexical_3way"].manifest() if "" in models else {},
               "engine_matches_freeze": validate_freeze(),
               "data_origin": "assistant-authored synthetic challenge; not independent human evaluation",
               "python": platform.python_version(), "code_sha256": code_fingerprints()}
    return frame, summary


def report_markdown(frame: pd.DataFrame, summary: dict) -> str:
    lines = ["# Nghiên cứu kiểm chứng mệnh đề FactGuard EDU v2", "", f"Lần chạy: {summary['created_at']} (UTC).",
             f"{summary['cases']} ca/phương pháp; {summary['event_clusters']} cụm sự kiện; 4 phương pháp.",
             "**Dữ liệu tổng hợp do trợ lý xây dựng, chưa gán nhãn độc lập. Không phải kết quả nghiên cứu học sinh.**", "",
             "## Câu hỏi nghiên cứu", "", "Tách mệnh đề và chặn quan hệ/phạm vi chưa rõ có giảm kết luận hỗ trợ sai trên bộ thử thách này không?", "",
             "## Đối chứng và ablation", "",
             "- lexical_3way: TF-IDF ký tự và 6 đặc trưng từ vựng, StandardScaler + LogisticRegression, học ba nhãn chỉ trên 24 ca development v1.",
             "- rules_single_v1: luật một dữ kiện của bản đầu, giữ nguyên.",
             "- claims_no_guard: bộ trích mệnh đề v2, tắt chốt tiền đề câu hỏi và nội dung dư; vẫn kiểm tra giá trị và tính hợp lệ nguồn.",
             "- claims_guarded: đầy đủ bộ trích, đối chiếu, chốt tiền đề/vai trò và theo dõi phần chưa xử lý.", "",
             "| Phương pháp | Accuracy | F1 macro | Hỗ trợ sai / ca không được hỗ trợ | Kết luận đúng/sai | Rủi ro trên ca có kết luận | Đúng nhãn + đủ bằng chứng |",
             "|---|---:|---:|---:|---:|---:|---:|"]
    def fmt(value):
        return "không xác định" if value is None else f"{value:.4f}"
    for method, m in summary["metrics"].items():
        lines.append(f"| {method} | {m['accuracy']:.4f} | {m['f1_macro']:.4f} | {fmt(m['false_support_rate'])} | {m['decisive_coverage']:.4f} | {fmt(m['decisive_risk'])} | {m['evidence_complete_accuracy']:.4f} |")
    lines += ["", "Accuracy tính mọi ca; undetermined vẫn tính sai. Coverage chỉ tính supported/contradicted; risk là tỷ lệ sai trong các ca đó.",
              "Hỗ trợ sai = số ca dự đoán supported khi nhãn chuẩn khác supported / tổng ca nhãn chuẩn khác supported.",
              "Đúng nhãn + đủ bằng chứng yêu cầu tập ID dữ kiện chuẩn nằm trong dữ kiện được phương pháp quy trách nhiệm; không tính các đoạn truy xuất ngẫu nhiên như đã kiểm chứng.", "",
              "## Phân tích từng giai đoạn", "", "| Phương pháp | Recall trích giá trị | Recall đúng nhãn mệnh đề | Precision trích giá trị | Thời gian TB / median / p95 (ms) |",
              "|---|---:|---:|---:|---:|"]
    for method, m in summary["metrics"].items():
        lines.append(f"| {method} | {fmt(m['claim_detection_recall'])} | {fmt(m['claim_label_recall'])} | {fmt(m['claim_precision'])} | {m['mean_ms']:.3f} / {m['median_ms']:.3f} / {m['p95_ms']:.3f} |")
    common = frame.loc[frame["method"] == "claims_guarded", "retrieval_recall_at_4"].dropna()
    lines += ["", f"Recall@4 trung bình của truy xuất từ vựng trước tra cứu có cấu trúc: {float(common.mean()):.4f}. Chỉ tính ca có ID bằng chứng chuẩn.",
              "Những ca nguồn bị rút khỏi kho làm phép thử mất bằng chứng; mọi phương pháp đều dùng cùng kho bị rút của ca đó.",
              "Các đối chứng không có bộ trích mệnh đề không được diễn giải điểm trích bằng 0 là lỗi phân loại; đó là khả năng không triển khai ở phương pháp đó.", "",
              "## Khoảng biến thiên theo cụm sự kiện", ""]
    interval = summary["paired_event_interval"]
    lines += ["```json", json.dumps(interval, ensure_ascii=False, indent=2), "```",
              "Bootstrap cặp 2.000 lần, cùng trọng số cho từng cụm sự kiện, seed cố định. Khoảng này có tính thăm dò trên số ít cụm do tác giả chọn; không phải bảo đảm xác suất cho câu trả lời mới hay kết luận tác động giáo dục.", ""]
    for method in METHODS:
        selected = frame.loc[frame["method"] == method]
        lines += [f"## {method}: theo nhóm", "", "| Nhóm | Số ca | Accuracy |", "|---|---:|---:|"]
        for group, sub in selected.groupby("group"):
            lines.append(f"| {group} | {len(sub)} | {sub['correct'].mean():.4f} |")
        m = summary["metrics"][method]
        lines += ["", "Chỉ số từng nhãn:", "", "```json", json.dumps(m["per_label"], ensure_ascii=False, indent=2), "```",
                  "", "Ma trận (hàng chuẩn/cột dự đoán, thứ tự supported, contradicted, insufficient, undetermined):", "", "```json", json.dumps(m["confusion_matrix"]), "```", "",
                  "### Các ca sai hoặc từ chối", ""]
        for row in selected.loc[~selected["correct"]].to_dict("records"):
            lines.append(f"- {row['id']}: chuẩn {row['gold']}, dự đoán {row['prediction']}. {row['explanation']}")
    lines += ["", "## Giới hạn diễn giải", "",
              "Bộ thử thách được tạo sau đóng băng mã nhưng cùng trợ lý thiết kế cả mã và dữ liệu; không phải đánh giá mù hoặc độc lập. V1 evaluation đã xem nên chỉ làm hồi quy. Nguồn và nhãn cần người thật thẩm định.",
              "Đây là kho đóng và ngữ pháp hữu hạn, chưa giải quyết mọi câu trả lời AI, mọi phép phủ định hoặc vai trò ngữ nghĩa. Không báo kết quả của người gán nhãn hay thử nghiệm học sinh khi chưa có dữ liệu thật.",
              f"Mã còn khớp bản đóng băng tại lúc đo: {summary['engine_matches_freeze']}.", ""]
    return "\n".join(lines)


def save_research(frame: pd.DataFrame, summary: dict, output: Path) -> None:
    output.mkdir(parents=True, exist_ok=True)
    (output / "results.csv").write_bytes(csv_bytes(frame))
    (output / "bao_cao_nghien_cuu.md").write_text(report_markdown(frame, summary), encoding="utf-8")
    atomic_json(output / "latest.json", summary)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--freeze", action="store_true")
    parser.add_argument("--output", type=Path, default=PROJECT_ROOT / "reports" / "research_v2")
    args = parser.parse_args()
    if args.freeze:
        freeze_engine()
        print("Engine frozen before challenge generation.")
        return
    base = PROJECT_ROOT / "data"
    sources = load_sources(base / "sources.json")
    facts = load_facts(base / "facts.csv", sources)
    all_cases = load_evaluation(base / "evaluation.csv", facts)
    development = all_cases.loc[all_cases["split"] == "development"].copy()
    path = base / "research" / "challenge.jsonl"
    cases = load_challenge(path, facts)
    frame, summary = run_research(facts, sources, development, cases)
    summary["challenge_sha256"] = digest_bytes(path.read_bytes())
    summary["development_sha256"] = digest_bytes((base / "evaluation.csv").read_bytes())
    save_research(frame, summary, args.output)
    print(json.dumps({"cases": summary["cases"], "accuracy": {m: r["accuracy"] for m, r in summary["metrics"].items()},
                      "matches_freeze": summary["engine_matches_freeze"]}, ensure_ascii=True))


if __name__ == "__main__":
    main()
