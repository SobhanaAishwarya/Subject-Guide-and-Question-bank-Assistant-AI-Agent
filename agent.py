
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
        task="text2text-generation",
        model=model,
        tokenizer=tokenizer,
        max_new_tokens=256,
        do_sample=False
    )

    return pipe


# Load model once
llm = get_llm()


# -----------------------------------
# PROMPTS
# -----------------------------------

def get_prompt(mode, context, query):

    if mode == "Ask Questions":

        return f"""
You are an Academic AI Assistant.

Answer the question using ONLY the context below.

Context:
{context}

Question:
{query}

Provide:
- Definition
- Explanation
- Example (if applicable)
- Key Points
"""

    elif mode == "Generate Quiz":

        return f"""
Generate 10 multiple-choice questions from the context.

Context:
{context}

For each question provide:
- Question
- Option A
- Option B
- Option C
- Option D
- Correct Answer
"""

    elif mode == "Generate Viva Questions":

        return f"""
Generate 10 important viva questions with answers.

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
Extract the top 10 most important topics.

Context:
{context}

For each topic provide:
- Topic Name
- Why it is important
"""

    elif mode == "Generate Notes":

        return f"""
Create concise study notes.

Context:
{context}

Format:

Topic:
Explanation:
Key Points:
"""

    elif mode == "Study Planner":

        return f"""
Create a 7-day study plan from the document.

Context:
{context}

For each day provide:
- Topics
- Hours Required
- Revision Tasks
"""

    return f"""
Answer the following question.

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
                "No relevant information found "
                "in the uploaded document."
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

        response = llm(
            prompt
        )

        result = response[0][
            "generated_text"
        ]

        unwanted = [
            "<div>",
            "</div>",
            "<br>",
            "Question:",
            "Answer:",
            "Final Answer:"
        ]

        for word in unwanted:

            result = result.replace(
                word,
                ""
            )

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
