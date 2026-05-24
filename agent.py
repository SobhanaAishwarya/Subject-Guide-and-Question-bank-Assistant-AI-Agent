
from transformers import (
    AutoTokenizer,
    AutoModelForSeq2SeqLM,
    pipeline
)

from langchain_community.llms import HuggingFacePipeline


# -----------------------------------
# LOAD LLM (FIXED)
# -----------------------------------
def get_llm():
    model_name = "google/flan-t5-base"

    tokenizer = AutoTokenizer.from_pretrained(model_name)

    model = AutoModelForSeq2SeqLM.from_pretrained(model_name)

    # IMPORTANT FIX: use text2text-generation (NOT text-generation)
    pipe = pipeline(
        "text2text-generation",
        model=model,
        tokenizer=tokenizer,
        max_new_tokens=200,
        do_sample=False
    )

    return HuggingFacePipeline(pipeline=pipe)


llm = get_llm()


# -----------------------------------
# CLEAN OUTPUT FUNCTION
# -----------------------------------
def clean_output(text: str) -> str:
    if not text:
        return ""

    unwanted_phrases = [
        "Question:",
        "Final Answer:",
        "Context:",
        "Answer:",
        "You are an expert",
        "Instructions:"
    ]

    for phrase in unwanted_phrases:
        text = text.replace(phrase, "")

    # remove extra spaces and weird formatting
    return text.strip()


# -----------------------------------
# GENERATE ANSWER
# -----------------------------------
def generate_answer(query, vectorstore):

    try:
        docs = vectorstore.similarity_search(query, k=5)

        if not docs:
            return "Not found in document."

        context = "\n\n".join(doc.page_content for doc in docs)

        # STRICT prompt (minimal + no echo risk)
        prompt = f"""
Answer the question using only the context.

If the answer is not in the context, reply exactly:
Not found in document.

Context:
{context}

"""

        result = llm.invoke(prompt)
        result = str(result)

        result = clean_output(result)

        # final safety fallback
        if len(result.strip()) < 2:
            return "Not found in document."

        return result

    except Exception as e:
        return "Error generating answer."