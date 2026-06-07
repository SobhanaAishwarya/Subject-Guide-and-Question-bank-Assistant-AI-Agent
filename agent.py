from transformers import (
    AutoTokenizer,
    AutoModelForSeq2SeqLM,
    pipeline
)

from langchain_community.llms import (
    HuggingFacePipeline
)

# -----------------------------------
# LOAD LLM
# -----------------------------------

def get_llm():

    model_name = "google/flan-t5-base"

    tokenizer = AutoTokenizer.from_pretrained(
        model_name
    )

    model = AutoModelForSeq2SeqLM.from_pretrained(
        model_name
    )

    pipe = pipeline(
        "text2text-generation",
        model=model,
        tokenizer=tokenizer
    )

    return HuggingFacePipeline(
        pipeline=pipe
    )

# Load model once
llm = get_llm()

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

        result = llm.invoke(prompt)

        result = str(result).strip()

        unwanted = [
            "<div>",
            "</div>",
            "<br>",
            "Question:",
            "Answer:",
            "Final Answer:"
        ]

        for word in unwanted:
            result = result.replace(
                word,
                ""
            )

        result = result.strip()

        if len(result) < 5:
            return (
                "Could not generate "
                "a proper answer."
            )

        return result

    except Exception as e:

        return (
            f"Error generating answer: "
            f"{str(e)}"
        )