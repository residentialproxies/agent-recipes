"""
UI styling (CSS injected via st.markdown).
"""

from __future__ import annotations

import streamlit as st

BASE_CSS = """
<style>
  .block-container { padding-top: 1.5rem; padding-bottom: 2rem; }
  [data-testid="stMetricValue"] { font-size: 1.1rem; }
  .onboarding-popup {
    position: fixed;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    background: white;
    padding: 2rem;
    border-radius: 10px;
    box-shadow: 0 4px 20px rgba(0,0,0,0.3);
    z-index: 9999;
    max-width: 500px;
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
    background: #f0f0f0;
    padding: 2px 6px;
    border-radius: 4px;
    font-family: monospace;
    font-size: 0.85rem;
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


def apply_styles() -> None:
    st.markdown(BASE_CSS, unsafe_allow_html=True)
    st.markdown(RESPONSIVE_CSS, unsafe_allow_html=True)
