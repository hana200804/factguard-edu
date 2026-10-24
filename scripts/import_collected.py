"""Load a filled answer sheet into the blind annotation queue (runtime/research.sqlite3).

All-or-nothing validation: if any filled row is invalid, nothing is imported.
"""
import argparse
import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.collection import (
    QUESTION_BANK,
    eligible_events,
    import_cases,
    load_question_bank,
    parse_answers,
    read_table,
)
from src.loader import DataError, load_evaluation, load_facts, load_sources
from src.review import ReviewRepository
from src.utils import PROJECT_ROOT, runtime_dir, utc_now


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("sheet", type=Path, help="Tệp CSV đã điền câu trả lời")
    parser.add_argument("--dry-run", action="store_true", help="Chỉ kiểm tra, không ghi vào hàng đợi gán nhãn")
    args = parser.parse_args()
    base = PROJECT_ROOT / "data"
    facts = load_facts(base / "facts.csv", load_sources(base / "sources.json"))
    cases = load_evaluation(base / "evaluation.csv", facts)
    try:
        bank = load_question_bank(QUESTION_BANK, eligible_events(facts, cases.loc[cases["split"] == "development"]))
        collected, errors, blank = parse_answers(read_table(args.sheet), bank)
    except DataError as error:
        raise SystemExit(f"Lỗi: {error}") from error
    print(f"{len(collected)} dòng hợp lệ, {len(errors)} dòng lỗi, {blank} dòng chưa điền câu trả lời.")
    if errors:
        print("\n".join(errors))
        raise SystemExit("Chưa nhập gì. Sửa các dòng lỗi rồi chạy lại.")
    if args.dry_run or not collected:
        return
    runtime = runtime_dir()
    log = import_cases(ReviewRepository(runtime), collected)
    destination = runtime / "collection_imports" / f"{utc_now().replace(':', '')}.csv"
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, ["row", "qid", "case_id", "status"])
        writer.writeheader()
        writer.writerows(log)
    added = sum(entry["status"] == "đã nhập" for entry in log)
    print(f"Đã nhập {added} ca mới, bỏ qua {len(log) - added} ca đã có. Nhật ký: {destination}")
    print("Mở ứng dụng → Phòng nghiên cứu → Gán nhãn độc lập để hai người gán nhãn.")


if __name__ == "__main__":
    main()
