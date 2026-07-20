"""Sticky sidebar: brand, navigation, model picker and index status.

Direct port of ``src/components/layout/Sidebar.tsx`` and ``Header.tsx``.
"""

from __future__ import annotations

import html

import streamlit as st

from config import AVAILABLE_MODELS, NAV_ITEMS, settings
from utils.session import get_vector_store, sign_out


def render_sidebar() -> str:
    """Render the sidebar and return the active page id."""
    store = get_vector_store()
    user = st.session_state.user

    with st.sidebar:
        # ---- Brand -------------------------------------------------- #
        st.markdown(
            """
            <div class="sidebar-brand">
              <div class="logo">S</div>
              <div>
                <div class="name">StudyAI</div>
                <div class="tag">Agentic Study Assistant</div>
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # ---- Navigation --------------------------------------------- #
        for item in NAV_ITEMS:
            is_active = st.session_state.page == item["id"]
            if st.button(
                item["label"],
                key=f"nav_{item['id']}",
                use_container_width=True,
                type="primary" if is_active else "secondary",
            ):
                st.session_state.page = item["id"]
                st.rerun()

        st.divider()

        # ---- Model picker ------------------------------------------- #
        current = st.session_state.get("model", settings.openrouter_model)
        options = list(dict.fromkeys([current] + AVAILABLE_MODELS))
        st.selectbox(
            "Model (via OpenRouter)",
            options=options,
            index=options.index(current),
            key="model",
        )

        # ---- Index status ------------------------------------------- #
        if store.is_empty:
            st.caption("No documents indexed")
        else:
            st.caption(
                f"{len(store.sources)} document(s) · {store.size} chunks indexed"
            )

        if not settings.is_configured:
            st.warning("OPENROUTER_API_KEY not set")

        st.divider()

        # ---- User card ---------------------------------------------- #
        st.markdown(
            f"""
            <div class="sidebar-user">
              <div class="avatar">{html.escape(user['avatar'])}</div>
              <div>
                <div style="font-size:13px;font-weight:700;">{html.escape(user['name'])}</div>
                <div style="font-size:11px;opacity:0.6;">{html.escape(user['semester'])}</div>
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        if st.button("Sign Out", key="nav_logout", use_container_width=True):
            sign_out()

    return st.session_state.page
