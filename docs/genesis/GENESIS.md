# GENESIS.md - Agent Navigator (v2)

## 1. Executive Summary

Agent Navigator transforms the awesome-llm-apps repository (100+ LLM application examples) into an intelligent discovery platform that helps developers find, evaluate, and clone the right agent for their use case in under 5 minutes. The MVP prioritizes simplicity and zero operational cost while maintaining sub-second search performance, targeting prototypers who need to quickly find working examples without wading through documentation.

**v2 Key Improvements:**

- LLM-enhanced indexer for deep metadata extraction (not just regex parsing)
- BM25 hybrid search (smarter than keyword, cheaper than embeddings)
- One-click playground links (Codespaces/Colab)
- Architecture visualization with Mermaid.js
- GitHub Actions automated refresh pipeline

---

## 2. Recommended Stack

| Layer             | Choice                    | Source       | Why                                                                                |
| ----------------- | ------------------------- | ------------ | ---------------------------------------------------------------------------------- |
| **Frontend**      | Streamlit                 | Simplicity   | Zero frontend complexity, rapid iteration                                          |
| **Data Store**    | JSON files                | Simplicity   | No database, version-controllable, ~100 agents fits fine                           |
| **Search**        | **BM25 (rank_bm25)**      | **Improved** | Smarter than keyword, zero API cost, "PDF bot" finds "Document Assistant"          |
| **Indexer**       | **LLM-enhanced**          | **Improved** | Claude extracts hidden tags: local model support, GPU requirement, design patterns |
| **AI Selector**   | Claude 3.5 Haiku          | Performance  | Low latency, streaming, cost-effective                                             |
| **Visualization** | **Mermaid.js**            | **Improved** | Auto-generate architecture flowcharts from tech_stack                              |
| **Hosting**       | Streamlit Community Cloud | Simplicity   | Free tier, zero DevOps                                                             |
| **Automation**    | **GitHub Actions**        | **Improved** | Weekly auto-sync, PR-based updates                                                 |

---

## 3. Trade-offs Accepted

| Sacrifice                 | Why Acceptable for MVP                                                   |
| ------------------------- | ------------------------------------------------------------------------ |
| **Vector embeddings**     | BM25 + LLM tags covers 95% of use cases; embeddings add infra complexity |
| **User accounts**         | No personalization needed; adds auth overhead                            |
| **Real-time sync**        | Weekly GitHub Actions refresh is sufficient                              |
| **Database**              | JSON handles 100 agents fine; SQLite is 2-hour migration if needed       |
| **Full Mermaid diagrams** | Start with simple flowcharts; complex viz is Phase 2                     |

---

## 4. Phase 1 Action Plan (MVP) - The 48-Hour Plan

### Hour 0-4: Data Layer (The Soul)

**File: `indexer.py` with LLM Enhancement**

1. Clone awesome-llm-apps repository
2. Walk directories, find all agent folders
3. **LLM Processing** (key improvement):
   - Feed each README to Claude 3.5 Haiku
   - Extract structured metadata:
     - `name`, `description`, `category`
     - `frameworks`: [langchain, crewai, autogen, raw_api...]
     - `llm_providers`: [openai, anthropic, ollama, local...]
     - `requires_gpu`: boolean
     - `supports_local_models`: boolean
     - `design_pattern`: [rag, react, plan_and_execute, multi_agent...]
     - `complexity`: [beginner, intermediate, advanced]
     - `quick_start`: installation + run commands
4. Output: `agents.json` with rich, searchable metadata

### Hour 4-8: Core UI

**File: `app.py` (<300 lines)**

1. Load agents.json into memory
2. **BM25 Search** (not simple `in`):
   - Tokenize all agent text (name + description + tags)
   - User searches "PDF bot" -> finds "Document Assistant"
3. Multi-dimensional filters:
   - Framework (LangChain, CrewAI, etc.)
   - LLM Provider (OpenAI, Anthropic, Local)
   - Complexity level
   - Design pattern
4. Agent cards with:
   - Title, one-line description
   - Framework/provider badges
   - **"Open in Codespaces"** button
   - **"Open in Colab"** button (if notebook exists)

### Hour 8-12: AI Feature + Visualization

1. **AI Selector**:
   - Natural language input: "I want to build a RAG chatbot for PDFs"
   - Claude Haiku returns top 3 matches with reasoning
   - Fallback to BM25 if API fails

2. **Architecture Preview** (Mermaid.js):
   - Auto-generate simple flowchart from `tech_stack`
   - Example: `User -> Streamlit -> LangChain -> OpenAI -> Response`

### Hour 12+: Deploy + Automate

1. Push to GitHub
2. Connect Streamlit Cloud
3. **Set up GitHub Actions**:
   ```yaml
   # .github/workflows/update-index.yml
   schedule:
     - cron: "0 0 * * 0" # Weekly Sunday
   jobs:
     update:
       - git pull awesome-llm-apps
       - python indexer.py
       - git commit -am "Update agents.json"
       - git push
   ```

---

## 5. Phase 2 Roadmap

**After MVP Validation:**

| Trigger                   | Upgrade                                      |
| ------------------------- | -------------------------------------------- |
| Search quality complaints | Add sentence embeddings (all-MiniLM-L6-v2)   |
| Users want comparison     | Side-by-side agent diff view                 |
| Traffic > 1000/day        | Move to VPS + SQLite FTS5                    |
| Data grows > 500 agents   | Multi-repo support (awesome-langchain, etc.) |

---

## 6. Key Risks (Updated)

### Risk 1: LLM Indexer Cost

- **Threat**: 100 agents x Claude API = $2-5 one-time cost
- **Mitigation**: Run only on new/changed agents, cache results
- **Reality**: This is a BUILD-TIME cost, not runtime. Acceptable.

### Risk 2: BM25 Search Quality

- **Threat**: May miss semantic matches
- **Mitigation**: LLM-generated tags act as "semantic bridges"
- **Fallback**: Add embedding layer in Phase 2

### Risk 3: Codespaces/Colab Links Break

- **Threat**: Not all repos support one-click run
- **Mitigation**: Validate links during indexing, hide button if invalid
- **Fallback**: Show "Clone locally" as default

---

## 7. Decision Points (Resolved)

| Question          | Decision                                               |
| ----------------- | ------------------------------------------------------ |
| AI Selector Scope | **MVP-critical** - key differentiator from GitHub      |
| Data Freshness    | **GitHub Actions weekly** - automated, hands-off       |
| Hosting           | **Streamlit Cloud** - start free, migrate if needed    |
| Scope             | **awesome-llm-apps only** - expand after validation    |
| Success Metric    | **100 weekly users + 10 GitHub clicks** in first month |

---

## 8. File Structure

```
agent-navigator/
├── app.py                    # Main Streamlit app (<300 lines)
├── indexer.py                # LLM-enhanced data extraction
├── search.py                 # BM25 search implementation
├── data/
│   └── agents.json           # Generated metadata (git-tracked)
├── .github/
│   └── workflows/
│       └── update-index.yml  # Weekly auto-refresh
├── requirements.txt
└── README.md
```

---

_Generated by Diamond Flow v2 | Stack: Simplicity + LLM-enhanced data + BM25 search_
