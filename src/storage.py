import json
import sqlite3
from pathlib import Path

from src.loader import DataError, extract_upload
from src.models import Document, Verdict
from src.utils import atomic_json, digest_bytes, utc_now


class Store:
    """Local operational data. Experiment runs do not inflate real verification count."""

    def __init__(self, root: Path):
        self.root = root
        root.mkdir(parents=True, exist_ok=True)
        self.database = root / "history.sqlite3"
        with self.connect() as connection:
            connection.execute("CREATE TABLE IF NOT EXISTS checks (id INTEGER PRIMARY KEY, created_at TEXT, question TEXT, answer TEXT, verdict TEXT)")

    def connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.database, timeout=10)

    def log(self, question: str, answer: str, verdict: Verdict) -> int:
        with self.connect() as connection:
            cursor = connection.execute("INSERT INTO checks (created_at, question, answer, verdict) VALUES (?,?,?,?)",
                                        (utc_now(), question, answer, json.dumps(verdict.to_dict(), ensure_ascii=False)))
            return int(cursor.lastrowid or 0)

    def count(self) -> int:
        with self.connect() as connection:
            return int(connection.execute("SELECT COUNT(*) FROM checks").fetchone()[0])

    def history(self, limit: int = 30) -> list[dict]:
        with self.connect() as connection:
            connection.row_factory = sqlite3.Row
            return [dict(row) for row in connection.execute("SELECT * FROM checks ORDER BY id DESC LIMIT ?", (limit,))]

    def import_document(self, name: str, content: bytes) -> int:
        chunks = extract_upload(name, content)
        digest = digest_bytes(content)
        destination = self.root / "uploads" / f"{digest}.json"
        if destination.exists():
            raise DataError("Tài liệu này đã có trong kho (trùng nội dung SHA-256).")
        atomic_json(destination, {"id": digest, "title": Path(name).name, "sha256": digest,
                                  "imported_at": utc_now(), "verified": False, "chunks": chunks})
        return len(chunks)

    def uploaded_documents(self) -> list[Document]:
        documents = []
        for path in sorted((self.root / "uploads").glob("*.json")):
            try:
                row = json.loads(path.read_text(encoding="utf-8"))
                for i, (location, text) in enumerate(row["chunks"]):
                    documents.append(Document(f"upload-{row['id']}-{i}", row["title"], text, location, verified=False))
            except (OSError, ValueError, KeyError, TypeError) as error:
                raise DataError(f"Tệp chỉ mục {path.name} bị lỗi; hãy kiểm tra hoặc nhập lại tài liệu.") from error
        return documents
