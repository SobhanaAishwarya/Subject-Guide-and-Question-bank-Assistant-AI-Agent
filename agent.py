from transformers import AutoTokenizer, AutoModelForSeq2SeqLM, pipeline
from langchain_community.llms import HuggingFacePipeline


# -------------------------
# LLM SETUP (CLOUD SAFE FIX)
# -------------------------
def get_llm():
    model_name = "google/flan-t5-base"

    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForSeq2SeqLM.from_pretrained(model_name)

    pipe = pipeline(
        "text-generation",
        model=model,
        tokenizer=tokenizer,
        max_new_tokens=256,
        do_sample=False
    )

    return HuggingFacePipeline(pipeline=pipe)


llm = get_llm()


# -------------------------
# MAIN FUNCTION
# -------------------------
def generate_answer(query, vectorstore):

    # retrieve similar docs
    docs = vectorstore.similarity_search(query, k=8)

    if not docs:
        return "No relevant information found in the document."

    # build context
    context = "\n\n".join([doc.page_content for doc in docs])

    prompt = f"""
You are an expert computer science academic assistant.

Use ONLY the context below to answer the question.

RULES:
- Do NOT repeat the context
- Do NOT include HTML tags like <div>
- Do NOT copy raw notes
- Answer ONLY in clean structured format
- If information is missing, say "Not found in document"

FORMAT YOUR ANSWER STRICTLY AS:

Definition:
Explanation:
Example:
Key Points:

-------------------------
CONTEXT:
{context}
-------------------------

QUESTION:
{query}

FINAL ANSWER:
"""
       # generate response (FIXED INDENTATION)
    result = llm.invoke(prompt)
    # safe return handling
    if hasattr(result, "content"):
        return result.content

    return result
