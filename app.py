"""
Company Relationship Explorer — Streamlit web app (terminal edition)
Enter a ticker: get live price/sector/country from Yahoo Finance, plus
AI-generated (unverified) competitor/supplier/customer estimates.
"""

import json
from datetime import datetime

import requests
import streamlit as st
import yfinance as yf

st.set_page_config(page_title="Company Relationship Explorer", layout="wide", initial_sidebar_state="collapsed")

# ---------------------------------------------------------------------------
# Terminal styling — jet black, amber/orange monospace, no rounded corners.
# (identical system to the other Villalobos terminal apps)
# ---------------------------------------------------------------------------
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500;600;700&display=swap');

    html, body, [class*="css"]  {
        font-family: 'IBM Plex Mono', 'Consolas', monospace !important;
    }

    .stApp {
        background-color: #000000;
        color: #FF8C00;
    }
    section[data-testid="stSidebar"] { display: none; }
    header[data-testid="stHeader"] { background-color: #000000; }
    div.block-container { padding-top: 1.2rem; max-width: 1400px; }

    h1, h2, h3, h4, h5, h6 { color: #FF8C00 !important; letter-spacing: 0.5px; }
    p, span, label, .stMarkdown, .stCaption { color: #FFB84D !important; }

    .term-subtitle {
        color: #7A5A2E !important;
        font-size: 0.78rem;
        letter-spacing: 1px;
        margin-top: -6px;
        margin-bottom: 10px;
    }

    .term-title {
        color: #FF8C00 !important;
        font-family: 'IBM Plex Mono', monospace;
        font-weight: 700;
        font-size: 2.4rem;
        letter-spacing: 0.5px;
        margin-top: 0.6em;
        margin-bottom: 6px;
    }

    div[data-testid="stVerticalBlockBorderWrapper"] {
        border: 1px solid #FF8C00 !important;
        border-radius: 0px !important;
        background-color: #050505 !important;
    }
    div[data-testid="stVerticalBlockBorderWrapper"] > div { border-radius: 0px !important; }

    .term-label {
        color: #FF8C00 !important;
        font-size: 0.7rem;
        letter-spacing: 1.5px;
        text-transform: uppercase;
        margin-bottom: 2px;
    }

    .stTextInput input {
        background-color: #000000 !important;
        color: #FF8C00 !important;
        border: 1px solid #FF8C00 !important;
        border-radius: 0px !important;
        font-family: 'IBM Plex Mono', monospace !important;
        font-weight: 600;
        caret-color: #FF8C00;
    }
    .stTextInput input:focus {
        box-shadow: 0 0 0 1px #FF8C00 !important;
        border: 1px solid #FFB84D !important;
    }

    .stButton button {
        background-color: #000000;
        color: #FF8C00;
        border: 1px solid #FF8C00;
        border-radius: 0px;
        font-family: 'IBM Plex Mono', monospace;
        font-weight: 700;
        letter-spacing: 1px;
        width: 100%;
        transition: none;
    }
    .stButton button:hover {
        background-color: #FF8C00;
        color: #000000;
        border: 1px solid #FF8C00;
    }

    div[data-testid="stAlert"] {
        background-color: #050505;
        color: #FF8C00;
        border: 1px solid #FF8C00;
        border-radius: 0px;
    }

    .stat-row {
        display: flex;
        gap: 40px;
        flex-wrap: wrap;
        margin: 6px 0 22px 0;
        padding-bottom: 16px;
        border-bottom: 1px solid #2a2a2a;
    }
    .stat-block { display: flex; flex-direction: column; }
    .stat-label {
        color: #7A5A2E !important;
        font-size: 0.62rem;
        letter-spacing: 1.5px;
        text-transform: uppercase;
        margin-bottom: 3px;
    }
    .stat-value {
        color: #FFFFFF !important;
        font-size: 1.2rem;
        font-weight: 700;
        font-family: 'IBM Plex Mono', monospace;
    }
    .stat-value.accent { color: #FF8C00 !important; }
    .stat-value.up { color: #4CAF50 !important; }
    .stat-value.down { color: #E74C3C !important; }

    .rel-col-title {
        color: #FF8C00 !important;
        font-size: 0.72rem;
        font-weight: 700;
        letter-spacing: 1.5px;
        text-transform: uppercase;
        text-align: center;
        margin-bottom: 10px;
        padding-bottom: 8px;
        border-bottom: 1px solid #FF8C00;
    }
    .rel-item {
        color: #FFB84D !important;
        font-size: 0.9rem;
        text-align: center;
        padding: 8px 6px;
        border-bottom: 1px solid #2a2a2a;
    }
    .rel-empty {
        color: #7A5A2E !important;
        font-size: 0.8rem;
        text-align: center;
        padding: 10px;
        font-style: italic;
    }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Access control (identical scheme to the other Villalobos terminal apps)
# ---------------------------------------------------------------------------
DEFAULT_ALLOWED_USERS = {("augustine", "villalobos"), ("david", "villalobos")}

def get_allowed_users() -> set:
    try:
        configured = st.secrets.get("allowed_users", None)
    except Exception:
        configured = None
    if not configured:
        return DEFAULT_ALLOWED_USERS
    return {
        (entry["first_name"].strip().lower(), entry["last_name"].strip().lower())
        for entry in configured
    }


if "authenticated" not in st.session_state:
    st.session_state.authenticated = False


def render_login():
    st.markdown("<br>", unsafe_allow_html=True)
    _, mid, _ = st.columns([1, 1.1, 1])
    with mid:
        with st.container(border=True):
            st.markdown("### RESTRICTED ACCESS")
            st.caption("ENTER YOUR FIRST AND LAST NAME TO CONTINUE")
            with st.form("login_form"):
                first = st.text_input("First name", placeholder="FIRST NAME")
                last = st.text_input("Last name", placeholder="LAST NAME")
                submitted = st.form_submit_button("ACCESS TERMINAL", use_container_width=True)

            if submitted:
                key = (first.strip().lower(), last.strip().lower())
                if key in get_allowed_users() and first.strip() and last.strip():
                    st.session_state.authenticated = True
                    st.rerun()
                else:
                    st.error("ACCESS DENIED — NAME NOT RECOGNIZED.")


if not st.session_state.authenticated:
    st.markdown('<div class="term-title">COMPANY RELATIONSHIP EXPLORER</div>', unsafe_allow_html=True)
    st.markdown('<div class="term-subtitle">CREATED BY AUGUSTINE VILLALOBOS</div>', unsafe_allow_html=True)
    render_login()
    st.stop()

# ---------------------------------------------------------------- helpers

@st.cache_data(ttl=300, show_spinner=False)
def fetch_company_snapshot(ticker: str):
    t = yf.Ticker(ticker)
    info = t.info or {}
    fi = t.fast_info

    price = fi.get("lastPrice")
    prev_close = fi.get("previousClose")
    if not price or not prev_close:
        hist = t.history(period="5d")["Close"].dropna()
        if hist.empty:
            raise ValueError("no price data — check the ticker symbol")
        price = float(hist.iloc[-1])
        prev_close = float(hist.iloc[-2]) if len(hist) > 1 else price

    change_pct = ((price - prev_close) / prev_close * 100) if prev_close else 0.0

    return {
        "ticker": ticker.upper(),
        "name": info.get("longName") or info.get("shortName") or ticker.upper(),
        "price": float(price),
        "change_pct": float(change_pct),
        "sector": info.get("sector") or "—",
        "industry": info.get("industry") or "—",
        "country": info.get("country") or "—",
    }


@st.cache_data(ttl=86400, show_spinner=False)
def fetch_relationships(company_name: str, ticker: str, sector: str, industry: str):
    """AI-generated, best-effort competitor/supplier/customer estimate.
    Returns None if no API key is configured, or a dict with an "error" key
    on failure, otherwise {"competitors": [...], "suppliers": [...], "customers": [...]}.
    """
    try:
        api_key = st.secrets["ANTHROPIC_API_KEY"]
    except Exception:
        return None

    prompt = (
        f'For the publicly traded company "{company_name}" (ticker {ticker}), '
        f"sector: {sector}, industry: {industry}, give your best-informed estimate of:\n"
        f"1. Its top 5 direct competitors\n"
        f"2. Its top 5 known suppliers (companies it buys key inputs/components from)\n"
        f"3. Its top 5 known customers (companies or industries that buy its products/services — "
        f"if it primarily sells to individual consumers rather than businesses, return an empty list here)\n\n"
        f"Respond with ONLY valid JSON, no markdown code fences, no preamble, in exactly this shape:\n"
        f'{{"competitors": ["...", "..."], "suppliers": ["...", "..."], "customers": ["...", "..."]}}\n'
        f"If you are not confident about a category, return fewer items or an empty list rather than guessing."
    )

    try:
        resp = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            json={
                "model": "claude-sonnet-5",
                "max_tokens": 2048,
                "thinking": {"type": "disabled"},
                "messages": [{"role": "user", "content": prompt}],
            },
            timeout=30,
        )
        if resp.status_code != 200:
            return {"error": True, "detail": f"HTTP {resp.status_code}: {resp.text[:300]}"}
        data = resp.json()
        text = "".join(
            block.get("text", "") for block in data.get("content", [])
            if block.get("type") == "text"
        ).strip()
        if text.startswith("```"):
            text = text.strip("`")
            if "\n" in text:
                text = text.split("\n", 1)[1]
        if not text:
            return {"error": True, "detail": "Empty response from the model (no text content returned)."}
        parsed = json.loads(text)
        return {
            "competitors": list(parsed.get("competitors", []))[:5],
            "suppliers": list(parsed.get("suppliers", []))[:5],
            "customers": list(parsed.get("customers", []))[:5],
        }
    except Exception as e:
        return {"error": True, "detail": f"{type(e).__name__}: {e}"}


def render_rel_column(title: str, items):
    st.markdown(f'<div class="rel-col-title">{title}</div>', unsafe_allow_html=True)
    if not items:
        st.markdown('<div class="rel-empty">NO DATA RETURNED</div>', unsafe_allow_html=True)
        return
    for item in items:
        st.markdown(f'<div class="rel-item">{item}</div>', unsafe_allow_html=True)


# ---------------------------------------------------------------- Header
st.markdown('<div class="term-title">COMPANY RELATIONSHIP EXPLORER</div>', unsafe_allow_html=True)
st.markdown('<div class="term-subtitle">CREATED BY AUGUSTINE VILLALOBOS</div>', unsafe_allow_html=True)
st.caption("TICKER LOOKUP  |  LIVE PRICE & SECTOR VIA YAHOO FINANCE  |  AI-ESTIMATED COMPETITORS / SUPPLIERS / CUSTOMERS")

# ---------------------------------------------------------------- Top command bar
with st.container(border=True):
    c1, c2 = st.columns([3, 1])
    with c1:
        st.markdown('<div class="term-label">TICKER</div>', unsafe_allow_html=True)
        ticker_raw = st.text_input("Ticker", value="AAPL", label_visibility="collapsed")
    with c2:
        st.markdown('<div class="term-label">&nbsp;</div>', unsafe_allow_html=True)
        run = st.button("ANALYZE", type="primary", use_container_width=True)
    st.caption("WORKS FOR ANY STOCK TICKER  |  DATA VIA YAHOO FINANCE, CACHED 5 MIN")

st.write("")

# ---------------------------------------------------------------- Main logic
if run:
    ticker = ticker_raw.strip().upper()
    if not ticker:
        st.error("PLEASE ENTER A TICKER.")
        st.stop()

    try:
        with st.spinner(f"FETCHING {ticker}..."):
            snap = fetch_company_snapshot(ticker)
    except Exception as e:
        st.error(f"COULD NOT LOAD '{ticker}' — {e}")
        st.stop()

    change_class = "up" if snap["change_pct"] > 0 else ("down" if snap["change_pct"] < 0 else "")
    change_sign = "+" if snap["change_pct"] >= 0 else ""

    st.markdown(f"### {snap['name']}")
    st.caption(f"TICKER: {snap['ticker']}")

    st.markdown(
        f"""
<div class="stat-row">
  <div class="stat-block"><div class="stat-label">Price</div><div class="stat-value accent">${snap['price']:,.2f}</div></div>
  <div class="stat-block"><div class="stat-label">Change Today</div><div class="stat-value {change_class}">{change_sign}{snap['change_pct']:.2f}%</div></div>
  <div class="stat-block"><div class="stat-label">Sector</div><div class="stat-value">{snap['sector']}</div></div>
  <div class="stat-block"><div class="stat-label">Country</div><div class="stat-value">{snap['country']}</div></div>
</div>
""",
        unsafe_allow_html=True,
    )

    st.warning(
        "COMPETITOR / SUPPLIER / CUSTOMER LISTS BELOW ARE AI-GENERATED ESTIMATES, "
        "NOT VERIFIED FINANCIAL DATA. THEY MAY BE INCOMPLETE, OUTDATED, OR WRONG — "
        "VERIFY INDEPENDENTLY BEFORE RELYING ON THEM."
    )

    with st.spinner("GENERATING RELATIONSHIP ESTIMATES..."):
        rel = fetch_relationships(snap["name"], snap["ticker"], snap["sector"], snap["industry"])

    if rel is None:
        st.info(
            "ADD AN ANTHROPIC_API_KEY TO STREAMLIT SECRETS TO ENABLE THE "
            "COMPETITOR / SUPPLIER / CUSTOMER LOOKUP."
        )
    elif rel.get("error"):
        st.warning("COULD NOT GENERATE RELATIONSHIP DATA RIGHT NOW.")
        if rel.get("detail"):
            st.caption(f"DETAIL: {rel['detail']}")
    else:
        col_left, col_center, col_right = st.columns(3)
        with col_left:
            render_rel_column("Suppliers", rel["suppliers"])
        with col_center:
            render_rel_column("Competitors", rel["competitors"])
        with col_right:
            render_rel_column("Customers", rel["customers"])

    st.caption(f"LAST RUN: {datetime.now():%Y-%m-%d %H:%M}")

else:
    st.info("ENTER A TICKER ABOVE, THEN PRESS ANALYZE.")
