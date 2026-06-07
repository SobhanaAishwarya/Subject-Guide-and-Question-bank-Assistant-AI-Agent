from transformers import pipeline
from langchain_community.llms import HuggingFacePipeline

# -----------------------------------
# LOAD LLM
# -----------------------------------
def get_llm():

    pipe = pipeline(
        task="text2text-generation",
        model="google/flan-t5-base",
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

        # Prompt
        prompt = f"""
Answer the question using the context below.
If the answer is not present in the context, say:
"I could not find the answer in the uploaded document."

Context:
{context}

Question:
{query}

Answer:
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