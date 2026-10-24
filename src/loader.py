import io
import json
from pathlib import Path
from urllib.parse import urlparse

import pandas as pd
from pypdf import PdfReader

from src.models import GOLD_LABELS, Document, Fact
from src.utils import normalize

FACT_COLUMNS = {
    "id", "topic", "event_id", "question", "answer", "kind", "canonical", "aliases",
    "anchors", "reference", "source_id", "location", "verified",
}
EVALUATION_COLUMNS = {"id", "fact_id", "event_id", "question", "answer", "label", "group", "split", "origin"}
MAX_UPLOAD_BYTES = 5 * 1024 * 1024


class DataError(ValueError):
    """An actionable, user-facing data validation error."""


def read_csv(path: Path, required: set[str]) -> pd.DataFrame:
    try:
        frame = pd.read_csv(path, dtype=str, keep_default_na=False, encoding="utf-8-sig")
    except (OSError, pd.errors.ParserError, pd.errors.EmptyDataError, UnicodeError) as error:
        raise DataError(f"Không đọc được CSV {path.name}: {error}") from error
    missing = required - set(frame.columns)
    if missing:
        raise DataError("Thiếu các cột: " + ", ".join(sorted(missing)))
    if frame.empty:
        raise DataError(f"{path.name} chưa có dữ liệu.")
    for column in required:
        if frame[column].str.strip().eq("").any():
            raise DataError(f"Cột {column} có ô trống.")
    if frame["id"].duplicated().any():
        raise DataError("ID bị trùng; mỗi bản ghi cần một ID riêng.")
    return frame


def load_sources(path: Path) -> dict[str, dict]:
    try:
        rows = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        raise DataError(f"Không đọc được danh mục nguồn: {error}") from error
    if not isinstance(rows, list):
        raise DataError("Danh mục nguồn phải là một danh sách JSON.")
    result = {}
    for row in rows:
        if not isinstance(row, dict) or not {"id", "title", "url", "verified", "checked_at", "file"} <= row.keys():
            raise DataError("Nguồn thiếu trường bắt buộc.")
        if not isinstance(row["verified"], bool):
            raise DataError("Trạng thái nguồn phải là true hoặc false.")
        if row["id"] in result:
            raise DataError("ID nguồn bị trùng.")
        url = urlparse(row["url"])
        if row["verified"] and (url.scheme not in {"https", "http"} or not url.hostname or not row["checked_at"]):
            raise DataError("Nguồn đã xác minh phải có URL và ngày kiểm tra.")
        result[row["id"]] = row
    return result


def load_facts(path: Path, sources: dict[str, dict]) -> list[Fact]:
    frame = read_csv(path, FACT_COLUMNS)
    if frame["question"].map(normalize).duplicated().any():
        raise DataError("Câu hỏi chuẩn bị trùng sau khi chuẩn hóa.")
    result = []
    for row in frame.to_dict("records"):
        if row["kind"] not in {"date", "year", "person", "place"}:
            raise DataError(f"Loại dữ kiện không hợp lệ: {row['kind']}")
        if row["verified"].lower() not in {"true", "false"}:
            raise DataError("verified chỉ nhận true hoặc false.")
        source = sources.get(row["source_id"])
        if source is None:
            raise DataError(f"Không tìm thấy nguồn {row['source_id']}.")
        verified = row["verified"].lower() == "true"
        if verified and not source["verified"]:
            raise DataError("Không thể đánh dấu dữ kiện đã xác minh khi nguồn chưa xác minh.")
        try:
            aliases = json.loads(row["aliases"])
            anchors = json.loads(row["anchors"])
        except ValueError as error:
            raise DataError("aliases và anchors phải là JSON hợp lệ.") from error
        if not isinstance(aliases, list) or not aliases or not all(isinstance(x, str) and x.strip() for x in aliases):
            raise DataError("aliases phải là danh sách tên/đáp án không rỗng.")
        if not isinstance(anchors, list) or not anchors or not all(
            isinstance(g, list) and g and all(isinstance(x, str) and x.strip() for x in g) for g in anchors
        ):
            raise DataError("anchors cần các nhóm cụm từ không rỗng.")
        if row["kind"] == "date":
            from datetime import date

            try:
                date.fromisoformat(row["canonical"])
            except ValueError as error:
                raise DataError("Ngày chuẩn phải theo YYYY-MM-DD và tồn tại.") from error
        result.append(Fact(**{k: str(row[k]) for k in FACT_COLUMNS - {"aliases", "anchors", "verified"}},
                           aliases=tuple(aliases), anchors=tuple(tuple(g) for g in anchors), verified=verified))
    return result


def load_evaluation(path: Path, facts: list[Fact]) -> pd.DataFrame:
    frame = read_csv(path, EVALUATION_COLUMNS)
    if not set(frame["label"]) <= set(GOLD_LABELS):
        raise DataError("Nhãn đánh giá không hợp lệ.")
    if not set(frame["split"]) <= {"development", "evaluation"}:
        raise DataError("split chỉ nhận development hoặc evaluation.")
    fact_map = {fact.id: fact for fact in facts}
    for row in frame.to_dict("records"):
        if row["fact_id"] != "OUTSIDE":
            fact = fact_map.get(row["fact_id"])
            if fact is None or not fact.verified:
                raise DataError("Ca kiểm thử phải tham chiếu dữ kiện đã kiểm tra nguồn.")
            if fact.event_id != row["event_id"]:
                raise DataError("event_id không khớp dữ kiện.")
    if frame.duplicated(["question", "answer"]).any():
        raise DataError("Ca đánh giá bị trùng câu hỏi và câu trả lời.")
    dev_events = set(frame.loc[frame["split"] == "development", "event_id"])
    test_events = set(frame.loc[frame["split"] == "evaluation", "event_id"])
    if dev_events & test_events:
        raise DataError("Một sự kiện xuất hiện ở cả tập phát triển và tập đánh giá.")
    return frame


def source_documents(base: Path, sources: dict[str, dict], facts: list[Fact]) -> list[Document]:
    docs = []
    for fact in facts:
        source = sources[fact.source_id]
        docs.append(Document(fact.id, source["title"], fact.reference, fact.location,
                             source["url"], fact.verified and source["verified"]))
    for source in sources.values():
        path = (base / "sources" / source["file"]).resolve()
        if not path.is_relative_to((base / "sources").resolve()):
            raise DataError("Đường dẫn tài liệu vượt thư mục sources.")
        try:
            content = path.read_text(encoding="utf-8")
        except OSError as error:
            raise DataError(f"Thiếu bản tóm lược nguồn {source['id']}.") from error
        docs.append(Document(source["id"], source["title"], content, "Bản tóm lược cục bộ",
                             source["url"], source["verified"]))
    return docs


def extract_upload(name: str, content: bytes) -> list[tuple[str, str]]:
    """Return (location, text) pairs; image PDFs are never reported as successful."""
    if not content:
        raise DataError("Tệp rỗng. Hãy chọn tệp có nội dung.")
    if len(content) > MAX_UPLOAD_BYTES:
        raise DataError("Tệp vượt giới hạn 5 MB.")
    suffix = Path(name).suffix.lower()
    if suffix in {".txt", ".md", ".markdown"}:
        try:
            text = content.decode("utf-8-sig")
        except UnicodeError as error:
            raise DataError("Tệp văn bản cần lưu ở UTF-8.") from error
        if "\x00" in text or not text.strip():
            raise DataError("Tệp không có văn bản hợp lệ.")
        paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
        return [(f"Đoạn {i + 1}", p[j:j + 1600]) for i, p in enumerate(paragraphs)
                for j in range(0, len(p), 1600)]
    if suffix != ".pdf":
        raise DataError("Chỉ nhận TXT, Markdown và PDF dạng văn bản.")
    try:
        reader = PdfReader(io.BytesIO(content), strict=True)
        if reader.is_encrypted:
            raise DataError("PDF có mật khẩu; hãy tải bản đã mở khóa.")
        if len(reader.pages) > 100:
            raise DataError("PDF vượt 100 trang; hãy chia thành các tệp nhỏ.")
        pages = [(f"Trang {i + 1}", page.extract_text() or "") for i, page in enumerate(reader.pages)]
    except DataError:
        raise
    except Exception as error:
        raise DataError("PDF không hợp lệ hoặc không đọc được. Hãy kiểm tra lại tệp.") from error
    if not any(len(text.strip()) >= 20 for _, text in pages):
        raise DataError("Không trích xuất được văn bản: PDF có thể là ảnh scan. Phiên bản này chưa có OCR.")
    return [(loc, text[j:j + 1600]) for loc, text in pages if text.strip()
            for j in range(0, len(text), 1600)]
