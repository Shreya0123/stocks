"""
Shared data fetching, computation, and helper logic.
Imported by both the CLI (stock_analyzer.py) and web app (app.py).
"""

import yfinance as yf
import pandas as pd
from datetime import datetime

# ── Currency ──────────────────────────────────────────────────────────────────

_CURRENCY_SYMBOLS = {
    "USD": "$", "TWD": "NT$", "EUR": "€", "GBP": "£",
    "JPY": "¥", "CNY": "CN¥", "CNH": "CN¥", "HKD": "HK$",
    "KRW": "₩", "INR": "₹", "AUD": "A$", "CAD": "C$",
    "CHF": "CHF ", "SEK": "kr", "NOK": "kr", "DKK": "kr",
    "SGD": "S$", "MXN": "MX$", "BRL": "R$", "ZAR": "R",
    "SAR": "SAR ", "AED": "AED ", "ILS": "₪", "TRY": "₺",
    "THB": "฿", "MYR": "RM", "IDR": "Rp", "PHP": "₱",
}

def currency_symbol(code):
    return _CURRENCY_SYMBOLS.get(code, f"{code} ") if code else "$"


def get_usd_rate(currency: str) -> float:
    if not currency or currency == "USD":
        return 1.0
    try:
        rate = yf.Ticker(f"{currency}USD=X").fast_info["last_price"]
        return float(rate) if rate else 1.0
    except Exception:
        return 1.0


# ── Country / Geopolitical Risk Data ─────────────────────────────────────────

COUNTRY_RISKS = {
    "Taiwan": [
        "Taiwan Strait: military conflict or blockade would threaten the entire operation — no off-island redundancy for leading-edge fabs",
        "China claims sovereignty — escalation is a structural risk, not a tail event",
        "US-China tensions directly impact Taiwan's security posture and investor sentiment",
        "Geographic concentration: ~90% of world's advanced chips made on a disputed island",
    ],
    "China": [
        "CCP regulatory risk: overnight intervention can destroy business models (Alibaba, DiDi precedent)",
        "VIE structure: foreign investors hold contractual rights only — not direct equity ownership",
        "HFCAA delisting risk: SEC can delist Chinese ADRs that fail PCAOB audit access",
        "US-China decoupling accelerating — export bans, investment restrictions, and tariffs widening",
        "Capital controls make repatriating profits slow and uncertain",
    ],
    "Hong Kong": [
        "National Security Law erodes rule-of-law premium historically priced into HK equities",
        "Mainland regulatory reach now extends into Hong Kong listings",
        "HKD peg: a break would cause significant currency dislocation",
    ],
    "South Korea": [
        "North Korea escalation: Seoul is within artillery range — conflict risk is a permanent discount",
        "Chaebol governance: concentrated family control limits minority shareholder protections",
        "KRW is a high-beta currency — falls sharply in global risk-off events",
    ],
    "Japan": [
        "Yen weakness structurally erodes USD-denominated returns for foreign investors",
        "Aging population and domestic deflation constrain long-run revenue growth",
        "Corporate governance improving but shareholder return culture still lags Western peers",
        "BOJ policy normalisation risk: decades of ultra-low rates unwinding could spike yields",
    ],
    "India": [
        "Regulatory unpredictability: sudden policy reversals can impair foreign investments",
        "INR structurally depreciates against USD — erodes total returns over time",
        "Infrastructure gaps and bureaucracy add friction and execution delays",
    ],
    "Germany": [
        "Energy transition costs: structurally high energy prices disadvantage German heavy industry",
        "China export dependence: slowdown in Chinese demand hits German manufacturers hard",
        "Digitisation lag relative to US and Asian peers constrains productivity gains",
    ],
    "United Kingdom": [
        "Post-Brexit trade friction adds ongoing cost and complexity for UK-EU business",
        "GBP has structural weakness vs USD — long-run depreciation trend erodes returns",
        "London financial centre faces sustained competition from EU post-Brexit",
    ],
    "France": [
        "Government has a history of strategic intervention and nationalisation in key sectors",
        "EU regulatory environment among the most aggressive globally (GDPR, DSA, DMA)",
        "Labour law rigidity limits ability to restructure quickly during downturns",
    ],
    "Netherlands": [
        "ASML export controls: Dutch government under US pressure to restrict chip equipment sales to China",
        "Small open economy highly sensitive to global trade volume and EU growth",
        "EU regulatory scrutiny intensifying — Brussels increasingly targets tech and industrial leaders",
    ],
    "Switzerland": [
        "CHF safe-haven appreciation during crises hurts exporters' competitiveness",
        "High cost base structurally limits price competitiveness in commodity markets",
    ],
    "Sweden": [
        "SEK is a risk-off currency — depreciates sharply during global downturns",
        "Small open economy highly exposed to European growth and global trade conditions",
    ],
    "Canada": [
        "~75% of exports go to the US — trade policy changes hit disproportionately hard",
        "CAD weakens in risk-off environments, amplifying USD-denominated return volatility",
        "Energy and materials heavy economy amplifies commodity cycle swings",
    ],
    "Australia": [
        "Heavy China trade dependence — iron ore, LNG exports highly exposed to China slowdown",
        "AUD is a commodity-linked, risk-sensitive currency — falls sharply in global downturns",
    ],
    "Brazil": [
        "Political instability and policy unpredictability create persistent governance discount",
        "BRL structural depreciation trend erodes USD returns over time",
        "Commodity dependence makes GDP, earnings, and FX highly cyclical",
    ],
    "Mexico": [
        "US tariff risk despite USMCA — nearshoring proximity is an opportunity but also a political target",
        "Rule of law and cartel-related security risk add operational friction",
        "MXN volatile around US election cycles and bilateral trade policy shifts",
    ],
    "Israel": [
        "Active regional conflict (Gaza, Hezbollah, Iran) creates ongoing business disruption risk",
        "Military reserve service obligations can temporarily reduce tech workforce availability",
        "Regional escalation with Iran could have severe and unpredictable consequences",
    ],
    "Russia": [
        "Comprehensive Western sanctions — effectively uninvestable for most foreign investors",
        "Asset seizure risk and strict capital controls prevent repatriation",
    ],
    "Saudi Arabia": [
        "Oil price dependence: government spending and activity tightly coupled to crude",
        "Iran-Saudi proxy tensions and regional conflict create geopolitical volatility",
        "Governance and rule-of-law risk limits minority shareholder protections",
    ],
    "Singapore": [
        "City-state open economy is highly sensitive to global trade volume shocks",
        "Positioned between US and Chinese spheres of influence — forced to navigate both carefully",
    ],
}

# ── Sector Risk Data ──────────────────────────────────────────────────────────

SECTOR_RISKS = {
    "Technology": [
        "Rate sensitivity: high-multiple tech compresses sharply when rates rise",
        "Antitrust scrutiny intensifying in US (DOJ/FTC) and EU",
        "AI valuation crowding — multiple compression risk if AI growth disappoints",
    ],
    "Semiconductors": [
        "US export controls (BIS) restrict advanced chip and equipment sales to China",
        "Supply chain concentration: TSMC and ASML are single points of failure",
        "Hyperscaler custom silicon (Google TPU, AWS Trainium) threatens GPU incumbents",
        "Demand cyclicality: datacenter and consumer buildouts can reverse quickly",
    ],
    "Semiconductor Equipment & Materials": [
        "China revenue at risk: export controls directly cut equipment sales to Chinese fabs",
        "Sole-source monopoly on EUV — but any China restriction immediately hits the top line",
        "Customer concentration: revenue tied to capex cycles of a handful of leading fabs",
    ],
    "Financial Services": [
        "Credit cycle risk: rising consumer and commercial real estate defaults",
        "NIM compression if rates fall; credit losses if rates stay elevated",
        "Basel III endgame capital rules increase cost of equity for large banks",
    ],
    "Consumer Cyclical": [
        "Consumer spending slows disproportionately in recessions",
        "Inflation erodes discretionary budgets and compresses margins",
        "Inventory build-up risk if demand falls faster than supply adjustments",
    ],
    "Healthcare": [
        "Drug pricing legislation (IRA) caps Medicare negotiation upside",
        "Clinical trial binary risk — pipeline failures can erase value instantly",
        "FDA approval timelines add execution uncertainty",
    ],
    "Energy": [
        "Oil and gas prices highly sensitive to OPEC+ policy and geopolitical supply shocks",
        "Energy transition policy accelerates long-term demand erosion",
        "Capital-intensive business model vulnerable to rate hikes",
    ],
    "Communication Services": [
        "Digital advertising is cyclical — pullback in recessions hits revenue hard",
        "Platform regulation tightening in US and EU (DSA, CMA)",
        "AI-driven search disruption threatens traditional advertising models",
    ],
    "Industrials": [
        "Global supply chain disruptions and tariffs raise input costs",
        "Capital expenditure cycles amplify revenue swings",
    ],
    "Real Estate": [
        "Cap rate expansion compresses valuations as rates rise",
        "Office and retail segments face structural demand shifts post-COVID",
        "Refinancing risk as debt matures into a higher rate environment",
    ],
    "Consumer Staples": [
        "Input cost inflation limits margin expansion despite pricing power",
        "Private label competition intensifies during consumer downturns",
    ],
    "Materials": [
        "Commodity price volatility driven by China construction and industrial demand",
        "Currency risk: revenues often USD but costs are local",
    ],
    "Utilities": [
        "Highly rate-sensitive — dividend yield competes directly with risk-free rates",
        "Regulatory pricing caps limit ability to pass through capex costs",
    ],
}

_MACRO_KEYWORDS = [
    "tariff", "trade war", "sanction", "export ban", "export restrict",
    "china", "geopolit", "inflation", "interest rate", "federal reserve", "fed rate",
    "recession", "regulat", "antitrust", "lawsuit", "supply chain",
    "shortage", "war", "conflict", "currency", "ban", "legislation",
    "opec", "ukraine", "taiwan", "deficit", "debt ceiling", "treasury yield",
    "import", "duties", "trade tension", "earnings miss", "guidance cut",
    "layoff", "downgrade", "investigation", "probe",
]

# ── Helpers ───────────────────────────────────────────────────────────────────

def safe(info, key, default=None):
    val = info.get(key, default)
    if val in (None, "Infinity", float("inf"), float("-inf")):
        return default
    if isinstance(val, float) and pd.isna(val):
        return default
    return val


def fmt_price(val, symbol="$"):
    return f"{symbol}{val:,.2f}" if val is not None else "N/A"


def fmt_pct(val):
    return f"{val * 100:.1f}%" if val is not None else "N/A"


def fmt_large(val, prefix="$"):
    if val is None:
        return "N/A"
    abs_val = abs(val)
    sign = "-" if val < 0 else ""
    if abs_val >= 1e12:
        return f"{sign}{prefix}{abs_val/1e12:.2f}T"
    if abs_val >= 1e9:
        return f"{sign}{prefix}{abs_val/1e9:.2f}B"
    if abs_val >= 1e6:
        return f"{sign}{prefix}{abs_val/1e6:.2f}M"
    return f"{sign}{prefix}{abs_val:,.0f}"


def fmt_ratio(val, decimals=2):
    return f"{val:.{decimals}f}x" if val is not None else "N/A"


# ── Technical Indicators ──────────────────────────────────────────────────────

def calc_rsi(prices, period=14):
    delta = prices.diff()
    gain = delta.clip(lower=0).ewm(com=period - 1, min_periods=period).mean()
    loss = (-delta.clip(upper=0)).ewm(com=period - 1, min_periods=period).mean()
    rs = gain / loss
    return float((100 - 100 / (1 + rs)).iloc[-1])


def calc_macd(prices):
    ema12 = prices.ewm(span=12, adjust=False).mean()
    ema26 = prices.ewm(span=26, adjust=False).mean()
    macd = ema12 - ema26
    signal = macd.ewm(span=9, adjust=False).mean()
    return float(macd.iloc[-1]), float(signal.iloc[-1])


# ── News ──────────────────────────────────────────────────────────────────────

def fetch_macro_news(ticker_obj):
    try:
        news = ticker_obj.news or []
    except Exception:
        return []
    results = []
    for item in news[:25]:
        title = item.get("title", "")
        if any(kw in title.lower() for kw in _MACRO_KEYWORDS):
            ts = item.get("providerPublishTime", 0)
            date = datetime.fromtimestamp(ts).strftime("%b %d") if ts else ""
            results.append((date, title))
    return results[:6]


# ── Bull / Bear Builder ───────────────────────────────────────────────────────

def build_bull_bear(current, ma50, ma200, pe, fpe, peg, net_margin,
                    rev_growth, earn_growth, de, target_mean, beta,
                    fcf, revenue, country):
    bull, bear = [], []

    if rev_growth is not None:
        if rev_growth > 0.30:
            bull.append(f"Hypergrowth at {rev_growth*100:.0f}% YoY — rare at this scale, commands a premium")
        elif rev_growth > 0.10:
            bull.append(f"Solid {rev_growth*100:.0f}% revenue growth YoY sustains the long-term thesis")
        elif rev_growth < 0:
            bear.append(f"Revenue contracting {rev_growth*100:.1f}% YoY — growth story is under pressure")

    if earn_growth is not None:
        if earn_growth > 0.30:
            bull.append(f"Earnings growing {earn_growth*100:.0f}% YoY — operating leverage is compounding")
        elif earn_growth < 0:
            bear.append(f"Earnings declining {earn_growth*100:.1f}% YoY — profitability under threat")

    if fpe is not None:
        if fpe < 18:
            bull.append(f"Forward P/E of {fpe:.1f}x — growth already priced in conservatively")
        elif fpe > 35:
            bear.append(f"Forward P/E of {fpe:.1f}x leaves no margin of safety — any miss punished hard")

    if peg is not None:
        if peg < 1:
            bull.append(f"PEG of {peg:.2f} — paying less than 1x for each unit of growth, a classic value signal")
        elif peg > 2.5:
            bear.append(f"PEG of {peg:.2f} — growth expectations may already be fully priced in")

    if pe is not None and pe > 50:
        bear.append(f"Trailing P/E of {pe:.0f}x reflects sky-high expectations; execution must be flawless")

    if net_margin is not None:
        if net_margin > 0.25:
            bull.append(f"{net_margin*100:.0f}% net margin reflects exceptional pricing power and a durable moat")
        elif net_margin > 0.10:
            bull.append(f"Healthy {net_margin*100:.0f}% net margin — business is efficiently run")
        elif net_margin < 0:
            bear.append(f"Unprofitable (net margin {net_margin*100:.1f}%) — path to profitability unclear")

    if de is not None:
        if de < 30:
            bull.append(f"Near debt-free (D/E: {de/100:.2f}) — can self-fund R&D and buybacks without dilution")
        elif de > 200:
            bear.append(f"High leverage (D/E: {de/100:.2f}) — vulnerable to rate hikes and refinancing risk")

    if fcf is not None and revenue is not None and revenue > 0:
        fcf_margin = fcf / revenue
        if fcf_margin > 0.20:
            bull.append(f"FCF margin of {fcf_margin*100:.0f}% generates substantial cash for growth and returns")
        elif fcf_margin < 0:
            bear.append("Negative free cash flow — growth is consuming more cash than it generates")

    if target_mean is not None and current:
        upside = (target_mean - current) / current * 100
        if upside > 25:
            bull.append(f"Analyst consensus targets {upside:.0f}% upside to ${target_mean:.0f} mean price")
        elif upside < -10:
            bear.append(f"Analyst community sees {abs(upside):.0f}% downside — consensus at ${target_mean:.0f}")

    if current > ma200 and ma50 > ma200:
        bull.append("Technical uptrend intact — price above both MAs with golden cross confirmed")
    elif current < ma200:
        bear.append("Trading below 200-day MA — medium-term trend is structurally bearish")

    if beta is not None and beta > 2.0:
        bear.append(f"Beta of {beta:.1f} amplifies market moves — a 10% market drop hits this ~{beta*10:.0f}%")

    country_bear = {
        "Taiwan": "Taiwan Strait military risk is an existential threat — entire advanced fab capacity on a disputed island",
        "China": "VIE structure and CCP intervention mean foreign investors have limited legal recourse",
        "Hong Kong": "National Security Law erodes the rule-of-law premium historically priced into HK equities",
        "South Korea": "North Korea escalation creates a permanent geopolitical discount on Korean equities",
        "Japan": "Yen weakness erodes USD-denominated returns — a headwind that compounds over time",
        "India": "INR structural depreciation quietly erodes USD total returns over a multi-year hold",
        "Brazil": "BRL depreciation and political instability are persistent headwinds to USD returns",
        "Russia": "Comprehensive Western sanctions — effectively uninvestable for foreign investors",
    }
    if country in country_bear:
        bear.append(country_bear[country])

    fallbacks_bull = [
        "Market leadership creates pricing power and switching cost moat",
        "Strong brand and ecosystem lock-in reduces customer churn risk",
    ]
    fallbacks_bear = [
        "Macro slowdown could compress multiples and dampen near-term spending",
        "Competitive landscape intensifying — market share gains not guaranteed",
    ]
    for fb in fallbacks_bull:
        if len(bull) >= 4: break
        bull.append(fb)
    for fb in fallbacks_bear:
        if len(bear) >= 4: break
        bear.append(fb)

    return bull[:5], bear[:5]


# ── Recommendation Builder ────────────────────────────────────────────────────

def build_recommendation(score, current, ma50, ma200, rsi, beta, pe, fpe,
                          target_mean, rev_growth, is_foreign, fin_currency):
    if score >= 7:
        action, style = "STRONG BUY", "strong_buy"
    elif score >= 4:
        action, style = "BUY", "buy"
    elif score >= 1:
        action, style = "ACCUMULATE", "accumulate"
    elif score >= -1:
        action, style = "HOLD", "hold"
    elif score >= -4:
        action, style = "REDUCE", "reduce"
    else:
        action, style = "SELL / AVOID", "sell"

    upside_str = ""
    if target_mean and current:
        upside = (target_mean - current) / current * 100
        upside_str = f" Analyst mean target of ${target_mean:.0f} implies {upside:+.0f}% upside."

    beta_note = ""
    if beta and beta > 1.5:
        beta_note = f" Given beta of {beta:.1f}, size this position at 50–70% of your normal allocation."

    if score >= 4:
        buying = f"Strong entry at current levels.{upside_str}{beta_note} Scale in over 2–3 tranches to manage timing risk."
        holding = f"Maintain or add to your position. Add on any pullback to the 50-day MA (${ma50:.2f}). Consider a trailing stop-loss below the 200-day MA (${ma200:.2f})."
    elif score >= 1:
        buying = f"Consider a half-position now.{upside_str} Wait for a retest of the 50-day MA (${ma50:.2f}) for a better entry before adding the rest.{beta_note}"
        holding = f"Hold your position. Watch for a break below the 50-day MA (${ma50:.2f}) as an early warning sign."
    elif score >= -1:
        buying = f"Neutral — watchlist only. Wait for a clearer technical setup (breakout above ${ma50:.2f}) or improving fundamentals before committing capital."
        holding = f"Hold with a defined stop-loss below the 200-day MA (${ma200:.2f}). No reason to add at current levels."
    else:
        buying = "Avoid. Multiple headwinds present. Better risk/reward opportunities likely available elsewhere."
        holding = f"Consider reducing or exiting. Look for a near-term bounce to sell at better prices. A break below the 200-day MA (${ma200:.2f}) would confirm further downside."

    risk_notes = []
    if beta and beta > 1.8:
        risk_notes.append(f"High beta ({beta:.1f}) amplifies volatility — expect sharp swings around earnings and macro events.")
    if rsi > 68:
        risk_notes.append(f"RSI at {rsi:.0f} is approaching overbought territory — a short-term pullback is possible.")
    if pe and pe > 45:
        risk_notes.append(f"Premium valuation (P/E {pe:.0f}x) means any earnings miss or guidance cut will be heavily penalised.")
    if rev_growth is not None and rev_growth < 0:
        risk_notes.append("Declining revenue — confirm this is cyclical, not structural, before holding through it.")
    if is_foreign and fin_currency and fin_currency != "USD":
        risk_notes.append(f"Currency risk: financials reported in {fin_currency} — a strengthening USD will reduce USD-denominated returns even if the local business performs well.")

    return action, style, buying, holding, risk_notes


# ── Signal Scoring ────────────────────────────────────────────────────────────

def compute_signals(pe, peg, net_margin, rev_growth, de, target_mean, current,
                    above50, above200, rsi, macd, macd_sig, golden_cross):
    signals = []
    score = 0

    def add(label, pts, bullish):
        nonlocal score
        signals.append({"label": label, "pts": pts, "bullish": bullish})
        score += pts

    add("Price above 50-day MA" if above50 else "Price below 50-day MA", 1 if above50 else -1, above50)
    add("Price above 200-day MA" if above200 else "Price below 200-day MA", 1 if above200 else -1, above200)

    if rsi < 30:
        add(f"RSI oversold ({rsi:.1f}) — potential reversal", 1, True)
    elif rsi > 70:
        add(f"RSI overbought ({rsi:.1f}) — potential pullback", -1, False)
    else:
        add(f"RSI neutral ({rsi:.1f})", 0, None)

    add("MACD bullish" if macd > macd_sig else "MACD bearish", 1 if macd > macd_sig else -1, macd > macd_sig)
    add("Golden cross (50MA > 200MA)" if golden_cross else "Death cross (50MA < 200MA)", 1 if golden_cross else -1, golden_cross)

    if pe is not None:
        if pe < 0:
            add(f"Negative P/E (unprofitable, {pe:.1f}x)", -1, False)
        elif pe < 20:
            add(f"Attractive P/E ({pe:.1f}x)", 1, True)
        elif pe > 40:
            add(f"High P/E ({pe:.1f}x)", -1, False)
        else:
            add(f"Fair P/E ({pe:.1f}x)", 0, None)

    if peg is not None:
        if peg < 1:
            add(f"PEG < 1 suggests undervaluation ({peg:.2f})", 1, True)
        elif peg > 2:
            add(f"PEG > 2 suggests overvaluation ({peg:.2f})", -1, False)

    if net_margin is not None:
        if net_margin > 0.15:
            add(f"Strong net margin ({net_margin*100:.1f}%)", 1, True)
        elif net_margin < 0:
            add(f"Negative net margin ({net_margin*100:.1f}%)", -1, False)

    if rev_growth is not None:
        if rev_growth > 0.10:
            add(f"Strong revenue growth ({rev_growth*100:.1f}% YoY)", 1, True)
        elif rev_growth < 0:
            add(f"Negative revenue growth ({rev_growth*100:.1f}% YoY)", -1, False)

    if de is not None:
        if de < 50:
            add(f"Low debt/equity ({de/100:.2f})", 1, True)
        elif de > 200:
            add(f"High debt/equity ({de/100:.2f})", -1, False)

    if target_mean and current:
        upside_val = (target_mean - current) / current * 100
        if upside_val > 20:
            add(f"Strong analyst upside ({upside_val:.1f}%)", 1, True)
        elif upside_val > 0:
            add(f"Modest analyst upside ({upside_val:.1f}%)", 0, None)
        else:
            add(f"Analyst sees downside ({upside_val:.1f}%)", -1, False)

    return signals, score


# ── Main Data Fetch ───────────────────────────────────────────────────────────

def fetch_stock_data(symbol: str) -> dict:
    ticker = yf.Ticker(symbol)
    info = ticker.info

    if not info or safe(info, "quoteType") is None:
        raise ValueError(f"Ticker not found: {symbol}")

    hist = ticker.history(period="1y")
    if hist.empty:
        raise ValueError(f"No price history for {symbol}")

    close = hist["Close"]
    current = float(close.iloc[-1])
    prev = float(close.iloc[-2])
    day_chg = current - prev
    day_pct = (day_chg / prev) * 100

    name = safe(info, "longName") or safe(info, "shortName") or symbol.upper()
    sector = safe(info, "sector", "")
    industry = safe(info, "industry", "")
    country = safe(info, "country", "")

    trade_currency = safe(info, "currency") or "USD"
    fin_currency = safe(info, "financialCurrency") or trade_currency
    fin_symbol = currency_symbol(fin_currency)
    trade_symbol = currency_symbol(trade_currency)
    is_foreign = country not in ("United States", "")
    fin_is_local = fin_currency != "USD"
    usd_rate = get_usd_rate(fin_currency)

    mktcap = safe(info, "marketCap")
    volume = safe(info, "volume")
    avg_vol = safe(info, "averageVolume")
    beta = safe(info, "beta")
    high52 = safe(info, "fiftyTwoWeekHigh")
    low52 = safe(info, "fiftyTwoWeekLow")
    pct_from_high = ((current - high52) / high52 * 100) if high52 else None
    pct_from_low = ((current - low52) / low52 * 100) if low52 else None

    pe = safe(info, "trailingPE")
    fpe = safe(info, "forwardPE")
    pb = safe(info, "priceToBook")
    ps = safe(info, "priceToSalesTrailing12Months")
    ev_ebitda = safe(info, "enterpriseToEbitda")
    peg = safe(info, "pegRatio")
    eps = safe(info, "trailingEps")
    feps = safe(info, "forwardEps")

    revenue = safe(info, "totalRevenue")
    gross_profit = safe(info, "grossProfits")
    ebitda = safe(info, "ebitda")
    net_income = safe(info, "netIncomeToCommon")
    fcf = safe(info, "freeCashflow")
    gross_margin = safe(info, "grossMargins")
    op_margin = safe(info, "operatingMargins")
    net_margin = safe(info, "profitMargins")
    rev_growth = safe(info, "revenueGrowth")
    earn_growth = safe(info, "earningsGrowth")

    de = safe(info, "debtToEquity")
    cur_ratio = safe(info, "currentRatio")
    quick = safe(info, "quickRatio")
    roe = safe(info, "returnOnEquity")
    roa = safe(info, "returnOnAssets")

    # USD-converted financials (for web app display)
    def to_usd(val):
        return val * usd_rate if val is not None else None

    revenue_usd = to_usd(revenue)
    gross_profit_usd = to_usd(gross_profit)
    ebitda_usd = to_usd(ebitda)
    net_income_usd = to_usd(net_income)
    fcf_usd = to_usd(fcf)

    div_yield = safe(info, "dividendYield")
    div_yield_frac = (div_yield / 100) if div_yield else None
    div_rate = safe(info, "dividendRate")
    payout = safe(info, "payoutRatio")
    ex_div = safe(info, "exDividendDate")

    ma50_series = close.rolling(50).mean()
    ma200_series = close.rolling(200).mean()
    ma50 = float(ma50_series.iloc[-1])
    ma200 = float(ma200_series.iloc[-1])
    rsi = calc_rsi(close)
    macd, macd_sig = calc_macd(close)
    above50 = current > ma50
    above200 = current > ma200
    golden_cross = ma50 > ma200

    target_mean = safe(info, "targetMeanPrice")
    target_high = safe(info, "targetHighPrice")
    target_low = safe(info, "targetLowPrice")
    rec = safe(info, "recommendationKey", "")
    num_analysts = safe(info, "numberOfAnalystOpinions")
    analyst_upside = ((target_mean - current) / current * 100) if target_mean else None

    country_risks = COUNTRY_RISKS.get(country, [])
    sector_risks = SECTOR_RISKS.get(sector, []) + SECTOR_RISKS.get(industry, [])
    macro_news = fetch_macro_news(ticker)

    bull_pts, bear_pts = build_bull_bear(
        current, ma50, ma200, pe, fpe, peg, net_margin,
        rev_growth, earn_growth, de, target_mean, beta, fcf, revenue, country
    )

    signals, score = compute_signals(
        pe, peg, net_margin, rev_growth, de, target_mean, current,
        above50, above200, rsi, macd, macd_sig, golden_cross
    )

    action, action_style, buying, holding, risk_notes = build_recommendation(
        score, current, ma50, ma200, rsi, beta, pe, fpe,
        target_mean, rev_growth, is_foreign, fin_currency
    )

    return {
        "symbol": symbol.upper(),
        "name": name,
        "sector": sector,
        "industry": industry,
        "country": country,
        "trade_currency": trade_currency,
        "fin_currency": fin_currency,
        "fin_symbol": fin_symbol,
        "trade_symbol": trade_symbol,
        "is_foreign": is_foreign,
        "fin_is_local": fin_is_local,
        "current": current,
        "day_chg": day_chg,
        "day_pct": day_pct,
        "mktcap": mktcap,
        "volume": volume,
        "avg_vol": avg_vol,
        "beta": beta,
        "high52": high52,
        "low52": low52,
        "pct_from_high": pct_from_high,
        "pct_from_low": pct_from_low,
        "pe": pe,
        "fpe": fpe,
        "pb": pb,
        "ps": ps,
        "ev_ebitda": ev_ebitda,
        "peg": peg,
        "eps": eps,
        "feps": feps,
        "usd_rate": usd_rate,
        "revenue": revenue,
        "gross_profit": gross_profit,
        "ebitda": ebitda,
        "net_income": net_income,
        "fcf": fcf,
        "revenue_usd": revenue_usd,
        "gross_profit_usd": gross_profit_usd,
        "ebitda_usd": ebitda_usd,
        "net_income_usd": net_income_usd,
        "fcf_usd": fcf_usd,
        "gross_margin": gross_margin,
        "op_margin": op_margin,
        "net_margin": net_margin,
        "rev_growth": rev_growth,
        "earn_growth": earn_growth,
        "de": de,
        "cur_ratio": cur_ratio,
        "quick": quick,
        "roe": roe,
        "roa": roa,
        "div_yield_frac": div_yield_frac,
        "div_rate": div_rate,
        "payout": payout,
        "ex_div": ex_div,
        "hist": hist,
        "ma50_series": ma50_series,
        "ma200_series": ma200_series,
        "ma50": ma50,
        "ma200": ma200,
        "rsi": rsi,
        "macd": macd,
        "macd_sig": macd_sig,
        "above50": above50,
        "above200": above200,
        "golden_cross": golden_cross,
        "target_mean": target_mean,
        "target_high": target_high,
        "target_low": target_low,
        "rec": rec,
        "num_analysts": num_analysts,
        "analyst_upside": analyst_upside,
        "country_risks": country_risks,
        "sector_risks": sector_risks,
        "macro_news": macro_news,
        "bull_pts": bull_pts,
        "bear_pts": bear_pts,
        "signals": signals,
        "score": score,
        "action": action,
        "action_style": action_style,
        "buying": buying,
        "holding": holding,
        "risk_notes": risk_notes,
    }
