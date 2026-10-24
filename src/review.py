"""Versioned local human review; never promotes an upload without an explicit review."""
import json
import sqlite3
import uuid
from pathlib import Path
from urllib.parse import urlparse

from src.claim_spans import date_spans
from src.loader import DataError
from src.models import GOLD_LABELS, Document, Fact
from src.utils import digest_bytes, normalize, utc_now


def stable_json(value) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def content_hash(question: str, answer: str) -> str:
    return digest_bytes(stable_json([question, answer]).encode("utf-8"))


class ReviewRepository:
    def __init__(self, root: Path):
        root.mkdir(parents=True, exist_ok=True)
        self.path = root / "research.sqlite3"
        with self.connect() as con:
            con.executescript("""
                CREATE TABLE IF NOT EXISTS drafts (
                  id TEXT PRIMARY KEY, payload TEXT NOT NULL, state TEXT NOT NULL, revision INTEGER NOT NULL);
                CREATE TABLE IF NOT EXISTS audit (
                  id INTEGER PRIMARY KEY, object_id TEXT NOT NULL, payload TEXT NOT NULL,
                  created_at TEXT NOT NULL, previous_hash TEXT NOT NULL, event_hash TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS annotations (
                  case_id TEXT NOT NULL, content_hash TEXT NOT NULL, reviewer_key TEXT NOT NULL,
                  payload TEXT NOT NULL, PRIMARY KEY(case_id, content_hash, reviewer_key));
                CREATE TABLE IF NOT EXISTS review_cases (
                  id TEXT PRIMARY KEY, content_hash TEXT UNIQUE NOT NULL, payload TEXT NOT NULL);
            """)

    def connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path, timeout=10)
        connection.row_factory = sqlite3.Row
        return connection

    @staticmethod
    def _append(con: sqlite3.Connection, object_id: str, payload: dict) -> None:
        prior = con.execute("SELECT event_hash FROM audit ORDER BY id DESC LIMIT 1").fetchone()
        previous = prior[0] if prior else "GENESIS"
        timestamp = utc_now()
        serialized = stable_json(payload)
        event_hash = digest_bytes(stable_json([previous, object_id, timestamp, serialized]).encode("utf-8"))
        con.execute("INSERT INTO audit(object_id,payload,created_at,previous_hash,event_hash) VALUES(?,?,?,?,?)",
                    (object_id, serialized, timestamp, previous, event_hash))

    def verify_audit(self) -> bool:
        previous = "GENESIS"
        latest = {}
        with self.connect() as con:
            for row in con.execute("SELECT * FROM audit ORDER BY id"):
                expected = digest_bytes(stable_json([previous, row["object_id"], row["created_at"], row["payload"]]).encode("utf-8"))
                if row["previous_hash"] != previous or row["event_hash"] != expected:
                    return False
                previous = row["event_hash"]
                event = json.loads(row["payload"])
                if event.get("action") in {"create", "approved", "rejected", "withdrawn"}:
                    latest[row["object_id"]] = event
            stored = {row["id"]: row for row in con.execute("SELECT * FROM drafts")}
            if stored.keys() != latest.keys():
                return False
            for identifier, event in latest.items():
                row = stored[identifier]
                state = "draft" if event["action"] == "create" else event["action"]
                if row["payload"] != stable_json(event["record"]) or row["state"] != state or row["revision"] != event["revision"]:
                    return False
        return True

    def create_draft(self, *, question: str, answer: str, kind: str, canonical: str,
                     anchors: list[list[str]], document: Document, excerpt: str,
                     author: str, event_id: str, url: str = "") -> str:
        if not all(text.strip() for text in [question, answer, canonical, excerpt, author, event_id]):
            raise DataError("Điền đầy đủ câu hỏi, đáp án, giá trị chuẩn, bằng chứng, người tạo và sự kiện.")
        if kind not in {"date", "year", "person", "place"}:
            raise DataError("Loại dữ kiện không hợp lệ.")
        if len(excerpt.strip()) < 20 or excerpt not in document.text:
            raise DataError("Bằng chứng cần ít nhất 20 ký tự và phải là đoạn nguyên văn có trong tài liệu đã chọn.")
        if not anchors or any(not group or any(not alias.strip() for alias in group) for group in anchors):
            raise DataError("Cần các nhóm neo sự kiện không rỗng.")
        if url and (urlparse(url).scheme not in {"http", "https"} or not urlparse(url).hostname):
            raise DataError("URL nguồn phải là http/https hợp lệ, hoặc để trống với tài liệu cục bộ.")
        if kind in {"date", "year"}:
            values, invalid = date_spans(excerpt)
            if invalid or not any(v.canonical == canonical or kind == "year" and v.canonical[:4] == canonical for v in values):
                raise DataError("Giá trị ngày/năm chuẩn phải xuất hiện trong bằng chứng và có định dạng hợp lệ.")
            answers, invalid_answer = date_spans(answer)
            if invalid_answer or not any(v.canonical == canonical or kind == "year" and v.canonical[:4] == canonical for v in answers):
                raise DataError("Đáp án hiển thị phải khớp giá trị ngày/năm chuẩn.")
        elif normalize(canonical) not in normalize(excerpt) or normalize(answer) not in normalize(excerpt):
            raise DataError("Tên riêng và đáp án phải xuất hiện trong đoạn bằng chứng.")
        identifier = "U" + uuid.uuid4().hex[:12]
        payload = {"id": identifier, "question": question.strip(), "answer": answer.strip(), "kind": kind,
                   "canonical": canonical.strip(), "anchors": anchors, "event_id": normalize(event_id).replace(" ", "_"),
                   "reference": excerpt, "source_id": "review-" + identifier, "location": document.location,
                   "document_id": document.id, "document_title": document.title, "url": url,
                   "document_sha256": digest_bytes(document.text.encode("utf-8")), "document_snapshot": document.text,
                   "author": author.strip(), "created_at": utc_now()}
        with self.connect() as con:
            con.execute("BEGIN IMMEDIATE")
            con.execute("INSERT INTO drafts VALUES(?,?,?,?)", (identifier, stable_json(payload), "draft", 1))
            self._append(con, identifier, {"action": "create", "revision": 1, "record": payload})
        return identifier

    def transition(self, identifier: str, *, state: str, reviewer: str, reason: str,
                   confirmed: bool, existing_facts: list[Fact] | None = None) -> None:
        if state not in {"approved", "rejected", "withdrawn"}:
            raise DataError("Trạng thái duyệt không hợp lệ.")
        if not confirmed or not reviewer.strip() or len(reason.strip()) < 5:
            raise DataError("Cần người duyệt, lý do và xác nhận đã trực tiếp đọc nguồn.")
        if not self.verify_audit():
            raise DataError("Nhật ký thẩm định không khớp chuỗi hash; dừng duyệt để kiểm tra.")
        with self.connect() as con:
            con.execute("BEGIN IMMEDIATE")
            row = con.execute("SELECT * FROM drafts WHERE id=?", (identifier,)).fetchone()
            if row is None:
                raise DataError("Không tìm thấy bản nháp.")
            if state == "withdrawn" and row["state"] != "approved" or state != "withdrawn" and row["state"] != "draft":
                raise DataError("Chỉ duyệt/từ chối bản nháp, hoặc thu hồi dữ kiện đã duyệt.")
            payload = json.loads(row["payload"])
            if state == "approved":
                candidates = existing_facts or []
                if any(normalize(f.question) == normalize(payload["question"]) for f in candidates):
                    raise DataError("Câu hỏi chuẩn đã tồn tại; không tạo đáp án cạnh tranh mà chưa đối chiếu xung đột.")
                if not all(any(normalize(alias) in normalize(payload["question"]) for alias in group)
                           for group in payload["anchors"]):
                    raise DataError("Câu hỏi chuẩn phải chứa ít nhất một cụm ở mỗi nhóm neo.")
            revision = row["revision"] + 1
            payload.update(reviewer=reviewer.strip(), review_reason=reason.strip(), reviewed_at=utc_now())
            con.execute("UPDATE drafts SET payload=?,state=?,revision=? WHERE id=?",
                        (stable_json(payload), state, revision, identifier))
            self._append(con, identifier, {"action": state, "revision": revision, "record": payload})

    def records(self) -> list[dict]:
        with self.connect() as con:
            return [{**json.loads(row["payload"]), "state": row["state"], "revision": row["revision"]}
                    for row in con.execute("SELECT * FROM drafts ORDER BY rowid DESC")]

    def approved(self) -> tuple[list[Fact], dict[str, dict], list[Document]]:
        if not self.verify_audit():
            raise DataError("Chuỗi nhật ký nguồn bị thay đổi; dữ kiện duyệt không được nạp.")
        facts, sources, documents = [], {}, []
        for row in self.records():
            if row["state"] != "approved":
                continue
            facts.append(Fact(row["id"], "Tài liệu do người dùng thẩm định", row["event_id"], row["question"],
                              row["answer"], row["kind"], row["canonical"], (row["answer"], row["canonical"]),
                              tuple(tuple(group) for group in row["anchors"]), row["reference"], row["source_id"], row["location"], True))
            sources[row["source_id"]] = {"id": row["source_id"], "title": row["document_title"], "url": row["url"],
                                          "publisher": "Người dùng tự thẩm định", "verified": True,
                                          "checked_at": row["reviewed_at"][:10], "reviewer": row["reviewer"],
                                          "verification_method": "Tự khai người duyệt; chưa xác thực danh tính", "runtime": True,
                                          "text": row["document_snapshot"]}
            documents.append(Document(row["id"], row["document_title"], row["reference"], row["location"], row["url"], True))
        return facts, sources, documents

    def annotate(self, *, case_id: str, question: str, answer: str, reviewer: str,
                 label: str, evidence_ids: list[str], note: str, confirmed: bool) -> None:
        if label not in GOLD_LABELS or not reviewer.strip() or len(note.strip()) < 5 or not confirmed:
            raise DataError("Cần người gán nhãn, nhãn hợp lệ, ghi chú và xác nhận đã kiểm tra nguồn.")
        if label in {"supported", "contradicted"} and not evidence_ids:
            raise DataError("Nhãn hỗ trợ/mâu thuẫn cần ID dữ kiện làm bằng chứng.")
        payload = {"case_id": case_id, "question": question, "answer": answer, "content_hash": content_hash(question, answer),
                   "reviewer": reviewer.strip(), "label": label, "evidence_ids": evidence_ids,
                   "note": note.strip(), "created_at": utc_now()}
        key = normalize(reviewer)
        with self.connect() as con:
            con.execute("BEGIN IMMEDIATE")
            con.execute("INSERT INTO annotations VALUES(?,?,?,?) ON CONFLICT(case_id,content_hash,reviewer_key) DO UPDATE SET payload=excluded.payload",
                        (case_id, payload["content_hash"], key, stable_json(payload)))
            self._append(con, case_id, {"action": "annotate", "record": payload})

    def annotations(self) -> list[dict]:
        with self.connect() as con:
            return [json.loads(row[0]) for row in con.execute("SELECT payload FROM annotations ORDER BY case_id,reviewer_key")]

    def add_case(self, *, question: str, answer: str, origin: str, submitter: str, event_id: str) -> str:
        if not all(value.strip() for value in [question, answer, origin, submitter, event_id]):
            raise DataError("Cần câu hỏi, câu trả lời, nguồn gốc, người thu thập và mã sự kiện.")
        if max(len(question), len(answer)) > 12000:
            raise DataError("Ca thu thập vượt giới hạn 12.000 ký tự.")
        identifier = "H" + uuid.uuid4().hex[:12]
        signature = content_hash(question, answer)
        payload = {"id": identifier, "question": question, "answer": answer, "origin": origin,
                   "submitter": submitter, "event_id": event_id, "content_hash": signature, "created_at": utc_now()}
        try:
            with self.connect() as con:
                con.execute("BEGIN IMMEDIATE")
                con.execute("INSERT INTO review_cases VALUES(?,?,?)", (identifier, signature, stable_json(payload)))
                self._append(con, identifier, {"action": "collect_case", "record": payload})
        except sqlite3.IntegrityError as error:
            raise DataError("Cặp câu hỏi/câu trả lời đã được thu thập.") from error
        return identifier

    def collected_cases(self) -> list[dict]:
        with self.connect() as con:
            return [json.loads(row[0]) for row in con.execute("SELECT payload FROM review_cases ORDER BY rowid")]

    def audit_export(self) -> list[dict]:
        with self.connect() as con:
            return [dict(row) for row in con.execute("SELECT * FROM audit ORDER BY id")]
