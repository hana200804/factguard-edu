import json

import pandas as pd
import pytest

from src.evaluator import calculate_metrics, csv_bytes, markdown_report, run_experiment, save_experiment


def test_metrics_count_abstention_as_error():
    frame = pd.DataFrame({"gold": ["supported", "contradicted", "insufficient"],
                          "prediction": ["supported", "undetermined", "insufficient"],
                          "elapsed_ms": [1.0, 2.0, 3.0]})
    metrics = calculate_metrics(frame)
    assert metrics["accuracy"] == pytest.approx(2 / 3)
    assert metrics["abstention_rate"] == pytest.approx(1 / 3)
    assert metrics["no_conclusive_rate"] == pytest.approx(2 / 3)
    assert metrics["confusion_matrix"][1][3] == 1
    assert metrics["per_label"]["contradicted"]["recall"] == 0
    assert sum(map(sum, metrics["confusion_matrix"])) == 3
    with pytest.raises(ValueError):
        calculate_metrics(pd.DataFrame())


def test_reproducible_predictions_and_export(facts, retriever, cases, tmp_path):
    first, summary = run_experiment(facts, retriever, cases, "development")
    second, _ = run_experiment(facts, retriever, cases, "development")
    pd.testing.assert_frame_equal(first.drop(columns="elapsed_ms"), second.drop(columns="elapsed_ms"))
    assert first.groupby("method")["id"].apply(list).iloc[0] == first.groupby("method")["id"].apply(list).iloc[1]
    assert (first["elapsed_ms"] > 0).all()
    save_experiment(first, summary, tmp_path)
    assert len(pd.read_csv(tmp_path / "results.csv")) == len(first)
    assert json.loads((tmp_path / "latest.json").read_text(encoding="utf-8"))["cases"] == len(first) // 2
    assert "Các ca thất bại" not in markdown_report(first, summary) or summary["cases"] > 0
    assert "người xây dựng" in markdown_report(first, summary)


def test_csv_export_is_excel_safe():
    data = csv_bytes(pd.DataFrame({"text": ["=HYPERLINK(\"x\")", "+cmd", "Thông tin lịch sử"], "n": [1, 2, 3]}))
    assert data.startswith(b"\xef\xbb\xbf")
    assert "'=HYPERLINK" in data.decode("utf-8-sig")
    assert "Thông tin lịch sử" in data.decode("utf-8-sig")


def test_bad_split(facts, retriever, cases):
    with pytest.raises(ValueError):
        run_experiment(facts, retriever, cases, "train")
