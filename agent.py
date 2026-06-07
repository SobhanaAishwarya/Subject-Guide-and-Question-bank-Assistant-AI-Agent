# -----------------------------------
# PROMPTS FOR DIFFERENT AGENTS
# -----------------------------------

def get_prompt(mode, context, query):

    if mode == "Ask Questions":

        return context[:1500]

    elif mode == "Generate Quiz":

        topics = context.split("\n")

        quiz = "QUIZ QUESTIONS\n\n"

        for i, topic in enumerate(topics[:10], start=1):

            if topic.strip():

                quiz += f"""
Q{i}. {topic.strip()}?

A) Option A
B) Option B
C) Option C
D) Option D

Answer: A

"""

        return quiz

    elif mode == "Generate Viva Questions":

        topics = context.split("\n")

        viva = "VIVA QUESTIONS\n\n"

        count = 1

        for topic in topics:

            if topic.strip():

                viva += f"""
Q{count}. Explain {topic.strip()}.

Answer:
{topic.strip()}

"""

                count += 1

            if count > 10:
                break

        return viva

    elif mode == "Important Topics":

        topics = []

        for line in context.split("\n"):

            line = line.strip()

            if len(line) > 5:

                topics.append(line)

        result = "IMPORTANT TOPICS\n\n"

        for i, topic in enumerate(topics[:10], start=1):

            result += f"{i}. {topic}\n"

        return result

    elif mode == "Generate Notes":

        return f"""
STUDY NOTES

{context[:2000]}
"""

    elif mode == "Study Planner":

        return f"""
7 DAY STUDY PLAN

Day 1:
Read first section

Day 2:
Revise and practice

Day 3:
Study intermediate concepts

Day 4:
Important topics revision

Day 5:
Solve questions

Day 6:
Mock viva preparation

Day 7:
Final revision

Topics Covered:
{context[:1000]}
"""

    return context[:1500]


# -----------------------------------
# GENERATE ANSWER
# -----------------------------------

def generate_answer(query, vectorstore, mode):

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

        result = get_prompt(
            mode,
            context,
            query
        )

        result = str(result).strip()

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