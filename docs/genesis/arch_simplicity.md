# Agent Navigator - Simplest Architecture

## Overview

A single Streamlit app that displays searchable, filterable cards for 100+ LLM examples. Everything runs from one Python file with JSON data files.

---

## Tech Stack

| Layer                  | Choice                    | Why                                             |
| ---------------------- | ------------------------- | ----------------------------------------------- |
| **Frontend + Backend** | Streamlit                 | Single file, Python-only, built-in UI           |
| **Data Storage**       | JSON files                | No database, version controlled, human readable |
| **Search**             | Python keyword matching   | Zero dependencies, good enough for 100 items    |
| **AI Search**          | OpenAI API (optional)     | Single API call, can disable                    |
| **Hosting**            | Streamlit Community Cloud | Free, one-click deploy                          |
| **Indexing**           | Python script (manual)    | Run once, output JSON                           |

---

## File Structure

```
agent-navigator/
├── app.py                 # Single Streamlit app (< 300 lines)
├── indexer.py             # One-time script to generate data
├── data/
│   └── agents.json        # All agent metadata (~50KB)
├── requirements.txt       # streamlit, openai (optional)
└── README.md
```

---

## Data Model (agents.json)

```json
[
  {
    "id": "ai-finance-agent",
    "name": "AI Finance Agent",
    "description": "Personal finance advisor using GPT-4",
    "category": "finance",
    "tech_stack": ["openai", "langchain", "streamlit"],
    "difficulty": "beginner",
    "github_url": "https://github.com/...",
    "quick_start": "pip install -r requirements.txt && streamlit run app.py"
  }
]
```

---

## MVP Features

### Build Now

| Feature           | Implementation        | Effort  |
| ----------------- | --------------------- | ------- |
| Card Grid         | st.columns() + CSS    | 2 hours |
| Text Search       | Python `in` operator  | 30 min  |
| Category Filter   | st.selectbox()        | 30 min  |
| Tech Stack Filter | st.multiselect()      | 30 min  |
| Agent Detail      | query_params + README | 2 hours |
| Quick Start Box   | Copy-paste block      | 30 min  |

### Defer to V2

- AI-powered natural language search
- Similar agents recommendations
- User favorites/history
- Auto-refresh from GitHub

---

## Cost Estimate

| Item                      | Cost                |
| ------------------------- | ------------------- |
| Streamlit Community Cloud | **Free**            |
| GitHub repo               | **Free**            |
| OpenAI API (optional)     | ~$0.01/100 searches |
| Domain (optional)         | ~$12/year           |

**Total MVP Cost: $0**

---

## Deployment

```bash
git push origin main
# Streamlit Cloud auto-deploys
```

---

## Why This is the Simplest

1. **One language** (Python only)
2. **One file** for the app
3. **No database** (JSON files)
4. **No backend server** (Streamlit handles everything)
5. **No build step** (no webpack, no npm)
6. **No Docker** (Streamlit Cloud handles deployment)
7. **No authentication** (public read-only site)
8. **Free hosting** (zero infrastructure cost)

---

## Confidence Score: 9/10

**Why not 10**: Streamlit's UI customization is limited. May need migration if heavy branding required.

**Time to MVP**: 1 weekend (8-12 hours)

**Maintainability**: A junior Python developer can maintain and extend this.
