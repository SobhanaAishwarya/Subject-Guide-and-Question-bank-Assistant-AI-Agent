```python
# -----------------------------------
# HELPER FUNCTIONS
# -----------------------------------

def get_relevant_lines(context, query):

    query_words = query.lower().split()

    scored_lines = []

    for line in context.split("\n"):

        line = line.strip()

        if not line:
            continue

        score = 0

        for word in query_words:

            if word in line.lower():
                score += 1

        scored_lines.append((score, line))

    scored_lines.sort(reverse=True)

    top_lines = [
        line
        for score, line in scored_lines[:10]
        if score > 0
    ]

    if not top_lines:
        top_lines = context.split("\n")[:10]

    return top_lines


# -----------------------------------
# AGENT LOGIC
# -----------------------------------

def get_prompt(mode, context, query):

    relevant_lines = get_relevant_lines(
        context,
        query
    )

    if mode == "Ask Questions":

        return (
            "ANSWER\n\n" +
            "\n".join(relevant_lines[:8])
        )

    elif mode == "Generate Quiz":

        result = "QUIZ QUESTIONS\n\n"

        for i, line in enumerate(
            relevant_lines[:10],
            start=1
        ):

            result += f"""
Q{i}. What is related to:

{line}

A) Option A
B) Option B
C) Option C
D) Option D

Answer: A

"""

        return result

    elif mode == "Generate Viva Questions":

        result = "VIVA QUESTIONS\n\n"

        for i, line in enumerate(
            relevant_lines[:10],
            start=1
        ):

            result += f"""
Q{i}. Explain:

{line}

Answer:
{line}

"""

        return result

    elif mode == "Important Topics":

        result = "IMPORTANT TOPICS\n\n"

        seen = set()

        count = 1

        for line in relevant_lines:

            if line not in seen:

                result += (
                    f"{count}. {line}\n\n"
                )

                seen.add(line)

                count += 1

            if count > 10:
                break

        return result

    elif mode == "Generate Notes":

        result = "STUDY NOTES\n\n"

        for line in relevant_lines[:10]:

            result += (
                f"• {line}\n"
            )

        return result

    elif mode == "Study Planner":

        result = "7 DAY STUDY PLAN\n\n"

        topics = relevant_lines[:7]

        for i, topic in enumerate(
            topics,
            start=1
        ):

            result += f"""
Day {i}

Topic:
{topic}

Task:
Study and revise

"""

        return result

    return "\n".join(
        relevant_lines[:10]
    )


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

        result = get_prompt(
            mode,
            context,
            query
        )

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

        return result.strip()

    except Exception as e:

        return (
            f"Error generating answer: "
            f"{str(e)}"
        )

