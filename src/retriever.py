from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from src.models import Document, Evidence, Fact
from src.utils import contains_phrase, normalize


class Retriever:
    """Local TF-IDF retrieval. Similarity ranks text; it is never a truth probability."""

    def __init__(self, documents: list[Document]):
        self.documents = tuple(documents)
        self.vectorizer = TfidfVectorizer(preprocessor=normalize, ngram_range=(1, 2), sublinear_tf=True)
        texts = [f"{doc.title} {doc.text}" for doc in documents]
        self.matrix = self.vectorizer.fit_transform(texts) if any(normalize(t) for t in texts) else None

    def search(self, query: str, top_k: int = 4) -> tuple[Evidence, ...]:
        if self.matrix is None or not normalize(query) or top_k <= 0:
            return ()
        scores = cosine_similarity(self.vectorizer.transform([query]), self.matrix).ravel()
        indices = sorted(range(len(scores)), key=lambda i: (-scores[i], self.documents[i].id))
        return tuple(Evidence(self.documents[i], round(float(scores[i]), 6))
                     for i in indices[:top_k] if scores[i] > 0)


def question_kind(question: str) -> str | None:
    text = normalize(question)
    if any(contains_phrase(text, p) for p in ["vi sao", "tai sao", "y nghia", "phan tich", "danh gia", "so sanh"]):
        return None
    if contains_phrase(text, "nam nao") and not contains_phrase(text, "ngay thang nam nao"):
        return "year"
    if any(contains_phrase(text, p) for p in ["ngay nao", "khi nao", "ngay thang nam nao", "thoi gian nao"]):
        return "date"
    if any(contains_phrase(text, p) for p in ["o dau", "noi nao", "dia diem nao", "tinh nao", "thanh pho nao"]):
        return "place"
    if contains_phrase(text, "ai") or contains_phrase(text, "nhan vat nao"):
        return "person"
    return None


def match_facts(question: str, facts: list[Fact]) -> list[Fact]:
    """Require intent plus every anchor group, independent of submitted answer."""
    kind = question_kind(question)
    if kind is None:
        return []
    matches = [fact for fact in facts if (fact.kind == kind or kind == "year" and fact.kind == "date")
               and all(any(contains_phrase(question, alias) for alias in group) for group in fact.anchors)]
    return matches
