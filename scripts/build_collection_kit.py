"""Write the blank answer-recording sheet from data/collection/cau_hoi.csv.

Refuses to overwrite a sheet that already holds pasted answers.
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.collection import (
    DEFAULT_TOOLS,
    QUESTION_BANK,
    TEMPLATE,
    eligible_events,
    load_question_bank,
    template_rows,
    write_template,
)
from src.loader import DataError, load_evaluation, load_facts, load_sources
from src.utils import PROJECT_ROOT


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--tools", nargs="+", default=DEFAULT_TOOLS, help="Một dòng cho mỗi công cụ, ví dụ ChatGPT Gemini Copilot")
    parser.add_argument("--output", type=Path, default=TEMPLATE)
    args = parser.parse_args()
    base = PROJECT_ROOT / "data"
    facts = load_facts(base / "facts.csv", load_sources(base / "sources.json"))
    cases = load_evaluation(base / "evaluation.csv", facts)
    try:
        bank = load_question_bank(QUESTION_BANK, eligible_events(facts, cases.loc[cases["split"] == "development"]))
        rows = template_rows(bank, args.tools)
        write_template(args.output, rows)
    except DataError as error:
        raise SystemExit(f"Lỗi: {error}") from error
    print(f"Đã ghi {len(rows)} dòng ({len(bank)} câu × {len(args.tools)} công cụ) vào {args.output}")


if __name__ == "__main__":
    main()
