import pytest

from src.loader import DataError
from src.storage import Store


def test_real_history_count_and_import_are_separate(tmp_path, verifier):
    store = Store(tmp_path)
    assert store.count() == 0
    result = verifier.verify("Ai chỉ huy chiến dịch Điện Biên Phủ?", "Võ Nguyên Giáp")
    store.log("question", "answer", result)
    assert store.count() == 1
    assert len(store.history()) == 1
    store.import_document("../../../history.txt", "Tài liệu lịch sử chưa xác minh nguồn.".encode())
    assert store.count() == 1
    documents = store.uploaded_documents()
    assert documents and not any(d.verified for d in documents)
    assert all(p.parent == tmp_path / "uploads" for p in (tmp_path / "uploads").glob("*.json"))
    with pytest.raises(DataError, match="trùng"):
        store.import_document("renamed.txt", "Tài liệu lịch sử chưa xác minh nguồn.".encode())
