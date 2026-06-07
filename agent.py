import streamlit as st
import google.generativeai as genai

# -----------------------------------
# CONFIGURE GEMINI
# -----------------------------------

genai.configure(
    api_key=st.secrets["GEMINI_API_KEY"]
)

model = genai.GenerativeModel(
    "gemini-1.5-flash"
)

# -----------------------------------
# GENERATE ANSWER
# -----------------------------------

def generate_answer(query, vectorstore):

    try:

        docs = vectorstore.similarity_search(
            query,
            k=5
        )

        if not docs:
            return (
                "No relevant information found "
                "in the uploaded document."
            )

        context = "\n\n".join(
            [
                doc.page_content
                for doc in docs
            ]
        )

        prompt = f"""
You are an Academic AI Assistant.

Use only the provided context.

Context:
{context}

Question:
{query}

Answer clearly and professionally.
"""

        response = model.generate_content(
            prompt
        )

        return response.text

    except Exception as e:
        return f"Error: {str(e)}"