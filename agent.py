
from langchain_ollama import ChatOllama

def generate_answer(query, vectorstore):

    # Retrieve similar chunks from vector database
    docs = vectorstore.similarity_search(query, k=8)

    print("Retrieved docs:", len(docs))

    if not docs:
        return "No relevant information found in the document."

    # Combine retrieved text into context
    context = "\n\n".join([doc.page_content for doc in docs])

    # Debug print (to check what text is retrieved)
    print("----- Retrieved Context Preview -----")
    print(context[:500])   # prints first 500 characters
    print("------------------------------------")

    # Load local LLM
    llm = ChatOllama(
        model="llama3"
    )

    prompt = f"""
You are a computer science academic assistant.

Use the context below to answer the question in a structured format.

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
    response = llm.invoke(prompt)

    return response.content