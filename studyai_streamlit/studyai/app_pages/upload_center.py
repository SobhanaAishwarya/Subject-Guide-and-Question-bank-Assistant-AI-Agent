"""
Upload Center — port of ``src/components/upload/UploadCenter.tsx``.

The original listed hardcoded files. This one runs the real pipeline:
extract → clean → chunk → embed → FAISS → persist.
"""

from __future__ import annotations

import html

import pandas as pd
import streamlit as st

from components.ui import empty_state, hero, metric_row
from config import SUBJECTS, settings
from models.schemas import Document
from services.document_processor import DocumentProcessor, UnsupportedFileType
from utils.logger import get_logger
from utils.session import get_database, get_vector_store
from utils.text_utils import human_size

logger = get_logger(__name__)


def _ingest(files, subject: str) -> None:
    """Run the full ingestion pipeline over the uploaded files."""
    store = get_vector_store()
    db = get_database()
    processor = DocumentProcessor()

    progress = st.progress(0.0, text="Starting…")
    status = st.empty()
    total_chunks = 0

    for position, uploaded in enumerate(files):
        base = position / len(files)
        step = 1 / len(files)

        try:
            data = uploaded.getvalue()
            size_mb = len(data) / (1024 * 1024)
            if size_mb > settings.max_upload_mb:
                st.error(f"❌ {uploaded.name} is {size_mb:.1f} MB — over the "
                         f"{settings.max_upload_mb} MB limit.")
                continue

            progress.progress(base + step * 0.15,
                              text=f"📄 Extracting text from {uploaded.name}…")
            pages = processor.extract(uploaded.name, data)

            progress.progress(base + step * 0.45,
                              text=f"✂️ Cleaning and chunking {uploaded.name}…")
            document = Document(
                name=uploaded.name,
                subject=subject,
                size_bytes=len(data),
                pages=len(pages),
                chunk_count=0,
                status="analyzing",
            )
            chunks = processor.chunk_pages(
                pages, source=uploaded.name, subject=subject, doc_id=document.doc_id
            )

            if not chunks:
                st.warning(f"⚠️ No readable text found in {uploaded.name}. "
                           f"If it is a scanned PDF, it needs OCR first.")
                continue

            progress.progress(base + step * 0.70,
                              text=f"🧠 Generating embeddings for {uploaded.name}…")
            store.add_chunks(chunks)

            document.chunk_count = len(chunks)
            document.status = "analyzed"
            store.register_document(document.doc_id, document.to_dict())
            db.add_document(document.to_dict())
            db.log_activity(f"Uploaded {uploaded.name}", icon="📁",
                            kind="upload", minutes=2)

            total_chunks += len(chunks)
            progress.progress(base + step, text=f"✅ {uploaded.name} indexed")
            status.success(
                f"✅ **{uploaded.name}** — {len(pages)} page(s), "
                f"{len(chunks)} chunks indexed"
            )

        except UnsupportedFileType as exc:
            st.error(f"❌ {uploaded.name}: {exc}")
        except Exception as exc:  # noqa: BLE001 - one bad file must not stop the batch
            logger.exception("Ingestion failed for %s", uploaded.name)
            st.error(f"❌ Failed to process {uploaded.name}: {exc}")

    if total_chunks:
        progress.progress(1.0, text="💾 Saving vector store…")
        store.save()
        progress.empty()
        st.success(f"🎉 Indexed {total_chunks} chunks. Every agent can now use them.")
        st.balloons()
    else:
        progress.empty()


def render() -> None:
    """Render the Upload Center."""
    store = get_vector_store()
    db = get_database()

    hero(
        "Upload Center",
        "Add your PDFs, Word files, slide decks and notes. Everything is chunked, "
        "embedded with all-MiniLM-L6-v2 and indexed into FAISS.",
        eyebrow="INGESTION",
    )

    documents = db.list_documents()
    metric_row(
        [
            {"icon": "📄", "value": len(documents), "label": "Documents"},
            {"icon": "🧩", "value": store.size, "label": "Indexed Chunks"},
            {"icon": "📚", "value": len({d["subject"] for d in documents}),
             "label": "Subjects"},
            {"icon": "💾", "value": human_size(sum(d["size_bytes"] for d in documents)),
             "label": "Total Size"},
        ]
    )

    st.write("")
    upload_tab, library_tab = st.tabs(["⬆️ Upload", "📚 Library"])

    # ---- Upload ------------------------------------------------------ #
    with upload_tab:
        subject = st.selectbox("Subject", SUBJECTS + ["Other"], key="upload_subject")
        if subject == "Other":
            subject = st.text_input("Custom subject", value="General",
                                    key="upload_custom_subject") or "General"

        files = st.file_uploader(
            "Drop your files here",
            type=list(settings.supported_extensions),
            accept_multiple_files=True,
            key="upload_files",
            help=f"PDF, DOCX, PPTX, TXT · up to {settings.max_upload_mb} MB each",
        )

        if files:
            st.caption(
                f"{len(files)} file(s) selected · "
                f"{human_size(sum(len(f.getvalue()) for f in files))}"
            )
            if st.button("🚀  Process & Index", type="primary",
                         use_container_width=True):
                _ingest(files, subject)
                st.rerun()
        else:
            empty_state(
                "📁",
                "Drop your study material here",
                "PDF · DOCX · PPTX · TXT — multiple files at once are fine.",
            )

    # ---- Library ------------------------------------------------------ #
    with library_tab:
        if not documents:
            empty_state("📚", "Library is empty", "Upload something to get started.")
            return

        table = pd.DataFrame(
            [
                {
                    "Document": d["name"],
                    "Subject": d["subject"],
                    "Pages": d["pages"],
                    "Chunks": d["chunk_count"],
                    "Size": human_size(d["size_bytes"]),
                    "Status": d["status"],
                }
                for d in documents
            ]
        )
        st.dataframe(table, use_container_width=True, hide_index=True)

        st.markdown("##### Manage")
        for document in documents:
            row_left, row_right = st.columns([5, 1])
            with row_left:
                st.markdown(
                    f"<div style='padding-top:6px;font-size:13px;'>"
                    f"📄 <b>{html.escape(document['name'])}</b> · "
                    f"{html.escape(document['subject'])} · "
                    f"{document['chunk_count']} chunks</div>",
                    unsafe_allow_html=True,
                )
            with row_right:
                if st.button("🗑️", key=f"del_{document['doc_id']}",
                             help="Remove from index"):
                    store.remove_source(document["name"])
                    store.save()
                    db.delete_document(document["doc_id"])
                    st.rerun()

        st.divider()
        if st.button("⚠️  Clear entire index", key="clear_index"):
            store.clear()
            for document in documents:
                db.delete_document(document["doc_id"])
            st.success("Index cleared.")
            st.rerun()
