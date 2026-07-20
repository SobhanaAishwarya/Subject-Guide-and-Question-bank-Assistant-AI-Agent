"""
Flashcard Agent — port of ``src/components/agents/FlashcardsPage.tsx``.

Generates cards from the indexed documents and reviews them with a Leitner
spaced-repetition box system persisted in SQLite.
"""

from __future__ import annotations

import html

import streamlit as st

from components.ui import empty_state, hero, metric_row, require_documents, source_selector
from utils.session import active_sources, get_agents, get_database, get_vector_store


def render() -> None:
    """Render the Flashcard Agent page."""
    store = get_vector_store()
    agents = get_agents()
    db = get_database()

    hero(
        "Flashcard Agent",
        "Spaced-repetition cards written from your own material. Cards you miss "
        "come back sooner.",
        eyebrow="FLASHCARDS",
    )

    if not require_documents(store):
        return

    generate_tab, review_tab = st.tabs(["Generate", "Review"])

    # ---- Generate ----------------------------------------------------- #
    with generate_tab:
        source_selector(store)
        left, right = st.columns([3, 1])
        with left:
            topic = st.text_input("Topic", key="flash_topic",
                                  placeholder="e.g. Process Scheduling")
        with right:
            count = st.number_input("Cards", 5, 30, 10, key="flash_count")

        if st.button("Generate Flashcards", type="primary",
                     use_container_width=True) and topic:
            with st.spinner("Writing flashcards from your documents…"):
                try:
                    cards, sources = agents.generate_flashcards(
                        topic, int(count), active_sources()
                    )
                except Exception as exc:  # noqa: BLE001
                    st.error(f"Generation failed: {exc}")
                    return

            if not cards:
                empty_state("No cards could be made",
                            "Your documents may not cover that topic.")
                return

            added = db.add_flashcards([c.__dict__ for c in cards])
            db.log_activity(f"Created {added} flashcards on {topic}",
                            icon="FC", kind="flashcards", minutes=3)
            st.success(f"Created {added} flashcards. Open the Review tab.")
            st.session_state.flash_index = 0
            st.session_state.flash_flipped = False

    # ---- Review -------------------------------------------------------- #
    with review_tab:
        all_cards = db.list_flashcards()
        if not all_cards:
            empty_state("No flashcards yet",
                        "Generate some in the first tab.")
            return

        topics = sorted({c["topic"] for c in all_cards if c["topic"]})
        chosen = st.selectbox("Deck", ["All decks"] + topics, key="flash_deck")
        deck = all_cards if chosen == "All decks" else [
            c for c in all_cards if c["topic"] == chosen
        ]
        if not deck:
            return

        mastered = sum(1 for c in deck if c["box"] >= 4)
        reviews = sum(c["reviews"] for c in deck)
        metric_row([
            {"value": len(deck), "label": "Cards in deck"},
            {"value": mastered, "label": "Mastered (box 4+)"},
            {"value": reviews, "label": "Total reviews"},
            {"value": f"{int(mastered / len(deck) * 100)}%",
             "label": "Deck mastery"},
        ])

        index = st.session_state.flash_index % len(deck)
        card = deck[index]

        st.write("")
        st.progress((index + 1) / len(deck), text=f"Card {index + 1} of {len(deck)}")

        face = "back" if st.session_state.flash_flipped else ""
        content = card["back"] if st.session_state.flash_flipped else card["front"]
        st.markdown(
            f'<div class="flashcard {face}">{html.escape(content)}</div>',
            unsafe_allow_html=True,
        )
        st.caption(
            f"Box {card['box']}/5 · {card['reviews']} reviews"
            + (f" · {card['source']}" if card["source"] else "")
        )

        st.write("")
        if not st.session_state.flash_flipped:
            if st.button("Flip card", type="primary", use_container_width=True):
                st.session_state.flash_flipped = True
                st.rerun()
        else:
            miss_column, hit_column = st.columns(2)
            with miss_column:
                if st.button("Didn't know it", use_container_width=True):
                    db.review_flashcard(card["id"], correct=False)
                    st.session_state.flash_index += 1
                    st.session_state.flash_flipped = False
                    st.rerun()
            with hit_column:
                if st.button("Got it", type="primary", use_container_width=True):
                    db.review_flashcard(card["id"], correct=True)
                    db.log_activity("Reviewed a flashcard", icon="FC",
                                    kind="review", minutes=1)
                    st.session_state.flash_index += 1
                    st.session_state.flash_flipped = False
                    st.rerun()

        st.divider()
        if st.button("Delete this deck", key="flash_delete"):
            db.delete_flashcards(None if chosen == "All decks" else chosen)
            st.session_state.flash_index = 0
            st.rerun()
