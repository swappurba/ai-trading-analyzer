import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots


def get_key_metrics(info: dict) -> dict:
    def safe(key, default=None):
        val = info.get(key, default)
        return val if val not in [None, "N/A", float("inf"), float("-inf")] else default

    metrics = {
        # Valuation
        "P/E Ratio (TTM)": safe("trailingPE"),
        "P/E Forward": safe("forwardPE"),
        "P/B Ratio": safe("priceToBook"),
        "P/S Ratio": safe("priceToSalesTrailing12Months"),
        "EV/EBITDA": safe("enterpriseToEbitda"),
        "EV/Revenue": safe("enterpriseToRevenue"),

        # Profitability
        "ROE (%)": _pct(safe("returnOnEquity")),
        "ROA (%)": _pct(safe("returnOnAssets")),
        "Profit Margin (%)": _pct(safe("profitMargins")),
        "Operating Margin (%)": _pct(safe("operatingMargins")),
        "Gross Margin (%)": _pct(safe("grossMargins")),
        "EBITDA Margin (%)": _pct(safe("ebitdaMargins")),

        # Growth
        "Revenue Growth (YoY %)": _pct(safe("revenueGrowth")),
        "Earnings Growth (YoY %)": _pct(safe("earningsGrowth")),
        "Quarterly Revenue Growth": _pct(safe("revenueQuarterlyGrowth")),
        "Quarterly Earnings Growth": _pct(safe("earningsQuarterlyGrowth")),

        # Liquidity & Debt
        "Current Ratio": safe("currentRatio"),
        "Quick Ratio": safe("quickRatio"),
        "Debt/Equity": safe("debtToEquity"),
        "Total Debt (B)": _billions(safe("totalDebt")),
        "Total Cash (B)": _billions(safe("totalCash")),
        "Free Cashflow (B)": _billions(safe("freeCashflow")),

        # Per Share
        "EPS (TTM)": safe("trailingEps"),
        "EPS Forward": safe("forwardEps"),
        "Book Value/Share": safe("bookValue"),
        "Revenue/Share": safe("revenuePerShare"),
        "Dividend Yield (%)": _pct(safe("dividendYield")),
        "Payout Ratio (%)": _pct(safe("payoutRatio")),

        # Market
        "Market Cap (B)": _billions(safe("marketCap")),
        "Enterprise Value (B)": _billions(safe("enterpriseValue")),
        "Beta": safe("beta"),
        "52W High": safe("fiftyTwoWeekHigh"),
        "52W Low": safe("fiftyTwoWeekLow"),
        "Avg Volume (M)": _millions(safe("averageVolume")),

        # Analyst
        "Target Price": safe("targetMeanPrice"),
        "Target High": safe("targetHighPrice"),
        "Target Low": safe("targetLowPrice"),
        "Recommendation": safe("recommendationKey", "N/A"),
        "Analyst Count": safe("numberOfAnalystOpinions"),
    }
    return {k: v for k, v in metrics.items() if v is not None}


def _pct(val):
    if val is None:
        return None
    try:
        return round(float(val) * 100, 2)
    except Exception:
        return None


def _billions(val):
    if val is None:
        return None
    try:
        return round(float(val) / 1e9, 3)
    except Exception:
        return None


def _millions(val):
    if val is None:
        return None
    try:
        return round(float(val) / 1e6, 2)
    except Exception:
        return None


def score_fundamental(metrics: dict) -> dict:
    score = 0
    total = 0
    notes = []

    # P/E Ratio
    pe = metrics.get("P/E Ratio (TTM)")
    if pe is not None:
        total += 1
        if pe < 10:
            score += 1; notes.append("P/E sangat murah (<10)")
        elif pe < 20:
            score += 0.5; notes.append(f"P/E moderat ({pe:.1f})")
        elif pe > 40:
            score -= 1; notes.append(f"P/E mahal (>{pe:.1f})")
        else:
            notes.append(f"P/E wajar ({pe:.1f})")

    # P/B Ratio
    pb = metrics.get("P/B Ratio")
    if pb is not None:
        total += 1
        if pb < 1:
            score += 1; notes.append("P/B < 1 (undervalued)")
        elif pb < 3:
            score += 0.5; notes.append(f"P/B wajar ({pb:.2f})")
        else:
            score -= 0.5; notes.append(f"P/B tinggi ({pb:.2f})")

    # ROE
    roe = metrics.get("ROE (%)")
    if roe is not None:
        total += 1
        if roe > 20:
            score += 1; notes.append(f"ROE tinggi ({roe:.1f}%)")
        elif roe > 10:
            score += 0.5; notes.append(f"ROE moderat ({roe:.1f}%)")
        else:
            score -= 0.5; notes.append(f"ROE rendah ({roe:.1f}%)")

    # Profit Margin
    pm = metrics.get("Profit Margin (%)")
    if pm is not None:
        total += 1
        if pm > 20:
            score += 1; notes.append(f"Margin profit tinggi ({pm:.1f}%)")
        elif pm > 10:
            score += 0.5
        elif pm < 0:
            score -= 1; notes.append(f"Rugi (margin {pm:.1f}%)")

    # Debt/Equity
    de = metrics.get("Debt/Equity")
    if de is not None:
        total += 1
        if de < 50:
            score += 1; notes.append(f"Utang rendah (D/E {de:.1f}%)")
        elif de < 150:
            score += 0
        else:
            score -= 1; notes.append(f"Utang tinggi (D/E {de:.1f}%)")

    # Earnings Growth
    eg = metrics.get("Earnings Growth (YoY %)")
    if eg is not None:
        total += 1
        if eg > 20:
            score += 1; notes.append(f"Laba tumbuh pesat ({eg:.1f}%)")
        elif eg > 0:
            score += 0.5; notes.append(f"Laba tumbuh ({eg:.1f}%)")
        else:
            score -= 1; notes.append(f"Laba turun ({eg:.1f}%)")

    # Revenue Growth
    rg = metrics.get("Revenue Growth (YoY %)")
    if rg is not None:
        total += 1
        if rg > 15:
            score += 1; notes.append(f"Pendapatan tumbuh pesat ({rg:.1f}%)")
        elif rg > 0:
            score += 0.5
        else:
            score -= 0.5; notes.append(f"Pendapatan turun ({rg:.1f}%)")

    # Dividend
    div = metrics.get("Dividend Yield (%)")
    if div is not None and div > 0:
        total += 1
        if div > 5:
            score += 1; notes.append(f"Dividen tinggi ({div:.2f}%)")
        elif div > 2:
            score += 0.5; notes.append(f"Dividen moderat ({div:.2f}%)")

    pct = (score / total * 100) if total > 0 else 0

    if pct > 50:
        rating = "FUNDAMENTALLY STRONG"
        color = "green"
    elif pct > 20:
        rating = "FUNDAMENTALLY FAIR"
        color = "orange"
    elif pct > -20:
        rating = "FUNDAMENTALLY NEUTRAL"
        color = "gray"
    else:
        rating = "FUNDAMENTALLY WEAK"
        color = "red"

    return {"score": round(score, 2), "total": total, "pct": round(pct, 1),
            "rating": rating, "color": color, "notes": notes}


def plot_financials(financials: dict, ticker: str) -> go.Figure:
    income = financials.get("income_stmt")
    if income is None or income.empty:
        return go.Figure()

    fig = make_subplots(rows=2, cols=2,
                        subplot_titles=["Pendapatan (Revenue)", "Laba Bersih (Net Income)",
                                        "Gross Profit", "EBITDA"],
                        vertical_spacing=0.15, horizontal_spacing=0.1)

    def safe_row(df, key):
        for k in df.index:
            if key.lower() in str(k).lower():
                row = df.loc[k].dropna()
                if not row.empty:
                    return row.sort_index()
        return None

    colors = ["#2196F3", "#4CAF50", "#FF9800", "#E91E63", "#9C27B0"]

    pairs = [
        (safe_row(income, "Total Revenue"), "Revenue", 1, 1),
        (safe_row(income, "Net Income"), "Net Income", 1, 2),
        (safe_row(income, "Gross Profit"), "Gross Profit", 2, 1),
        (safe_row(income, "EBITDA"), "EBITDA", 2, 2),
    ]

    for data, name, row, col in pairs:
        if data is not None and not data.empty:
            vals = data.values / 1e9
            labels = [str(d)[:4] for d in data.index]
            bar_colors = [colors[2] if v < 0 else colors[0] for v in vals]
            fig.add_trace(go.Bar(x=labels, y=vals, name=name,
                                  marker_color=bar_colors, showlegend=False), row=row, col=col)

    fig.update_layout(height=500, template="plotly_dark",
                      title=f"<b>{ticker}</b> - Laporan Keuangan (dalam Miliar)",
                      paper_bgcolor="#0E1117", plot_bgcolor="#161B22")
    return fig


def plot_financial_ratios(metrics: dict) -> go.Figure:
    ratio_groups = {
        "Valuation": {"P/E Ratio (TTM)": metrics.get("P/E Ratio (TTM)"),
                       "P/B Ratio": metrics.get("P/B Ratio"),
                       "EV/EBITDA": metrics.get("EV/EBITDA")},
        "Profitability (%)": {"ROE (%)": metrics.get("ROE (%)"),
                               "ROA (%)": metrics.get("ROA (%)"),
                               "Profit Margin (%)": metrics.get("Profit Margin (%)")},
        "Growth (%)": {"Revenue Growth (YoY %)": metrics.get("Revenue Growth (YoY %)"),
                        "Earnings Growth (YoY %)": metrics.get("Earnings Growth (YoY %)")},
    }

    fig = make_subplots(rows=1, cols=3, subplot_titles=list(ratio_groups.keys()),
                        horizontal_spacing=0.08)

    for idx, (group_name, ratios) in enumerate(ratio_groups.items(), 1):
        filtered = {k: v for k, v in ratios.items() if v is not None}
        if filtered:
            colors = ["#26A69A" if v >= 0 else "#EF5350" for v in filtered.values()]
            fig.add_trace(go.Bar(
                x=list(filtered.keys()), y=list(filtered.values()),
                name=group_name, marker_color=colors, showlegend=False,
                text=[f"{v:.1f}" for v in filtered.values()],
                textposition="outside",
            ), row=1, col=idx)

    fig.update_layout(height=380, template="plotly_dark",
                      paper_bgcolor="#0E1117", plot_bgcolor="#161B22")
    return fig


def get_analyst_targets(info: dict) -> dict:
    current = info.get("currentPrice") or info.get("regularMarketPrice")
    target_mean = info.get("targetMeanPrice")
    target_high = info.get("targetHighPrice")
    target_low = info.get("targetLowPrice")
    rec = info.get("recommendationKey", "N/A")
    analyst_count = info.get("numberOfAnalystOpinions", 0)

    upside = None
    if current and target_mean:
        upside = ((target_mean - current) / current) * 100

    return {
        "current_price": current,
        "target_mean": target_mean,
        "target_high": target_high,
        "target_low": target_low,
        "recommendation": rec,
        "analyst_count": analyst_count,
        "upside_pct": upside,
    }
