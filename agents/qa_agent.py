import google.generativeai as genai

from config.secrets import (
    GEMINI_API_KEY
)

from rag.prompt_templates import (
    QA_PROMPT
)

genai.configure(
    api_key=GEMINI_API_KEY
)

model = genai.GenerativeModel(
    "gemini-1.5-flash"
)


def ask_question(
        question,
        context
):

    prompt = QA_PROMPT.format(
        context=context,
        question=question
    )

    response = model.generate_content(
        prompt
    )

    return response.text