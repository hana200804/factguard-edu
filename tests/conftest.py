import pytest

from src.loader import load_evaluation, load_facts, load_sources, source_documents
from src.retriever import Retriever
from src.utils import PROJECT_ROOT
from src.verifier import ProposedVerifier


@pytest.fixture(scope="session")
def corpus():
    base = PROJECT_ROOT / "data"
    sources = load_sources(base / "sources.json")
    facts = load_facts(base / "facts.csv", sources)
    docs = source_documents(base, sources, facts)
    return sources, facts, docs


@pytest.fixture(scope="session")
def facts(corpus):
    return corpus[1]


@pytest.fixture(scope="session")
def retriever(corpus):
    return Retriever(corpus[2])


@pytest.fixture(scope="session")
def verifier(facts, retriever):
    return ProposedVerifier(facts, retriever)


@pytest.fixture(scope="session")
def cases(facts):
    return load_evaluation(PROJECT_ROOT / "data" / "evaluation.csv", facts)
