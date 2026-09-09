import streamlit as st
from dotenv import load_dotenv

from document_processor import extract_text, create_chunks
from rag_engine import RAGEngine


# =========================================================
# CONFIGURATION
# =========================================================

load_dotenv()

st.set_page_config(
    page_title="Enterprise Knowledge Copilot",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)


# =========================================================
# CUSTOM CSS
# =========================================================

st.markdown(
    """
<style>
.stApp {
    background-color: #f8fafc;
}

.block-container {
    max-width: 1250px;
    padding-top: 2rem;
    padding-bottom: 3rem;
}

.hero {
    background: linear-gradient(135deg, #0f172a, #1e293b, #334155);
    padding: 2.2rem;
    border-radius: 20px;
    color: white;
    margin-bottom: 1.5rem;
    box-shadow: 0 8px 25px rgba(15, 23, 42, 0.15);
}

.hero-title {
    font-size: 2.2rem;
    font-weight: 750;
    margin-bottom: 0.5rem;
}

.hero-subtitle {
    font-size: 1rem;
    color: #cbd5e1;
    line-height: 1.6;
}

.status-badge {
    display: inline-block;
    margin-top: 1rem;
    padding: 0.4rem 0.9rem;
    border-radius: 999px;
    background: rgba(255,255,255,0.12);
    color: #e2e8f0;
    font-size: 0.82rem;
}

.metric-card {
    background: white;
    border: 1px solid #e2e8f0;
    border-radius: 16px;
    padding: 1.2rem;
    text-align: center;
    box-shadow: 0 3px 12px rgba(15, 23, 42, 0.05);
}

.metric-number {
    font-size: 1.8rem;
    font-weight: 750;
    color: #0f172a;
}

.metric-label {
    font-size: 0.85rem;
    color: #64748b;
    margin-top: 0.25rem;
}

.section-title {
    font-size: 1.25rem;
    font-weight: 700;
    color: #0f172a;
    margin-top: 1.2rem;
    margin-bottom: 0.7rem;
}

.source-card {
    background: white;
    border: 1px solid #e2e8f0;
    border-radius: 12px;
    padding: 0.9rem 1rem;
    margin-bottom: 0.6rem;
    box-shadow: 0 2px 8px rgba(15, 23, 42, 0.04);
}

.empty-state {
    background: white;
    border: 1px dashed #cbd5e1;
    border-radius: 18px;
    padding: 2.5rem;
    text-align: center;
    margin-top: 1.5rem;
}

.empty-icon {
    font-size: 2.5rem;
}

.empty-title {
    font-size: 1.2rem;
    font-weight: 700;
    color: #0f172a;
    margin-top: 0.6rem;
}

.empty-text {
    color: #64748b;
    margin-top: 0.4rem;
}

section[data-testid="stSidebar"] {
    background-color: #ffffff;
    border-right: 1px solid #e2e8f0;
}

.stButton > button {
    border-radius: 10px;
    font-weight: 600;
}
</style>
""",
    unsafe_allow_html=True
)


# =========================================================
# SESSION STATE
# =========================================================

if "rag" not in st.session_state:
    st.session_state.rag = RAGEngine()

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

if "documents" not in st.session_state:
    st.session_state.documents = []


# =========================================================
# HERO HEADER
# =========================================================

hero_html = """
<div class="hero">
<div class="hero-title">🤖 Enterprise Knowledge Copilot</div>
<div class="hero-subtitle">
AI-powered enterprise knowledge assistant for document-based
question answering, summarization, comparison and decision support.
</div>
<div class="status-badge">🟢 RAG Knowledge System Online</div>
</div>
"""

st.markdown(
    hero_html,
    unsafe_allow_html=True
)


# =========================================================
# METRICS
# =========================================================

documents_count = len(
    st.session_state.documents
)

chunks_count = len(
    st.session_state.rag.embeddings
)

questions_count = len(
    [
        message
        for message in st.session_state.chat_history
        if message["role"] == "user"
    ]
)


col1, col2, col3 = st.columns(3)


with col1:

    st.markdown(
        f"""
<div class="metric-card">
<div class="metric-number">{documents_count}</div>
<div class="metric-label">📄 Documents</div>
</div>
""",
        unsafe_allow_html=True
    )


with col2:

    st.markdown(
        f"""
<div class="metric-card">
<div class="metric-number">{chunks_count}</div>
<div class="metric-label">🧩 Knowledge Chunks</div>
</div>
""",
        unsafe_allow_html=True
    )


with col3:

    st.markdown(
        f"""
<div class="metric-card">
<div class="metric-number">{questions_count}</div>
<div class="metric-label">💬 Questions Asked</div>
</div>
""",
        unsafe_allow_html=True
    )


st.markdown("<br>", unsafe_allow_html=True)


# =========================================================
# SIDEBAR
# =========================================================

with st.sidebar:

    st.header("📚 Knowledge Base")

    st.caption(
        "Upload enterprise documents and build "
        "your searchable AI knowledge base."
    )

    uploaded_files = st.file_uploader(
        "Upload Documents",
        type=["pdf", "docx", "txt"],
        accept_multiple_files=True
    )


    # -----------------------------------------------------
    # PROCESS DOCUMENTS
    # -----------------------------------------------------

    if st.button(
        "🚀 Process Documents",
        use_container_width=True
    ):

        if not uploaded_files:

            st.warning(
                "Please upload at least one document."
            )

        else:

            progress = st.progress(0)

            total_files = len(uploaded_files)

            processed_count = 0
            skipped_count = 0


            for file_number, file in enumerate(
                uploaded_files,
                start=1
            ):

                try:

                    if file.name in st.session_state.documents:

                        skipped_count += 1

                        st.info(
                            f"⏭️ {file.name} already processed."
                        )

                    else:

                        text = extract_text(file)

                        chunks = create_chunks(
                            text
                        )

                        metadata = []


                        for chunk_number, chunk in enumerate(
                            chunks,
                            start=1
                        ):

                            metadata.append(
                                {
                                    "text": chunk,
                                    "source": file.name,
                                    "chunk_id": chunk_number
                                }
                            )


                        st.session_state.rag.add_documents(
                            metadata
                        )


                        st.session_state.documents.append(
                            file.name
                        )


                        processed_count += 1


                except Exception as e:

                    st.error(
                        f"❌ {file.name}: {e}"
                    )


                progress.progress(
                    file_number / total_files
                )


            if processed_count > 0:

                st.success(
                    f"✅ {processed_count} document(s) processed successfully."
                )


            if skipped_count > 0:

                st.info(
                    f"⏭️ {skipped_count} duplicate document(s) skipped."
                )


    st.divider()


    # -----------------------------------------------------
    # DOCUMENT LIST
    # -----------------------------------------------------

    st.subheader("📄 Documents")


    if st.session_state.documents:

        for document in st.session_state.documents:

            st.markdown(
                f"📑 `{document}`"
            )

    else:

        st.caption(
            "No documents processed yet."
        )


    st.divider()


    # -----------------------------------------------------
    # SYSTEM STATUS
    # -----------------------------------------------------

    st.subheader("📊 System Status")


    if st.session_state.rag.embeddings:

        st.success(
            "🟢 Knowledge base ready"
        )

    else:

        st.warning(
            "🟡 Waiting for documents"
        )


    st.divider()


    # -----------------------------------------------------
    # CLEAR CHAT
    # -----------------------------------------------------

    if st.button(
        "🗑️ Clear Chat",
        use_container_width=True
    ):

        st.session_state.chat_history = []

        st.rerun()


# =========================================================
# EMPTY STATE
# =========================================================

if not st.session_state.documents:

    empty_html = """
<div class="empty-state">
<div class="empty-icon">📚</div>
<div class="empty-title">
Build Your Enterprise Knowledge Base
</div>
<div class="empty-text">
Upload HR policies, IT policies, reports, guidelines
or other enterprise documents using the sidebar.
</div>
</div>
"""

    st.markdown(
        empty_html,
        unsafe_allow_html=True
    )

else:

    st.markdown(
        '<div class="section-title">💬 Ask Your Enterprise Copilot</div>',
        unsafe_allow_html=True
    )


# =========================================================
# CHAT HISTORY
# =========================================================

for message in st.session_state.chat_history:

    with st.chat_message(
        message["role"]
    ):

        st.markdown(
            message["content"]
        )


# =========================================================
# CHAT INPUT
# =========================================================

question = st.chat_input(
    "Ask a question about your enterprise documents..."
)


# =========================================================
# QUESTION PROCESSING
# =========================================================

if question:

    with st.chat_message("user"):

        st.markdown(
            question
        )


    st.session_state.chat_history.append(
        {
            "role": "user",
            "content": question
        }
    )


    # -----------------------------------------------------
    # NO DOCUMENTS
    # -----------------------------------------------------

    if not st.session_state.rag.embeddings:

        answer = (
            "Please upload and process enterprise "
            "documents before asking a question."
        )


        with st.chat_message("assistant"):

            st.warning(
                answer
            )


    # -----------------------------------------------------
    # RAG
    # -----------------------------------------------------

    else:

        with st.chat_message("assistant"):

            with st.spinner(
                "🔍 Searching enterprise knowledge..."
            ):

                retrieved_documents = (
                    st.session_state.rag.search(
                        question,
                        top_k=5
                    )
                )


            with st.spinner(
                "🤖 Generating answer..."
            ):

                answer = (
                    st.session_state.rag.generate_answer(
                        question,
                        retrieved_documents,
                        st.session_state.chat_history
                    )
                )


            st.markdown(
                answer
            )


            # ------------------------------------------------
            # SOURCES
            # ------------------------------------------------

            if retrieved_documents:

                st.divider()

                st.markdown(
                    "### 📚 Sources"
                )


                displayed_sources = set()


                for document in retrieved_documents:

                    source_key = (
                        document["source"],
                        document["chunk_id"]
                    )


                    if source_key in displayed_sources:

                        continue


                    displayed_sources.add(
                        source_key
                    )


                    score = document.get(
                        "score",
                        0
                    )


                    with st.expander(
                        f"📄 {document['source']} — Chunk {document['chunk_id']}"
                    ):

                        st.write(
                            f"**Similarity:** {score:.3f}"
                        )

                        st.caption(
                            "Retrieved from the enterprise knowledge base."
                        )


    # -----------------------------------------------------
    # SAVE ANSWER
    # -----------------------------------------------------

    st.session_state.chat_history.append(
        {
            "role": "assistant",
            "content": answer
        }
    )