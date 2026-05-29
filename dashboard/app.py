"""
AEGIS Dashboard - Automated Answer Script Grading System
A Streamlit-based web interface for submitting answer scripts and viewing grading results.
"""

import streamlit as st
import json
import time
import os
import requests
import redis
import streamlit.components.v1 as components
from datetime import datetime
from typing import Dict, Optional, List, Any
import pandas as pd
from api_client import AEGISClient

# Configuration
API_BASE_URL = st.secrets.get("API_BASE_URL", "http://localhost:8000")
OCR_SERVER_URL = os.environ.get("OCR_SERVER_URL", st.secrets.get("OCR_SERVER_URL", "http://localhost:5000"))

# Redis Configuration
redis_host = os.environ.get("REDIS_HOST", st.secrets.get("REDIS_HOST", "localhost"))
redis_port = os.environ.get("REDIS_PORT", st.secrets.get("REDIS_PORT", 6379))
redis_user = os.environ.get("REDIS_USERNAME", st.secrets.get("REDIS_USERNAME", ""))
redis_password = os.environ.get("REDIS_PASSWORD", st.secrets.get("REDIS_PASSWORD", ""))

if redis_password:
    if redis_user:
        REDIS_URL = f"redis://{redis_user}:{redis_password}@{redis_host}:{redis_port}/0"
    else:
        REDIS_URL = f"redis://:{redis_password}@{redis_host}:{redis_port}/0"
else:
    REDIS_URL = os.environ.get("REDIS_URL", f"redis://{redis_host}:{redis_port}/0")

AGENT_NAME = "aegis-agent"

# Initialize Client
client = AEGISClient(base_url=API_BASE_URL)

# Page configuration
st.set_page_config(
    page_title="AEGIS - Automated Grading System",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS for a polished, colorful Streamlit UI
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Google+Sans:wght@400;500;600;700;800&family=Inter:wght@400;500;600;700&display=swap');

    :root {
        --google-blue: #4285F4;
        --google-red: #EA4335;
        --google-yellow: #FBBC04;
        --google-green: #34A853;
        --ink: #202124;
        --muted: #5f6368;
        --heading: #3c4043;
        --app-bg: #f8fbff;
        --surface: rgba(255, 255, 255, 0.88);
        --surface-soft: rgba(255, 255, 255, 0.72);
        --surface-strong: rgba(255, 255, 255, 0.94);
        --input-bg: rgba(255, 255, 255, 0.92);
        --input-focus-bg: #ffffff;
        --placeholder: #6f7277;
        --blue-ink: #174ea6;
        --yellow-ink: #7a4f00;
        --green-ink: #137333;
        --red-ink: #a50e0e;
        --line: rgba(32, 33, 36, 0.1);
        --shadow: 0 18px 45px rgba(60, 64, 67, 0.16);
        --soft-shadow: 0 8px 24px rgba(60, 64, 67, 0.10);
        --app-gradient:
            linear-gradient(145deg, rgba(66, 133, 244, 0.13), rgba(255, 255, 255, 0) 34%),
            linear-gradient(235deg, rgba(251, 188, 4, 0.16), rgba(255, 255, 255, 0) 38%),
            linear-gradient(340deg, rgba(52, 168, 83, 0.13), rgba(234, 67, 53, 0.07) 52%, rgba(255, 255, 255, 0) 70%);
        --sidebar-gradient:
            linear-gradient(180deg, rgba(255, 255, 255, 0.94), rgba(248, 251, 255, 0.9)),
            linear-gradient(135deg, rgba(66, 133, 244, 0.10), rgba(251, 188, 4, 0.10));
        --hero-gradient:
            linear-gradient(100deg, rgba(255,255,255,0.94), rgba(255,255,255,0.72)),
            linear-gradient(135deg, rgba(66, 133, 244, 0.22), rgba(251, 188, 4, 0.24) 46%, rgba(52, 168, 83, 0.18));
        --metric-gradient:
            linear-gradient(180deg, rgba(255, 255, 255, 0.92), rgba(248, 251, 255, 0.84)),
            linear-gradient(135deg, rgba(66, 133, 244, 0.12), rgba(52, 168, 83, 0.08));
    }

    @media (prefers-color-scheme: dark) {
        :root {
            --google-blue: #8ab4f8;
            --google-red: #f28b82;
            --google-yellow: #fdd663;
            --google-green: #81c995;
            --ink: #f1f3f4;
            --muted: #c1c7d0;
            --heading: #e8eaed;
            --app-bg: #0f1117;
            --surface: rgba(27, 31, 43, 0.86);
            --surface-soft: rgba(30, 34, 47, 0.78);
            --surface-strong: rgba(35, 39, 52, 0.94);
            --input-bg: rgba(19, 22, 31, 0.96);
            --input-focus-bg: rgba(24, 28, 39, 0.98);
            --placeholder: #aeb4bf;
            --blue-ink: #d2e3fc;
            --yellow-ink: #fef2c0;
            --green-ink: #ceead6;
            --red-ink: #fad2cf;
            --line: rgba(232, 234, 237, 0.14);
            --shadow: 0 24px 58px rgba(0, 0, 0, 0.45);
            --soft-shadow: 0 12px 30px rgba(0, 0, 0, 0.35);
            --app-gradient:
                linear-gradient(145deg, rgba(138, 180, 248, 0.18), rgba(15, 17, 23, 0) 34%),
                linear-gradient(235deg, rgba(253, 214, 99, 0.13), rgba(15, 17, 23, 0) 40%),
                linear-gradient(340deg, rgba(129, 201, 149, 0.13), rgba(242, 139, 130, 0.09) 54%, rgba(15, 17, 23, 0) 72%);
            --sidebar-gradient:
                linear-gradient(180deg, rgba(28, 32, 43, 0.96), rgba(19, 22, 31, 0.93)),
                linear-gradient(135deg, rgba(138, 180, 248, 0.12), rgba(253, 214, 99, 0.08));
            --hero-gradient:
                linear-gradient(100deg, rgba(31, 35, 48, 0.96), rgba(21, 24, 34, 0.84)),
                linear-gradient(135deg, rgba(138, 180, 248, 0.19), rgba(253, 214, 99, 0.14) 46%, rgba(129, 201, 149, 0.16));
            --metric-gradient:
                linear-gradient(180deg, rgba(31, 35, 48, 0.94), rgba(21, 24, 34, 0.90)),
                linear-gradient(135deg, rgba(138, 180, 248, 0.14), rgba(129, 201, 149, 0.09));
        }
    }

    html[data-theme="dark"],
    body[data-theme="dark"],
    .stApp[data-theme="dark"],
    [data-theme="dark"],
    html[data-aegis-theme="dark"],
    html[data-aegis-theme="dark"] body,
    html[data-aegis-theme="dark"] .stApp {
        --google-blue: #8ab4f8;
        --google-red: #f28b82;
        --google-yellow: #fdd663;
        --google-green: #81c995;
        --ink: #f1f3f4;
        --muted: #c1c7d0;
        --heading: #e8eaed;
        --app-bg: #0f1117;
        --surface: rgba(27, 31, 43, 0.86);
        --surface-soft: rgba(30, 34, 47, 0.78);
        --surface-strong: rgba(35, 39, 52, 0.94);
        --input-bg: rgba(19, 22, 31, 0.96);
        --input-focus-bg: rgba(24, 28, 39, 0.98);
        --placeholder: #aeb4bf;
        --blue-ink: #d2e3fc;
        --yellow-ink: #fef2c0;
        --green-ink: #ceead6;
        --red-ink: #fad2cf;
        --line: rgba(232, 234, 237, 0.14);
        --shadow: 0 24px 58px rgba(0, 0, 0, 0.45);
        --soft-shadow: 0 12px 30px rgba(0, 0, 0, 0.35);
        --app-gradient:
            linear-gradient(145deg, rgba(138, 180, 248, 0.18), rgba(15, 17, 23, 0) 34%),
            linear-gradient(235deg, rgba(253, 214, 99, 0.13), rgba(15, 17, 23, 0) 40%),
            linear-gradient(340deg, rgba(129, 201, 149, 0.13), rgba(242, 139, 130, 0.09) 54%, rgba(15, 17, 23, 0) 72%);
        --sidebar-gradient:
            linear-gradient(180deg, rgba(28, 32, 43, 0.96), rgba(19, 22, 31, 0.93)),
            linear-gradient(135deg, rgba(138, 180, 248, 0.12), rgba(253, 214, 99, 0.08));
        --hero-gradient:
            linear-gradient(100deg, rgba(31, 35, 48, 0.96), rgba(21, 24, 34, 0.84)),
            linear-gradient(135deg, rgba(138, 180, 248, 0.19), rgba(253, 214, 99, 0.14) 46%, rgba(129, 201, 149, 0.16));
        --metric-gradient:
            linear-gradient(180deg, rgba(31, 35, 48, 0.94), rgba(21, 24, 34, 0.90)),
            linear-gradient(135deg, rgba(138, 180, 248, 0.14), rgba(129, 201, 149, 0.09));
    }

    html[data-aegis-theme="light"],
    html[data-aegis-theme="light"] body,
    html[data-aegis-theme="light"] .stApp {
        --google-blue: #4285F4;
        --google-red: #EA4335;
        --google-yellow: #FBBC04;
        --google-green: #34A853;
        --ink: #202124;
        --muted: #5f6368;
        --heading: #3c4043;
        --app-bg: #f8fbff;
        --surface: rgba(255, 255, 255, 0.88);
        --surface-soft: rgba(255, 255, 255, 0.72);
        --surface-strong: rgba(255, 255, 255, 0.94);
        --input-bg: rgba(255, 255, 255, 0.92);
        --input-focus-bg: #ffffff;
        --placeholder: #6f7277;
        --blue-ink: #174ea6;
        --yellow-ink: #7a4f00;
        --green-ink: #137333;
        --red-ink: #a50e0e;
        --line: rgba(32, 33, 36, 0.1);
        --shadow: 0 18px 45px rgba(60, 64, 67, 0.16);
        --soft-shadow: 0 8px 24px rgba(60, 64, 67, 0.10);
        --app-gradient:
            linear-gradient(145deg, rgba(66, 133, 244, 0.13), rgba(255, 255, 255, 0) 34%),
            linear-gradient(235deg, rgba(251, 188, 4, 0.16), rgba(255, 255, 255, 0) 38%),
            linear-gradient(340deg, rgba(52, 168, 83, 0.13), rgba(234, 67, 53, 0.07) 52%, rgba(255, 255, 255, 0) 70%);
        --sidebar-gradient:
            linear-gradient(180deg, rgba(255, 255, 255, 0.94), rgba(248, 251, 255, 0.9)),
            linear-gradient(135deg, rgba(66, 133, 244, 0.10), rgba(251, 188, 4, 0.10));
        --hero-gradient:
            linear-gradient(100deg, rgba(255,255,255,0.94), rgba(255,255,255,0.72)),
            linear-gradient(135deg, rgba(66, 133, 244, 0.22), rgba(251, 188, 4, 0.24) 46%, rgba(52, 168, 83, 0.18));
        --metric-gradient:
            linear-gradient(180deg, rgba(255, 255, 255, 0.92), rgba(248, 251, 255, 0.84)),
            linear-gradient(135deg, rgba(66, 133, 244, 0.12), rgba(52, 168, 83, 0.08));
    }

    html, body, [class*="css"] {
        font-family: "Google Sans", "Inter", sans-serif;
    }

    .stApp {
        color: var(--ink);
        background: var(--app-gradient), var(--app-bg);
    }

    .block-container {
        max-width: 1180px;
        padding-top: 2rem;
        padding-bottom: 3rem;
    }

    header[data-testid="stHeader"] {
        background: transparent;
    }

    section[data-testid="stSidebar"] {
        background: var(--sidebar-gradient);
        border-right: 1px solid var(--line);
    }

    section[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] h2 {
        color: var(--ink);
        font-size: 1rem;
        letter-spacing: 0;
    }

    .aegis-hero {
        position: relative;
        overflow: hidden;
        border: 1px solid var(--line);
        border-radius: 8px;
        padding: 2.2rem 2.4rem;
        margin-bottom: 1.4rem;
        background: var(--hero-gradient);
        box-shadow: var(--shadow);
    }

    .aegis-hero:before {
        content: "";
        position: absolute;
        inset: 0;
        background:
            repeating-linear-gradient(90deg, color-mix(in srgb, var(--google-blue) 16%, transparent) 0 1px, transparent 1px 44px),
            repeating-linear-gradient(0deg, color-mix(in srgb, var(--google-green) 13%, transparent) 0 1px, transparent 1px 44px);
        mask-image: linear-gradient(90deg, transparent, #000 16%, #000 78%, transparent);
        pointer-events: none;
    }

    .aegis-hero:after {
        content: "";
        position: absolute;
        left: 0;
        right: 0;
        top: 0;
        height: 5px;
        background: linear-gradient(90deg, var(--google-blue), var(--google-red), var(--google-yellow), var(--google-green));
    }

    .hero-content {
        position: relative;
        z-index: 1;
    }

    .main-header {
        font-size: clamp(2.7rem, 7vw, 5.8rem);
        line-height: 0.95;
        font-weight: 800;
        letter-spacing: 0;
        color: var(--ink);
        margin-bottom: 0.65rem;
    }

    .main-header .g-blue { color: var(--google-blue); }
    .main-header .g-red { color: var(--google-red); }
    .main-header .g-yellow { color: var(--google-yellow); }
    .main-header .g-green { color: var(--google-green); }

    .sub-header {
        max-width: 760px;
        font-size: 1.08rem;
        color: var(--muted);
        margin-bottom: 1rem;
        line-height: 1.6;
    }

    .hero-chips {
        display: flex;
        flex-wrap: wrap;
        gap: 0.65rem;
        margin-top: 1.2rem;
    }

    .hero-chip {
        display: inline-flex;
        align-items: center;
        gap: 0.4rem;
        min-height: 32px;
        padding: 0.36rem 0.72rem;
        border-radius: 8px;
        background: var(--surface);
        border: 1px solid var(--line);
        color: var(--muted);
        font-size: 0.88rem;
        font-weight: 600;
        box-shadow: 0 3px 12px rgba(60, 64, 67, 0.08);
    }

    .section-kicker {
        display: inline-flex;
        align-items: center;
        gap: 0.45rem;
        padding: 0.34rem 0.68rem;
        border-radius: 8px;
        background: color-mix(in srgb, var(--google-blue) 14%, transparent);
        border: 1px solid color-mix(in srgb, var(--google-blue) 28%, transparent);
        color: var(--blue-ink);
        font-weight: 700;
        font-size: 0.82rem;
        margin-bottom: 0.55rem;
    }

    .stMarkdown h3 {
        color: var(--ink);
        font-weight: 800;
        letter-spacing: 0;
    }

    .stMarkdown h4,
    .stMarkdown h5 {
        color: var(--heading);
        font-weight: 700;
    }

    .stTabs [data-baseweb="tab-list"] {
        gap: 0.45rem;
        padding: 0.35rem;
        border: 1px solid var(--line);
        border-radius: 8px;
        background: var(--surface-soft);
        box-shadow: 0 5px 18px rgba(60, 64, 67, 0.08);
    }

    .stTabs [data-baseweb="tab"] {
        height: 3rem;
        white-space: pre-wrap;
        border-radius: 8px;
        color: var(--muted);
        font-size: 1rem;
        font-weight: 700;
        padding-inline: 1rem;
        transition: all 160ms ease;
    }

    .stTabs [data-baseweb="tab"]:hover {
        background: color-mix(in srgb, var(--google-blue) 12%, transparent);
        color: var(--ink);
    }

    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, color-mix(in srgb, var(--google-blue) 20%, transparent), color-mix(in srgb, var(--google-green) 14%, transparent));
        color: var(--blue-ink);
        box-shadow: inset 0 0 0 1px color-mix(in srgb, var(--google-blue) 28%, transparent);
    }

    div[data-testid="stForm"] {
        border: 1px solid var(--line);
        border-radius: 8px;
        padding: 1.2rem 1.25rem 1.35rem;
        background: var(--surface);
        box-shadow: var(--soft-shadow);
    }

    div[data-testid="stTextInput"] input,
    div[data-testid="stTextArea"] textarea {
        border-radius: 8px;
        border: 1px solid var(--line);
        background: var(--input-bg);
        color: var(--ink);
        transition: border-color 140ms ease, box-shadow 140ms ease, background 140ms ease;
    }

    div[data-testid="stTextInput"] input::placeholder,
    div[data-testid="stTextArea"] textarea::placeholder {
        color: var(--placeholder);
        opacity: 0.82;
    }

    div[data-testid="stTextInput"] input:focus,
    div[data-testid="stTextArea"] textarea:focus {
        border-color: var(--google-blue);
        box-shadow: 0 0 0 3px color-mix(in srgb, var(--google-blue) 24%, transparent);
        background: var(--input-focus-bg);
    }

    label[data-testid="stWidgetLabel"] p {
        color: var(--heading);
        font-weight: 700;
    }

    .stButton > button,
    .stDownloadButton > button,
    div[data-testid="stFormSubmitButton"] button {
        border-radius: 8px;
        border: 0;
        background: linear-gradient(135deg, var(--google-blue), #6d9df7);
        color: #fff;
        font-weight: 800;
        letter-spacing: 0;
        box-shadow: 0 10px 22px color-mix(in srgb, var(--google-blue) 30%, transparent);
        transition: transform 140ms ease, box-shadow 140ms ease, filter 140ms ease;
    }

    .stButton > button:hover,
    .stDownloadButton > button:hover,
    div[data-testid="stFormSubmitButton"] button:hover {
        color: #fff;
        transform: translateY(-1px);
        filter: saturate(1.08);
        box-shadow: 0 14px 30px color-mix(in srgb, var(--google-blue) 36%, transparent);
    }

    .stButton > button:active,
    .stDownloadButton > button:active,
    div[data-testid="stFormSubmitButton"] button:active {
        transform: translateY(0);
    }

    div[data-testid="stFileUploader"] section {
        border-radius: 8px;
        border-color: color-mix(in srgb, var(--google-blue) 32%, transparent);
        background:
            linear-gradient(135deg, color-mix(in srgb, var(--google-blue) 10%, transparent), color-mix(in srgb, var(--google-yellow) 10%, transparent)),
            var(--surface);
    }

    div[data-testid="stExpander"] {
        border: 1px solid var(--line);
        border-radius: 8px;
        overflow: hidden;
        background: var(--surface);
        box-shadow: 0 6px 18px rgba(60, 64, 67, 0.08);
    }

    div[data-testid="stExpander"] details summary {
        font-weight: 800;
        color: var(--heading);
    }

    div[data-testid="stAlert"] {
        border-radius: 8px;
        border: 1px solid var(--line);
        box-shadow: 0 6px 18px rgba(60, 64, 67, 0.07);
    }

    div[data-testid="stDataFrame"] {
        border-radius: 8px;
        overflow: hidden;
        box-shadow: var(--soft-shadow);
    }

    code {
        border-radius: 8px;
        color: var(--blue-ink);
        background: color-mix(in srgb, var(--google-blue) 13%, transparent);
    }

    .success-box {
        padding: 1rem;
        border-radius: 8px;
        background-color: color-mix(in srgb, var(--google-green) 17%, transparent);
        border: 1px solid color-mix(in srgb, var(--google-green) 32%, transparent);
        color: var(--green-ink);
    }

    .warning-box {
        padding: 1rem;
        border-radius: 8px;
        background-color: color-mix(in srgb, var(--google-yellow) 20%, transparent);
        border: 1px solid color-mix(in srgb, var(--google-yellow) 36%, transparent);
        color: var(--yellow-ink);
    }

    .error-box {
        padding: 1rem;
        border-radius: 8px;
        background-color: color-mix(in srgb, var(--google-red) 16%, transparent);
        border: 1px solid color-mix(in srgb, var(--google-red) 32%, transparent);
        color: var(--red-ink);
    }

    .metric-card {
        position: relative;
        overflow: hidden;
        padding: 1.2rem;
        border-radius: 8px;
        background: var(--metric-gradient);
        border: 1px solid var(--line);
        text-align: left;
        color: var(--ink);
        box-shadow: var(--soft-shadow);
        min-height: 108px;
    }

    .metric-card:before {
        content: "";
        position: absolute;
        inset: 0 0 auto 0;
        height: 4px;
        background: linear-gradient(90deg, var(--google-blue), var(--google-red), var(--google-yellow), var(--google-green));
    }

    .metric-card div:first-child {
        color: var(--muted) !important;
        font-size: 0.78rem !important;
        font-weight: 800;
        text-transform: uppercase;
        letter-spacing: 0.04em;
    }

    .metric-card div:last-child {
        color: var(--ink);
        font-size: clamp(1.25rem, 2vw, 1.65rem) !important;
        font-weight: 800 !important;
        margin-top: 0.35rem;
        line-height: 1.2;
    }

    .footer-note {
        text-align: center;
        color: var(--muted);
        padding: 1.2rem 0 0.25rem;
        font-size: 0.92rem;
    }

    hr {
        border-color: var(--line);
        margin: 1.6rem 0;
    }

    @media (max-width: 720px) {
        .block-container {
            padding-inline: 1rem;
        }

        .aegis-hero {
            padding: 1.45rem;
        }

        .stTabs [data-baseweb="tab"] {
            padding-inline: 0.65rem;
            font-size: 0.9rem;
        }
    }
</style>
""", unsafe_allow_html=True)


components.html(
    """
    <script>
    (() => {
        const rootWindow = window.parent;
        const rootDocument = rootWindow.document;

        const parseRgb = (value) => {
            const match = value && value.match(/rgba?\\((\\d+),\\s*(\\d+),\\s*(\\d+)/i);
            return match ? match.slice(1, 4).map(Number) : null;
        };

        const luminance = ([r, g, b]) => {
            const [sr, sg, sb] = [r, g, b].map((channel) => {
                const value = channel / 255;
                return value <= 0.03928 ? value / 12.92 : ((value + 0.055) / 1.055) ** 2.4;
            });
            return 0.2126 * sr + 0.7152 * sg + 0.0722 * sb;
        };

        const syncAegisTheme = () => {
            const bodyStyles = rootWindow.getComputedStyle(rootDocument.body);
            const sampledColor = parseRgb(bodyStyles.backgroundColor);
            if (!sampledColor) return;

            const theme = luminance(sampledColor) < 0.45 ? "dark" : "light";
            rootDocument.documentElement.dataset.aegisTheme = theme;
        };

        syncAegisTheme();
        rootWindow.requestAnimationFrame(syncAegisTheme);

        const observer = new MutationObserver(syncAegisTheme);
        observer.observe(rootDocument.documentElement, {
            attributes: true,
            attributeFilter: ["class", "style", "data-theme"]
        });
        observer.observe(rootDocument.body, {
            attributes: true,
            attributeFilter: ["class", "style", "data-theme"]
        });

        rootWindow.addEventListener("storage", syncAegisTheme);
        rootWindow.matchMedia("(prefers-color-scheme: dark)").addEventListener("change", syncAegisTheme);
        setInterval(syncAegisTheme, 500);
    })();
    </script>
    """,
    height=0,
    width=0,
)

# Initialize session state
if 'grading_history' not in st.session_state:
    st.session_state.grading_history = []
if 'current_session_id' not in st.session_state:
    st.session_state.current_session_id = None
if 'grading_result' not in st.session_state:
    st.session_state.grading_result = None
if 'ocr_result_key' not in st.session_state:
    st.session_state.ocr_result_key = None


def process_events_to_result(events: List[Dict]) -> Dict:
    """Convert ADK events to the dashboard result format."""
    output = {}
    final_score = "N/A"
    
    # Map agent names to output keys
    agent_mapping = {
        "arbiter_agent": "arbiter_assessment",
        "scrutinizer_agent": "scrutinizer_analysis",
        "validator_agent": "validator_report",
        "mentor_agent": "mentor_feedback"
    }
    
    for event in events:
        author = event.get("author")
        if author in agent_mapping:
            # Extract text content
            content = ""
            if "content" in event and "parts" in event["content"]:
                for part in event["content"]["parts"]:
                    if "text" in part:
                        content += part["text"]
            
            # Append to existing content (in case of multiple messages/chunks)
            key = agent_mapping[author]
            if key in output:
                output[key] += content
            else:
                output[key] = content

    return {
        "status": "completed",
        "final_score": final_score,
        "timestamp": datetime.now().isoformat(),
        "output": output,
        "raw_events": events
    }


def render_header():
    """Render the dashboard header."""
    st.markdown(
        """
        <div class="aegis-hero">
            <div class="hero-content">
                <div class="main-header">
                    <span class="g-blue">A</span><span class="g-red">E</span><span class="g-yellow">G</span><span class="g-blue">I</span><span class="g-green">S</span>
                </div>
                <div class="sub-header">
                    Automated Educational Grading Intelligent System for thoughtful, multi-agent assessment.
                </div>
                <div class="hero-chips">
                    <span class="hero-chip">✨ Assistive grading</span>
                    <span class="hero-chip">🔎 Rubric-aware review</span>
                    <span class="hero-chip">📚 Mentor feedback</span>
                    <span class="hero-chip">🌈 Clear insights</span>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    # API status indicator
    if client.health_check():
        st.success("✅ API Connected")
    else:
        st.error(f"❌ API Unavailable - Check if the server is running at {API_BASE_URL}")


def format_grading_result(result: Dict) -> None:
    """Display formatted grading results."""
    if not result:
        st.warning("No grading result available.")
        return
    
    # Handle new evaluation format
    if "evaluation" in result:
        eval_data = result["evaluation"]
        final_score = eval_data.get("final_score", "N/A")
        timestamp = result.get("timestamp", datetime.now().isoformat())
        
        st.markdown('<div class="section-kicker">📊 Final readout</div>', unsafe_allow_html=True)
        st.markdown("### Grading Results")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown(f"""
            <div class="metric-card">
                <div style="font-size: 14px; color: #666;">Status</div>
                <div style="font-size: 24px; font-weight: 600;">✅ Completed</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
            <div class="metric-card">
                <div style="font-size: 14px; color: #666;">Final Score</div>
                <div style="font-size: 24px; font-weight: 600;">{final_score}</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            st.markdown(f"""
            <div class="metric-card">
                <div style="font-size: 14px; color: #666;">Graded At</div>
                <div style="font-size: 24px; font-weight: 600;">{timestamp[:19].replace("T", " ")}</div>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # Display detailed feedback
        st.markdown("#### Evaluation Details")
        
        with st.expander("🔍 Score Reasoning", expanded=True):
            st.markdown(eval_data.get("score_reasoning", "No reasoning provided."))
            
        agent_feedback = eval_data.get("agent_feedback", {})
        if agent_feedback:
            with st.expander("👨‍🏫 Mentor Feedback", expanded=True):
                st.markdown("##### Score Justification")
                st.markdown(agent_feedback.get("score_justification", ""))
                st.markdown("##### Improvement Advice")
                st.markdown(agent_feedback.get("improvement_advice", ""))
                
        # Initial Score comparison
        if "initial_score" in eval_data:
            st.info(f"ℹ️ Initial Assessment Score: {eval_data['initial_score']}")

        with st.expander("🔧 Raw API Response"):
            st.json(result)
        return

    # Extract key information (Legacy format support)
    st.markdown('<div class="section-kicker">📊 Final readout</div>', unsafe_allow_html=True)
    st.markdown("### Grading Results")
    
    # Display in columns
    col1, col2, col3 = st.columns(3)
    
    with col1:
        status = "✅ Completed" if result.get("status") == "completed" else "⏳ Processing"
        st.markdown(f"""
        <div class="metric-card">
            <div style="font-size: 14px; color: #666;">Status</div>
            <div style="font-size: 24px; font-weight: 600;">{status}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        score = result.get("final_score", "N/A")
        st.markdown(f"""
        <div class="metric-card">
            <div style="font-size: 14px; color: #666;">Final Score</div>
            <div style="font-size: 24px; font-weight: 600;">{score}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        timestamp = result.get("timestamp", datetime.now().isoformat())
        st.markdown(f"""
        <div class="metric-card">
            <div style="font-size: 14px; color: #666;">Graded At</div>
            <div style="font-size: 24px; font-weight: 600;">{timestamp[:19].replace("T", " ")}</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Display detailed feedback
    if "output" in result:
        output = result["output"]
        
        # Arbiter Assessment
        if "arbiter_assessment" in output:
            with st.expander("🎯 Arbiter - Initial Assessment", expanded=True):
                st.markdown(output["arbiter_assessment"])
        
        # Scrutinizer Analysis
        if "scrutinizer_analysis" in output:
            with st.expander("🔍 Scrutinizer - Detailed Analysis"):
                st.markdown(output["scrutinizer_analysis"])
        
        # Validator Report
        if "validator_report" in output:
            with st.expander("✓ Validator - Quality Check"):
                st.markdown(output["validator_report"])
        
        # Mentor Feedback
        if "mentor_feedback" in output:
            with st.expander("👨‍🏫 Mentor - Personalized Feedback", expanded=True):
                st.markdown(output["mentor_feedback"])
    
    # Raw response (for debugging)
    with st.expander("🔧 Raw API Response"):
        st.json(result)


def get_redis_keys(pattern: str = "student_answer_script:*") -> List[str]:
    """Fetch keys from Redis matching the pattern."""
    try:
        r = redis.from_url(REDIS_URL)
        keys = [k.decode('utf-8') for k in r.keys(pattern)]
        return keys
    except Exception as e:
        st.error(f"Error connecting to Redis: {e}")
        return []


def get_redis_value(key: str) -> Optional[str]:
    """Fetch value from Redis for a given key."""
    try:
        r = redis.from_url(REDIS_URL)
        value = r.get(key)
        if value:
            return value.decode('utf-8')
        return None
    except Exception as e:
        st.error(f"Error fetching from Redis: {e}")
        return None


def process_ocr_upload(files, assignment_id):
    """Handle OCR upload."""
    ocr_url = OCR_SERVER_URL
    
    try:
        with st.spinner("Uploading files to OCR server..."):
            files_payload = []
            for i, f in enumerate(files):
                # Reset pointer just in case
                f.seek(0)
                files_payload.append((f"file{i+1}", (f.name, f.read(), "application/pdf")))
            
            response = requests.post(f"{ocr_url}/ocr", files=files_payload, timeout=60)
            response.raise_for_status()
            
            request_uuid = response.headers.get("X-Request-ID")
            if request_uuid:
                st.success(f"✅ Upload successful! Request ID: {request_uuid}")
                st.info("The file is being processed in the background. Please refresh the list below to see the result.")
            else:
                st.warning("Upload successful, but Server did not return a Request ID.")
            
    except requests.exceptions.ConnectionError:
        st.error(f"❌ Could not connect to OCR server at {ocr_url}")
    except Exception as e:
        st.error(f"❌ Error during upload: {str(e)}")


def render_ocr_tab():
    """Render the OCR and grading tab."""
    st.markdown('<div class="section-kicker">📄 OCR Pipeline</div>', unsafe_allow_html=True)
    st.markdown("### OCR & Grade")
    st.caption("Upload two PDFs, collect the processed script, and evaluate it with the same AEGIS flow.")

    with st.form("ocr_submission_form"):
        # Assignment ID
        assignment_id = st.text_input(
            "Assignment ID *",
            placeholder="e.g., CS101-Assignment-1-OCR",
            help="Unique identifier for this assignment",
            key="ocr_assignment_id_input"
        )
        
        # File Uploader
        uploaded_files = st.file_uploader(
            "Upload Answer Scripts (Select exactly 2 PDF files) *", 
            type="pdf", 
            accept_multiple_files=True,
            key="ocr_files_input"
        )

        submit_ocr = st.form_submit_button("📤 Upload & Process OCR", use_container_width=True)

    if submit_ocr:
        if not assignment_id:
            st.error("⚠️ Assignment ID is required!")
        elif not uploaded_files or len(uploaded_files) != 2:
            st.error("⚠️ Please upload exactly two PDF files.")
        else:
            # Process OCR
            process_ocr_upload(uploaded_files, assignment_id)

    st.markdown("---")
    st.markdown('<div class="section-kicker">📋 Processed scripts</div>', unsafe_allow_html=True)
    st.markdown("### Available OCR Results")
    
    col_refresh, _ = st.columns([1, 4])
    with col_refresh:
        if st.button("🔄 Refresh List"):
            st.rerun()

    # Fetch keys
    keys = get_redis_keys()
    
    if not keys:
        st.info("No processed scripts found in Redis.")
    else:
        # Try to sort by idle time (approximation of recency)
        try:
            r = redis.from_url(REDIS_URL)
            # Sort keys by idle time (ascending) -> most recently touched first
            keys_with_idle = []
            for k in keys:
                try:
                    idle = r.object("idletime", k)
                    keys_with_idle.append((k, idle if idle is not None else float('inf')))
                except:
                    keys_with_idle.append((k, float('inf')))
            
            keys_with_idle.sort(key=lambda x: x[1])
            keys = [k[0] for k in keys_with_idle]
        except Exception:
            pass # Fallback to unsorted if redis connection fails here

        # Display keys
        for key in keys:
            with st.container():
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.code(key, language="text")
                with col2:
                    if st.button("Select", key=f"btn_{key}"):
                        st.session_state.selected_ocr_key = key
                        st.rerun()
        
        st.markdown("---")
        
        # Evaluation Section for Selected Key
        if 'selected_ocr_key' in st.session_state and st.session_state.selected_ocr_key:
            st.markdown('<div class="section-kicker">🚀 Ready for review</div>', unsafe_allow_html=True)
            st.markdown(f"### Evaluate: `{st.session_state.selected_ocr_key}`")
            
            # Fetch content
            redis_content = get_redis_value(st.session_state.selected_ocr_key)
            
            if redis_content:
                with st.expander("📄 View OCR Content", expanded=True):
                    st.markdown(redis_content, unsafe_allow_html=True)
            else:
                st.error("Could not retrieve content from Redis.")
                redis_content = ""

            # Assignment ID (optional override or use from upload if we tracked it, but we don't track it per key in redis)
            # So we ask for it or use a default
            eval_assignment_id = st.text_input(
                "Assignment ID for Grading",
                value=st.session_state.get("ocr_assignment_id_input", ""),
                help="Identifier for this grading session"
            )
            
            if st.button("Evaluate Answer Script", use_container_width=True):
                if not eval_assignment_id:
                    st.error("⚠️ Please provide an Assignment ID.")
                elif not redis_content:
                    st.error("⚠️ No content to evaluate.")
                else:
                    with st.spinner("🤖 AI Agents are evaluating the OCR result..."):
                        # Use the redis content as the student answer prompt
                        # Rubric is passed as empty string as per user request
                        
                        result = client.evaluate_answer(
                            student_answer=redis_content,
                            rubric="", 
                            assignment_id=eval_assignment_id
                        )
                        
                        if result:
                            if "timestamp" not in result:
                                result["timestamp"] = datetime.now().isoformat()
                            
                            st.session_state.grading_result = result
                            st.session_state.grading_history.append({
                                "assignment_id": eval_assignment_id,
                                "timestamp": result["timestamp"],
                                "result": result
                            })
                            st.success("✅ Grading completed successfully! Check the Results tab.")
                            st.balloons()
                        else:
                            st.error("❌ Grading failed.")


def render_submission_tab():
    """Render the answer submission form."""
    st.markdown('<div class="section-kicker">📝 Guided submission</div>', unsafe_allow_html=True)
    st.markdown("### Submit Answer Script")
    
    with st.form("answer_submission_form"):
        # Assignment ID
        assignment_id = st.text_input(
            "Assignment ID *",
            placeholder="e.g., CS101-Assignment-1",
            help="Unique identifier for this assignment"
        )
        
        # Rubric/Answer Key
        rubric = st.text_area(
            "Grading Rubric / Answer Key *",
            height=250,
            placeholder="Enter the grading rubric or answer key here...",
            help="Detailed rubric with scoring criteria and expected answers"
        )

        # Student Answer
        student_answer = st.text_area(
            "Student Answer *",
            height=250,
            placeholder="Enter the student's answer here...",
            help="The student's complete answer to be graded"
        )
        
        # Submit button
        submitted = st.form_submit_button("🚀 Submit for Grading", use_container_width=True)
        
        if submitted:
            # Validation
            if not assignment_id or not student_answer or not rubric:
                st.error("⚠️ All fields are required!")
                return
            
            # Show progress
            st.markdown("### 🔄 Grading Progress")
            
            try:
                with st.spinner("🤖 AI Agents are evaluating the answer... This may take a minute."):
                    # Call the new evaluate endpoint
                    result = client.evaluate_answer(student_answer, rubric, assignment_id)
                
                if result:
                    # Add timestamp if not present
                    if "timestamp" not in result:
                        result["timestamp"] = datetime.now().isoformat()
                        
                    st.session_state.grading_result = result
                    st.session_state.grading_history.append({
                        "assignment_id": assignment_id,
                        "timestamp": result["timestamp"],
                        "result": result
                    })
                    st.success("✅ Grading completed successfully!")
                    st.balloons()
                else:
                    st.error("❌ Grading failed. No result produced.")
                    
            except Exception as e:
                st.error(f"Error during grading: {str(e)}")


def render_results_tab():
    """Render the grading results view."""
    st.markdown('<div class="section-kicker">📊 Assessment output</div>', unsafe_allow_html=True)
    st.markdown("### Grading Results")
    
    if st.session_state.grading_result:
        format_grading_result(st.session_state.grading_result)
        
        # Option to download results
        if st.button("📥 Download Results as JSON"):
            json_str = json.dumps(st.session_state.grading_result, indent=2)
            st.download_button(
                label="Download JSON",
                data=json_str,
                file_name=f"grading_result_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json"
            )
    else:
        st.info("ℹ️ No grading results yet. Submit an answer in the 'Submit' tab to get started.")


def render_history_tab():
    """Render the grading history view."""
    st.markdown('<div class="section-kicker">📚 Session memory</div>', unsafe_allow_html=True)
    st.markdown("### Grading History")
    
    if not st.session_state.grading_history:
        st.info("ℹ️ No grading history yet. Submit answers to build your history.")
        return
    
    # Convert history to DataFrame for better display
    history_data = []
    for item in st.session_state.grading_history:
        history_data.append({
            "Assignment ID": item["assignment_id"],
            "Timestamp": item["timestamp"][:19].replace("T", " "),
            "Status": "Completed"
        })
    
    df = pd.DataFrame(history_data)
    st.dataframe(df, use_container_width=True)
    
    # Option to view individual results
    st.markdown("---")
    st.markdown("#### View Individual Results")
    
    selected_idx = st.selectbox(
        "Select a grading session:",
        range(len(st.session_state.grading_history)),
        format_func=lambda x: f"{st.session_state.grading_history[x]['assignment_id']} - {st.session_state.grading_history[x]['timestamp'][:19]}"
    )
    
    if st.button("View Details"):
        selected_result = st.session_state.grading_history[selected_idx]["result"]
        format_grading_result(selected_result)


def render_analytics_tab():
    """Render analytics and statistics."""
    st.markdown('<div class="section-kicker">📈 Learning signals</div>', unsafe_allow_html=True)
    st.markdown("### Analytics & Statistics")
    
    if not st.session_state.grading_history:
        st.info("ℹ️ No data available yet. Submit answers to see analytics.")
        return
    
    # Basic statistics
    total_graded = len(st.session_state.grading_history)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <div style="font-size: 14px; color: #666;">Total Graded</div>
            <div style="font-size: 24px; font-weight: 600;">{total_graded}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        today_count = len([h for h in st.session_state.grading_history 
                                 if h["timestamp"][:10] == datetime.now().isoformat()[:10]])
        st.markdown(f"""
        <div class="metric-card">
            <div style="font-size: 14px; color: #666;">Today</div>
            <div style="font-size: 24px; font-weight: 600;">{today_count}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class="metric-card">
            <div style="font-size: 14px; color: #666;">Success Rate</div>
            <div style="font-size: 24px; font-weight: 600;">100%</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Timeline chart
    st.markdown("#### Grading Activity Timeline")
    timeline_data = pd.DataFrame([
        {"Time": h["timestamp"][:19], "Count": 1} 
        for h in st.session_state.grading_history
    ])
    
    if not timeline_data.empty:
        st.line_chart(timeline_data.set_index("Time"))


def main():
    """Main dashboard application."""
    # Render header
    render_header()
    
    # Sidebar
    with st.sidebar:
        st.markdown("## ⚙️ Settings")
        
        # API URL configuration
        api_url = st.text_input(
            "API Base URL",
            value=API_BASE_URL,
            help="The base URL of the AEGIS API server"
        )
        
        st.markdown("---")
        
        st.markdown("## 📊 Quick Stats")
        
        graded_today = len([h for h in st.session_state.grading_history 
                                         if h["timestamp"][:10] == datetime.now().isoformat()[:10]])
        st.markdown(f"""
        <div class="metric-card" style="padding: 1rem; margin-bottom: 1rem;">
            <div style="font-size: 14px; color: #666;">Graded Today</div>
            <div style="font-size: 24px; font-weight: 600;">{graded_today}</div>
        </div>
        """, unsafe_allow_html=True)
        
        total_history = len(st.session_state.grading_history)
        st.markdown(f"""
        <div class="metric-card" style="padding: 1rem;">
            <div style="font-size: 14px; color: #666;">Total History</div>
            <div style="font-size: 24px; font-weight: 600;">{total_history}</div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # Clear history button
        if st.button("🗑️ Clear History", use_container_width=True):
            st.session_state.grading_history = []
            st.session_state.grading_result = None
            st.success("History cleared!")
            st.rerun()
    
    # Main tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📝 Submit",
        "📄 OCR & Grade",
        "📊 Results",
        "📚 History",
        "📈 Analytics"
    ])
    
    with tab1:
        render_submission_tab()

    with tab2:
        render_ocr_tab()
    
    with tab3:
        render_results_tab()
    
    with tab4:
        render_history_tab()
    
    with tab5:
        render_analytics_tab()
    
    # Footer
    st.markdown("---")
    st.markdown(
        "<div style='text-align: center; color: #666;'>"
        "AEGIS - Automated Educational Grading Intelligent System | "
        f"© {datetime.now().year} | Powered by AI"
        "</div>",
        unsafe_allow_html=True
    )


if __name__ == "__main__":
    main()
