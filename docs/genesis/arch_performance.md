# Agent Navigator - Performance-Optimized Architecture

## Executive Summary

A sub-100ms search architecture for 100+ LLM agent examples, built on Streamlit with aggressive caching and pre-computation strategies.

---

## Tech Stack Selection

| Layer           | Choice                                | Rationale                                                    |
| --------------- | ------------------------------------- | ------------------------------------------------------------ |
| **Frontend**    | Streamlit + st.cache_data             | Native Python, zero JS overhead, built-in caching            |
| **Database**    | SQLite + FTS5                         | Single-file, in-process, fastest for read-heavy <10K records |
| **Search**      | SQLite FTS5 + Pre-computed embeddings | No external service latency                                  |
| **AI Selector** | Claude 3.5 Haiku via streaming        | Fastest Claude model, streaming for perceived speed          |
| **Caching**     | Multi-layer: Memory -> SQLite -> File | Sub-ms cache hits                                            |
| **Hosting**     | Single VPS with NVMe                  | No network hops between components                           |

---

## Database Schema (SQLite + FTS5)

```sql
CREATE TABLE agents (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    category TEXT,
    tech_stack TEXT,
    github_url TEXT,
    readme_html TEXT,
    quick_start TEXT,
    stars INTEGER DEFAULT 0,
    embedding BLOB,
    created_at INTEGER,
    updated_at INTEGER
);

CREATE VIRTUAL TABLE agents_fts USING fts5(
    name, description, tech_stack, category,
    content='agents',
    tokenize='porter unicode61'
);

CREATE INDEX idx_category ON agents(category);
CREATE INDEX idx_tech_stack ON agents(tech_stack);
CREATE INDEX idx_stars ON agents(stars DESC);
```

---

## Caching Strategy

### Three-Layer Cache Architecture

| Layer | Storage              | TTL     | Latency |
| ----- | -------------------- | ------- | ------- |
| L1    | Python Memory (dict) | Session | <0.1ms  |
| L2    | st.cache_data        | 1 hour  | <1ms    |
| L3    | SQLite query cache   | 6 hours | <5ms    |

---

## Search Performance Targets

| Query Type          | Expected Latency | Technique                  |
| ------------------- | ---------------- | -------------------------- |
| Empty (list all)    | <5ms             | Pre-cached full list       |
| Keyword (1-2 words) | <20ms            | FTS5 with BM25             |
| Phrase search       | <30ms            | FTS5 phrase matching       |
| Semantic search     | <80ms            | Pre-loaded vectors + NumPy |
| Filtered search     | +5-10ms          | Covering index lookups     |

---

## AI Selector Optimization

- Use Claude 3.5 Haiku for fastest response
- Stream responses for perceived speed
- Time to first token: ~200-400ms
- Pre-compute agent summary for prompt

---

## Performance Budget

| Operation          | Budget | Technique                    |
| ------------------ | ------ | ---------------------------- |
| Initial page load  | <500ms | Pre-loaded data, cached HTML |
| Search query       | <100ms | FTS5 + in-memory vectors     |
| Filter change      | <50ms  | Covering indexes             |
| Agent detail page  | <200ms | Pre-rendered README HTML     |
| AI selector (TTFT) | <400ms | Haiku + streaming            |

---

## Confidence Score: 8/10

**Strengths:**

- SQLite FTS5 is proven fast for this scale
- Pre-computed embeddings eliminate runtime ML inference
- Streamlit caching is mature and well-tested
- Single-process architecture eliminates network latency

**Risks:**

- Streamlit may add UI overhead (~50-100ms)
- Claude Haiku TTFT varies with load
- Vector search quality depends on embedding model
