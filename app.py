import streamlit as st
import plotly.graph_objects as go
from core import fetch_stock_data, fmt_large, fmt_pct, fmt_price, fmt_ratio

st.set_page_config(
    page_title="Stock Analyzer",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown("""
<style>
    .block-container { padding-top: 2rem; }
    .metric-label { font-size: 0.8rem; color: #888; }
    .signal-bull { color: #4caf50; }
    .signal-bear { color: #f44336; }
    .signal-neutral { color: #ff9800; }
    div[data-testid="stMetric"] { background: #1a1a2e; border-radius: 8px; padding: 12px; }
</style>
""", unsafe_allow_html=True)

# ── Header ────────────────────────────────────────────────────────────────────

st.title("📈 Stock Analyzer")
st.caption("Fundamental + Technical analysis via Yahoo Finance")

col_input, col_btn = st.columns([4, 1])
with col_input:
    ticker_input = st.text_input(
        "Ticker", placeholder="Enter a ticker — AAPL, NVDA, TSM, ASML...",
        label_visibility="collapsed"
    )
with col_btn:
    analyze_btn = st.button("Analyze", type="primary", use_container_width=True)

st.divider()

if not ticker_input and not analyze_btn:
    st.markdown("""
    **How to use:**
    1. Type a stock ticker in the box above (e.g. `AAPL`, `NVDA`, `TSM`)
    2. Click **Analyze**
    3. Get fundamentals, technicals, macro risks, and a recommendation

    Works for US stocks and international ADRs (TSMC, ASML, Samsung, etc.)
    """)
    st.stop()

if not ticker_input:
    st.warning("Enter a ticker symbol.")
    st.stop()

symbol = ticker_input.strip().upper()

# ── Fetch Data ────────────────────────────────────────────────────────────────

@st.cache_data(ttl=300, show_spinner=False)
def get_data(sym):
    return fetch_stock_data(sym)

with st.spinner(f"Fetching data for {symbol}..."):
    try:
        d = get_data(symbol)
    except ValueError as e:
        st.error(str(e))
        st.stop()
    except Exception as e:
        st.error(f"Unexpected error: {e}")
        st.stop()

# ── Company Header ────────────────────────────────────────────────────────────

chg_color = "green" if d["day_chg"] >= 0 else "red"
arrow = "▲" if d["day_chg"] >= 0 else "▼"
subtitle = f"{d['sector']}  ·  {d['industry']}"
if d["country"] and d["country"] != "United States":
    subtitle += f"  ·  {d['country']}"

st.subheader(f"{d['name']}  ({d['symbol']})")
st.caption(subtitle)

price_col, chg_col, mktcap_col, vol_col = st.columns(4)
price_col.metric("Price", f"{d['trade_symbol']}{d['current']:,.2f}")
chg_col.metric("Today", f"{arrow} {d['trade_symbol']}{abs(d['day_chg']):.2f}", f"{d['day_pct']:+.2f}%")
mktcap_col.metric("Market Cap", fmt_large(d["mktcap"]))
vol_col.metric("Volume", f"{d['volume']:,}" if d["volume"] else "N/A")

# International note
if d["is_foreign"]:
    notes = []
    if d["fin_is_local"]:
        notes.append(f"📌 Financials below are in **{d['fin_currency']}** ({d['fin_symbol'].strip()}), not USD.")
    notes.append(f"💱 FX between **{d['fin_currency']}** and USD affects total returns for US investors.")
    if d["div_yield_frac"] and d["div_yield_frac"] > 0:
        notes.append("🧾 Dividend withholding tax may apply for US investors.")
    st.info("  \n".join(notes))

st.divider()

# ── Tabs ──────────────────────────────────────────────────────────────────────

tab1, tab2, tab3 = st.tabs(["📊 Fundamentals", "📈 Technical & Analysts", "🌍 Risk & Decision"])

# ══════════════════════════════════════════════════════════════════════════════
# TAB 1 — FUNDAMENTALS
# ══════════════════════════════════════════════════════════════════════════════
with tab1:

    # Valuation row
    st.subheader("Valuation")
    v1, v2, v3, v4, v5, v6 = st.columns(6)
    v1.metric("Trailing P/E", fmt_ratio(d["pe"]))
    v2.metric("Forward P/E", fmt_ratio(d["fpe"]))
    v3.metric("PEG", fmt_ratio(d["peg"]))
    v4.metric("EV/EBITDA", fmt_ratio(d["ev_ebitda"]))
    v5.metric("Price/Book", fmt_ratio(d["pb"]))
    v6.metric("Price/Sales", fmt_ratio(d["ps"]))

    e1, e2 = st.columns(2)
    e1.metric("EPS (TTM)", f"{d['trade_symbol']}{d['eps']:.2f}" if d["eps"] else "N/A")
    e2.metric("EPS (Forward)", f"{d['trade_symbol']}{d['feps']:.2f}" if d["feps"] else "N/A")

    st.divider()

    # Financials
    fin_label = "Financials"
    if d["fin_is_local"]:
        fin_label += f"  (in {d['fin_currency']})"
    st.subheader(fin_label)

    s = d["fin_symbol"]
    f1, f2, f3, f4 = st.columns(4)
    f1.metric("Revenue", fmt_large(d["revenue"], s))
    f2.metric("Gross Profit", fmt_large(d["gross_profit"], s))
    f3.metric("Net Income", fmt_large(d["net_income"], s))
    f4.metric("Free Cash Flow", fmt_large(d["fcf"], s))

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Gross Margin", fmt_pct(d["gross_margin"]))
    m2.metric("Operating Margin", fmt_pct(d["op_margin"]))
    m3.metric("Net Margin", fmt_pct(d["net_margin"]))
    m4.metric("EBITDA", fmt_large(d["ebitda"], s))

    g1, g2 = st.columns(2)
    g1.metric("Revenue Growth YoY", fmt_pct(d["rev_growth"]))
    g2.metric("Earnings Growth YoY", fmt_pct(d["earn_growth"]))

    st.divider()

    # Balance sheet
    st.subheader("Balance Sheet Health")
    b1, b2, b3, b4, b5 = st.columns(5)
    de_display = f"{d['de']/100:.2f}" if d["de"] is not None else "N/A"
    b1.metric("Debt / Equity", de_display)
    b2.metric("Current Ratio", fmt_ratio(d["cur_ratio"]))
    b3.metric("Quick Ratio", fmt_ratio(d["quick"]))
    b4.metric("Return on Equity", fmt_pct(d["roe"]))
    b5.metric("Return on Assets", fmt_pct(d["roa"]))

    # Dividends
    if d["div_yield_frac"] and d["div_yield_frac"] > 0:
        st.divider()
        st.subheader("Dividends")
        d1, d2, d3, d4 = st.columns(4)
        d1.metric("Dividend Yield", fmt_pct(d["div_yield_frac"]))
        d2.metric("Annual Dividend", f"{d['trade_symbol']}{d['div_rate']:.2f}" if d["div_rate"] else "N/A")
        d3.metric("Payout Ratio", fmt_pct(d["payout"]))
        from datetime import datetime
        ex_str = datetime.fromtimestamp(d["ex_div"]).strftime("%Y-%m-%d") if d["ex_div"] else "N/A"
        d4.metric("Ex-Div Date", ex_str)

    # 52-week range
    st.divider()
    st.subheader("52-Week Range")
    r1, r2, r3, r4 = st.columns(4)
    r1.metric("52W High", fmt_price(d["high52"], d["trade_symbol"]))
    r2.metric("52W Low", fmt_price(d["low52"], d["trade_symbol"]))
    r3.metric("From 52W High", f"{d['pct_from_high']:.1f}%" if d["pct_from_high"] is not None else "N/A")
    r4.metric("Beta", f"{d['beta']:.2f}" if d["beta"] else "N/A")


# ══════════════════════════════════════════════════════════════════════════════
# TAB 2 — TECHNICAL & ANALYSTS
# ══════════════════════════════════════════════════════════════════════════════
with tab2:

    # Price chart
    st.subheader("Price Chart (1 Year)")
    hist = d["hist"]
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=hist.index, y=hist["Close"].round(2),
        name="Price", line=dict(color="#7B68EE", width=2), fill="tozeroy",
        fillcolor="rgba(123,104,238,0.05)"
    ))
    fig.add_trace(go.Scatter(
        x=hist.index, y=d["ma50_series"].round(2),
        name="50-Day MA", line=dict(color="#FFA500", width=1.5, dash="dot")
    ))
    fig.add_trace(go.Scatter(
        x=hist.index, y=d["ma200_series"].round(2),
        name="200-Day MA", line=dict(color="#FF6B6B", width=1.5, dash="dot")
    ))
    fig.update_layout(
        template="plotly_dark",
        height=380,
        margin=dict(l=0, r=0, t=10, b=0),
        legend=dict(orientation="h", y=-0.15),
        yaxis_title=f"Price ({d['trade_symbol'].strip()})",
        hovermode="x unified",
    )
    st.plotly_chart(fig, use_container_width=True)

    st.divider()

    # Technical indicators
    st.subheader("Technical Indicators")
    t1, t2, t3, t4, t5 = st.columns(5)
    t1.metric("50-Day MA", fmt_price(d["ma50"], d["trade_symbol"]), "Above ▲" if d["above50"] else "Below ▼")
    t2.metric("200-Day MA", fmt_price(d["ma200"], d["trade_symbol"]), "Above ▲" if d["above200"] else "Below ▼")
    t3.metric("RSI (14)", f"{d['rsi']:.1f}", "Oversold" if d["rsi"] < 30 else ("Overbought" if d["rsi"] > 70 else "Neutral"))
    t4.metric("MACD", f"{d['macd']:.3f}", "Bullish" if d["macd"] > d["macd_sig"] else "Bearish")
    t5.metric("MA Cross", "Golden ▲" if d["golden_cross"] else "Death ▼")

    st.divider()

    # Analyst ratings
    if d["target_mean"]:
        st.subheader("Analyst Ratings")
        a1, a2, a3, a4, a5 = st.columns(5)
        a1.metric("Consensus", d["rec"].replace("_", " ").title() if d["rec"] else "N/A")
        a2.metric("# Analysts", str(d["num_analysts"]) if d["num_analysts"] else "N/A")
        a3.metric("Mean Target", fmt_price(d["target_mean"], d["trade_symbol"]))
        a4.metric("Upside", f"{d['analyst_upside']:+.1f}%" if d["analyst_upside"] is not None else "N/A")
        a5.metric("Target Range", f"{fmt_price(d['target_low'], d['trade_symbol'])} – {fmt_price(d['target_high'], d['trade_symbol'])}")


# ══════════════════════════════════════════════════════════════════════════════
# TAB 3 — RISK & DECISION
# ══════════════════════════════════════════════════════════════════════════════
with tab3:

    # Macro risks
    st.subheader("🌍 Macro & Geopolitical Risks")

    if d["country_risks"]:
        st.markdown(f"**{d['country']} — Country / Geopolitical Risks**")
        for risk in d["country_risks"]:
            st.markdown(f"🔴 {risk}")

    if d["sector_risks"]:
        label = d["sector"]
        if d["industry"] and d["industry"] != d["sector"]:
            label += f" / {d['industry']}"
        st.markdown(f"**{label} — Sector Risks**")
        for risk in d["sector_risks"]:
            st.markdown(f"🟡 {risk}")

    if d["macro_news"]:
        st.markdown("**Recent Headlines**")
        for date, headline in d["macro_news"]:
            st.markdown(f"[{date}] {headline}")

    if not d["country_risks"] and not d["sector_risks"] and not d["macro_news"]:
        st.info("No specific macro risks identified.")

    st.divider()

    # Bull vs Bear
    st.subheader("Bull vs Bear")
    bull_col, bear_col = st.columns(2)
    with bull_col:
        st.markdown("### 🟢 Bull Case")
        for pt in d["bull_pts"]:
            st.markdown(f"▲ {pt}")
    with bear_col:
        st.markdown("### 🔴 Bear Case")
        for pt in d["bear_pts"]:
            st.markdown(f"▼ {pt}")

    st.divider()

    # Decision summary
    st.subheader("Decision Summary")
    for sig in d["signals"]:
        if sig["bullish"] is True:
            st.markdown(f"🟢 {sig['label']}")
        elif sig["bullish"] is False:
            st.markdown(f"🔴 {sig['label']}")
        else:
            st.markdown(f"🟡 {sig['label']}")

    score = d["score"]
    score_color = "green" if score >= 4 else ("red" if score <= -2 else "orange")
    st.markdown(f"**Score: {score:+d}**")

    st.divider()

    # Recommendation
    st.subheader("Recommendation")
    action_colors = {
        "strong_buy": ("🟢", "STRONG BUY"),
        "buy": ("🟢", "BUY"),
        "accumulate": ("🟡", "ACCUMULATE"),
        "hold": ("🟡", "HOLD"),
        "reduce": ("🔴", "REDUCE"),
        "sell": ("🔴", "SELL / AVOID"),
    }
    icon, label = action_colors.get(d["action_style"], ("⚪", d["action"]))
    st.markdown(f"## {icon} {label}")

    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**If buying:**")
        st.info(d["buying"])
    with c2:
        st.markdown("**If holding:**")
        st.info(d["holding"])

    if d["risk_notes"]:
        st.markdown("**Risk notes:**")
        for note in d["risk_notes"]:
            st.warning(note)

    st.caption("For informational purposes only — not financial advice.")
