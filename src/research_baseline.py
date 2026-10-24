"""A three-class learned lexical baseline fitted only on development labels."""
from time import perf_counter
from typing import Any, cast

import numpy as np
import pandas as pd
from rapidfuzz.fuzz import token_set_ratio
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from src.models import GOLD_LABELS, INSUFFICIENT, Document, Evidence, Fact, Verdict
from src.utils import normalize


class LexicalThreeWay:
    def __init__(self, facts: list[Fact], development: pd.DataFrame):
        if set(development["split"]) != {"development"}:
            raise ValueError("Đối chứng chỉ được huấn luyện bằng tập development.")
        if set(development["label"]) != set(GOLD_LABELS):
            raise ValueError("Development phải có đủ ba nhãn.")
        self.facts = [fact for fact in facts if fact.verified]
        if not self.facts:
            raise ValueError("Cần kho tham chiếu đã xác minh.")
        self.vectorizer = TfidfVectorizer(preprocessor=normalize, analyzer="char_wb", ngram_range=(3, 5))
        self.vectorizer.fit([f.question + " " + f.reference + " " + f.answer for f in self.facts])
        self.question_matrix = self.vectorizer.transform([f.question for f in self.facts])
        self.reference_matrix = self.vectorizer.transform([f.reference for f in self.facts])
        rows = cast(Any, development).to_dict("records")
        features = [self.features(row["question"], row["answer"])[0] for row in rows]
        self.model = make_pipeline(StandardScaler(), LogisticRegression(C=1.0, class_weight="balanced",
                                                                        max_iter=1000, random_state=20261024))
        self.model.fit(np.asarray(features), [row["label"] for row in rows])
        self.training_ids = [row["id"] for row in rows]

    def features(self, question: str, answer: str) -> tuple[list[float], Fact]:
        q = self.vectorizer.transform([question])
        scores = cosine_similarity(q, self.question_matrix).ravel()
        index = int(np.argmax(scores))
        fact = self.facts[index]
        words = set(normalize(answer).split())
        reference_words = set(normalize(fact.reference).split())
        vector = self.vectorizer.transform([answer])
        features = [token_set_ratio(normalize(question), normalize(fact.question)) / 100,
                    max(token_set_ratio(normalize(answer), normalize(alias)) for alias in fact.aliases) / 100,
                    float(cosine_similarity(vector, self.reference_matrix[index:index + 1])[0, 0]),
                    float(scores[index]), min(len(words), 100) / 100,
                    len(words & reference_words) / max(1, len(words))]
        return features, fact

    def verify(self, question: str, answer: str) -> Verdict:
        started = perf_counter()
        if not question.strip() or not answer.strip():
            return Verdict(INSUFFICIENT, "Thiếu đầu vào.", method="lexical_3way")
        features, fact = self.features(question, answer)
        prediction = str(self.model.predict(np.asarray([features]))[0])
        return Verdict(prediction, "Đối chứng Logistic Regression ba nhãn dựa trên đặc trưng từ vựng; chưa phân tích quan hệ hay mệnh đề.",
                       evidence=(Evidence(Document(fact.id, fact.source_id, fact.reference, fact.location, verified=True), features[3]),),
                       method="lexical_3way", elapsed_ms=(perf_counter() - started) * 1000,
                       metadata={"nearest_fact": fact.id, "features": features, "training_split": "development"})

    def manifest(self) -> dict:
        classifier = self.model.named_steps["logisticregression"]
        return {"training_ids": self.training_ids, "classes": classifier.classes_.tolist(),
                "coefficients": classifier.coef_.tolist(), "intercept": classifier.intercept_.tolist(),
                "C": 1.0, "class_weight": "balanced", "random_state": 20261024}
