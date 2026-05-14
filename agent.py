from langchain_community.llms import HuggingFacePipeline
from transformers import pipeline

# -------------------------
# LLM SETUP (CLOUD SAFE)
# -------------------------
def get_llm():
    pipe = pipeline(
        "text2text-generation",
        model="google/flan-t5-base",
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

    # Generate response (IMPORTANT FIX)
    response = llm(prompt)

    return response