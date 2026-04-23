#!/usr/bin/env python3
"""
Stock Analyzer — CLI version
Usage: python stock_analyzer.py <TICKER>
"""

import sys
import argparse
from datetime import datetime

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich.rule import Rule
from rich import box

from core import (
    fetch_stock_data, fmt_large, fmt_pct, fmt_price, fmt_ratio,
    currency_symbol, SECTOR_RISKS, COUNTRY_RISKS,
)

console = Console()


def signal_color(text, good):
    if good is True:
        return f"[green]{text}[/green]"
    if good is False:
        return f"[red]{text}[/red]"
    return f"[yellow]{text}[/yellow]"


def _two_col_table():
    t = Table(box=box.SIMPLE, show_header=False, padding=(0, 2))
    t.add_column("Metric", style="dim")
    t.add_column("Value", style="bold")
    t.add_column("Metric", style="dim")
    t.add_column("Value", style="bold")
    return t


def display(d: dict):
    s = d["trade_symbol"]
    fin_s = d["fin_symbol"]

    # ── Header ────────────────────────────────────────────────────────────────
    console.print(Rule())
    title = Text()
    title.append(f" {d['name']} ", style="bold white")
    subtitle = f"({d['symbol']})  ·  {d['sector']}  ·  {d['industry']}"
    if d["country"] and d["country"] != "United States":
        subtitle += f"  ·  {d['country']}"
    title.append(subtitle, style="dim")
    console.print(Panel(title, box=box.SIMPLE, padding=(0, 1)))

    price_line = Text()
    price_line.append(f"  {s}{d['current']:,.2f}", style="bold white")
    chg_color = "green" if d["day_chg"] >= 0 else "red"
    arrow = "▲" if d["day_chg"] >= 0 else "▼"
    price_line.append(f"   {arrow} {s}{abs(d['day_chg']):.2f}  ({abs(d['day_pct']):.2f}%)", style=f"bold {chg_color}")
    if d["is_foreign"]:
        price_line.append(f"   [dim]Trades in {d['trade_currency']} on US exchange[/dim]")
    console.print(price_line)
    console.print()

    # ── International note ────────────────────────────────────────────────────
    if d["is_foreign"]:
        adr_t = Table(box=box.SIMPLE, show_header=False, padding=(0, 1))
        adr_t.add_column("", width=2)
        adr_t.add_column("")
        if d["fin_is_local"]:
            adr_t.add_row("[yellow]![/yellow]", f"Financial statements are reported in [bold]{d['fin_currency']}[/bold] ({d['fin_symbol'].strip()}), not USD. Absolute figures below are in {d['fin_currency']}.")
        adr_t.add_row("[yellow]![/yellow]", f"Domiciled in [bold]{d['country']}[/bold]. FX between {d['fin_currency']} and USD affects total returns for US investors.")
        console.print(Panel(adr_t, title="[bold yellow]International Stock Note[/bold yellow]", box=box.ROUNDED))

    # ── Overview ──────────────────────────────────────────────────────────────
    t = _two_col_table()
    t.add_row("Market Cap", fmt_large(d["mktcap"]), "Beta", f"{d['beta']:.2f}" if d["beta"] else "N/A")
    t.add_row("52W High", fmt_price(d["high52"], s), "52W Low", fmt_price(d["low52"], s))
    t.add_row(
        "From 52W High",
        signal_color(f"{d['pct_from_high']:.1f}%" if d["pct_from_high"] is not None else "N/A", d["pct_from_high"] and d["pct_from_high"] > -10),
        "From 52W Low",
        signal_color(f"+{d['pct_from_low']:.1f}%" if d["pct_from_low"] is not None else "N/A", True),
    )
    t.add_row("Volume", f"{d['volume']:,}" if d["volume"] else "N/A", "Avg Volume", f"{d['avg_vol']:,}" if d["avg_vol"] else "N/A")
    console.print(Panel(t, title="[bold]Overview[/bold]", box=box.ROUNDED))

    # ── Valuation ─────────────────────────────────────────────────────────────
    def pe_sig(val):
        if val is None: return ""
        if val < 0: return "[red]Negative[/red]"
        if val < 15: return "[green]Cheap[/green]"
        if val < 25: return "[yellow]Fair[/yellow]"
        if val < 40: return "[yellow]Elevated[/yellow]"
        return "[red]Very High[/red]"

    tv = Table(box=box.SIMPLE, show_header=False, padding=(0, 2))
    for _ in range(6): tv.add_column()
    tv.add_row("Trailing P/E", fmt_ratio(d["pe"]), pe_sig(d["pe"]), "Forward P/E", fmt_ratio(d["fpe"]), pe_sig(d["fpe"]))
    tv.add_row(
        "Price/Book", fmt_ratio(d["pb"]),
        signal_color("Low", True) if d["pb"] and d["pb"] < 1 else (signal_color("High", False) if d["pb"] and d["pb"] > 5 else ""),
        "Price/Sales", fmt_ratio(d["ps"]),
        signal_color("Low", True) if d["ps"] and d["ps"] < 2 else (signal_color("High", False) if d["ps"] and d["ps"] > 10 else ""),
    )
    tv.add_row(
        "EV/EBITDA", fmt_ratio(d["ev_ebitda"]),
        signal_color("Low", True) if d["ev_ebitda"] and d["ev_ebitda"] < 10 else (signal_color("High", False) if d["ev_ebitda"] and d["ev_ebitda"] > 20 else ""),
        "PEG Ratio", fmt_ratio(d["peg"]),
        signal_color("Undervalued", True) if d["peg"] and d["peg"] < 1 else (signal_color("Overvalued", False) if d["peg"] and d["peg"] > 2 else ""),
    )
    tv.add_row("EPS (TTM)", f"{s}{d['eps']:.2f}" if d["eps"] else "N/A", "", "EPS (Fwd)", f"{s}{d['feps']:.2f}" if d["feps"] else "N/A", "")
    console.print(Panel(tv, title="[bold]Valuation[/bold]", box=box.ROUNDED))

    # ── Financials ────────────────────────────────────────────────────────────
    fin_title = "[bold]Financials[/bold]" + (f"  [dim](in {d['fin_currency']})[/dim]" if d["fin_is_local"] else "")
    ft = _two_col_table()
    ft.add_row("Revenue", fmt_large(d["revenue"], fin_s), "Free Cash Flow", fmt_large(d["fcf"], fin_s))
    ft.add_row("Gross Profit", fmt_large(d["gross_profit"], fin_s), "EBITDA", fmt_large(d["ebitda"], fin_s))
    ft.add_row("Net Income", fmt_large(d["net_income"], fin_s), "", "")
    ft.add_row("Gross Margin", signal_color(fmt_pct(d["gross_margin"]), d["gross_margin"] and d["gross_margin"] > 0.40), "Operating Margin", signal_color(fmt_pct(d["op_margin"]), d["op_margin"] and d["op_margin"] > 0.15))
    ft.add_row("Net Margin", signal_color(fmt_pct(d["net_margin"]), d["net_margin"] and d["net_margin"] > 0.10), "", "")
    ft.add_row("Revenue Growth (YoY)", signal_color(fmt_pct(d["rev_growth"]), d["rev_growth"] and d["rev_growth"] > 0), "Earnings Growth (YoY)", signal_color(fmt_pct(d["earn_growth"]), d["earn_growth"] and d["earn_growth"] > 0))
    console.print(Panel(ft, title=fin_title, box=box.ROUNDED))

    # ── Balance Sheet ─────────────────────────────────────────────────────────
    bt = Table(box=box.SIMPLE, show_header=False, padding=(0, 2))
    for _ in range(6): bt.add_column()
    de_display = f"{d['de']/100:.2f}" if d["de"] is not None else "N/A"
    bt.add_row("Debt/Equity", de_display, signal_color("Low", True) if d["de"] and d["de"] < 50 else (signal_color("High", False) if d["de"] and d["de"] > 200 else ""), "Current Ratio", fmt_ratio(d["cur_ratio"]), signal_color("Healthy", True) if d["cur_ratio"] and d["cur_ratio"] >= 1.5 else (signal_color("Low", False) if d["cur_ratio"] and d["cur_ratio"] < 1 else ""))
    bt.add_row("Quick Ratio", fmt_ratio(d["quick"]), signal_color("Healthy", True) if d["quick"] and d["quick"] >= 1 else (signal_color("Low", False) if d["quick"] and d["quick"] < 0.5 else ""), "", "", "")
    bt.add_row("Return on Equity", signal_color(fmt_pct(d["roe"]), d["roe"] and d["roe"] > 0.15), "", "Return on Assets", signal_color(fmt_pct(d["roa"]), d["roa"] and d["roa"] > 0.05), "")
    console.print(Panel(bt, title="[bold]Balance Sheet Health[/bold]", box=box.ROUNDED))

    # ── Dividends ─────────────────────────────────────────────────────────────
    if d["div_yield_frac"] and d["div_yield_frac"] > 0:
        dt = _two_col_table()
        dt.add_row("Dividend Yield", signal_color(fmt_pct(d["div_yield_frac"]), True), "Annual Dividend", f"{s}{d['div_rate']:.2f}" if d["div_rate"] else "N/A")
        dt.add_row("Payout Ratio", signal_color(fmt_pct(d["payout"]), d["payout"] and d["payout"] < 0.6), "Ex-Div Date", datetime.fromtimestamp(d["ex_div"]).strftime("%Y-%m-%d") if d["ex_div"] else "N/A")
        div_title = "[bold]Dividends[/bold]" + ("  [dim](withholding tax may apply for US investors)[/dim]" if d["is_foreign"] else "")
        console.print(Panel(dt, title=div_title, box=box.ROUNDED))

    # ── Technical ─────────────────────────────────────────────────────────────
    tech_t = Table(box=box.SIMPLE, show_header=False, padding=(0, 2))
    for _ in range(6): tech_t.add_column()
    rsi_lbl = signal_color("Oversold" if d["rsi"] < 30 else ("Overbought" if d["rsi"] > 70 else "Neutral"), True if d["rsi"] < 30 else (False if d["rsi"] > 70 else None))
    macd_lbl = signal_color("Bullish" if d["macd"] > d["macd_sig"] else "Bearish", d["macd"] > d["macd_sig"])
    tech_t.add_row("50-Day MA", fmt_price(d["ma50"], s), signal_color("Price Above ▲" if d["above50"] else "Price Below ▼", d["above50"]), "200-Day MA", fmt_price(d["ma200"], s), signal_color("Price Above ▲" if d["above200"] else "Price Below ▼", d["above200"]))
    tech_t.add_row("RSI (14)", f"{d['rsi']:.1f}", rsi_lbl, "MACD", f"{d['macd']:.3f} / {d['macd_sig']:.3f}", macd_lbl)
    tech_t.add_row("MA Cross", signal_color("Golden Cross ▲" if d["golden_cross"] else "Death Cross ▼", d["golden_cross"]), "", "", "", "")
    console.print(Panel(tech_t, title="[bold]Technical Indicators[/bold]", box=box.ROUNDED))

    # ── Analyst ───────────────────────────────────────────────────────────────
    if d["target_mean"]:
        at = _two_col_table()
        at.add_row("Consensus", f"[bold]{d['rec'].replace('_', ' ').title()}[/bold]" if d["rec"] else "N/A", "# Analysts", str(d["num_analysts"]) if d["num_analysts"] else "N/A")
        at.add_row("Mean Target", fmt_price(d["target_mean"], s), "Upside", signal_color(f"{d['analyst_upside']:+.1f}%", d["analyst_upside"] and d["analyst_upside"] > 0))
        at.add_row("Low Target", fmt_price(d["target_low"], s), "High Target", fmt_price(d["target_high"], s))
        console.print(Panel(at, title="[bold]Analyst Ratings[/bold]", box=box.ROUNDED))

    # ── Macro risks ───────────────────────────────────────────────────────────
    macro_t = Table(box=box.SIMPLE, show_header=False, padding=(0, 1))
    macro_t.add_column("", width=2)
    macro_t.add_column("")
    if d["country_risks"]:
        macro_t.add_row("", f"[bold dim]{d['country']} — Country / Geopolitical Risks[/bold dim]")
        for r in d["country_risks"]: macro_t.add_row("[red]·[/red]", r)
        if d["sector_risks"]: macro_t.add_row("", "")
    if d["sector_risks"]:
        lbl = d["sector"] + (f" / {d['industry']}" if d["industry"] and d["industry"] != d["sector"] else "")
        macro_t.add_row("", f"[bold dim]{lbl} — Sector Risks[/bold dim]")
        for r in d["sector_risks"]: macro_t.add_row("[yellow]·[/yellow]", r)
    if d["macro_news"]:
        if d["country_risks"] or d["sector_risks"]: macro_t.add_row("", "")
        macro_t.add_row("", "[bold dim]Recent Headlines[/bold dim]")
        for date, headline in d["macro_news"]: macro_t.add_row(f"[dim]{date}[/dim]", headline)
    if not d["country_risks"] and not d["sector_risks"] and not d["macro_news"]:
        macro_t.add_row("", "[dim]No specific macro risks identified.[/dim]")
    console.print(Panel(macro_t, title="[bold]Macro & Geopolitical Risks[/bold]", box=box.ROUNDED))

    # ── Bull vs Bear ──────────────────────────────────────────────────────────
    bb_t = Table(box=box.SIMPLE, show_header=True, padding=(0, 1))
    bb_t.add_column("[bold green]Bull Case[/bold green]", ratio=1)
    bb_t.add_column("[bold red]Bear Case[/bold red]", ratio=1)
    for i in range(max(len(d["bull_pts"]), len(d["bear_pts"]))):
        b = f"[green]▲[/green] {d['bull_pts'][i]}" if i < len(d["bull_pts"]) else ""
        dr = f"[red]▼[/red] {d['bear_pts'][i]}" if i < len(d["bear_pts"]) else ""
        bb_t.add_row(b, dr)
    console.print(Panel(bb_t, title="[bold]Bull vs Bear[/bold]", box=box.ROUNDED))

    # ── Decision Summary ──────────────────────────────────────────────────────
    st = Table(box=box.SIMPLE, show_header=False, padding=(0, 1))
    st.add_column("", width=3)
    st.add_column("")
    for sig in d["signals"]:
        if sig["bullish"] is True:
            st.add_row("[green]▲[/green]", sig["label"])
        elif sig["bullish"] is False:
            st.add_row("[red]▼[/red]", sig["label"])
        else:
            st.add_row("[yellow]◆[/yellow]", sig["label"])
    st.add_row("", "")
    st.add_row("", f"Score: [bold]{d['score']:+d}[/bold]")
    console.print(Panel(st, title="[bold]Decision Summary[/bold]", box=box.ROUNDED))

    # ── Recommendation ────────────────────────────────────────────────────────
    style_map = {"strong_buy": "bold green", "buy": "green", "accumulate": "yellow", "hold": "yellow", "reduce": "red", "sell": "bold red"}
    rich_style = style_map.get(d["action_style"], "white")
    rec_t = Table(box=box.SIMPLE, show_header=False, padding=(0, 1))
    rec_t.add_column("", width=12, style="dim")
    rec_t.add_column("")
    rec_t.add_row("Action", f"[{rich_style}][bold]{d['action']}[/bold][/{rich_style}]")
    rec_t.add_row("", "")
    rec_t.add_row("If buying", d["buying"])
    rec_t.add_row("", "")
    rec_t.add_row("If holding", d["holding"])
    if d["risk_notes"]:
        rec_t.add_row("", "")
        for note in d["risk_notes"]:
            rec_t.add_row("[yellow]Risk[/yellow]", note)
    rec_t.add_row("", "")
    rec_t.add_row("", "[dim italic]For informational purposes only — not financial advice.[/dim italic]")
    console.print(Panel(rec_t, title="[bold]Recommendation[/bold]", box=box.ROUNDED))
    console.print()


def main():
    parser = argparse.ArgumentParser(description="Stock Analyzer CLI")
    parser.add_argument("ticker", help="Stock ticker symbol (e.g. AAPL, TSM, ASML)")
    args = parser.parse_args()
    symbol = args.ticker.upper()
    try:
        data = fetch_stock_data(symbol)
    except ValueError as e:
        console.print(f"[red]{e}[/red]")
        sys.exit(1)
    display(data)


if __name__ == "__main__":
    main()
