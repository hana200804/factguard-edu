import sqlite3

import pytest

from src.loader import DataError
from src.models import Document
from src.review import ReviewRepository


def create(repository):
    document = Document("upload-test", "Tài liệu thử nghiệm phần mềm", "Sự kiện kiểm thử diễn ra ngày 7/5/1954 tại địa điểm minh họa.", "Đoạn 1")
    return repository.create_draft(question="Sự kiện kiểm thử diễn ra ngày nào?", answer="7/5/1954", kind="date",
                                   canonical="1954-05-07", anchors=[["sự kiện kiểm thử"]], document=document,
                                   excerpt=document.text, author="Người kiểm thử", event_id="test_event")


def test_review_lifecycle_and_history(tmp_path):
    repository = ReviewRepository(tmp_path)
    identifier = create(repository)
    assert repository.approved()[0] == []
    with pytest.raises(DataError):
        repository.transition(identifier, state="approved", reviewer="", reason="Đã đọc.", confirmed=False)
    repository.transition(identifier, state="approved", reviewer="Người kiểm thử", reason="Đã đối chiếu đoạn văn thử.", confirmed=True)
    facts, sources, documents = repository.approved()
    assert len(facts) == 1 and documents[0].verified and sources
    repository.transition(identifier, state="withdrawn", reviewer="Người kiểm thử", reason="Thu hồi dữ liệu kiểm thử.", confirmed=True)
    assert not repository.approved()[0]
    assert len(repository.audit_export()) == 3 and repository.verify_audit()
    assert repository.records()[0]["revision"] == 3


def test_audit_modification_detected(tmp_path):
    repository = ReviewRepository(tmp_path)
    create(repository)
    with sqlite3.connect(repository.path) as con:
        con.execute("UPDATE audit SET payload='{}' WHERE id=1")
    assert not repository.verify_audit()
    with pytest.raises(DataError, match="nhật ký"):
        repository.approved()


def test_evidence_must_contain_value_and_be_original(tmp_path):
    repository = ReviewRepository(tmp_path)
    with pytest.raises(DataError, match="nguyên văn"):
        repository.create_draft(question="Ngày nào?", answer="1954", kind="year", canonical="1954", anchors=[["a"]],
                                document=Document("a", "b", "original text", "c"), excerpt="Invented source text that never existed", author="Tester", event_id="test")


def test_real_annotations_not_auto_filled(tmp_path):
    repository = ReviewRepository(tmp_path)
    assert repository.annotations() == []
    with pytest.raises(DataError, match="bằng chứng"):
        repository.annotate(case_id="C1", question="q", answer="a", reviewer="Reviewer", label="supported", evidence_ids=[], note="Đã đọc lại.", confirmed=True)
    repository.annotate(case_id="C1", question="q", answer="a", reviewer="Reviewer", label="supported", evidence_ids=["F001"], note="Đã đọc lại.", confirmed=True)
    repository.annotate(case_id="C1", question="q", answer="a", reviewer="Reviewer", label="contradicted", evidence_ids=["F001"], note="Đổi sau khi đọc lại.", confirmed=True)
    assert len(repository.annotations()) == 1
    assert len(repository.audit_export()) == 2
