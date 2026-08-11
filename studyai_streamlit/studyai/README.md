# StudyAI — Agentic Study Assistant

A complete Python/Streamlit port of the original Next.js + TypeScript project.
Upload your study material, and every answer comes back grounded in **your own
documents** — with citations, and an honest refusal when the answer isn't there.

Powered entirely by **OpenRouter**. No OpenAI, Gemini, Anthropic, Azure, Groq or
local model SDK is used anywhere in this codebase.

---

## What it does

| Feature | Where |
|---|---|
| Chat with your documents (streaming, cited) | Chat |
| Multi-file upload: PDF, DOCX, PPTX, TXT | Upload Center |
| Question answering with page citations | Chat |
| Summarization (short / medium / long) | Notes → Summary |
| Chapter & topic explanation (4 levels) | Notes → Explain |
| Question bank (2/5/10-mark) | Notes → Question Bank |
| Important questions | Notes → Question Bank |
| Previous paper analysis | Notes → Previous Papers |
| Notes generation | Notes |
| Quiz generation + auto-grading | Quiz |
| Flashcards with Leitner spaced repetition | Flashcards |
| Study planner (day-by-day schedule) | Planner |
| Rapid revision sheets | Revision |
| Weak topic diagnostics | Weak Topics |
| AI mock interviews with grading | Interview |
| Cross-document reasoning | Cross Subject |
| Charts & progress analytics | Analytics |
| Related question suggestions | Chat |
| Conversation history & session memory | Chat / Profile |

---

## Quick start (local)

```bash
# 1. Install
pip install -r requirements.txt

# 2. Configure
cp .env.example .env
#    then edit .env and paste your OpenRouter key

# 3. Run
streamlit run streamlit_app.py
```

Open http://localhost:8501

> First run downloads the `all-MiniLM-L6-v2` embedding model (~90 MB). That
> happens once; afterwards it's cached.

---

## Deploy to Streamlit Cloud

This app is deployed from `agentic_ai_clean` (the repo root, one level above
this folder), via a thin `streamlit_app.py` shim there that runs this
folder's `streamlit_app.py`. The steps below assume that layout.

1. Push the repo to GitHub (`.env` and `.streamlit/secrets.toml` are
   gitignored — keep it that way).
2. Go to [share.streamlit.io](https://share.streamlit.io) → **New app**.
3. Main file path: **`streamlit_app.py`** (the one at the repo root, not
   this folder's).
4. Open **Advanced settings → Secrets** and paste the contents of
   `.streamlit/secrets.toml.example` with real values filled in — this
   **must** include `TURSO_DATABASE_URL` / `TURSO_AUTH_TOKEN` (see
   **Persistence** below), or every account anyone signs up will vanish the
   next time the app redeploys or reboots.
5. Deploy.

**Resource note:** `sentence-transformers` pulls in PyTorch. `requirements.txt`
pins the CPU-only wheel via `--extra-index-url` specifically so the build fits
inside Streamlit Cloud's 1 GB limit. Don't remove that line.

---

## Persistence (Turso)

Streamlit Cloud rebuilds the app in a fresh container on every deploy or
reboot, which wipes any local SQLite file. Sign-up/sign-in only survives
across redeploys if the app is pointed at [Turso](https://turso.tech) (a
free, hosted libSQL/SQLite-compatible database) instead:

1. `turso db create studyai` (after installing the Turso CLI and signing in).
2. `turso db show studyai` → copy the URL into `TURSO_DATABASE_URL`.
3. `turso db tokens create studyai` → copy the token into `TURSO_AUTH_TOKEN`.
4. Put both in your local `.env` (for local dev) **and** in the Streamlit
   Cloud app's **Settings → Secrets** (for the deployment) — they're
   separate, both need it.

Without these two variables set, `config.py` silently falls back to a local
SQLite file (`database/studyai.db`), which is fine for local development but
not for a Cloud deployment that needs accounts to persist.

### Demo account

`seed_demo.py` creates a fully-populated showcase account
(`abhi@gmail.com`) with two indexed documents, quiz history, flashcards,
chat history and a week of activity — useful for demoing the product
without waiting for a real user to build up that history. Every other
account (including one you sign up with your own email) starts completely
empty; documents, chats, quizzes, flashcards and activity are all scoped
per-user, so nothing seeded here is visible to anyone else.

```bash
cd studyai_streamlit/studyai
python seed_demo.py
```

Run it once, locally, with the **same** `TURSO_DATABASE_URL` /
`TURSO_AUTH_TOKEN` in your `.env` that the deployed app uses in its
Secrets — otherwise it only seeds your local SQLite file, and the deployed
app won't see the demo account. It's idempotent: re-running it is a no-op
once the account already has data.

---

## How the RAG pipeline works

```
Upload PDF/DOCX/PPTX/TXT
        ↓  PyPDF2 / python-docx / python-pptx
Extract text (page numbers preserved)
        ↓  utils/text_utils.clean_text
Clean text (ligatures, hyphen breaks, page-number noise)
        ↓  RecursiveCharacterTextSplitter (900 chars, 150 overlap)
Chunk text
        ↓  sentence-transformers/all-MiniLM-L6-v2 (normalized, 384-dim)
Generate embeddings
        ↓  faiss.IndexFlatIP
Store in FAISS
        ↓  cosine similarity search, top-k = 5
Semantic search
        ↓  drop anything below min_similarity (0.25)
Retrieve relevant chunks
        ↓  numbered, citable context block
Send ONLY retrieved context to OpenRouter
        ↓
Generate answer  →  Show sources [1] [2] [3]
```

### The anti-hallucination guarantee

Two independent guardrails:

1. **Retrieval gate.** If no chunk clears the similarity floor, the LLM is
   **never called**. The app returns
   `"I couldn't find this information in the uploaded documents."` directly.
2. **Prompt constraint.** The system prompt forbids outside knowledge and
   requires inline `[n]` citations for every factual claim.

So asking *"What is Normalization?"* against a DBMS PDF returns a cited answer
from that PDF; asking it against an unrelated PDF returns the refusal.

---

## Project structure

```
streamlit_app.py             Entry point + router
config.py                   Settings, paths, model catalogue, nav
seed_demo.py                 One-off script: seeds the abhi@gmail.com demo account
requirements.txt
README.md
.env.example
.gitignore

.streamlit/
  config.toml               Butter yellow theme + upload limits
  secrets.toml.example

assets/css/
  style.css                 Full custom theme (glassmorphism, animations)

components/
  ui.py                     Cards, metrics, hero, citations, guards
  sidebar.py                Sticky sidebar navigation

app_pages/                  One module per page
  login.py                  ← src/components/auth/LoginPage.tsx
  dashboard.py              ← src/components/dashboard/Dashboard.tsx
  upload_center.py          ← src/components/upload/UploadCenter.tsx
  chat.py                   ← NEW: the RAG chat surface
  notes.py                  ← src/components/agents/NotesPage.tsx
  quiz.py                   ← src/components/agents/QuizPage.tsx
  flashcards.py             ← src/components/agents/FlashcardsPage.tsx
  planner.py                ← src/components/agents/PlannerPage.tsx
  revision.py               ← src/components/agents/RevisionPage.tsx
  weak_topics.py            ← src/components/agents/WeakTopicsPage.tsx
  interview.py              ← src/components/agents/InterviewPage.tsx
  cross_subject.py          ← src/components/agents/CrossSubjectPage.tsx
  analytics.py              ← src/components/analytics/AnalyticsPage.tsx
  profile.py                ← src/components/profile/ProfilePage.tsx

services/
  openrouter_client.py      OpenRouter API (blocking + streaming + JSON)
  document_processor.py     Extract → clean → chunk
  embeddings.py             sentence-transformers wrapper (cached)
  vectorstore.py            FAISS index + persistence
  rag_engine.py             Retrieval + grounded generation
  agents.py                 All AI agents

database/
  db.py                     SQLite: docs, chats, quizzes, cards, activity

models/schemas.py           Typed dataclasses
utils/
  logger.py                 Logging setup
  text_utils.py             Cleaning helpers
  session.py                Session state + cached singletons

uploads/ vectorstore/ chat_history/    Runtime data (gitignored)
```

> **Why `app_pages/` and not `pages/`?**
> Streamlit treats a top-level `pages/` directory as magic — it auto-generates
> its own navigation menu, which would fight with the custom sidebar. Renaming
> it avoids that conflict entirely.

---

## TypeScript → Python mapping

| Original (Next.js) | Python replacement |
|---|---|
| `src/app/page.tsx` (router + state) | `app.py` (`ROUTES` dict + `st.session_state`) |
| `src/app/layout.tsx` | `st.set_page_config` + `load_css()` |
| `src/components/layout/Sidebar.tsx` | `components/sidebar.py` |
| `src/components/layout/Header.tsx` | merged into `components/sidebar.py` |
| `src/components/ui/App*.tsx` | `components/ui.py` |
| `src/components/**/*Page.tsx` | `app_pages/*.py` |
| `src/styles/tailwind.css` | `assets/css/style.css` |
| `package.json` | `requirements.txt` |
| `next.config.mjs` | `.streamlit/config.toml` |
| `.env` (Supabase/OpenAI/Gemini/…) | `.env` (OpenRouter only) |
| React `useState` | `st.session_state` |
| Hardcoded mock arrays | SQLite (`database/db.py`) |
| *(no backend existed)* | `services/` — the whole RAG stack |

---

## Tuning

Everything lives in `config.py`:

| Setting | Default | Effect |
|---|---|---|
| `chunk_size` | 900 | Larger = more context per chunk, less precise retrieval |
| `chunk_overlap` | 150 | Prevents ideas being split across a boundary |
| `top_k` | 5 | Chunks sent to the LLM per question |
| `min_similarity` | 0.25 | **Raise** if you get loose answers; **lower** if it refuses too often |
| `temperature` | 0.2 | Low on purpose — factual, not creative |

---

## Troubleshooting

| Symptom | Fix |
|---|---|
| "No OpenRouter API key found" | Add `OPENROUTER_API_KEY` to `.env` or Streamlit Secrets |
| 401 from OpenRouter | Key is wrong or revoked — regenerate at openrouter.ai/keys |
| 402 from OpenRouter | Out of credits |
| "No readable text found" | Scanned PDF — it's images, not text. Needs OCR first |
| Always says "couldn't find this" | Lower `min_similarity` in `config.py` |
| Slow first load | One-time embedding model download (~90 MB) |
| Build fails on Streamlit Cloud | Don't remove the `--extra-index-url` torch line |

---

## Security

- Keys are read from `.env` / Streamlit Secrets — never hardcoded.
- `.env` and `.streamlit/secrets.toml` are gitignored.
- Only *retrieved chunks* are sent to OpenRouter, never whole documents.

> The original ZIP had a live OpenRouter key committed in
> `.streamlit/secrets.toml`. If that key is still active, **rotate it now** at
> [openrouter.ai/keys](https://openrouter.ai/keys).
