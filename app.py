"""Run with: python -m streamlit run app.py"""
import streamlit as st

from src.claim_verifier import ClaimVerifier
from src.loader import DataError, load_evaluation, load_facts, load_sources, source_documents
from src.retriever import Retriever
from src.review import ReviewRepository
from src.storage import Store
from src.ui import (
    PAGE_NAMES,
    comparison_page,
    experiment_page,
    knowledge_page,
    load_style,
    methodology_page,
    overview,
    verify_page,
)
from src.utils import PROJECT_ROOT, runtime_dir

st.set_page_config(page_title="FactGuard EDU | Kiểm chứng để hiểu đúng", page_icon="🛡️", layout="wide")
load_style()

with st.sidebar:
    st.html('<div class="brand"><span class="brand-mark">F<span>✓</span></span><div><strong>FactGuard</strong><small>EDU / Lịch sử THPT</small></div></div>')
    st.caption("Không gian kiểm chứng")
    navigation = st.radio("Điều hướng", PAGE_NAMES, key="navigation", label_visibility="collapsed")
    st.divider()
    st.markdown("**Bằng chứng trước kết luận**")
    st.caption("Chạy trên máy của bạn.\nKhông cần API key hay GPU.")
    st.html('<div class="offline"><span></span> Sẵn sàng kiểm chứng offline</div>')

try:
    base = PROJECT_ROOT / "data"
    sources = load_sources(base / "sources.json")
    facts = load_facts(base / "facts.csv", sources)
    cases = load_evaluation(base / "evaluation.csv", facts)
    documents = source_documents(base, sources, facts)
    seed_facts = list(facts)
    seed_sources = dict(sources)
    runtime = runtime_dir()
    store = Store(runtime)
    repository = ReviewRepository(runtime)
    reviewed_facts, reviewed_sources, reviewed_documents = repository.approved()
    facts = facts + reviewed_facts
    sources = {**sources, **reviewed_sources}
    retriever = Retriever(documents + reviewed_documents + store.uploaded_documents())
    verifier = ClaimVerifier(facts, retriever)
except (DataError, OSError) as error:
    st.error(f"Không thể mở kho dữ liệu: {error}")
    st.info("Kiểm tra data/facts.csv, data/evaluation.csv, data/sources.json và quyền ghi thư mục runtime. Xem README.md để khôi phục dữ liệu.")
    st.stop()

if navigation == PAGE_NAMES[0]:
    report_dir = runtime / "research_v2"
    if not (report_dir / "latest.json").exists():
        report_dir = PROJECT_ROOT / "reports" / "research_v2"
    overview(facts, sources, cases, store, report_dir)
elif navigation == PAGE_NAMES[1]:
    verify_page(facts, verifier, store)
elif navigation == PAGE_NAMES[2]:
    knowledge_page(facts, sources, store, repository)
elif navigation == PAGE_NAMES[3]:
    comparison_page(facts, verifier)
elif navigation == PAGE_NAMES[4]:
    experiment_page(facts, documents, cases, runtime)
elif navigation == PAGE_NAMES[5]:
    methodology_page()
else:
    from src.research_ui import research_page

    research_page(seed_facts, seed_sources, cases.loc[cases["split"] == "development"].copy(), runtime, repository)

st.divider()
st.caption("FactGuard EDU · Hỗ trợ học tập Lịch sử THPT · Kết luận phụ thuộc phạm vi và chất lượng kho tham chiếu.")
