"""
UI styling (CSS injected via st.markdown).
"""

from __future__ import annotations

import streamlit as st

# Dark mode CSS variables + theme toggle
THEME_CSS = """
<style>
  :root {
    --bg-primary: #ffffff;
    --bg-secondary: #f8f9fa;
    --bg-tertiary: #f0f0f0;
    --text-primary: #1a1a1a;
    --text-secondary: #6b7280;
    --text-muted: #9ca3af;
    --border-color: #e5e7eb;
    --accent: #667eea;
    --accent-hover: #5a67d8;
    --accent-light: #e0e7ff;
    --card-bg: #ffffff;
    --shadow-color: rgba(0, 0, 0, 0.1);
    --skeleton-start: #f0f0f0;
    --skeleton-mid: #e0e0e0;
    --skeleton-end: #f0f0f0;
    --comparison-bg: #f8f9fa;
    --comparison-border: #e9ecef;
    --comparison-diff: #fff3cd;
    --comparison-diff-border: #ffc107;
    --onboarding-bg: #ffffff;
    --keyboard-bg: #f0f0f0;
    --loading-overlay: rgba(255,255,255,0.7);
    --skeleton-card-bg: #fafafa;
    --skeleton-card-border: #e0e0e0;
  }

  [data-theme="dark"] {
    --bg-primary: #0f0f0f;
    --bg-secondary: #1a1a1a;
    --bg-tertiary: #262626;
    --text-primary: #f5f5f5;
    --text-secondary: #a3a3a3;
    --text-muted: #737373;
    --border-color: #333333;
    --accent: #818cf8;
    --accent-hover: #a5b4fc;
    --accent-light: #1e1b4b;
    --card-bg: #1a1a1a;
    --shadow-color: rgba(0, 0, 0, 0.4);
    --skeleton-start: #262626;
    --skeleton-mid: #333333;
    --skeleton-end: #262626;
    --comparison-bg: #262626;
    --comparison-border: #404040;
    --comparison-diff: #422006;
    --comparison-diff-border: #b45309;
    --onboarding-bg: #1a1a1a;
    --keyboard-bg: #262626;
    --loading-overlay: rgba(0,0,0,0.7);
    --skeleton-card-bg: #1a1a1a;
    --skeleton-card-border: #333333;
  }

  /* Apply theme to Streamlit elements */
  .main {
    background-color: var(--bg-primary);
    color: var(--text-primary);
  }

  [data-testid="stAppViewContainer"] {
    background-color: var(--bg-primary);
  }

  [data-testid="stSidebar"] {
    background-color: var(--bg-secondary);
    border-right: 1px solid var(--border-color);
  }

  [data-testid="stSidebarContent"] {
    background-color: transparent;
  }

  /* Theme toggle button */
  .theme-toggle {
    position: fixed;
    top: 1rem;
    right: 1rem;
    z-index: 9999;
    background: var(--bg-secondary);
    border: 1px solid var(--border-color);
    border-radius: 50%;
    width: 44px;
    height: 44px;
    display: flex;
    align-items: center;
    justify-content: center;
    cursor: pointer;
    box-shadow: 0 2px 10px var(--shadow-color);
    transition: all 0.2s ease;
  }

  .theme-toggle:hover {
    background: var(--bg-tertiary);
    transform: scale(1.05);
  }

  .theme-toggle svg {
    width: 22px;
    height: 22px;
    fill: var(--text-primary);
  }

  .theme-toggle .sun-icon { display: block; }
  .theme-toggle .moon-icon { display: none; }

  [data-theme="dark"] .theme-toggle .sun-icon { display: none; }
  [data-theme="dark"] .theme-toggle .moon-icon { display: block; }
</style>
"""

BASE_CSS = """
<style>
  .block-container { padding-top: 1.5rem; padding-bottom: 2rem; }
  [data-testid="stMetricValue"] { font-size: 1.1rem; }
  .onboarding-popup {
    position: fixed;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    background: var(--onboarding-bg);
    padding: 2rem;
    border-radius: 10px;
    box-shadow: 0 4px 20px var(--shadow-color);
    z-index: 9999;
    max-width: 500px;
    border: 1px solid var(--border-color);
  }
  .trending-badge {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    padding: 2px 8px;
    border-radius: 12px;
    font-size: 0.75rem;
    font-weight: bold;
  }
  .new-badge {
    background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
    color: white;
    padding: 2px 8px;
    border-radius: 12px;
    font-size: 0.75rem;
    font-weight: bold;
  }
  .keyboard-shortcut {
    background: var(--keyboard-bg);
    padding: 2px 6px;
    border-radius: 4px;
    font-family: monospace;
    font-size: 0.85rem;
    color: var(--text-primary);
    border: 1px solid var(--border-color);
  }
  /* Skeleton loading styles */
  .skeleton {
    background: linear-gradient(90deg, var(--skeleton-start) 25%, var(--skeleton-mid) 50%, var(--skeleton-end) 75%);
    background-size: 200% 100%;
    animation: skeleton-loading 1.5s infinite;
    border-radius: 4px;
  }
  @keyframes skeleton-loading {
    0% { background-position: 200% 0; }
    100% { background-position: -200% 0; }
  }
  .skeleton-title {
    height: 24px;
    width: 60%;
    margin-bottom: 8px;
  }
  .skeleton-text {
    height: 16px;
    width: 100%;
    margin-bottom: 6px;
  }
  .skeleton-text-short {
    height: 16px;
    width: 70%;
  }
  .skeleton-badge {
    height: 20px;
    width: 60px;
    display: inline-block;
    margin-right: 6px;
    border-radius: 4px;
  }
  .skeleton-button {
    height: 36px;
    width: 100%;
    border-radius: 4px;
  }
  .skeleton-card {
    padding: 1rem;
    border: 1px solid var(--skeleton-card-border);
    border-radius: 8px;
    background: var(--skeleton-card-bg);
  }
  .loading-overlay {
    position: relative;
  }
  .loading-overlay::after {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: var(--loading-overlay);
    display: flex;
    align-items: center;
    justify-content: center;
  }
  .retry-button {
    margin-top: 1rem;
  }
  /* Comparison table styles */
  .comparison-bar {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    padding: 12px 16px;
    border-radius: 8px;
    margin-bottom: 16px;
    text-align: center;
  }
  .comparison-cell {
    background: var(--comparison-bg);
    border: 1px solid var(--comparison-border);
    border-radius: 6px;
    padding: 12px;
    min-height: 40px;
    text-align: center;
    color: var(--text-primary);
  }
  .comparison-cell-diff {
    background: var(--comparison-diff);
    border-color: var(--comparison-diff-border);
    font-weight: 500;
  }
  /* Card backgrounds */
  .agent-card {
    background: var(--card-bg);
    border: 1px solid var(--border-color);
    border-radius: 8px;
    padding: 1rem;
    transition: box-shadow 0.2s ease;
  }
  .agent-card:hover {
    box-shadow: 0 4px 15px var(--shadow-color);
  }
</style>
"""

RESPONSIVE_CSS = """
<style>
  @media (max-width: 768px) {
    .block-container { padding-left: 1rem; padding-right: 1rem; }
    /* Avoid iOS zoom on focus */
    .stTextInput input, .stTextArea textarea, .stSelectbox select { font-size: 16px !important; }
    /* 44x44 touch targets */
    .stButton button, .stDownloadButton button, .stLinkButton a {
      min-height: 44px !important;
      padding-top: 0.6rem !important;
      padding-bottom: 0.6rem !important;
    }
    /* Make Streamlit columns stack vertically */
    [data-testid="stAppViewContainer"] .stHorizontalBlock {
      flex-wrap: wrap !important;
      gap: 0.75rem !important;
    }
    [data-testid="stAppViewContainer"] .stHorizontalBlock > div {
      flex: 1 1 100% !important;
      width: 100% !important;
      min-width: 0 !important;
    }
    /* Prevent long content from forcing horizontal scroll */
    [data-testid="stMarkdownContainer"] { overflow-wrap: anywhere; }
    [data-testid="stMarkdownContainer"] table { display: block; overflow-x: auto; width: 100%; }
    [data-testid="stMarkdownContainer"] pre { overflow-x: auto; max-width: 100%; }
    /* Prevent accidental horizontal scroll */
    html, body, [data-testid="stAppViewContainer"] { overflow-x: hidden; }
  }
</style>
"""


THEME_JS = """
<script>
(function() {
    const THEME_KEY = 'agent_navigator_theme';

    // Get saved theme or prefer system preference
    function getInitialTheme() {
        const saved = localStorage.getItem(THEME_KEY);
        if (saved === 'dark' || saved === 'light') return saved;

        // Check system preference
        if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
            return 'dark';
        }
        return 'light';
    }

    // Apply theme to document
    function applyTheme(theme) {
        document.documentElement.setAttribute('data-theme', theme);
        localStorage.setItem(THEME_KEY, theme);
    }

    // Toggle theme
    function toggleTheme() {
        const current = document.documentElement.getAttribute('data-theme') || 'light';
        const next = current === 'dark' ? 'light' : 'dark';
        applyTheme(next);
    }

    // Initialize theme on load
    const initialTheme = getInitialTheme();
    applyTheme(initialTheme);

    // Create theme toggle button
    function createThemeToggle() {
        const existing = document.querySelector('.theme-toggle');
        if (existing) return;

        const button = document.createElement('button');
        button.className = 'theme-toggle';
        button.setAttribute('aria-label', 'Toggle theme');
        button.innerHTML = `
            <svg class="sun-icon" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                <path d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z" stroke="currentColor" stroke-width="2" stroke-linecap="round" fill="none"/>
            </svg>
            <svg class="moon-icon" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                <path d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" fill="none"/>
            </svg>
        `;
        button.addEventListener('click', toggleTheme);
        document.body.appendChild(button);
    }

    // Listen for system theme changes
    if (window.matchMedia) {
        window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', (e) => {
            // Only auto-switch if user hasn't manually set a preference
            if (!localStorage.getItem(THEME_KEY)) {
                applyTheme(e.matches ? 'dark' : 'light');
            }
        });
    }

    // Create toggle when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', createThemeToggle);
    } else {
        createThemeToggle();
    }

    // Expose globally
    window.AgentTheme = {
        toggle: toggleTheme,
        apply: applyTheme,
        get: () => document.documentElement.getAttribute('data-theme')
    };
})();
</script>
"""

SEARCH_JS = """
<script>
(function() {
    // Search history management (max 5 entries)
    const HISTORY_KEY = 'agent_search_history';
    const MAX_HISTORY = 5;

    function getSearchHistory() {
        try {
            return JSON.parse(localStorage.getItem(HISTORY_KEY) || '[]');
        } catch {
            return [];
        }
    }

    function saveSearchHistory(query) {
        query = query.trim();
        if (!query) return;
        const history = getSearchHistory().filter(q => q !== query);
        history.unshift(query);
        localStorage.setItem(HISTORY_KEY, JSON.stringify(history.slice(0, MAX_HISTORY)));
    }

    function clearSearchHistory() {
        localStorage.removeItem(HISTORY_KEY);
    }

    // Debounce function
    let searchTimeout;
    function debounceSearch(func, delay) {
        return function(...args) {
            clearTimeout(searchTimeout);
            searchTimeout = setTimeout(() => func.apply(this, args), delay);
        };
    }

    // Keyboard shortcuts
    document.addEventListener('keydown', (e) => {
        // '/' to focus search input
        if (e.key === '/' && !['INPUT', 'TEXTAREA', 'SELECT'].includes(document.activeElement?.tagName)) {
            e.preventDefault();
            const searchInput = document.querySelector('input[data-testid="stTextInput"]');
            if (searchInput) {
                searchInput.focus();
                searchInput.select();
            }
        }

        // Escape to clear search
        if (e.key === 'Escape') {
            const searchInput = document.querySelector('input[data-testid="stTextInput"]');
            if (searchInput && document.activeElement === searchInput) {
                searchInput.value = '';
                searchInput.dispatchEvent(new Event('input', { bubbles: true }));
            }
        }

        // Arrow navigation for search history (Ctrl/Cmd + Up/Down)
        if ((e.ctrlKey || e.metaKey) && document.activeElement?.tagName === 'INPUT') {
            const history = getSearchHistory();
            let currentIndex = parseInt(document.activeElement.dataset.historyIndex || '-1');

            if (e.key === 'ArrowDown') {
                e.preventDefault();
                currentIndex = Math.min(currentIndex + 1, history.length - 1);
                if (history[currentIndex]) {
                    document.activeElement.value = history[currentIndex];
                    document.activeElement.dataset.historyIndex = currentIndex;
                }
            } else if (e.key === 'ArrowUp') {
                e.preventDefault();
                currentIndex = Math.max(currentIndex - 1, 0);
                if (history[currentIndex]) {
                    document.activeElement.value = history[currentIndex];
                    document.activeElement.dataset.historyIndex = currentIndex;
                }
            }
        }
    });

    // Highlight matching keywords in search results
    function highlightKeywords(container, query) {
        if (!query || !container) return;
        const keywords = query.toLowerCase().split(/\\s+/).filter(k => k.length > 2);
        if (keywords.length === 0) return;

        const regex = new RegExp(`(${keywords.map(k => k.replace(/[.*+?^${}()|[\\]\\\\]/g, '\\\\$&')).join('|')})`, 'gi');
        const highlights = container.querySelectorAll('.search-highlight-target');

        highlights.forEach(el => {
            const originalText = el.dataset.originalText || el.textContent;
            if (!el.dataset.originalText) el.dataset.originalText = originalText;
            el.innerHTML = originalText.replace(regex, '<mark class="search-highlight">$1</mark>');
        });
    }

    // Debounced search input handler
    const debouncedSearch = debounceSearch(function(value) {
        saveSearchHistory(value);
        // Trigger Streamlit rerun by dispatching change event
        const searchInput = document.querySelector('input[data-testid="stTextInput"]');
        if (searchInput && value !== searchInput.value) {
            searchInput.value = value;
        }
    }, 500);

    // Observe for search input changes with debounce
    const observer = new MutationObserver(() => {
        const searchInput = document.querySelector('input[data-testid="stTextInput"]');
        if (searchInput && !searchInput.dataset.enhanced) {
            searchInput.dataset.enhanced = 'true';
            searchInput.setAttribute('autocomplete', 'off');
            searchInput.setAttribute('list', 'search-history');

            // Create datalist for search history
            let datalist = document.getElementById('search-history');
            if (!datalist) {
                datalist = document.createElement('datalist');
                datalist.id = 'search-history';
                document.body.appendChild(datalist);
            }

            // Update datalist with history on focus
            searchInput.addEventListener('focus', () => {
                const history = getSearchHistory();
                datalist.innerHTML = history.map(q => `<option value="${q.replace(/"/g, '&quot;')}">`).join('');
            });

            // Debounce input events
            searchInput.addEventListener('input', (e) => {
                debouncedSearch(e.target.value);
            });
        }
    });

    observer.observe(document.body, { childList: true, subtree: true });

    // Expose globally for external use
    window.AgentSearchEnhancements = {
        getSearchHistory,
        saveSearchHistory,
        clearSearchHistory,
        highlightKeywords
    };
})();
</script>
"""

SEARCH_HIGHLIGHT_CSS = """
<style>
  mark.search-highlight {
    background: linear-gradient(120deg, #ffd54f 0%, #ffeb3b 100%);
    color: #000;
    padding: 0 2px;
    border-radius: 2px;
    font-weight: 500;
  }
  .search-history-indicator {
    position: absolute;
    right: 8px;
    top: 50%;
    transform: translateY(-50%);
    color: #888;
    font-size: 0.8rem;
    pointer-events: none;
  }
</style>
"""


def apply_styles() -> None:
    st.markdown(THEME_CSS, unsafe_allow_html=True)
    st.markdown(BASE_CSS, unsafe_allow_html=True)
    st.markdown(RESPONSIVE_CSS, unsafe_allow_html=True)
    st.markdown(SEARCH_HIGHLIGHT_CSS, unsafe_allow_html=True)
    st.markdown(THEME_JS, unsafe_allow_html=True)
    st.markdown(SEARCH_JS, unsafe_allow_html=True)
