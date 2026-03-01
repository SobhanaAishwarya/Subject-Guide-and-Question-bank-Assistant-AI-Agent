# agent.py

from langchain_openai import ChatOpenAI


def generate_answer(query, vectorstore):
    
    # 1️⃣ Retrieve similar chunks
    docs = vectorstore.similarity_search(query, k=4)
    
    # 2️⃣ Combine context
    context = ""
    for doc in docs:
        context += doc.page_content + "\n\n"
    
    # 3️⃣ Load LLM
    llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0)
    
    # 4️⃣ Create structured prompt
    prompt = f"""
    Answer the question in structured format:

    1. Definition
    2. Explanation
    3. Example
    4. Important Points

    Context:
    {context}

    Question:
    {query}
    """
    
    # 5️⃣ Generate response
    response = llm.predict(prompt)
    
    return response