from transformers import (
AutoTokenizer,
AutoModelForSeq2SeqLM,
pipeline
)

# -----------------------------------

# LOAD MODEL

# -----------------------------------

def get_llm():
model_name = "google/flan-t5-small"

tokenizer = AutoTokenizer.from_pretrained(
    model_name
)

model = AutoModelForSeq2SeqLM.from_pretrained(
    model_name
)

pipe = pipeline(
    "text2text-generation",
    model=model,
    tokenizer=tokenizer,
    max_new_tokens=512,
    do_sample=False
)

return pipe

llm = get_llm()

# -----------------------------------

# PROMPTS

# -----------------------------------

def get_prompt(mode, context, query):
context = context[:2500]

if mode == "Ask Questions":

    return f"""

Answer the question based ONLY on the context.

Context:
{context}

Question:
{query}

Provide:
Definition:
Explanation:
Example:
Key Points:
"""


elif mode == "Generate Quiz":

    return f"""


Create 10 multiple choice questions from the context.

Context:
{context}

Format:

Q1.
A)
B)
C)
D)

Correct Answer:

Q2.
...
"""


elif mode == "Generate Viva Questions":

    return f"""


Generate 10 viva interview questions and answers.

Context:
{context}

Format:

Q1:
Answer:

Q2:
Answer:
"""


elif mode == "Important Topics":

    return f"""


Read the context carefully.

Extract the TOP 10 MOST IMPORTANT TOPICS.

For each topic provide:

Topic:
Importance:

Context:
{context}
"""


elif mode == "Generate Notes":

    return f"""

Create student-friendly study notes.

Context:
{context}

Format:

Topic:
Explanation:
Key Points:
"""


elif mode == "Study Planner":

    return f"""

Create a 7-day study plan.

Context:
{context}

For each day provide:

Day:
Topics:
Tasks:
Revision:
"""

return f"""
```

Answer the question.

Context:
{context}

Question:
{query}
"""

# -----------------------------------

# GENERATE ANSWER

# -----------------------------------

def generate_answer(
query,
vectorstore,
mode
):
try:

    docs = vectorstore.similarity_search(
        query,
        k=5
    )

    if not docs:

        return (
            "No relevant information found in the uploaded document."
        )

    context = "\n\n".join(
        [
            doc.page_content
            for doc in docs
        ]
    )

    prompt = get_prompt(
        mode,
        context,
        query
    )

    response = llm(prompt)

    result = response[0]["generated_text"]

    result = result.replace(
        "Answer:",
        ""
    )

    result = result.replace(
        "Final Answer:",
        ""
    )

    result = result.strip()

    if len(result) < 10:

        return (
            "The model could not generate a meaningful response."
        )

    return result

except Exception as e:

    return (
        f"Error generating answer: {str(e)}"
    )
