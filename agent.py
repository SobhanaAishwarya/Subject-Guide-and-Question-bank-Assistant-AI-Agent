from langchain_community.llms import HuggingFacePipeline
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM, pipeline


# -------------------------
# LLM SETUP (CLOUD SAFE)
# -------------------------
def get_llm():
    model_name = "google/flan-t5-base"

    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForSeq2SeqLM.from_pretrained(model_name)

    pipe = pipeline(
        "text2text-generation",
        model=model,
        tokenizer=tokenizer,
        max_length=256,
        do_sample=False
    )

    return HuggingFacePipeline(pipeline=pipe)


llm = get_llm()


# -------------------------
# MAIN FUNCTION
# -------------------------
def generate_answer(query, vectorstore):

    # Retrieve relevant documents
    docs = vectorstore.similarity_search(query, k=8)

    print("Retrieved docs:", len(docs))

    if not docs:
        return "No relevant information found in the document."

    # Combine context
    context = "\n\n".join([doc.page_content for doc in docs])

    prompt = f"""
You are a computer science academic assistant.

Use the context below to answer the question in a structured format:

1. Definition
2. Explanation
3. Example
4. Key Points

Context:
{context}

Question:
{query}

Answer:
"""

    # Generate response
    result = llm(prompt)

    # Extract clean text safely (important for Streamlit)
    if hasattr(result, "content"):
        return result.content
    return result