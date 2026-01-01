# Technical Debt Backlog - Agent Navigator

**Last Updated:** 2025-12-30
**Total Items:** 18
**Critical (P0):** 5 | High (P1):** 7 | Medium (P2):** 6

---

## P0 - Critical (Fix within 1 week)

### TD-001: Missing Input Validation

**File:** `/Volumes/SSD/dev/new/agent-recipes/src/app.py`
**Lines:** 93-104
**Risk:** Security vulnerability - SSRF, XSS, injection attacks

```python
# Current (INSECURE):
def fetch_readme_markdown(readme_url: str) -> str:
    parsed = urlparse(readme_url)
    if parsed.scheme not in ("http", "https") or parsed.netloc != "raw.githubusercontent.com":
        raise ValueError("Blocked README URL")
```

**Required Fix:**

- [ ] Implement URL whitelist validation
- [ ] Add path traversal checks
- [ ] Validate all user inputs (search queries, filters)
- [ ] Sanitize HTML output
- [ ] Add request size limits

**Estimated Effort:** 2 days

---

### TD-002: Client-Side Rate Limiting Bypassable

**File:** `/Volumes/SSD/dev/new/agent-recipes/src/app.py`
**Lines:** 130-139
**Risk:** API cost overrun, abuse

```python
# Current (BYPASSABLE):
history = st.session_state.get("_ai_calls", [])
if len(history) >= limit:
    return f"Rate limited..."
```

**Required Fix:**

- [ ] Implement server-side rate limiting with Redis
- [ ] Add per-IP tracking
- [ ] Implement API key quotas
- [ ] Add request signing
- [ ] Create admin override endpoint

**Estimated Effort:** 1 day

---

### TD-003: Bare Except Clauses Hide Errors

**Files:** Multiple
**Risk:** Silent failures, debugging nightmare

```python
# Current (BAD PRACTICE):
try:
    from src.search import AgentSearch
except Exception:  # ← Catches everything
    from search import AgentSearch
```

**Required Fix:**

- [ ] Replace all bare `except` with specific exceptions
- [ ] Add error logging
- [ ] Implement error monitoring (Sentry)
- [ ] Create error escalation policy

**Estimated Effort:** 1 day

---

### TD-004: API Keys in Environment Variables

**Files:** Multiple
**Risk:** Keys visible in process list, `ps aux`, `/proc`

**Required Fix:**

- [ ] Implement secret management service
- [ ] Add key rotation mechanism
- [ ] Use short-lived tokens
- [ ] Encrypt secrets at rest
- [ ] Audit secret access logs

**Estimated Effort:** 1 day

---

### TD-005: Unsanitized LLM Output

**File:** `/Volumes/SSD/dev/new/agent-recipes/src/indexer.py`
**Lines:** 469-491
**Risk:** Prompt injection, malicious JSON crashes parser

**Required Fix:**

- [ ] Implement JSON schema validation
- [ ] Add output sanitization
- [ ] Limit string lengths
- [ ] Validate enum values
- [ ] Add fallback for malformed data

**Estimated Effort:** 2 days

---

## P1 - High Priority (Fix within 1 month)

### TD-006: No Dependency Version Locking

**File:** `/Volumes/SSD/dev/new/agent-recipes/requirements.txt`
**Risk:** Deployment instability, reproducibility issues

**Required Fix:**

- [ ] Pin all dependency versions
- [ ] Add `requirements.lock` or use Poetry
- [ ] Implement dependency scanning in CI/CD
- [ ] Add security vulnerability scanning
- [ ] Document dependency update process

**Estimated Effort:** 1 day

---

### TD-007: Sequential LLM Processing (Performance)

**File:** `/Volumes/SSD/dev/new/agent-recipes/src/indexer.py`
**Lines:** 478-482
**Impact:** 5 min indexing time (should be <45 sec)

**Required Fix:**

- [ ] Implement async/await for LLM calls
- [ ] Add concurrent processing (10 parallel)
- [ ] Implement batching for API requests
- [ ] Add progress indicators
- [ ] Optimize file system scanning

**Estimated Effort:** 3 days

---

### TD-008: Insufficient Test Coverage

**Current:** ~15%
**Target:** 60%
**Risk:** Regression, deployment failures

**Required Fix:**

- [ ] Add unit tests for all modules
- [ ] Add integration tests for workflows
- [ ] Add performance benchmarks
- [ ] Add security tests
- [ ] Implement test coverage reporting

**Estimated Effort:** 5 days

---

### TD-009: No Logging/Monitoring

**Risk:** Production blindness, slow incident response

**Required Fix:**

- [ ] Implement structured logging
- [ ] Add request/response logging
- [ ] Set up error monitoring (Sentry)
- [ ] Implement performance metrics
- [ ] Create alerting rules

**Estimated Effort:** 2 days

---

### TD-010: Hardcoded Configuration Values

**Files:** Multiple
**Impact:** Deployment friction, testing difficulty

**Required Fix:**

- [ ] Create `config.py` with Pydantic settings
- [ ] Move all constants to config
- [ ] Add environment-specific configs
- [ ] Implement config validation
- [ ] Document all configuration options

**Estimated Effort:** 1 day

---

### TD-011: No Database Migration Path

**Current:** JSON files
**Risk:** Scalability blocker at 500+ agents

**Required Fix:**

- [ ] Implement Repository pattern
- [ ] Add SQLite backend option
- [ ] Create data migration scripts
- [ ] Add feature flags for backend switch
- [ ] Document migration procedure

**Estimated Effort:** 3 days

---

### TD-012: Missing Critical SEO Meta Tags

**File:** `/Volumes/SSD/dev/new/agent-recipes/src/export_static.py`
**Impact:** Poor search engine discoverability

**Required Fix:**

- [ ] Add Open Graph tags
- [ ] Add Twitter Card meta tags
- [ ] Implement JSON-LD structured data
- [ ] Improve URL structure with slugs
- [ ] Generate category landing pages

**Estimated Effort:** 2 days

---

## P2 - Medium Priority (Technical improvements)

### TD-013: No Code Formatter Enforced

**Impact:** Inconsistent code style

**Required Fix:**

- [ ] Add black to project
- [ ] Add ruff for linting
- [ ] Add mypy for type checking
- [ ] Configure pre-commit hooks
- [ ] Add to CI/CD pipeline

**Estimated Effort:** 1 day

---

### TD-014: Functions Too Long

**Files:** `app.py`, `indexer.py`
**Impact:** Maintainability, testing difficulty

**Required Fix:**

- [ ] Split `render_search_page()` (119 lines)
- [ ] Split `_heuristic_extract()` (110 lines)
- [ ] Extract smaller helper functions
- [ ] Improve function cohesion
- [ ] Add function documentation

**Estimated Effort:** 2 days

---

### TD-015: Missing Type Hints

**Coverage:** ~70%
**Target:** >90%

**Required Fix:**

- [ ] Add type hints to all functions
- [ ] Run mypy in strict mode
- [ ] Fix type errors
- [ ] Add type stubs for external libs
- [ ] Enable type checking in CI/CD

**Estimated Effort:** 2 days

---

### TD-016: No API Documentation

**Impact:** Onboarding friction, maintenance

**Required Fix:**

- [ ] Generate API docs with Sphinx/MkDocs
- [ ] Add docstrings to all public functions
- [ ] Create architecture diagrams
- [ ] Add usage examples
- [ ] Set up auto-deployment of docs

**Estimated Effort:** 3 days

---

### TD-017: No Performance Benchmarks

**Risk:** Performance regressions undetected

**Required Fix:**

- [ ] Create benchmark suite
- [ ] Add baseline measurements
- [ ] Implement regression detection
- [ ] Add to CI/CD pipeline
- [ ] Create performance dashboard

**Estimated Effort:** 2 days

---

### TD-018: CSS/JS Not Minified

**File:** `/Volumes/SSD/dev/new/agent-recipes/src/export_static.py`
**Impact:** Slower page loads, bandwidth waste

**Required Fix:**

- [ ] Minify CSS in production
- [ ] Minify JS in production
- [ ] Add build step optimization
- [ ] Implement asset versioning
- [ ] Add gzip compression

**Estimated Effort:** 1 day

---

## Summary Statistics

**Total Effort Required:**

- P0 (Critical): 7 days
- P1 (High): 18 days
- P2 (Medium): 13 days
- **Total: 38 days (~8 weeks)**

**Recommended Timeline:**

- Week 1: Complete all P0 items
- Weeks 2-4: Complete P1 items (TD-006 through TD-009)
- Weeks 5-8: Complete remaining P1 items and start P2 items

**Risk if Not Addressed:**

- P0 items: Security breach, production downtime
- P1 items: Performance degradation, scalability blockers
- P2 items: Maintainability issues, developer friction

---

## Quick Reference Commands

```bash
# Security scan
pip install safety bandit
safety check
bandit -r src/

# Type checking
mypy src/ --strict

# Formatting
black src/ tests/
ruff check src/ tests/

# Testing with coverage
pytest --cov=src --cov-report=html --cov-report=term

# Performance benchmarking
pytest tests/ --benchmark-only

# Dependency audit
pip-audit
pip install pip-check
pip-check
```

---

**Next Review:** 2025-01-06 (Weekly during P0 resolution)
**Owner:** Development Team
**Status:** Active
