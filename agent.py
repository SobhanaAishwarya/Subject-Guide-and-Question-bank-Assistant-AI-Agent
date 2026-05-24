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

    # IMPORTANT FIX
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

        # Build context
        context = "\n\n".join(
            [
                doc.page_content
                for doc in docs
            ]
        )

        # Cleaner prompt
        prompt = f"""
You are an expert academic assistant.

Answer ONLY using the provided context.

Instructions:
- Give a clean and short answer.
- Do NOT include:
  Question:
  Final Answer:
- Do NOT output HTML tags.
- Do NOT copy raw extracted notes.
- If information is unavailable, say:
"Not found in document."

Context:
{context}

User Question:
{query}

Answer:
"""

        # Generate response
        result = llm.invoke(prompt)

        result = str(result)

        # Clean weird outputs
        result = (
            result.replace("<div>", "")
            .replace("</div>", "")
            .replace("Question:", "")
            .replace("Final Answer:", "")
            .replace("<br>", "")
            .strip()
        )

        # Fallback
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