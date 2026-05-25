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

    # Better pipeline for FLAN-T5
    pipe = pipeline(
        "text2text-generation",
        model=model,
        tokenizer=tokenizer,
        max_new_tokens=200,
        do_sample=False
    )

    return HuggingFacePipeline(
        pipeline=pipe
    )


llm = get_llm()


# -----------------------------------
# GENERATE ANSWER
# -----------------------------------
def generate_answer(query, vectorstore):

    try:

        # Retrieve relevant chunks
        docs = vectorstore.similarity_search(
            query,
            k=5
        )

        if not docs:
            return (
                "No relevant information "
                "found in document."
            )

        # Combine retrieved chunks
        context = "\n\n".join(
            [
                doc.page_content
                for doc in docs
            ]
        )

        # Better prompt
        prompt = f"""
Answer the question using the context below.
Give only a clean answer.

Context:
{context}

Question:
{query}
"""

        # Generate response
        result = llm.invoke(prompt)

        result = str(result).strip()

        # Clean unwanted output
        unwanted = [
            "<div>",
            "</div>",
            "<br>",
            "Question:",
            "Answer:",
            "Final Answer:"
        ]

        for word in unwanted:
            result = result.replace(word, "")

        result = result.strip()

        # Fallback response
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