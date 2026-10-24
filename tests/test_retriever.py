from src.models import Document
from src.retriever import Retriever, match_facts, question_kind
from src.utils import normalize


def test_retrieves_relevant_evidence_accent_insensitive(retriever):
    hits = retriever.search("chien dich Dien Bien Phu ket thuc")
    assert hits
    assert any("Điện Biên Phủ" in hit.document.text for hit in hits)
    assert all(0 <= hit.similarity <= 1 for hit in hits)
    assert list(hits) == sorted(hits, key=lambda h: (-h.similarity, h.document.id))


def test_empty_and_oov_are_safe():
    assert Retriever([]).search("1945") == ()
    retriever = Retriever([Document("one", "", "1945", "line1")])
    assert retriever.search("") == ()
    assert retriever.search("zyxqu") == ()
    assert retriever.search("1945", top_k=0) == ()


def test_intent_and_anchor_are_required(facts):
    assert question_kind("Vì sao Điện Biên Phủ quan trọng?") is None
    assert question_kind("Ai chỉ huy chiến dịch Điện Biên Phủ?") == "person"
    assert question_kind("Tuyên ngôn Độc lập được đọc năm nào?") == "year"
    assert not match_facts("Chiến dịch Biên giới kết thúc vào ngày nào?", facts)
    assert len(match_facts("Chiến dịch Điện Biên Phủ kết thúc vào ngày nào?", facts)) == 1
    assert normalize("Độc Lập") == "doc lap"
