import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import time
from modules.data_fetcher import get_stock_data, get_current_price
from config import GLOBAL_INDICES, COMMODITIES, CURRENCIES, INDONESIAN_INDICES


def get_global_markets_summary() -> list:
    results = []
    all_markets = {**INDONESIAN_INDICES, **GLOBAL_INDICES}
    for name, ticker in all_markets.items():
        data = get_current_price(ticker)
        if data:
            results.append({
                "name": name,
                "ticker": ticker,
                "price": data.get("price"),
                "change": data.get("change"),
                "pct_change": data.get("pct_change"),
            })
        time.sleep(0.05)
    return results


def get_commodities_summary() -> list:
    results = []
    for name, ticker in COMMODITIES.items():
        data = get_current_price(ticker)
        if data:
            results.append({
                "name": name,
                "ticker": ticker,
                "price": data.get("price"),
                "change": data.get("change"),
                "pct_change": data.get("pct_change"),
            })
        time.sleep(0.05)
    return results


def get_currencies_summary() -> list:
    results = []
    for name, ticker in CURRENCIES.items():
        data = get_current_price(ticker)
        if data:
            results.append({
                "name": name,
                "ticker": ticker,
                "price": data.get("price"),
                "change": data.get("change"),
                "pct_change": data.get("pct_change"),
            })
        time.sleep(0.05)
    return results


def get_macro_data_history(period: str = "1y") -> dict:
    data = {}
    key_tickers = {
        "IHSG": "^JKSE",
        "S&P500": "^GSPC",
        "Gold": "GC=F",
        "Oil (WTI)": "CL=F",
        "USD/IDR": "USDIDR=X",
        "US 10Y Bond": "^TNX",
    }
    for name, ticker in key_tickers.items():
        df = get_stock_data(ticker, period=period)
        if not df.empty:
            data[name] = df["Close"]
        time.sleep(0.1)
    return data


def plot_macro_overview(macro_data: dict) -> go.Figure:
    if not macro_data:
        return go.Figure()

    n = len(macro_data)
    cols = 2
    rows = (n + 1) // 2
    titles = list(macro_data.keys())

    fig = make_subplots(rows=rows, cols=cols, subplot_titles=titles,
                        vertical_spacing=0.1, horizontal_spacing=0.08)

    colors = ["#2196F3", "#4CAF50", "#FF9800", "#E91E63", "#9C27B0", "#00BCD4"]

    def hex_to_rgba(hex_color: str, alpha: float = 0.1) -> str:
        h = hex_color.lstrip("#")
        r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
        return f"rgba({r},{g},{b},{alpha})"

    for idx, (name, series) in enumerate(macro_data.items()):
        row = idx // cols + 1
        col = idx % cols + 1
        color = colors[idx % len(colors)]

        pct_change = (series / series.iloc[0] - 1) * 100 if len(series) > 0 else series

        fig.add_trace(go.Scatter(
            x=series.index, y=pct_change,
            name=name, line=dict(color=color, width=1.5),
            fill="tozeroy",
            fillcolor=hex_to_rgba(color, 0.1),
        ), row=row, col=col)

        fig.add_hline(y=0, line_dash="dot", line_color="gray", opacity=0.5, row=row, col=col)

    fig.update_layout(
        height=max(400, rows * 250),
        template="plotly_dark",
        title="<b>Performa Makro Ekonomi (% dari Awal Periode)</b>",
        showlegend=False,
        paper_bgcolor="#0E1117",
        plot_bgcolor="#161B22",
    )
    return fig


def plot_correlation_heatmap(macro_data: dict) -> go.Figure:
    if len(macro_data) < 2:
        return go.Figure()

    df = pd.DataFrame(macro_data).pct_change().dropna()
    corr = df.corr()

    fig = go.Figure(go.Heatmap(
        z=corr.values,
        x=corr.columns.tolist(),
        y=corr.index.tolist(),
        colorscale="RdBu",
        zmid=0,
        text=[[f"{v:.2f}" for v in row] for row in corr.values],
        texttemplate="%{text}",
        colorbar=dict(title="Korelasi"),
    ))

    fig.update_layout(
        title="<b>Korelasi Antar Aset</b>",
        height=450,
        template="plotly_dark",
        paper_bgcolor="#0E1117",
        plot_bgcolor="#161B22",
    )
    return fig


def assess_macro_environment(markets: list, commodities: list, currencies: list) -> dict:
    score = 0
    notes = []
    risk_factors = []
    opportunities = []

    # IHSG performance
    ihsg = next((m for m in markets if "JKSE" in m.get("ticker", "")), None)
    if ihsg and ihsg.get("pct_change") is not None:
        pct = ihsg["pct_change"]
        if pct > 0.5:
            score += 1; opportunities.append(f"IHSG menguat {pct:+.2f}%")
        elif pct < -0.5:
            score -= 1; risk_factors.append(f"IHSG melemah {pct:+.2f}%")

    # S&P500 as global proxy
    sp500 = next((m for m in markets if "GSPC" in m.get("ticker", "")), None)
    if sp500 and sp500.get("pct_change") is not None:
        pct = sp500["pct_change"]
        if pct > 0.5:
            score += 0.5; opportunities.append(f"S&P 500 positif {pct:+.2f}% (sentimen global baik)")
        elif pct < -1:
            score -= 1; risk_factors.append(f"S&P 500 melemah {pct:+.2f}% (risiko global)")

    # Gold as safe haven indicator
    gold = next((c for c in commodities if "Gold" in c.get("name", "")), None)
    if gold and gold.get("pct_change") is not None:
        pct = gold["pct_change"]
        if pct > 0.5:
            risk_factors.append(f"Emas naik {pct:+.2f}% (investor cari aman, risiko geopolitik)")
            score -= 0.3
        elif pct < -0.5:
            opportunities.append(f"Emas turun {pct:+.2f}% (selera risiko meningkat)")
            score += 0.3

    # Oil price
    oil = next((c for c in commodities if "Oil" in c.get("name", "")), None)
    if oil and oil.get("pct_change") is not None:
        pct = oil["pct_change"]
        if pct > 2:
            risk_factors.append(f"Minyak naik tajam {pct:+.2f}% (risiko inflasi)")
            score -= 0.5
        elif pct < -2:
            notes.append(f"Minyak turun {pct:+.2f}% (potensi deflasi/permintaan lemah)")

    # USD/IDR
    usdidr = next((c for c in currencies if "USDIDR" in c.get("ticker", "")), None)
    if usdidr and usdidr.get("pct_change") is not None:
        pct = usdidr["pct_change"]
        if pct > 0.3:
            risk_factors.append(f"Rupiah melemah {pct:+.2f}% vs USD (tekanan impor, potensi kenaikan BI Rate)")
            score -= 0.5
        elif pct < -0.3:
            opportunities.append(f"Rupiah menguat {pct:+.2f}% vs USD")
            score += 0.3

    if score > 1:
        env = "RISK ON 🟢"
        desc = "Kondisi makro mendukung kenaikan pasar saham"
    elif score > 0:
        env = "MILD POSITIVE ⬆️"
        desc = "Kondisi makro cenderung positif"
    elif score < -1:
        env = "RISK OFF 🔴"
        desc = "Kondisi makro menekan pasar, waspadai downside"
    elif score < 0:
        env = "MILD NEGATIVE ⬇️"
        desc = "Kondisi makro cenderung negatif"
    else:
        env = "NEUTRAL ⚪"
        desc = "Kondisi makro netral/mixed"

    return {
        "environment": env,
        "description": desc,
        "score": round(score, 2),
        "opportunities": opportunities,
        "risk_factors": risk_factors,
        "notes": notes,
    }


def get_sector_rotation_view() -> dict:
    return {
        "Risk On (Expansion)": {
            "sectors": ["Teknologi", "Konsumer Diskresioner", "Keuangan", "Industri"],
            "description": "Suku bunga rendah, pertumbuhan ekonomi tinggi",
            "color": "green",
        },
        "Risk Off (Contraction)": {
            "sectors": ["Utilitas", "Kesehatan", "Konsumer Staples", "Emas"],
            "description": "Suku bunga tinggi, pertumbuhan ekonomi melambat",
            "color": "red",
        },
        "Recovery": {
            "sectors": ["Properti", "Keuangan", "Industri"],
            "description": "Suku bunga mulai turun, ekonomi mulai pulih",
            "color": "blue",
        },
        "Peak": {
            "sectors": ["Energi", "Material", "Tambang"],
            "description": "Suku bunga tinggi, komoditi masih kuat",
            "color": "orange",
        },
    }


def get_bi_rate_context() -> dict:
    return {
        "current_rate_assumption": "5.75% (asumsi, verifikasi di bi.go.id)",
        "impact": {
            "Saham Perbankan": "Sensitif terhadap perubahan BI Rate — margin bunga bersih (NIM) terpengaruh",
            "Properti & Konstruksi": "BI Rate tinggi → cicilan KPR mahal → permintaan properti turun",
            "Konsumer": "BI Rate tinggi → daya beli masyarakat tertekan",
            "Pertambangan": "Relatif tidak terpengaruh langsung — tergantung harga komoditi global",
            "Teknologi": "BI Rate tinggi → cost of capital naik → valuasi growth stock tertekan",
        },
        "note": "Update data BI Rate di https://www.bi.go.id",
    }
