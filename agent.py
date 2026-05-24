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

    # STREAMLIT CLOUD FIX
    pipe = pipeline(
        "text-generation",
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

        docs = vectorstore.similarity_search(
            query,
            k=5
        )

        if not docs:
            return (
                "No relevant information "
                "found in document."
            )

        context = "\n\n".join(
            [
                doc.page_content
                for doc in docs
            ]
        )

        prompt = f"""

Context:
{context}

"""

        result = llm.invoke(prompt)

        result = str(result)

        # clean weird output
        result = (
            result.replace("<div>", "")
            .replace("</div>", "")
            .replace("Question:", "")
            .replace("Final Answer:", "")
            .replace("<br>", "")
            .strip()
        )

        # fallback
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