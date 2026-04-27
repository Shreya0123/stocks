import streamlit as st
import plotly.graph_objects as go
from datetime import datetime
from core import fetch_stock_data, fmt_large, fmt_pct, fmt_price, fmt_ratio

st.set_page_config(
    page_title="Stock Analyzer",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown("""
<style>
    .block-container { padding-top: 1.5rem; }
    div[data-testid="stMetric"] {
        background: #1a1a2e;
        border-radius: 10px;
        padding: 14px 18px;
        border: 1px solid #2a2a4a;
    }
    .verdict-box {
        border-radius: 12px;
        padding: 20px 28px;
        margin: 12px 0;
        font-size: 1.1rem;
        line-height: 1.7;
    }
    .glossary-term {
        font-weight: 700;
        font-size: 1rem;
        margin-top: 1rem;
    }
    .glossary-body {
        font-size: 0.9rem;
        color: #ccc;
        line-height: 1.6;
    }
</style>
""", unsafe_allow_html=True)

# ── Header ────────────────────────────────────────────────────────────────────

st.title("📈 Stock Analyzer")
st.caption("Fundamental + Technical + Macro analysis via Yahoo Finance")

col_input, col_btn = st.columns([4, 1])
with col_input:
    ticker_input = st.text_input(
        "Ticker", placeholder="Type a ticker — AAPL, NVDA, TSM, ASML...",
        label_visibility="collapsed"
    )
with col_btn:
    st.write("")
    analyze_btn = st.button("Analyze", type="primary", use_container_width=True)

st.divider()

if not ticker_input and not analyze_btn:
    st.markdown("""
    **How to use:**  type a stock ticker above and hit **Analyze**.

    Works for US stocks and international ADRs — all financials shown in **USD**.

    > `AAPL` · `NVDA` · `MSFT` · `TSM` · `ASML` · `BABA` · `TM` · `SAP`
    """)
    st.stop()

if not ticker_input:
    st.warning("Enter a ticker symbol first.")
    st.stop()

symbol = ticker_input.strip().upper()

# ── Fetch ─────────────────────────────────────────────────────────────────────

@st.cache_data(ttl=300, show_spinner=False)
def get_data(sym):
    return fetch_stock_data(sym)

with st.spinner(f"Fetching data for **{symbol}**..."):
    try:
        d = get_data(symbol)
    except ValueError as e:
        st.error(str(e))
        st.stop()
    except Exception as e:
        st.error(f"Something went wrong: {e}")
        st.stop()

# ── Company Header ────────────────────────────────────────────────────────────

arrow = "▲" if d["day_chg"] >= 0 else "▼"
chg_sign = "+" if d["day_chg"] >= 0 else ""
subtitle = f"{d['sector']}  ·  {d['industry']}"
if d["country"] and d["country"] != "United States":
    subtitle += f"  ·  {d['country']}"

st.subheader(f"{d['name']}   ({d['symbol']})")
st.caption(subtitle)

h1, h2, h3, h4, h5 = st.columns(5)
h1.metric("Price (USD)", f"${d['current']:,.2f}")
h2.metric("Today", f"{arrow} ${abs(d['day_chg']):.2f}", f"{chg_sign}{d['day_pct']:.2f}%")
h3.metric("Market Cap", fmt_large(d["mktcap"]))
h4.metric("52W Range", f"${d['low52']:,.0f} – ${d['high52']:,.0f}" if d["low52"] and d["high52"] else "N/A")
h5.metric("Beta", f"{d['beta']:.2f}" if d["beta"] else "N/A")

if d["is_foreign"] and d["fin_is_local"]:
    usd_rate = d.get("usd_rate", 1.0)
    st.info(f"💱  Financials converted from **{d['fin_currency']}** to USD (rate: 1 {d['fin_currency']} = ${usd_rate:.4f}). Ratios and margins are unaffected.")

st.divider()

# ── Tabs ──────────────────────────────────────────────────────────────────────

tab1, tab2, tab3, tab4 = st.tabs(["📊 Fundamentals", "📈 Technical & Analysts", "🌍 Risk & Decision", "📚 Glossary"])

# ══════════════════════════════════════════════════════════════════════════════
# TAB 1 — FUNDAMENTALS
# ══════════════════════════════════════════════════════════════════════════════
with tab1:

    st.subheader("Valuation")
    v1, v2, v3, v4, v5, v6 = st.columns(6)
    v1.metric("Trailing P/E", fmt_ratio(d["pe"]))
    v2.metric("Forward P/E", fmt_ratio(d["fpe"]))
    v3.metric("PEG Ratio", fmt_ratio(d["peg"]))
    v4.metric("EV / EBITDA", fmt_ratio(d["ev_ebitda"]))
    v5.metric("Price / Book", fmt_ratio(d["pb"]))
    v6.metric("Price / Sales", fmt_ratio(d["ps"]))

    e1, e2 = st.columns(2)
    e1.metric("EPS (TTM)", f"${d['eps']:.2f}" if d["eps"] else "N/A")
    e2.metric("EPS (Forward)", f"${d['feps']:.2f}" if d["feps"] else "N/A")

    st.divider()
    st.subheader("Financials (USD)")

    f1, f2, f3, f4 = st.columns(4)
    f1.metric("Revenue", fmt_large(d["revenue_usd"]))
    f2.metric("Gross Profit", fmt_large(d["gross_profit_usd"]))
    f3.metric("Net Income", fmt_large(d["net_income_usd"]))
    f4.metric("Free Cash Flow", fmt_large(d["fcf_usd"]))

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Gross Margin", fmt_pct(d["gross_margin"]))
    m2.metric("Operating Margin", fmt_pct(d["op_margin"]))
    m3.metric("Net Margin", fmt_pct(d["net_margin"]))
    m4.metric("EBITDA", fmt_large(d["ebitda_usd"]))

    g1, g2 = st.columns(2)
    g1.metric("Revenue Growth YoY", fmt_pct(d["rev_growth"]))
    g2.metric("Earnings Growth YoY", fmt_pct(d["earn_growth"]))

    st.divider()
    st.subheader("Balance Sheet")
    b1, b2, b3, b4, b5 = st.columns(5)
    b1.metric("Debt / Equity", f"{d['de']/100:.2f}" if d["de"] is not None else "N/A")
    b2.metric("Current Ratio", fmt_ratio(d["cur_ratio"]))
    b3.metric("Quick Ratio", fmt_ratio(d["quick"]))
    b4.metric("Return on Equity", fmt_pct(d["roe"]))
    b5.metric("Return on Assets", fmt_pct(d["roa"]))

    if d["div_yield_frac"] and d["div_yield_frac"] > 0:
        st.divider()
        st.subheader("Dividends")
        d1, d2, d3, d4 = st.columns(4)
        d1.metric("Dividend Yield", fmt_pct(d["div_yield_frac"]))
        d2.metric("Annual Dividend", f"${d['div_rate']:.2f}" if d["div_rate"] else "N/A")
        d3.metric("Payout Ratio", fmt_pct(d["payout"]))
        ex_str = datetime.fromtimestamp(d["ex_div"]).strftime("%Y-%m-%d") if d["ex_div"] else "N/A"
        d4.metric("Ex-Div Date", ex_str)
        if d["is_foreign"]:
            st.caption("⚠️ Withholding tax may apply on dividends for US investors.")

# ══════════════════════════════════════════════════════════════════════════════
# TAB 2 — TECHNICAL & ANALYSTS
# ══════════════════════════════════════════════════════════════════════════════
with tab2:

    st.subheader("Price Chart — 1 Year")
    hist = d["hist"]
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=hist.index, y=hist["Close"].round(2),
        name="Price", line=dict(color="#818cf8", width=2),
        fill="tozeroy", fillcolor="rgba(129,140,248,0.05)"
    ))
    fig.add_trace(go.Scatter(
        x=hist.index, y=d["ma50_series"].round(2),
        name="50-Day MA", line=dict(color="#fb923c", width=1.5, dash="dot")
    ))
    fig.add_trace(go.Scatter(
        x=hist.index, y=d["ma200_series"].round(2),
        name="200-Day MA", line=dict(color="#f87171", width=1.5, dash="dot")
    ))
    fig.update_layout(
        template="plotly_dark", height=380,
        margin=dict(l=0, r=0, t=10, b=0),
        legend=dict(orientation="h", y=-0.15),
        yaxis_title="Price (USD)", hovermode="x unified",
    )
    st.plotly_chart(fig, use_container_width=True)

    st.divider()

    # RSI gauge + MACD side by side
    st.subheader("Technical Indicators")
    gauge_col, metrics_col = st.columns([1, 2])

    with gauge_col:
        rsi_val = d["rsi"]
        rsi_color = "#4caf50" if rsi_val < 30 else ("#f44336" if rsi_val > 70 else "#fb923c")
        fig_rsi = go.Figure(go.Indicator(
            mode="gauge+number",
            value=round(rsi_val, 1),
            title={"text": "RSI (14)", "font": {"size": 14}},
            gauge={
                "axis": {"range": [0, 100], "tickwidth": 1},
                "bar": {"color": rsi_color, "thickness": 0.25},
                "steps": [
                    {"range": [0, 30], "color": "rgba(76,175,80,0.2)"},
                    {"range": [30, 70], "color": "rgba(251,146,60,0.1)"},
                    {"range": [70, 100], "color": "rgba(244,67,54,0.2)"},
                ],
                "threshold": {"line": {"color": "white", "width": 3}, "thickness": 0.75, "value": rsi_val},
            }
        ))
        fig_rsi.update_layout(
            template="plotly_dark", height=220,
            margin=dict(l=20, r=20, t=40, b=10),
        )
        st.plotly_chart(fig_rsi, use_container_width=True)
        rsi_label = "🟢 Oversold — potential buy zone" if rsi_val < 30 else ("🔴 Overbought — potential pullback" if rsi_val > 70 else "🟡 Neutral territory")
        st.caption(rsi_label)

    with metrics_col:
        t1, t2 = st.columns(2)
        t1.metric("50-Day MA", fmt_price(d["ma50"]), "Price Above ▲" if d["above50"] else "Price Below ▼")
        t2.metric("200-Day MA", fmt_price(d["ma200"]), "Price Above ▲" if d["above200"] else "Price Below ▼")
        t3, t4 = st.columns(2)
        t3.metric("MACD", f"{d['macd']:.3f}", "Bullish" if d["macd"] > d["macd_sig"] else "Bearish")
        t4.metric("MA Cross", "Golden Cross ▲" if d["golden_cross"] else "Death Cross ▼")

    st.divider()

    if d["target_mean"]:
        st.subheader("Analyst Ratings")
        a1, a2, a3, a4, a5 = st.columns(5)
        a1.metric("Consensus", d["rec"].replace("_", " ").title() if d["rec"] else "N/A")
        a2.metric("# Analysts", str(d["num_analysts"]) if d["num_analysts"] else "N/A")
        a3.metric("Mean Target", fmt_price(d["target_mean"]))
        a4.metric("Upside", f"{d['analyst_upside']:+.1f}%" if d["analyst_upside"] is not None else "N/A")
        a5.metric("Target Range", f"${d['target_low']:,.0f} – ${d['target_high']:,.0f}" if d["target_low"] and d["target_high"] else "N/A")

# ══════════════════════════════════════════════════════════════════════════════
# TAB 3 — RISK & DECISION
# ══════════════════════════════════════════════════════════════════════════════
with tab3:

    # Score gauge + verdict side by side
    score = d["score"]
    gauge_c, verdict_c = st.columns([1, 2])

    with gauge_c:
        needle_color = "#4caf50" if score >= 4 else ("#f44336" if score <= -2 else "#fb923c")
        fig_score = go.Figure(go.Indicator(
            mode="gauge+number",
            value=score,
            title={"text": "Overall Score", "font": {"size": 14}},
            gauge={
                "axis": {"range": [-10, 10], "tickwidth": 1},
                "bar": {"color": needle_color, "thickness": 0.25},
                "steps": [
                    {"range": [-10, -4], "color": "rgba(244,67,54,0.25)"},
                    {"range": [-4, -1], "color": "rgba(244,67,54,0.1)"},
                    {"range": [-1, 1],  "color": "rgba(251,146,60,0.1)"},
                    {"range": [1, 4],   "color": "rgba(76,175,80,0.1)"},
                    {"range": [4, 10],  "color": "rgba(76,175,80,0.25)"},
                ],
                "threshold": {"line": {"color": "white", "width": 3}, "thickness": 0.75, "value": score},
            }
        ))
        fig_score.update_layout(
            template="plotly_dark", height=240,
            margin=dict(l=20, r=20, t=40, b=10),
        )
        st.plotly_chart(fig_score, use_container_width=True)

    with verdict_c:
        action_map = {
            "strong_buy": ("🟢", "STRONG BUY",   "#14532d", "#4ade80"),
            "buy":        ("🟢", "BUY",           "#14532d", "#86efac"),
            "accumulate": ("🟡", "ACCUMULATE",    "#422006", "#fbbf24"),
            "hold":       ("🟡", "HOLD",          "#422006", "#fde68a"),
            "reduce":     ("🔴", "REDUCE",        "#450a0a", "#f87171"),
            "sell":       ("🔴", "SELL / AVOID",  "#450a0a", "#ef4444"),
        }
        icon, label, bg, fg = action_map.get(d["action_style"], ("⚪", d["action"], "#1f2937", "#fff"))
        st.markdown(f"""
        <div style="background:{bg}; border-radius:12px; padding:20px 24px; margin-top:8px;">
            <div style="font-size:2rem; font-weight:800; color:{fg};">{icon} {label}</div>
            <div style="margin-top:12px; color:#e5e7eb; font-size:0.95rem;">
                <b>If buying:</b> {d['buying']}<br><br>
                <b>If holding:</b> {d['holding']}
            </div>
        </div>
        """, unsafe_allow_html=True)

    if d["risk_notes"]:
        for note in d["risk_notes"]:
            st.warning(note)

    st.divider()

    # Signal checklist
    st.subheader("Signal Breakdown")
    sig_col1, sig_col2 = st.columns(2)
    half = len(d["signals"]) // 2
    for i, sig in enumerate(d["signals"]):
        col = sig_col1 if i < half else sig_col2
        if sig["bullish"] is True:
            col.markdown(f"🟢 {sig['label']}")
        elif sig["bullish"] is False:
            col.markdown(f"🔴 {sig['label']}")
        else:
            col.markdown(f"🟡 {sig['label']}")

    st.divider()

    # Macro risks
    st.subheader("🌍 Macro & Geopolitical Risks")

    if d["country_risks"]:
        with st.expander(f"🔴 {d['country']} — Country Risks", expanded=True):
            for r in d["country_risks"]:
                st.markdown(f"- {r}")

    if d["sector_risks"]:
        label = d["sector"] + (f" / {d['industry']}" if d["industry"] and d["industry"] != d["sector"] else "")
        with st.expander(f"🟡 {label} — Sector Risks", expanded=True):
            for r in d["sector_risks"]:
                st.markdown(f"- {r}")

    if d["macro_news"]:
        with st.expander("📰 Recent Macro Headlines", expanded=False):
            for date, headline in d["macro_news"]:
                st.markdown(f"**[{date}]** {headline}")

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

    st.caption("For informational purposes only — not financial advice.")

# ══════════════════════════════════════════════════════════════════════════════
# TAB 4 — GLOSSARY
# ══════════════════════════════════════════════════════════════════════════════
with tab4:
    st.subheader("📚 What Does Each Metric Mean?")
    st.caption("Plain-English definitions so you know exactly what you're looking at.")

    GLOSSARY = [
        {
            "section": "💰 Valuation — Are you paying a fair price?",
            "terms": [
                {
                    "name": "P/E Ratio (Trailing)",
                    "what": "Price divided by last 12 months of earnings per share. Tells you how much you're paying for every $1 of profit the company made.",
                    "high": "Expensive. The market expects strong future growth. Higher risk if growth disappoints.",
                    "low": "Cheap — either a genuine bargain or the market sees problems ahead.",
                    "range": "< 15 = cheap  ·  15–25 = fair  ·  25–40 = elevated  ·  > 40 = very expensive",
                },
                {
                    "name": "Forward P/E",
                    "what": "Same as P/E but uses next year's expected earnings instead of last year's. More forward-looking.",
                    "high": "Market is pricing in a lot of growth. If earnings disappoint, the stock drops hard.",
                    "low": "Either cheap or analysts are too optimistic. Check revenue growth to decide.",
                    "range": "< 15 = cheap  ·  15–25 = fair  ·  > 35 = expensive",
                },
                {
                    "name": "PEG Ratio",
                    "what": "P/E divided by the earnings growth rate. Adjusts the P/E for growth — a high P/E is fine if the company is growing fast.",
                    "high": "> 2: You're overpaying relative to growth. The stock needs to grow very fast to justify the price.",
                    "low": "< 1: Classic 'undervalued relative to growth' signal. You're paying less than 1x for each unit of growth.",
                    "range": "< 1 = undervalued  ·  1–2 = fairly valued  ·  > 2 = overvalued",
                },
                {
                    "name": "Price / Book (P/B)",
                    "what": "Share price divided by book value per share (assets minus liabilities). Tells you how much you pay vs what the company actually owns.",
                    "high": "> 5: You're paying a big premium for the brand, earnings power, or intangibles. Fine for quality businesses.",
                    "low": "< 1: Trading below its asset value — could be a deep value opportunity, or the assets are overvalued.",
                    "range": "< 1 = below book  ·  1–3 = normal  ·  > 5 = premium",
                },
                {
                    "name": "Price / Sales (P/S)",
                    "what": "Market cap divided by annual revenue. Useful for companies that aren't yet profitable.",
                    "high": "> 10: Very expensive on a revenue basis. Needs exceptional growth to justify.",
                    "low": "< 2: Cheap on revenue. Often seen in mature, low-margin industries.",
                    "range": "< 2 = cheap  ·  2–5 = fair  ·  > 10 = very expensive",
                },
                {
                    "name": "EV / EBITDA",
                    "what": "Enterprise value (market cap + debt - cash) divided by operating profit. A cleaner version of P/E that accounts for debt. Widely used in M&A.",
                    "high": "> 20: Expensive. Common in high-growth tech.",
                    "low": "< 10: Cheap. Common in value sectors like energy or industrials.",
                    "range": "< 10 = cheap  ·  10–20 = fair  ·  > 20 = expensive",
                },
            ]
        },
        {
            "section": "📈 Growth & Profitability — Is the business healthy?",
            "terms": [
                {
                    "name": "Revenue Growth (YoY)",
                    "what": "How much the company's total sales grew compared to the same period last year.",
                    "high": "> 20%: Strong growth — the business is expanding fast.",
                    "low": "Negative: Revenue is shrinking. This is a red flag unless it's a one-off.",
                    "range": "< 0% = declining  ·  0–10% = slow  ·  10–20% = solid  ·  > 30% = hypergrowth",
                },
                {
                    "name": "Gross Margin",
                    "what": "Revenue minus cost of goods sold, as a percentage. Shows how much is left after making the product, before paying salaries, rent, and other overheads.",
                    "high": "> 60%: Exceptional. Software and pharma companies often have this. Pricing power is strong.",
                    "low": "< 20%: Thin. Common in retail and manufacturing. Little room for error.",
                    "range": "< 20% = thin  ·  20–40% = decent  ·  40–60% = strong  ·  > 60% = exceptional",
                },
                {
                    "name": "Net Margin",
                    "what": "The percentage of revenue that becomes actual profit after all expenses, taxes, and interest.",
                    "high": "> 20%: Very profitable business. Strong pricing power and cost discipline.",
                    "low": "Negative: The company is losing money. Not always bad (early-stage growth) but needs watching.",
                    "range": "< 0% = losing money  ·  0–10% = low  ·  10–20% = healthy  ·  > 25% = excellent",
                },
                {
                    "name": "Free Cash Flow (FCF)",
                    "what": "Cash the business generates after spending on maintaining and growing its assets. The most honest measure of profitability — harder to fake than earnings.",
                    "high": "Positive and growing: The company is printing money. Can fund buybacks, dividends, acquisitions.",
                    "low": "Negative: Burning cash. Could be fine if it's investing for growth, but dangerous if it's structural.",
                    "range": "Positive = healthy  ·  Negative = cash burn  ·  FCF margin > 20% = exceptional",
                },
                {
                    "name": "Return on Equity (ROE)",
                    "what": "How much profit the company generates for every $1 of shareholder equity. Measures how efficiently management uses your money.",
                    "high": "> 20%: Management is creating strong returns. A hallmark of quality businesses.",
                    "low": "< 5%: Capital is being used inefficiently. Or the business is capital-light but unprofitable.",
                    "range": "< 5% = weak  ·  5–15% = decent  ·  15–30% = strong  ·  > 30% = exceptional",
                },
                {
                    "name": "Return on Assets (ROA)",
                    "what": "Profit generated per $1 of total assets. Shows how efficiently the company uses everything it owns.",
                    "high": "> 10%: Very efficient. Asset-light businesses (software, services) often score here.",
                    "low": "< 2%: Capital-heavy industries (banks, utilities) often have low ROA. Not always bad.",
                    "range": "< 2% = low  ·  2–5% = fair  ·  5–15% = strong  ·  > 15% = exceptional",
                },
            ]
        },
        {
            "section": "🏦 Balance Sheet — Can it survive a downturn?",
            "terms": [
                {
                    "name": "Debt / Equity (D/E)",
                    "what": "Total debt divided by shareholder equity. Shows how much the company relies on borrowed money vs its own capital.",
                    "high": "> 2: Highly leveraged. Works fine in good times but dangerous in recessions or rising rate environments.",
                    "low": "< 0.5: Conservative. Lots of financial flexibility. Less risk but may be leaving growth on the table.",
                    "range": "< 0.5 = conservative  ·  0.5–1.5 = normal  ·  > 2 = high leverage",
                },
                {
                    "name": "Current Ratio",
                    "what": "Current assets divided by current liabilities. Can the company pay its bills due within the next 12 months?",
                    "high": "> 2: Very liquid. Plenty of cushion to cover short-term obligations.",
                    "low": "< 1: More short-term debt than assets. Could struggle if cash flow dips.",
                    "range": "< 1 = risky  ·  1–1.5 = okay  ·  > 1.5 = healthy  ·  > 3 = very safe",
                },
                {
                    "name": "Quick Ratio",
                    "what": "Like the current ratio but excludes inventory (which can be hard to sell quickly). A stricter test of short-term financial health.",
                    "high": "> 1.5: Very comfortable. Can cover debts without selling any inventory.",
                    "low": "< 0.5: Could face liquidity problems if business slows suddenly.",
                    "range": "< 0.5 = risky  ·  0.5–1 = tight  ·  > 1 = healthy",
                },
            ]
        },
        {
            "section": "📉 Technical Indicators — What is the chart saying?",
            "terms": [
                {
                    "name": "RSI — Relative Strength Index",
                    "what": "A momentum indicator from 0–100 that measures how fast and how much a stock has moved recently. Used to spot when a stock has been overbought or oversold.",
                    "high": "> 70: Overbought. The stock has risen fast and may pull back in the short term.",
                    "low": "< 30: Oversold. The stock has fallen fast and may bounce. Often a buying opportunity.",
                    "range": "< 30 = oversold (bullish)  ·  30–70 = neutral  ·  > 70 = overbought (bearish)",
                },
                {
                    "name": "MACD",
                    "what": "Moving Average Convergence Divergence. Compares two moving averages to spot momentum shifts. When the MACD line is above the signal line, momentum is bullish.",
                    "high": "MACD above signal line: Bullish momentum — uptrend is strengthening.",
                    "low": "MACD below signal line: Bearish momentum — downtrend may be forming.",
                    "range": "MACD > signal = bullish  ·  MACD < signal = bearish",
                },
                {
                    "name": "50-Day & 200-Day Moving Average",
                    "what": "The average closing price over the last 50 or 200 trading days. A stock above its moving average is in an uptrend; below means downtrend.",
                    "high": "Price above MA: Bullish. The stock is trending up relative to its recent history.",
                    "low": "Price below MA: Bearish. The stock is underperforming its recent average.",
                    "range": "Above 200MA = long-term uptrend  ·  Below 200MA = long-term downtrend",
                },
                {
                    "name": "Golden Cross / Death Cross",
                    "what": "When the 50-day MA crosses above the 200-day MA it's a Golden Cross (bullish long-term signal). The opposite — 50-day crossing below 200-day — is a Death Cross (bearish).",
                    "high": "Golden Cross: Long-term uptrend confirmed. Historically strong bullish signal.",
                    "low": "Death Cross: Long-term downtrend confirmed. Often precedes further weakness.",
                    "range": "Golden Cross = bullish  ·  Death Cross = bearish",
                },
                {
                    "name": "Beta",
                    "what": "Measures how much a stock moves relative to the overall market. Beta of 1 = moves with the market. Beta of 2 = moves twice as much.",
                    "high": "> 1.5: High volatility stock. Bigger gains in bull markets, bigger losses in crashes.",
                    "low": "< 0.5: Defensive stock. Moves less than the market. Good for stability.",
                    "range": "< 0.5 = defensive  ·  0.5–1.5 = normal  ·  > 1.5 = volatile  ·  > 2 = very volatile",
                },
            ]
        },
        {
            "section": "🎯 Analyst Metrics",
            "terms": [
                {
                    "name": "Price Target (Mean)",
                    "what": "The average price analysts believe the stock should reach within 12 months, based on their financial models.",
                    "high": "Mean target well above current price: Analysts see significant upside — bullish signal.",
                    "low": "Mean target below current price: Analysts think the stock is overvalued at current levels.",
                    "range": "> 20% upside = bullish  ·  0–20% = modest  ·  Negative = bearish",
                },
                {
                    "name": "Consensus Rating",
                    "what": "The overall Buy/Hold/Sell rating across all analysts covering the stock, averaged into one verdict.",
                    "high": "Strong Buy: Most analysts are bullish. High conviction from professional research.",
                    "low": "Sell / Underperform: Most analysts think the stock will fall. Take seriously but always do your own research.",
                    "range": "Strong Buy → Buy → Hold → Underperform → Sell",
                },
            ]
        },
    ]

    for section in GLOSSARY:
        st.markdown(f"### {section['section']}")
        for term in section["terms"]:
            with st.expander(f"**{term['name']}**"):
                st.markdown(f"**What it measures:**  {term['what']}")
                st.markdown(f"**If high →**  {term['high']}")
                st.markdown(f"**If low →**  {term['low']}")
                st.markdown(f"**Benchmarks:**  `{term['range']}`")
        st.write("")
