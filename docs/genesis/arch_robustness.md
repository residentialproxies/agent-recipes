# Agent Navigator - Robustness-First Architecture

## Executive Summary

This architecture prioritizes **reliability over performance**, designed to survive failures gracefully while maintaining functionality. Uses static-first principles, aggressive caching, and multiple fallback layers.

---

## Tech Stack for 99.99% Uptime

| Layer          | Primary             | Fallback                | Rationale                                               |
| -------------- | ------------------- | ----------------------- | ------------------------------------------------------- |
| **Frontend**   | Streamlit           | Static HTML export      | Streamlit simplicity; static fallback for degraded mode |
| **Data Store** | SQLite + JSON files | In-memory cache         | No external DB dependencies                             |
| **Search**     | SQLite FTS5         | Simple Python filtering | Native full-text; no Elasticsearch                      |
| **AI Search**  | Claude API          | Keyword fallback        | Graceful degradation                                    |
| **Hosting**    | Streamlit Cloud     | GitHub Pages (static)   | Free tier; static fallback                              |
| **Cache**      | File-based (JSON)   | Memory dict             | Survives restarts                                       |

---

## Failure Modes and Recovery

| Failure Mode       | Detection            | Recovery                   | RTO     |
| ------------------ | -------------------- | -------------------------- | ------- |
| Streamlit crash    | Process monitor      | Auto-restart (3 attempts)  | <30s    |
| SQLite corruption  | Integrity check      | Rebuild from JSON backup   | <5min   |
| Claude API down    | Timeout + error code | Keyword search fallback    | Instant |
| GitHub unavailable | HTTP 5xx/timeout     | Use cached repository data | Instant |
| Memory exhaustion  | Threshold alert      | Restart + reduce cache     | <1min   |
| Disk full          | Space monitor        | Purge old caches           | <2min   |

---

## Security Features

1. **Input Validation**: Sanitize all user inputs, block SQL injection patterns
2. **Rate Limiting**: Token bucket (30 searches/min, 10 AI searches/min)
3. **Circuit Breaker**: Prevent cascade failures from external services
4. **Security Headers**: X-Content-Type-Options, X-Frame-Options, CSP

---

## Scaling Strategy

| Phase   | Users  | Architecture                      | Resources         |
| ------- | ------ | --------------------------------- | ----------------- |
| Phase 1 | 1-100  | Single Streamlit                  | 1 CPU, 1GB RAM    |
| Phase 2 | 100-1K | Load balanced (3 instances)       | 3 CPU, 3GB RAM    |
| Phase 3 | 1K-10K | Static site + Streamlit (AI only) | CDN + 3 instances |

---

## Backup Strategy

- **Frequency**: Every 6 hours
- **Retention**: Last 7 backups
- **Method**: SQLite backup API + JSON export
- **Verification**: SHA256 checksums
- **Recovery**: Point-in-time restore from any backup

---

## Monitoring

### Health Checks

- Database integrity
- Cache freshness
- Disk space
- Memory usage
- External API circuit state

### Metrics

- Request counters (success/error)
- Response time histograms (p50, p95, p99)
- Cache hit rates

### Alerting

- Error rate > 5%: Critical
- p95 latency > 3s: Warning
- Database unhealthy: Critical
- Disk < 1GB: Warning

---

## Confidence Score: 8/10

**Strengths:**

- Zero external dependencies for core functionality
- Multiple fallback layers ensure graceful degradation
- File-based state survives restarts
- Static fallback provides ultimate reliability

**Risks:**

- Streamlit scaling limits at 10K+ users
- SQLite write concurrency limitation
- No distributed state for horizontal scaling
