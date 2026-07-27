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
import plotly.graph_objects as go

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
    on failure, otherwise {"competitors": [...], "suppliers": [...], "customers": [...]}
    where each item is {"name": str, "ticker": str or None}.
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
        f"For each company, include its stock ticker symbol if it is publicly traded (use the primary "
        f"US listing symbol where one exists, e.g. an ADR ticker for a foreign company), or null if it "
        f"is privately held.\n\n"
        f"Respond with ONLY valid JSON, no markdown code fences, no preamble, in exactly this shape:\n"
        f'{{"competitors": [{{"name": "...", "ticker": "..."}}, ...], '
        f'"suppliers": [{{"name": "...", "ticker": "..."}}, ...], '
        f'"customers": [{{"name": "...", "ticker": null}}, ...]}}\n'
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

        def _clean(items):
            out = []
            for it in list(items)[:5]:
                if isinstance(it, dict):
                    out.append({"name": it.get("name", "?"), "ticker": it.get("ticker") or None})
                else:
                    out.append({"name": str(it), "ticker": None})
            return out

        return {
            "competitors": _clean(parsed.get("competitors", [])),
            "suppliers": _clean(parsed.get("suppliers", [])),
            "customers": _clean(parsed.get("customers", [])),
        }
    except Exception as e:
        return {"error": True, "detail": f"{type(e).__name__}: {e}"}


@st.cache_data(ttl=300, show_spinner=False)
def fetch_change_pct(ticker: str):
    """Just today's % change for a related-company box. Returns None on any failure."""
    if not ticker:
        return None
    try:
        t = yf.Ticker(ticker)
        fi = t.fast_info
        price = fi.get("lastPrice")
        prev_close = fi.get("previousClose")
        if price and prev_close:
            return float((price - prev_close) / prev_close * 100)
    except Exception:
        pass
    return None


GRAY = (110, 110, 110)
GREEN_LIME = (144, 238, 144)
GREEN_DEEP = (11, 102, 35)
RED_PINK = (247, 198, 199)
RED_DEEP = (178, 34, 34)


def _lerp(c1, c2, t):
    return tuple(int(c1[i] + (c2[i] - c1[i]) * t) for i in range(3))


def _rgb_to_hex(rgb):
    return "#{:02X}{:02X}{:02X}".format(*rgb)


def change_to_color(pct) -> str:
    """Red (down) -> gray (flat/unknown) -> green (up) gradient, scaled by magnitude."""
    if pct is None or abs(pct) <= 0.05:
        return _rgb_to_hex(GRAY)
    if pct > 0:
        t = min(pct / 10.0, 1.0)
        rgb = _lerp(GREEN_LIME, GREEN_DEEP, t) if pct > 1 else _lerp(GRAY, GREEN_LIME, pct)
    else:
        mag = abs(pct)
        t = min((mag - 1) / 9.0, 1.0)
        rgb = _lerp(RED_PINK, RED_DEEP, t) if mag > 1 else _lerp(GRAY, RED_PINK, mag)
    return _rgb_to_hex(rgb)


def build_tree_diagram(center, suppliers, competitors, customers):
    """Node-link diagram: suppliers left, customers right, competitors below,
    all connected to a central company box, each colored by today's % change."""
    fig = go.Figure()
    shapes = []
    annotations = []

    def add_box(x0, x1, y0, y1, color, lines):
        shapes.append(dict(
            type="rect", x0=x0, x1=x1, y0=y0, y1=y1,
            line=dict(color="#000000", width=2), fillcolor=color,
        ))
        annotations.append(dict(
            x=(x0 + x1) / 2, y=(y0 + y1) / 2,
            text="<br>".join(lines), showarrow=False,
            font=dict(family="IBM Plex Mono", color="#000000", size=11),
            align="center",
        ))

    def add_connector(x0, y0, x1, y1):
        shapes.append(dict(
            type="line", x0=x0, y0=y0, x1=x1, y1=y1,
            line=dict(color="#7A5A2E", width=1.5),
        ))

    # Center box
    cx0, cx1, cy0, cy1 = 4.0, 6.0, 4.0, 6.0
    center_color = change_to_color(center["change_pct"])
    add_box(cx0, cx1, cy0, cy1, center_color, [
        f"<b>{center['ticker']}</b>", center['name'][:26],
        f"{center['change_pct']:+.2f}%",
    ])

    box_w, gap = 2.0, 0.35

    def side_column(items, x0, x1, align_right_edge_to_center):
        n = len(items)
        if n == 0:
            return
        total_h = n * 1.3 + (n - 1) * gap
        y_top = 5.0 + total_h / 2
        for i, item in enumerate(items):
            y1 = y_top - i * (1.3 + gap)
            y0 = y1 - 1.3
            color = change_to_color(item["change_pct"])
            label = [f"<b>{item['ticker'] or 'N/A'}</b>", item['name'][:22]]
            if item["change_pct"] is not None:
                label.append(f"{item['change_pct']:+.2f}%")
            else:
                label.append("PRIVATE / N/A")
            add_box(x0, x1, y0, y1, color, label)
            conn_x = x1 if align_right_edge_to_center else x0
            target_x = cx0 if align_right_edge_to_center else cx1
            add_connector(conn_x, (y0 + y1) / 2, target_x, (cy0 + cy1) / 2)

    side_column(suppliers, 0.0, 0.0 + box_w, True)
    side_column(customers, 10.0 - box_w, 10.0, False)

    # Competitors row below center
    n = len(competitors)
    if n:
        total_w = n * 2.0 + (n - 1) * 0.3
        x_start = 5.0 - total_w / 2
        for i, item in enumerate(competitors):
            x0 = x_start + i * (2.0 + 0.3)
            x1 = x0 + 2.0
            y0, y1 = 0.8, 1.9
            color = change_to_color(item["change_pct"])
            label = [f"<b>{item['ticker'] or 'N/A'}</b>", item['name'][:22]]
            if item["change_pct"] is not None:
                label.append(f"{item['change_pct']:+.2f}%")
            else:
                label.append("PRIVATE / N/A")
            add_box(x0, x1, y0, y1, color, label)
            add_connector((x0 + x1) / 2, y1, (cx0 + cx1) / 2, cy0)

    fig.update_layout(
        shapes=shapes,
        annotations=annotations,
        xaxis=dict(visible=False, range=[-0.3, 10.3]),
        yaxis=dict(visible=False, range=[0.3, 9.5], scaleanchor="x"),
        height=650,
        paper_bgcolor="#000000",
        plot_bgcolor="#000000",
        margin=dict(l=10, r=10, t=30, b=10),
        showlegend=False,
    )

    # column headers
    fig.add_annotation(x=1.0, y=9.2, text="SUPPLIERS", showarrow=False,
                        font=dict(family="IBM Plex Mono", color="#FF8C00", size=13))
    fig.add_annotation(x=9.0, y=9.2, text="CUSTOMERS", showarrow=False,
                        font=dict(family="IBM Plex Mono", color="#FF8C00", size=13))
    fig.add_annotation(x=5.0, y=0.55, text="COMPETITORS", showarrow=False,
                        font=dict(family="IBM Plex Mono", color="#FF8C00", size=13))

    return fig




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
        with st.spinner("PRICING RELATED COMPANIES..."):
            for group in ("suppliers", "competitors", "customers"):
                for item in rel[group]:
                    item["change_pct"] = fetch_change_pct(item["ticker"])

        center = {"name": snap["name"], "ticker": snap["ticker"], "change_pct": snap["change_pct"]}
        fig_tree = build_tree_diagram(center, rel["suppliers"], rel["competitors"], rel["customers"])
        st.plotly_chart(fig_tree, use_container_width=True)
        st.caption(
            "BOX COLOR = THAT COMPANY'S OWN PRICE CHANGE TODAY  |  GRAY = FLAT OR NO TICKER FOUND  |  "
            "GREEN SCALES TO DEEP EVERGREEN AT +10%  |  RED SCALES TO DEEP RED AT -10%"
        )

    st.caption(f"LAST RUN: {datetime.now():%Y-%m-%d %H:%M}")

else:
    st.info("ENTER A TICKER ABOVE, THEN PRESS ANALYZE.")
