# Subject Guide & Question Bank Assistant (AI Agent)

An agentic study assistant, built with Python/Streamlit. Upload your own study
material — PDF, DOCX, PPTX, TXT — and every answer, summary, quiz question,
flashcard, or mock-interview question it generates is grounded in *your*
documents, with citations, powered entirely by OpenRouter.

## Screenshots

| Sign in | Dashboard |
| --- | --- |
| ![Sign in](studyai_streamlit/studyai/screenshots/01-sign-in.png) | ![Dashboard](studyai_streamlit/studyai/screenshots/02-dashboard.png) |

| Sign up |
| --- |
| ![Sign up](studyai_streamlit/studyai/screenshots/03-sign-up.png) |

## What it does

- Chat with your own documents (streaming answers, cited to source pages)
- Multi-file upload: PDF, DOCX, PPTX, TXT
- Summarization, chapter/topic explanation, notes generation
- Question bank generation (2/5/10-mark), important questions, previous-paper analysis
- Quiz generation with auto-grading
- Flashcards with Leitner spaced repetition
- Day-by-day study planner and rapid revision sheets
- Weak-topic diagnostics and cross-document reasoning
- AI mock interviews with grading
- Progress analytics

## Project layout

This repository wraps a Streamlit app that lives at
[`studyai_streamlit/studyai/`](studyai_streamlit/studyai/) — see
[**that folder's README**](studyai_streamlit/studyai/README.md) for the full
feature list, architecture, and setup/deployment instructions (an OpenRouter
API key is required to run it). `streamlit_app.py` at the repo root is a thin
entry point Streamlit Cloud uses to launch the app from that subfolder.
