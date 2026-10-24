import io
import json

import pandas as pd
import pytest
from pypdf import PdfWriter
from pypdf.generic import DecodedStreamObject, DictionaryObject, NameObject

from src.loader import (
    FACT_COLUMNS,
    DataError,
    extract_upload,
    load_evaluation,
    load_facts,
    load_sources,
    read_csv,
    source_documents,
)
from src.utils import PROJECT_ROOT


def test_dataset_integrity_and_split(corpus, cases):
    sources, facts, docs = corpus
    assert len(facts) >= 20 and len(sources) >= 3 and docs
    assert all(f.verified and sources[f.source_id]["verified"] for f in facts)
    dev = set(cases[cases["split"] == "development"]["event_id"])
    test = set(cases[cases["split"] == "evaluation"]["event_id"])
    assert not dev & test
    assert cases[cases["split"] == "evaluation"]["question"].nunique() >= 20


def test_empty_and_missing_columns(tmp_path):
    path = tmp_path / "empty.csv"
    path.write_text("", encoding="utf-8")
    with pytest.raises(DataError):
        read_csv(path, FACT_COLUMNS)
    path.write_text("id,question\na,b\n", encoding="utf-8")
    with pytest.raises(DataError, match="Thiếu"):
        read_csv(path, FACT_COLUMNS)


@pytest.mark.parametrize("mutation", ["duplicate_id", "duplicate_question", "unknown_source", "bad_date", "bad_verified", "bad_kind", "bad_alias", "bad_anchor", "unverified_source", "blank"])
def test_invalid_fact_rows_rejected(tmp_path, corpus, mutation):
    sources = json.loads(json.dumps(corpus[0]))
    frame = pd.read_csv(PROJECT_ROOT / "data" / "facts.csv", dtype=str, keep_default_na=False)
    if mutation == "duplicate_id":
        frame.loc[1, "id"] = frame.loc[0, "id"]
    elif mutation == "duplicate_question":
        frame.loc[1, "question"] = frame.loc[0, "question"].upper()
    elif mutation == "unknown_source":
        frame.loc[0, "source_id"] = "unknown"
    elif mutation == "bad_date":
        frame.loc[0, "canonical"] = "1945-02-31"
    elif mutation == "bad_verified":
        frame.loc[0, "verified"] = "yes"
    elif mutation == "bad_kind":
        frame.loc[0, "kind"] = "hallucination"
    elif mutation == "bad_alias":
        frame.loc[0, "aliases"] = "[]"
    elif mutation == "bad_anchor":
        frame.loc[0, "anchors"] = '["bad"]'
    elif mutation == "unverified_source":
        sources["S01"]["verified"] = False
    elif mutation == "blank":
        frame.loc[0, "reference"] = " "
    path = tmp_path / "facts.csv"
    frame.to_csv(path, index=False)
    with pytest.raises(DataError):
        load_facts(path, sources)


@pytest.mark.parametrize("mutation", ["label", "split", "fact", "event", "leak", "duplicate"])
def test_invalid_evaluation_rejected(tmp_path, facts, cases, mutation):
    frame = cases.copy()
    if mutation == "label":
        frame.loc[0, "label"] = "unknown"
    elif mutation == "split":
        frame.loc[0, "split"] = "train"
    elif mutation == "fact":
        frame.loc[0, "fact_id"] = "missing"
    elif mutation == "event":
        frame.loc[0, "event_id"] = "missing"
    elif mutation == "leak":
        frame.loc[0, "split"] = "development"
    elif mutation == "duplicate":
        frame.loc[1, ["question", "answer"]] = frame.loc[0, ["question", "answer"]]
    path = tmp_path / "eval.csv"
    frame.to_csv(path, index=False)
    with pytest.raises(DataError):
        load_evaluation(path, facts)


def test_bad_source_json_and_path(tmp_path, corpus):
    path = tmp_path / "sources.json"
    path.write_text("{}", encoding="utf-8")
    with pytest.raises(DataError):
        load_sources(path)
    rows = list(corpus[0].values())
    bad = [dict(rows[0], url="javascript:alert(1)")]
    path.write_text(json.dumps(bad), encoding="utf-8")
    with pytest.raises(DataError):
        load_sources(path)
    sources = dict(corpus[0])
    sources["S01"] = dict(sources["S01"], file="../../outside.md")
    with pytest.raises(DataError, match="vượt"):
        source_documents(tmp_path, sources, corpus[1])


def test_text_upload_and_chunks():
    chunks = extract_upload("bài học.md", ("Lịch sử Việt Nam.\n\n" + "x" * 3500).encode())
    assert len(chunks) == 4
    assert chunks[0][1] == "Lịch sử Việt Nam."


@pytest.mark.parametrize("name,content", [("a.txt", b""), ("a.txt", b"\xff"), ("a.exe", b"text"), ("a.pdf", b"not a pdf"), ("a.txt", b" \n "), ("a.txt", b"hello\x00world"), ("a.txt", b"a" * (5 * 1024 * 1024 + 1))], ids=["empty", "encoding", "extension", "invalid_pdf", "whitespace", "binary", "oversize"])
def test_bad_uploads(name, content):
    with pytest.raises(DataError):
        extract_upload(name, content)


def test_scan_and_encrypted_pdf_rejected():
    writer = PdfWriter()
    writer.add_blank_page(width=300, height=300)
    buffer = io.BytesIO()
    writer.write(buffer)
    with pytest.raises(DataError, match="scan"):
        extract_upload("scan.pdf", buffer.getvalue())
    writer.encrypt("test-password")
    buffer = io.BytesIO()
    writer.write(buffer)
    with pytest.raises(DataError, match="mật khẩu"):
        extract_upload("locked.pdf", buffer.getvalue())


def test_pdf_text_extracts_with_page_location():
    writer = PdfWriter()
    page = writer.add_blank_page(width=300, height=300)
    font = DictionaryObject({NameObject("/Type"): NameObject("/Font"), NameObject("/Subtype"): NameObject("/Type1"), NameObject("/BaseFont"): NameObject("/Helvetica")})
    page[NameObject("/Resources")] = DictionaryObject({NameObject("/Font"): DictionaryObject({NameObject("/F1"): writer._add_object(font)})})
    stream = DecodedStreamObject()
    stream.set_data(b"BT /F1 12 Tf 30 200 Td (Historical evidence for students 1945.) Tj ET")
    page[NameObject("/Contents")] = writer._add_object(stream)
    buffer = io.BytesIO()
    writer.write(buffer)
    chunks = extract_upload("text.pdf", buffer.getvalue())
    assert chunks[0][0] == "Trang 1"
    assert "Historical evidence" in chunks[0][1]
