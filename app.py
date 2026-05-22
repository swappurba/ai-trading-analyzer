import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import time
import os
from datetime import datetime

# ── Page config (must be first) ──────────────────────────────────────────────
st.set_page_config(
    page_title="AI Trading Analyzer",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── Auto-refresh (opsional, diaktifkan via sidebar) ───────────────────────────
try:
    from streamlit_autorefresh import st_autorefresh
    AUTOREFRESH_AVAILABLE = True
except ImportError:
    AUTOREFRESH_AVAILABLE = False

# ── Imports ───────────────────────────────────────────────────────────────────
from config import (
    POPULAR_IDX_STOCKS, POPULAR_GLOBAL_STOCKS, TIMEFRAMES, INTERVALS,
    SECTOR_MAP, INDONESIAN_INDICES, GLOBAL_INDICES, COMMODITIES, CURRENCIES,
    fetch_all_idx_stocks,
)
from modules.data_fetcher import (
    get_stock_data, get_stock_info, get_financials,
    get_current_price, get_economic_calendar,
)
from modules.technical_analysis import (
    calculate_indicators, get_signals, get_support_resistance,
    plot_candlestick_chart, plot_rsi_stochastic,
)
from modules.fundamental_analysis import (
    get_key_metrics, score_fundamental, plot_financials,
    plot_financial_ratios, get_analyst_targets,
)
from modules.news_analysis import (
    get_stock_news, get_macro_news, aggregate_sentiment,
    summarize_news_sentiment,
)
from modules.macro_analysis import (
    get_global_markets_summary, get_commodities_summary,
    get_currencies_summary, get_macro_data_history,
    plot_macro_overview, plot_correlation_heatmap,
    assess_macro_environment, get_sector_rotation_view,
    get_bi_rate_context,
)
from modules.ai_analysis import get_ai_analysis
from modules.smc_analysis import (
    find_order_blocks, find_fvg, find_bos_choch,
    find_liquidity_zones, get_premium_discount,
    get_smc_bias, plot_smc_chart,
)
from modules.advanced_ta import (
    auto_fibonacci, plot_fibonacci,
    find_divergences, calculate_volume_profile, plot_volume_profile,
    detect_candlestick_patterns, detect_wyckoff_phase, multi_timeframe_bias,
)
from modules.risk_management import (
    calculate_returns, calculate_var, calculate_performance_ratios,
    monte_carlo_simulation, plot_monte_carlo, kelly_criterion,
    calculate_risk_reward, plot_performance_dashboard,
)
from modules.live_price import (
    get_live_price, get_intraday_data, start_websocket,
    finnhub_quote, finnhub_news, finnhub_sentiment,
    finnhub_earnings, finnhub_recommendation,
    is_market_open, format_price, format_timestamp,
    live_screener, WS_AVAILABLE,
    batch_live_prices, get_sparkline_data, yahoo_v8_realtime,
)
from config import FINNHUB_API_KEY

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    .main { background-color: #0E1117; }
    .stMetric { background-color: #161B22; border-radius: 8px; padding: 12px; border: 1px solid #30363D; }
    .metric-card { background: #161B22; border-radius: 10px; padding: 16px; border: 1px solid #30363D; margin: 4px 0; }
    .signal-buy { background: rgba(38, 166, 154, 0.15); border: 1px solid #26A69A; border-radius: 6px; padding: 8px; margin: 3px 0; }
    .signal-sell { background: rgba(239, 83, 80, 0.15); border: 1px solid #EF5350; border-radius: 6px; padding: 8px; margin: 3px 0; }
    .signal-neutral { background: rgba(100, 100, 100, 0.15); border: 1px solid #555; border-radius: 6px; padding: 8px; margin: 3px 0; }
    .news-card { background: #161B22; border-radius: 8px; padding: 12px; border-left: 3px solid #2196F3; margin: 6px 0; }
    .news-bull { border-left-color: #26A69A !important; }
    .news-bear { border-left-color: #EF5350 !important; }
    .section-header { font-size: 1.3rem; font-weight: 700; color: #E8EAED; margin: 16px 0 8px 0; border-bottom: 2px solid #30363D; padding-bottom: 6px; }
    div[data-testid="stMetricValue"] { font-size: 1.4rem !important; font-weight: 700; }
    .stTabs [data-baseweb="tab"] { font-size: 0.95rem; font-weight: 600; }
    .recommendation-box { border-radius: 12px; padding: 20px; margin: 10px 0; text-align: center; font-size: 1.5rem; font-weight: 800; }
    .live-badge { display:inline-block; background:#EF5350; color:white; font-size:0.7rem; font-weight:700; padding:2px 7px; border-radius:12px; animation: pulse 1.5s infinite; margin-left:6px; vertical-align:middle; }
    .delayed-badge { display:inline-block; background:#FF9800; color:white; font-size:0.7rem; font-weight:700; padding:2px 7px; border-radius:12px; margin-left:6px; vertical-align:middle; }
    @keyframes pulse { 0%,100%{opacity:1} 50%{opacity:0.4} }
    .ticker-bar { background:#161B22; border:1px solid #30363D; border-radius:8px; padding:10px 16px; margin-bottom:10px; display:flex; align-items:center; gap:24px; flex-wrap:wrap; }
    .price-up { color:#26A69A; font-weight:700; }
    .price-down { color:#EF5350; font-weight:700; }
    /* ── Hide sidebar completely ── */
    [data-testid="stSidebar"] { display: none !important; }
    [data-testid="collapsedControl"] { display: none !important; }
    .main .block-container { padding-top: 0.5rem !important; max-width: 100% !important; }
    header[data-testid="stHeader"] { display: none !important; }
    .intraday-label { background:#1F2937; border-radius:6px; padding:4px 10px; font-size:0.8rem; color:#8B949E; }
    .idx-card { background:#161B22; border:1px solid #30363D; border-radius:10px; padding:14px 16px; cursor:pointer; transition:border-color 0.2s; margin-bottom:6px; }
    .idx-card:hover { border-color:#58A6FF; }
    .idx-card-active { border-color:#26A69A !important; background:rgba(38,166,154,0.08) !important; }
    .idx-price-up { color:#26A69A; font-weight:700; font-size:1.15rem; }
    .idx-price-down { color:#EF5350; font-weight:700; font-size:1.15rem; }
    .idx-ticker-label { font-size:0.78rem; color:#8B949E; font-weight:600; letter-spacing:0.5px; }
    .idx-company { font-size:0.82rem; color:#C9D1D9; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; max-width:120px; }
    .idx-sector-badge { display:inline-block; background:#21262D; color:#8B949E; border-radius:4px; padding:1px 6px; font-size:0.7rem; }
    .idx-change-up { color:#26A69A; font-size:0.85rem; }
    .idx-change-down { color:#EF5350; font-size:0.85rem; }
    .summary-bar { background:#161B22; border:1px solid #30363D; border-radius:8px; padding:12px 20px; margin-bottom:12px; display:flex; align-items:center; gap:20px; flex-wrap:wrap; }
</style>
""", unsafe_allow_html=True)


# ── Session state (init sebelum sidebar) ─────────────────────────────────────
DEFAULT_TICKER = "^JKSE"

if "ticker" not in st.session_state:
    st.session_state.ticker = ""
if "df" not in st.session_state:
    st.session_state.df = pd.DataFrame()
if "info" not in st.session_state:
    st.session_state.info = {}
if "ai_result" not in st.session_state:
    st.session_state.ai_result = ""
if "news" not in st.session_state:
    st.session_state.news = []
if "macro_env" not in st.session_state:
    st.session_state.macro_env = {}
if "live_mode" not in st.session_state:
    st.session_state.live_mode = False
if "idx_prices_cache" not in st.session_state:
    st.session_state.idx_prices_cache = {}
if "idx_prices_ts" not in st.session_state:
    st.session_state.idx_prices_ts = 0
if "idx_active_ticker" not in st.session_state:
    st.session_state.idx_active_ticker = ""
if "idx_open_popup" not in st.session_state:
    st.session_state.idx_open_popup = False
if "last_analyzed" not in st.session_state:
    st.session_state.last_analyzed = ""
if "last_timeframe" not in st.session_state:
    st.session_state.last_timeframe = ""
if "last_interval" not in st.session_state:
    st.session_state.last_interval = ""


def _run_analysis(ticker: str, period: str, iv: str):
    """Jalankan seluruh pipeline analisis dan simpan ke session_state."""
    with st.spinner(f"📡 Mengambil data {ticker}..."):
        df_raw = get_stock_data(ticker, period=period, interval=iv)
        info   = get_stock_info(ticker)
        fin    = get_financials(ticker)
        pd_    = get_current_price(ticker)

    if df_raw.empty:
        st.error(f"❌ Tidak dapat mengambil data untuk **{ticker}**. Periksa kode saham.")
        return False

    with st.spinner("📊 Menghitung indikator teknikal..."):
        df      = calculate_indicators(df_raw)
        signals = get_signals(df)
        sr      = get_support_resistance(df)

    with st.spinner("🏦 Menganalisis Smart Money Concepts..."):
        obs        = find_order_blocks(df)
        fvgs       = find_fvg(df)
        bos_events = find_bos_choch(df)
        liq        = find_liquidity_zones(df)
        pd_zone    = get_premium_discount(df)
        smc_bias   = get_smc_bias(obs, fvgs, bos_events, pd_zone, liq)

    with st.spinner("📐 Advanced TA: Fibonacci, Wyckoff, MTF..."):
        fib         = auto_fibonacci(df)
        wyckoff     = detect_wyckoff_phase(df)
        mtf         = multi_timeframe_bias(df)
        divergences = find_divergences(df)
        candle_pat  = detect_candlestick_patterns(df)
        vp          = calculate_volume_profile(df)

    with st.spinner("📉 Menghitung risk metrics..."):
        returns  = calculate_returns(df)
        ratios   = calculate_performance_ratios(returns)
        var_data = calculate_var(returns)
        mc_data  = monte_carlo_simulation(df, days=30, simulations=500)
        kelly    = kelly_criterion(returns)

    with st.spinner("📰 Mengambil berita & sentimen..."):
        cname = info.get("longName") or info.get("shortName") or ticker
        news  = get_stock_news(ticker, cname)

    with st.spinner("🌍 Memuat data makro..."):
        markets     = get_global_markets_summary()
        commodities = get_commodities_summary()
        currencies  = get_currencies_summary()
        macro_env   = assess_macro_environment(markets, commodities, currencies)

    st.session_state.ticker       = ticker
    st.session_state.df           = df
    st.session_state.info         = info
    st.session_state.financials   = fin
    st.session_state.price_data   = pd_
    st.session_state.signals      = signals
    st.session_state.sr           = sr
    st.session_state.obs          = obs
    st.session_state.fvgs         = fvgs
    st.session_state.bos_events   = bos_events
    st.session_state.liq          = liq
    st.session_state.pd_zone      = pd_zone
    st.session_state.smc_bias     = smc_bias
    st.session_state.fib          = fib
    st.session_state.wyckoff      = wyckoff
    st.session_state.mtf          = mtf
    st.session_state.divergences  = divergences
    st.session_state.candle_pat   = candle_pat
    st.session_state.vp           = vp
    st.session_state.ratios       = ratios
    st.session_state.var_data     = var_data
    st.session_state.mc_data      = mc_data
    st.session_state.kelly        = kelly
    st.session_state.news         = news
    st.session_state.markets      = markets
    st.session_state.commodities  = commodities
    st.session_state.currencies   = currencies
    st.session_state.macro_env    = macro_env
    st.session_state.company_name = cname
    st.session_state.ai_result    = ""
    st.session_state.last_analyzed   = ticker
    st.session_state.last_timeframe  = period
    st.session_state.last_interval   = iv
    return True


# ── Sidebar hidden — variabel default (sidebar di-hide via CSS) ───────────────
# Kontrol utama ada di top bar IDX Dashboard
stock_input   = st.session_state.get("last_analyzed", DEFAULT_TICKER) or DEFAULT_TICKER
timeframe     = "1 Tahun"
interval      = "Harian"
show_ichimoku = False
live_mode     = True
show_intraday = False
intraday_interval = "5m"
ai_btn        = False




# ── Helper functions ──────────────────────────────────────────────────────────
def color_metric(val, positive_is_good=True):
    if val is None:
        return "normal"
    try:
        v = float(val)
        if positive_is_good:
            return "normal" if v >= 0 else "inverse"
        else:
            return "inverse" if v >= 0 else "normal"
    except Exception:
        return "normal"


def fmt_num(val, decimals=2, suffix=""):
    if val is None:
        return "N/A"
    try:
        return f"{float(val):.{decimals}f}{suffix}"
    except Exception:
        return str(val)


def render_signal_badge(signal: str, note: str):
    if "BUY" in signal:
        css = "signal-buy"
        icon = "🟢"
    elif "SELL" in signal:
        css = "signal-sell"
        icon = "🔴"
    else:
        css = "signal-neutral"
        icon = "⚪"
    st.markdown(f'<div class="{css}">{icon} <b>{signal}</b> — {note}</div>', unsafe_allow_html=True)


def render_news_card(article: dict):
    sent = article.get("sentiment", {})
    label = sent.get("label", "Neutral")
    emoji = sent.get("emoji", "⚪")
    title = article.get("title_clean") or article.get("title", "")[:120]
    desc = article.get("desc_clean") or article.get("description", "")[:200]
    source = article.get("source", {}).get("name", "")
    date = article.get("date_display", "")
    url = article.get("url", "#")

    css_extra = "news-bull" if label == "Bullish" else ("news-bear" if label == "Bearish" else "")
    desc_html = f"<p style='color:#8B949E;font-size:0.85rem;margin:4px 0'>{desc}</p>" if desc else ""
    link_html = f'<a href="{url}" target="_blank" style="color:#58A6FF;font-size:0.8rem">Baca selengkapnya →</a>' if url and url != "#" else ""

    st.markdown(f"""
<div class="news-card {css_extra}">
    <b>{emoji} {title}</b>
    {desc_html}
    <span style='color:#555;font-size:0.78rem'>{source} · {date}</span>
    {link_html}
</div>""", unsafe_allow_html=True)


# ── Auto-trigger analisis default (IHSG on first load) ────────────────────────
_period = st.session_state.get("_top_period",  "1y")
_iv     = st.session_state.get("_top_interval", "1d")
_needs_analysis = (
    not st.session_state.last_analyzed
)
if _needs_analysis:
    ok = _run_analysis(DEFAULT_TICKER, _period, _iv)
    if ok:
        st.rerun()
    else:
        st.stop()


if ai_btn and st.session_state.ticker:
    with st.spinner("🤖 Claude Opus 4.7 sedang menganalisis secara mendalam..."):
        _info    = st.session_state.info
        _metrics = get_key_metrics(_info)
        _fscore  = score_fundamental(_metrics)
        _mtf_copy = dict(st.session_state.get("mtf", {}))
        result = get_ai_analysis(
            ticker=st.session_state.ticker,
            company_name=st.session_state.get("company_name", st.session_state.ticker),
            current_price=st.session_state.get("price_data", {}),
            tech_signals=st.session_state.get("signals", {}),
            fund_metrics=_metrics,
            fund_score=_fscore,
            news_articles=st.session_state.get("news", []),
            macro_env=st.session_state.get("macro_env", {}),
            sr_levels=st.session_state.get("sr", {}),
            smc_bias=st.session_state.get("smc_bias"),
            wyckoff=st.session_state.get("wyckoff"),
            fib=st.session_state.get("fib"),
            mtf=_mtf_copy,
            ratios=st.session_state.get("ratios"),
            var_data=st.session_state.get("var_data"),
            mc_data=st.session_state.get("mc_data"),
            kelly=st.session_state.get("kelly"),
            candle_patterns=st.session_state.get("candle_pat"),
            divergences=st.session_state.get("divergences"),
            vp=st.session_state.get("vp"),
        )
    st.session_state.ai_result = result
    st.rerun()


# ── Active ticker dashboard ───────────────────────────────────────────────────
ticker = st.session_state.ticker
df = st.session_state.df
info = st.session_state.info
price_data = st.session_state.get("price_data", {})
signals = st.session_state.get("signals", {})
sr = st.session_state.get("sr", {})
news = st.session_state.get("news", [])
markets = st.session_state.get("markets", [])
commodities = st.session_state.get("commodities", [])
currencies = st.session_state.get("currencies", [])
macro_env = st.session_state.get("macro_env", {})
company_name = st.session_state.get("company_name", ticker)
financials = st.session_state.get("financials", {})
metrics = get_key_metrics(info)
fund_score = score_fundamental(metrics)
tech_overall = signals.get("_overall", {})

# ── Header ─────────────────────────────────────────────────────────────────────
price = price_data.get("price")
change = price_data.get("change")
pct_change = price_data.get("pct_change")
volume = price_data.get("volume")

# For IDX Composite, fetch fresh live price for display
_is_ihsg = ticker in ("^JKSE", "^JKLQ45")
if _is_ihsg:
    try:
        from modules.live_price import yahoo_v8_realtime
        _ihsg_live = yahoo_v8_realtime(ticker)
        if _ihsg_live and _ihsg_live.get("price"):
            price      = _ihsg_live["price"]
            change     = _ihsg_live.get("change", 0)
            pct_change = _ihsg_live.get("pct_change", 0)
            volume     = _ihsg_live.get("volume") or volume
    except Exception:
        pass

col_title, col_rec = st.columns([3, 1])
with col_title:
    if _is_ihsg:
        _ihsg_name = "IDX Composite (IHSG)" if ticker == "^JKSE" else "LQ45 Index"
        _ihsg_arrow = "▲" if (change or 0) >= 0 else "▼"
        _ihsg_color = "#26A69A" if (change or 0) >= 0 else "#EF5350"
        _ihsg_price_fmt = f"{price:,.2f}" if price else "—"
        _ihsg_chg_fmt   = f"{_ihsg_arrow} {abs(change or 0):,.2f} ({abs(pct_change or 0):.2f}%)"
        st.markdown(f"## {_ihsg_name} `{ticker}`")
        st.markdown(
            f'<span style="font-size:1.8rem;font-weight:800;color:#E6EDF3">{_ihsg_price_fmt}</span>'
            f'&nbsp;&nbsp;<span style="font-size:1.1rem;color:{_ihsg_color};font-weight:600">{_ihsg_chg_fmt}</span>',
            unsafe_allow_html=True,
        )
        st.markdown("*Indeks Harga Saham Gabungan · Bursa Efek Indonesia*")
    else:
        sector = info.get("sector", "")
        industry = info.get("industry", "")
        exchange = info.get("exchange", "")
        country = info.get("country", "")
        st.markdown(f"## {company_name} `{ticker}`")
        st.markdown(f"*{sector} · {industry} · {exchange} · {country}*")

with col_rec:
    if _is_ihsg:
        _mkt_color = "#26A69A" if (change or 0) >= 0 else "#EF5350"
        _mkt_bg    = "rgba(38,166,154,0.2)" if (change or 0) >= 0 else "rgba(239,83,80,0.2)"
        _mkt_label = "MARKET UP" if (change or 0) >= 0 else "MARKET DOWN"
        st.markdown(f"""<div style="background:{_mkt_bg};border:2px solid {_mkt_color};border-radius:10px;
            padding:12px;text-align:center;margin-top:10px">
            <div style="color:{_mkt_color};font-size:1.3rem;font-weight:800">{_mkt_label}</div>
            <div style="color:#8B949E;font-size:0.8rem">Kondisi Pasar IDX</div>
        </div>""", unsafe_allow_html=True)
    else:
        rec = tech_overall.get("recommendation", "N/A")
        if "STRONG BUY" in rec:
            rec_color, rec_bg = "#26A69A", "rgba(38,166,154,0.2)"
        elif "BUY" in rec:
            rec_color, rec_bg = "#4CAF50", "rgba(76,175,80,0.2)"
        elif "STRONG SELL" in rec:
            rec_color, rec_bg = "#EF5350", "rgba(239,83,80,0.2)"
        elif "SELL" in rec:
            rec_color, rec_bg = "#F44336", "rgba(244,67,54,0.2)"
        else:
            rec_color, rec_bg = "#FF9800", "rgba(255,152,0,0.2)"
        st.markdown(f"""<div style="background:{rec_bg};border:2px solid {rec_color};border-radius:10px;
            padding:12px;text-align:center;margin-top:10px">
            <div style="color:{rec_color};font-size:1.3rem;font-weight:800">{rec}</div>
            <div style="color:#8B949E;font-size:0.8rem">Sinyal Teknikal</div>
        </div>""", unsafe_allow_html=True)

st.markdown("---")

# ── Live Price Bar ─────────────────────────────────────────────────────────────
if live_mode:
    live_data = get_live_price(ticker)
    if live_data and live_data.get("price"):
        price      = live_data["price"]
        change     = live_data.get("change", 0)
        pct_change = live_data.get("pct_change", 0)
        volume     = live_data.get("volume") or volume
        source     = live_data.get("source", "")
        ts_str     = format_timestamp(live_data.get("timestamp"))

        source_badge = (
            '<span class="live-badge">● LIVE</span>'
            if "WS" in source or "Finnhub" in source
            else '<span class="delayed-badge">⏱ ~15min</span>'
        )
        price_class = "price-up" if (change or 0) >= 0 else "price-down"
        arrow = "▲" if (change or 0) >= 0 else "▼"

        market_open = is_market_open(ticker)
        market_label = "🟢 Pasar Buka" if market_open else "🔴 Pasar Tutup"

        st.markdown(f"""
        <div class="ticker-bar">
            <span style="font-size:1.3rem;font-weight:800">{ticker}</span>
            {source_badge}
            <span class="{price_class}" style="font-size:1.6rem">{format_price(price)}</span>
            <span class="{price_class}">{arrow} {abs(change or 0):.2f} ({abs(pct_change or 0):.2f}%)</span>
            <span class="intraday-label">High: {format_price(live_data.get('high'))}</span>
            <span class="intraday-label">Low: {format_price(live_data.get('low'))}</span>
            <span class="intraday-label">Open: {format_price(live_data.get('open'))}</span>
            <span style="color:#555;font-size:0.78rem;margin-left:auto">{market_label} · {source} · {ts_str}</span>
        </div>""", unsafe_allow_html=True)
    else:
        st.warning("⚠️ Gagal memuat harga live. Coba refresh atau periksa koneksi.")

# ── Price Metrics Row ──────────────────────────────────────────────────────────
c1, c2, c3, c4, c5, c6 = st.columns(6)
with c1:
    st.metric("💵 Harga", fmt_num(price), f"{pct_change:+.2f}%" if pct_change else None)
with c2:
    st.metric("📈 High Hari Ini", fmt_num(price_data.get("high")))
with c3:
    st.metric("📉 Low Hari Ini", fmt_num(price_data.get("low")))
with c4:
    vol = volume
    vol_str = f"{vol/1e9:.2f}B" if vol and vol > 1e9 else (f"{vol/1e6:.2f}M" if vol and vol > 1e6 else fmt_num(vol, 0))
    st.metric("📊 Volume", vol_str)
with c5:
    st.metric("📅 52W High", fmt_num(sr.get("52w_high")))
with c6:
    st.metric("📅 52W Low", fmt_num(sr.get("52w_low")))

# ── Load state ────────────────────────────────────────────────────────────────
obs        = st.session_state.get("obs", [])
fvgs       = st.session_state.get("fvgs", [])
bos_events = st.session_state.get("bos_events", [])
liq        = st.session_state.get("liq", {})
pd_zone    = st.session_state.get("pd_zone", {})
smc_bias   = st.session_state.get("smc_bias", {})
fib        = st.session_state.get("fib", {})
wyckoff    = st.session_state.get("wyckoff", {})
mtf        = st.session_state.get("mtf", {})
divergences = st.session_state.get("divergences", [])
candle_pat  = st.session_state.get("candle_pat", [])
vp          = st.session_state.get("vp", {})
ratios      = st.session_state.get("ratios", {})
var_data    = st.session_state.get("var_data", {})
mc_data     = st.session_state.get("mc_data", {})
kelly       = st.session_state.get("kelly", {})

# ── Main Tabs ─────────────────────────────────────────────────────────────────
tabs = st.tabs([
    "🇮🇩 IDX Dashboard",
    "🗺️ Pasar Global",
])

# ════════════════════════════════════════════════════════════════════════════════
# TAB 0: IDX DASHBOARD — Papan harga besar + analisis inline
# ════════════════════════════════════════════════════════════════════════════════
with tabs[0]:

    # ── Handle ticker selection & analysis trigger (sebelum render) ──
    if "_idx_pending_ticker" in st.session_state:
        _pending   = st.session_state.pop("_idx_pending_ticker")
        _p_forced  = st.session_state.get("_top_period",  "1y")
        _iv_forced = st.session_state.get("_top_interval", "1d")
        with st.spinner(f"🔍 Menganalisis {_pending} — mohon tunggu..."):
            _run_analysis(_pending, _p_forced, _iv_forced)
        st.rerun()

    # ── Auto-refresh live harga setiap 60 detik ──
    if AUTOREFRESH_AVAILABLE:
        st_autorefresh(interval=60_000, key="idx_live_refresh")

    # ── Fetch & cache harga IDX ──
    _now_ts = time.time()
    _cache_stale = (_now_ts - st.session_state.idx_prices_ts) > 55
    _ticker_sector: dict = {}
    for _sec, _tks in SECTOR_MAP.items():
        for _tk in _tks:
            _ticker_sector[_tk] = _sec

    # ── Top control bar (pengganti sidebar) ──
    _ts_lbl = datetime.fromtimestamp(st.session_state.idx_prices_ts).strftime("%H:%M:%S") if st.session_state.idx_prices_ts else "—"
    _hc1, _hc2, _hc3, _hc4, _hc5, _hc6 = st.columns([3, 1.5, 1, 1, 1, 1])
    with _hc1:
        st.markdown(f"""
        <div style="display:flex;align-items:center;gap:10px">
          <span style="font-size:1.4rem;font-weight:800">🇮🇩 IDX Market Board</span>
          <span style="background:#26A69A;color:#000;font-size:0.65rem;font-weight:800;padding:2px 7px;border-radius:10px;animation:pulse 1.5s infinite">● LIVE</span>
        </div>
        <div style="color:#555;font-size:0.75rem">Yahoo Finance v8 · Update {_ts_lbl} · Auto-refresh 60s</div>
        """, unsafe_allow_html=True)
    with _hc2:
        _filter_sector = st.selectbox("", ["Semua"] + list(SECTOR_MAP.keys()), key="idx_sector_filter", label_visibility="collapsed")
    with _hc3:
        _period_sel = st.selectbox("", list(TIMEFRAMES.keys()), index=3, key="top_period", label_visibility="collapsed")
    with _hc4:
        _interval_sel = st.selectbox("", list(INTERVALS.keys()), index=0, key="top_interval", label_visibility="collapsed")
    with _hc5:
        _refresh_dash = st.button("🔄 Refresh", key="idx_refresh", use_container_width=True)
    with _hc6:
        # Search box
        _search_input = st.text_input("", placeholder="Cari: BBCA", key="idx_search", label_visibility="collapsed").upper().strip()

    # Update global period/interval dari top bar
    _period  = TIMEFRAMES[_period_sel]
    _iv      = INTERVALS[_interval_sel]
    st.session_state["_top_period"]   = _period
    st.session_state["_top_interval"] = _iv

    # Ambil daftar saham lengkap dari API IDX (cache di session)
    if "idx_full_list" not in st.session_state or not st.session_state.idx_full_list:
        with st.spinner("📋 Memuat daftar lengkap saham IDX..."):
            st.session_state.idx_full_list = fetch_all_idx_stocks()
    _idx_stock_list = st.session_state.idx_full_list or POPULAR_IDX_STOCKS

    if _refresh_dash or _cache_stale or not st.session_state.idx_prices_cache:
        with st.spinner(f"⏳ Mengambil harga {len(_idx_stock_list):,} saham IDX..."):
            _all_prices = batch_live_prices(_idx_stock_list, max_workers=20)
        st.session_state.idx_prices_cache = _all_prices
        st.session_state.idx_prices_ts = time.time()
    else:
        _all_prices = st.session_state.idx_prices_cache

    # Build stock list
    _all_stocks = []
    for _tk in _idx_stock_list:
        _pd2 = _all_prices.get(_tk, {})
        _all_stocks.append({
            "ticker": _tk, "code": _tk.replace(".JK",""),
            "sector": _ticker_sector.get(_tk, "Lainnya"),
            "price": _pd2.get("price"), "change": _pd2.get("change",0) or 0,
            "pct": _pd2.get("pct_change",0) or 0, "volume": _pd2.get("volume",0) or 0,
            "high": _pd2.get("high"), "low": _pd2.get("low"),
        })
    _display_list = [s for s in _all_stocks
                     if (_filter_sector=="Semua" or s["sector"]==_filter_sector)
                     and (_search_input=="" or _search_input in s["code"])]
    _loaded_all   = [s for s in _display_list if s["price"] is not None]

    # ── Market stats bar ──
    _n_up   = sum(1 for s in _loaded_all if s["pct"]>0)
    _n_down = sum(1 for s in _loaded_all if s["pct"]<0)
    _n_flat = len(_loaded_all)-_n_up-_n_down
    _avg_pct = (sum(s["pct"] for s in _loaded_all)/len(_loaded_all)) if _loaded_all else 0
    _avg_c  = "#26A69A" if _avg_pct>=0 else "#EF5350"

    # Ticker tape (scrolling marquee)
    _tape_items = ""
    for _s in sorted(_loaded_all, key=lambda x: x["code"]):
        _tc = "#26A69A" if _s["pct"]>=0 else "#EF5350"
        _ta = "▲" if _s["pct"]>=0 else "▼"
        _tape_items += f'<span style="margin:0 18px;white-space:nowrap"><b style="color:#E8EAED">{_s["code"]}</b> <span style="color:{_tc}">{_s["price"]:,.0f} {_ta}{abs(_s["pct"]):.2f}%</span></span>'

    st.markdown(f"""
    <style>
    @keyframes ticker-scroll {{
        0%   {{ transform: translateX(0); }}
        100% {{ transform: translateX(-50%); }}
    }}
    .ticker-wrap {{ overflow:hidden; background:#0D1117; border:1px solid #21262D; border-radius:8px; padding:8px 0; margin:10px 0 14px 0; }}
    .ticker-inner {{ display:inline-flex; animation: ticker-scroll 40s linear infinite; white-space:nowrap; font-size:0.88rem; }}
    .ticker-inner:hover {{ animation-play-state: paused; cursor:default; }}
    </style>
    <div class="ticker-wrap">
      <div class="ticker-inner">{_tape_items}{_tape_items}</div>
    </div>
    <div style="display:flex;gap:10px;flex-wrap:wrap;margin-bottom:12px;align-items:center">
      <span style="background:#0d1f0d;color:#26A69A;border:1px solid #26A69A;border-radius:16px;padding:3px 12px;font-size:0.82rem;font-weight:700">🟢 Naik {_n_up}</span>
      <span style="background:#1f0d0d;color:#EF5350;border:1px solid #EF5350;border-radius:16px;padding:3px 12px;font-size:0.82rem;font-weight:700">🔴 Turun {_n_down}</span>
      <span style="background:#21262D;color:#8B949E;border:1px solid #30363D;border-radius:16px;padding:3px 12px;font-size:0.82rem">⚪ Flat {_n_flat}</span>
      <span style="background:#21262D;color:{_avg_c};border:1px solid #30363D;border-radius:16px;padding:3px 12px;font-size:0.82rem;font-weight:700">Avg {_avg_pct:+.2f}%</span>
    </div>
    """, unsafe_allow_html=True)

    # ════════════ PAPAN HARGA BESAR — 7 kolom per baris via st.columns ════════════
    _BOARD_COLS = 7
    _active_tk  = st.session_state.get("idx_active_ticker", "")

    # Wrapper hitam
    st.markdown("""
    <div style="background:#0D1117;border:1px solid #21262D;border-radius:12px;
                padding:12px 10px 6px 10px;margin-bottom:8px">
    """, unsafe_allow_html=True)

    for _row_s in range(0, len(_display_list), _BOARD_COLS):
        _row = _display_list[_row_s : _row_s + _BOARD_COLS]
        _gcols = st.columns(_BOARD_COLS)
        for _ci, _s in enumerate(_row):
            with _gcols[_ci]:
                _p    = _s["price"]
                _pct  = _s["pct"]
                _is_active = (_s["ticker"] == _active_tk)
                _border = "#26A69A" if _is_active else "#30363D"
                _bg     = "rgba(38,166,154,0.10)" if _is_active else "#161B22"
                _prefix = "✓ " if _is_active else ""

                if _p is not None:
                    _pc = "#26A69A" if _pct >= 0 else "#EF5350"
                    _ar = "▲" if _pct >= 0 else "▼"
                    _vol = (f"{_s['volume']/1e6:.1f}M" if _s['volume'] >= 1e6
                            else f"{_s['volume']/1e3:.0f}K" if _s['volume'] >= 1e3 else "")
                    st.markdown(f"""
                    <div style="background:{_bg};border:1.5px solid {_border};border-radius:8px;
                                padding:8px 4px;text-align:center;margin-bottom:4px">
                        <div style="font-size:0.68rem;font-weight:800;color:#8B949E;
                                    letter-spacing:0.6px">{_prefix}{_s['code']}</div>
                        <div style="font-size:0.85rem;font-weight:800;color:{_pc};
                                    margin:3px 0;line-height:1.1">Rp {_p:,.0f}</div>
                        <div style="font-size:0.7rem;color:{_pc}">{_ar}{abs(_pct):.2f}%</div>
                        <div style="font-size:0.62rem;color:#444">{_vol}</div>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown(f"""
                    <div style="background:#161B22;border:1px solid #21262D;border-radius:8px;
                                padding:8px 4px;text-align:center;margin-bottom:4px">
                        <div style="font-size:0.68rem;font-weight:800;color:#555">{_s['code']}</div>
                        <div style="font-size:0.78rem;color:#333">—</div>
                    </div>
                    """, unsafe_allow_html=True)

                # Tombol klik — langsung trigger analisis otomatis
                _is_sel   = (_active_tk == _s["ticker"])
                _btn_type = "primary" if _is_sel else "secondary"
                _pct_txt  = f" {_pct:+.1f}%" if _p else ""
                if st.button(f"{_s['code']}{_pct_txt}", key=f"bd_{_s['ticker']}",
                             use_container_width=True, type=_btn_type):
                    st.session_state["idx_active_ticker"] = _s["ticker"]
                    st.session_state["_idx_pending_ticker"] = _s["ticker"]
                    st.session_state["idx_open_popup"] = True
                    st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)

    # Determine active ticker for analysis
    _active_ticker = st.session_state.get("idx_active_ticker", "")
    if not _active_ticker and st.session_state.last_analyzed in [s["ticker"] for s in _display_list]:
        _active_ticker = st.session_state.last_analyzed

    # ════════════ POPUP DIALOG ANALISIS ════════════
    @st.dialog("📊 Analisis Saham", width="large")
    def _show_analysis_popup(active_ticker, all_prices, display_list):
        _act_stock      = next((s for s in display_list if s["ticker"]==active_ticker), None)
        _act_price_data = all_prices.get(active_ticker, {})
        _act_price = _act_price_data.get("price")
        _act_pct   = _act_price_data.get("pct_change", 0) or 0
        _act_chg   = _act_price_data.get("change", 0) or 0
        _act_high  = _act_price_data.get("high")
        _act_low   = _act_price_data.get("low")
        _act_vol   = _act_price_data.get("volume", 0) or 0
        _act_code  = active_ticker.replace(".JK","")
        _act_color = "#26A69A" if _act_pct>=0 else "#EF5350"
        _act_arrow = "▲" if _act_pct>=0 else "▼"

        # Header harga di popup
        _ah1, _ah2, _ah3 = st.columns([3, 1, 1])
        with _ah1:
            st.markdown(f"""
            <div style="display:flex;align-items:center;gap:14px;flex-wrap:wrap">
                <span style="font-size:1.6rem;font-weight:800;color:#E8EAED">{_act_code}</span>
                <span style="font-size:0.85rem;background:#21262D;color:#8B949E;padding:3px 10px;border-radius:12px">{_act_stock['sector'] if _act_stock else '—'}</span>
                <span style="font-size:1.3rem;font-weight:700;color:{_act_color}">
                    {'Rp {:,.0f}'.format(_act_price) if _act_price else '—'}
                    &nbsp;{_act_arrow}{abs(_act_pct):.2f}% ({_act_chg:+.0f})
                </span>
                <span style="font-size:0.78rem;color:#555">
                    H:{'Rp {:,.0f}'.format(_act_high) if _act_high else '—'}
                    &nbsp;L:{'Rp {:,.0f}'.format(_act_low) if _act_low else '—'}
                    &nbsp;Vol:{'{:.1f}M'.format(_act_vol/1e6) if _act_vol>=1e6 else str(_act_vol)}
                </span>
            </div>
            """, unsafe_allow_html=True)
        with _ah2:
            if st.button("🔄 Refresh", key="dlg_refresh", use_container_width=True):
                st.session_state["_idx_pending_ticker"] = active_ticker
                st.session_state["idx_open_popup"] = True
                st.rerun()
        with _ah3:
            if st.button("🤖 AI Analisis", type="primary", use_container_width=True, key="dlg_ai"):
                st.session_state["_idx_pending_ticker"] = active_ticker
                st.session_state["_trigger_ai"] = True
                st.session_state["idx_open_popup"] = True
                st.rerun()

        _need_run = (st.session_state.last_analyzed != active_ticker or st.session_state.df.empty)
        if _need_run:
            st.info(f"⏳ Memuat analisis **{_act_code}**...")
        else:
            # ── Data dari session_state ──
            _d_ticker  = st.session_state.ticker
            _d_df      = st.session_state.df
            _d_info    = st.session_state.info
            _d_signals = st.session_state.get("signals", {})
            _d_sr      = st.session_state.get("sr", {})
            _d_smc     = st.session_state.get("smc_bias")
            _d_wyck    = st.session_state.get("wyckoff", {})
            _d_mtf     = st.session_state.get("mtf", {})
            _d_fib     = st.session_state.get("fib", {})
            _d_diverg  = st.session_state.get("divergences", [])
            _d_candle  = st.session_state.get("candle_pat", [])
            _d_vp      = st.session_state.get("vp", {})
            _d_var     = st.session_state.get("var_data", {})
            _d_ratios  = st.session_state.get("ratios", {})
            _d_kelly   = st.session_state.get("kelly", {})
            _d_mc      = st.session_state.get("mc_data", {})
            _d_obs     = st.session_state.get("obs", [])
            _d_fvgs    = st.session_state.get("fvgs", [])
            _d_bos     = st.session_state.get("bos_events", [])
            _d_liq     = st.session_state.get("liq", [])
            _d_pd_zone = st.session_state.get("pd_zone", {})
            _d_overall = _d_signals.get("_overall", {})
            _live_price = _act_price or (float(_d_df["Close"].iloc[-1]) if not _d_df.empty else None)
            _rec     = _d_overall.get("recommendation", "N/A")
            _rec_color = "#26A69A" if "BUY" in _rec else ("#EF5350" if "SELL" in _rec else "#FF9800")
            _cname   = st.session_state.get("company_name", _d_ticker)

            # Recommendation badge
            st.markdown(f"""
            <div style="display:flex;align-items:center;gap:10px;margin:8px 0 14px 0">
                <span style="font-size:0.85rem;color:#8B949E">{_cname} · {_d_info.get('exchange','IDX')}</span>
                <span style="background:{'rgba(38,166,154,0.2)' if 'BUY' in _rec else 'rgba(239,83,80,0.2)' if 'SELL' in _rec else 'rgba(255,152,0,0.2)'};
                      color:{_rec_color};border:1px solid {_rec_color};border-radius:6px;
                      padding:3px 14px;font-weight:700;font-size:0.88rem">{_rec}</span>
                <span style="font-size:0.78rem;color:#555">Data: {st.session_state.last_timeframe} · {st.session_state.last_interval}</span>
            </div>
            """, unsafe_allow_html=True)

            # ── SUB-TABS ANALISIS LENGKAP ──
            _ptab1, _ptab2, _ptab3, _ptab4, _ptab5, _ptab6, _ptab7, _ptab8 = st.tabs([
                "📈 Chart & Teknikal",
                "🏦 SMC & Struktur",
                "📐 Advanced TA",
                "📉 Risk & Quant",
                "💰 Fundamental",
                "📰 Berita & Sentimen",
                "🌍 Makro Ekonomi",
                "🤖 AI Analysis",
            ])

            with _ptab1:
                try:
                    _fig_c = plot_candlestick_chart(_d_df, _d_ticker, show_ichimoku=False)
                    st.plotly_chart(_fig_c, use_container_width=True, config={"displayModeBar": False})
                except Exception as _ce:
                    st.warning(f"Chart error: {_ce}")

            # ── 3 KOLOM INDIKATOR (masih di tab Chart & Teknikal) ──
            _ic1, _ic2, _ic3 = st.columns(3)

            with _ic1:
                st.markdown("""<div style="background:#161B22;border:1px solid #30363D;border-radius:8px;padding:12px 14px;height:100%">
                <div style="font-weight:700;color:#E8EAED;margin-bottom:8px;border-bottom:1px solid #30363D;padding-bottom:6px">📊 Sinyal Teknikal</div>""", unsafe_allow_html=True)
                _sig_map = [
                    ("RSI", _d_signals.get("rsi",{})),
                    ("MACD", _d_signals.get("macd",{})),
                    ("MA Cross", _d_signals.get("ma_cross",{})),
                    ("Bollinger", _d_signals.get("bollinger",{})),
                    ("Stochastic", _d_signals.get("stochastic",{})),
                    ("Volume", _d_signals.get("volume",{})),
                ]
                _last_rsi = float(_d_df["RSI"].iloc[-1]) if "RSI" in _d_df.columns and not _d_df.empty else None
                for _sname, _sval in _sig_map:
                    if isinstance(_sval, dict) and _sval:
                        _sig = _sval.get("signal","—")
                        _sc = "#26A69A" if "BUY" in str(_sig) else ("#EF5350" if "SELL" in str(_sig) else "#8B949E")
                        _extra = f" <span style='color:#555;font-size:0.75rem'>({_last_rsi:.1f})</span>" if _sname=="RSI" and _last_rsi else ""
                        st.markdown(f"<div style='display:flex;justify-content:space-between;padding:4px 0;border-bottom:1px solid #21262D'><span style='color:#8B949E;font-size:0.82rem'>{_sname}{_extra}</span><span style='color:{_sc};font-weight:700;font-size:0.82rem'>{_sig}</span></div>", unsafe_allow_html=True)
                # S/R
                _supports = _d_sr.get("support",[])
                _resists  = _d_sr.get("resistance",[])
                st.markdown("<div style='margin-top:8px;font-size:0.78rem;color:#8B949E;font-weight:700'>🎯 Support / Resistance</div>", unsafe_allow_html=True)
                for _lv in _resists[:2]:
                    st.markdown(f"<div style='font-size:0.78rem;color:#EF5350;padding:2px 0'>R: Rp {_lv:,.0f}</div>", unsafe_allow_html=True)
                if _live_price:
                    st.markdown(f"<div style='font-size:0.78rem;color:#58A6FF;font-weight:700;padding:2px 0'>● Rp {_live_price:,.0f}</div>", unsafe_allow_html=True)
                for _lv in _supports[:2]:
                    st.markdown(f"<div style='font-size:0.78rem;color:#26A69A;padding:2px 0'>S: Rp {_lv:,.0f}</div>", unsafe_allow_html=True)
                st.markdown("</div>", unsafe_allow_html=True)

            with _ic2:
                st.markdown("""<div style="background:#161B22;border:1px solid #30363D;border-radius:8px;padding:12px 14px;height:100%">
                <div style="font-weight:700;color:#E8EAED;margin-bottom:8px;border-bottom:1px solid #30363D;padding-bottom:6px">🏦 SMC & Market Structure</div>""", unsafe_allow_html=True)

                def _smc_row(label, val, color="#C9D1D9"):
                    st.markdown(f"<div style='display:flex;justify-content:space-between;padding:4px 0;border-bottom:1px solid #21262D'><span style='color:#8B949E;font-size:0.82rem'>{label}</span><span style='color:{color};font-weight:700;font-size:0.82rem'>{val}</span></div>", unsafe_allow_html=True)

                if _d_smc is not None:
                    _bs = _d_smc if isinstance(_d_smc,(int,float)) else _d_smc.get("score",0) if isinstance(_d_smc,dict) else 0
                    _bl = "BULLISH" if _bs>0 else ("BEARISH" if _bs<0 else "NEUTRAL")
                    _bc2 = "#26A69A" if _bs>0 else ("#EF5350" if _bs<0 else "#8B949E")
                    _smc_row("SMC Bias", _bl, _bc2)
                _bull_obs = [o for o in _d_obs if o.get("type")=="bullish"]
                _bear_obs = [o for o in _d_obs if o.get("type")=="bearish"]
                _smc_row("Order Blocks", f"🟢{len(_bull_obs)} 🔴{len(_bear_obs)}")
                _smc_row("FVG unfilled", str(len(_d_fvgs)), "#FF9800")
                _bos_n   = sum(1 for b in _d_bos if b.get("type")=="BOS")
                _choch_n = sum(1 for b in _d_bos if b.get("type")=="CHOCH")
                _smc_row("BOS / CHoCH", f"{_bos_n} / {_choch_n}")
                _wyck_phase = _d_wyck.get("phase","—") if isinstance(_d_wyck,dict) else "—"
                _smc_row("Wyckoff Phase", _wyck_phase, "#9C27B0")
                if isinstance(_d_mtf, dict):
                    _mw = _d_mtf.get("weekly",{}).get("bias","—")
                    _md = _d_mtf.get("daily",{}).get("bias","—")
                    _m4 = _d_mtf.get("h4",{}).get("bias","—")
                    _smc_row("MTF Weekly", _mw, "#26A69A" if "Bull" in str(_mw) else "#EF5350")
                    _smc_row("MTF Daily",  _md, "#26A69A" if "Bull" in str(_md) else "#EF5350")
                    _smc_row("MTF 4H",     _m4, "#26A69A" if "Bull" in str(_m4) else "#EF5350")
                # Pola Candlestick
                if _d_candle:
                    st.markdown("<div style='margin-top:8px;font-size:0.78rem;color:#8B949E;font-weight:700'>🕯️ Pola Candlestick</div>", unsafe_allow_html=True)
                    for _pat in _d_candle[:4]:
                        _pn = _pat.get("pattern",""); _ps = _pat.get("signal","")
                        _pc2 = "#26A69A" if "Bullish" in _ps else "#EF5350"
                        st.markdown(f"<div style='font-size:0.75rem;color:{_pc2};padding:2px 0'>● {_pn}</div>", unsafe_allow_html=True)
                st.markdown("</div>", unsafe_allow_html=True)

            with _ic3:
                st.markdown("""<div style="background:#161B22;border:1px solid #30363D;border-radius:8px;padding:12px 14px;height:100%">
                <div style="font-weight:700;color:#E8EAED;margin-bottom:8px;border-bottom:1px solid #30363D;padding-bottom:6px">📉 Risk & Quant</div>""", unsafe_allow_html=True)

                def _risk_row(label, val, fmt=".2f", suffix="", col=None):
                    if val is None: return
                    _vc = col or ("#26A69A" if float(val)>=0 else "#EF5350")
                    st.markdown(f"<div style='display:flex;justify-content:space-between;padding:4px 0;border-bottom:1px solid #21262D'><span style='color:#8B949E;font-size:0.82rem'>{label}</span><span style='color:{_vc};font-weight:700;font-size:0.82rem'>{float(val):{fmt}}{suffix}</span></div>", unsafe_allow_html=True)

                _risk_row("Annual Return", _d_ratios.get("annual_return"), suffix="%")
                _risk_row("Sharpe Ratio", _d_ratios.get("sharpe_ratio"), col="#26A69A" if (_d_ratios.get("sharpe_ratio") or 0)>1 else "#FF9800" if (_d_ratios.get("sharpe_ratio") or 0)>0 else "#EF5350")
                _risk_row("Sortino Ratio", _d_ratios.get("sortino_ratio"))
                _risk_row("Max Drawdown", _d_ratios.get("max_drawdown"), suffix="%", col="#EF5350")
                _risk_row("Calmar Ratio", _d_ratios.get("calmar_ratio"))
                _var_hist = _d_var.get("historical",{}) if isinstance(_d_var,dict) else {}
                _risk_row("VaR 95% (hist)", _var_hist.get("var_95"), suffix="%", col="#EF5350")
                _risk_row("CVaR 95%", _var_hist.get("cvar_95"), suffix="%", col="#EF5350")
                _kf = _d_kelly.get("kelly_fraction") if isinstance(_d_kelly,dict) else None
                if _kf is not None:
                    _risk_row("Kelly Fraction", float(_kf)*100, suffix="%", col="#2196F3")
                # Fib & VP
                st.markdown("<div style='margin-top:8px;font-size:0.78rem;color:#8B949E;font-weight:700'>📐 Fibonacci & VP</div>", unsafe_allow_html=True)
                _fib_levels = _d_fib.get("levels",{}) if isinstance(_d_fib,dict) else {}
                for _fl, _fv in list(_fib_levels.items())[:5]:
                    _fc2 = "#26A69A" if (_live_price and _fv<=_live_price) else "#EF5350"
                    st.markdown(f"<div style='font-size:0.75rem;display:flex;justify-content:space-between'><span style='color:#555'>{_fl}</span><span style='color:{_fc2}'>Rp {_fv:,.0f}</span></div>", unsafe_allow_html=True)
                if isinstance(_d_vp,dict) and _d_vp.get("poc"):
                    st.markdown(f"<div style='font-size:0.75rem;display:flex;justify-content:space-between;padding-top:3px'><span style='color:#555'>POC</span><span style='color:#FF9800;font-weight:700'>Rp {_d_vp['poc']:,.0f}</span></div>", unsafe_allow_html=True)
                st.markdown("</div>", unsafe_allow_html=True)

            with _ptab2:
                # SMC Chart
                try:
                    _fig_smc = plot_smc_chart(_d_df, _d_ticker, _d_obs, _d_fvgs, _d_bos, _d_pd_zone, _d_liq)
                    st.plotly_chart(_fig_smc, use_container_width=True, config={"displayModeBar":False})
                except Exception as _e:
                    st.warning(f"SMC Chart error: {_e}")
                # Detail SMC
                _sc1, _sc2 = st.columns(2)
                with _sc1:
                    st.markdown("**Order Blocks**")
                    for _ob in _d_obs[:5]:
                        _oc = "#26A69A" if _ob.get("type")=="bullish" else "#EF5350"
                        st.markdown(f"<div style='font-size:0.8rem;color:{_oc}'>● {_ob.get('type','').upper()} @ Rp {_ob.get('price',0):,.0f}</div>", unsafe_allow_html=True)
                with _sc2:
                    st.markdown("**FVG & BOS/CHoCH**")
                    for _fv in _d_fvgs[:5]:
                        st.markdown(f"<div style='font-size:0.8rem;color:#FF9800'>⬡ FVG {_fv.get('type','')} @ Rp {_fv.get('price',0):,.0f}</div>", unsafe_allow_html=True)
                    for _bv in _d_bos[:3]:
                        _bc = "#26A69A" if "BOS" in str(_bv.get("type","")) else "#9C27B0"
                        st.markdown(f"<div style='font-size:0.8rem;color:{_bc}'>▸ {_bv.get('type','')} @ bar {_bv.get('index',0)}</div>", unsafe_allow_html=True)

            with _ptab3:
                # Advanced TA — Fibonacci + Volume Profile
                _fib_levels = _d_fib.get("levels",{}) if isinstance(_d_fib,dict) else {}
                if _fib_levels:
                    st.markdown("**📐 Level Fibonacci**")
                    for _fl, _fv in _fib_levels.items():
                        _fc = "#26A69A" if (_live_price and _fv<=_live_price) else "#EF5350"
                        st.markdown(f"<div style='display:flex;justify-content:space-between;padding:3px 0;border-bottom:1px solid #21262D'><span style='color:#8B949E'>{_fl}</span><span style='color:{_fc};font-weight:700'>Rp {_fv:,.0f}</span></div>", unsafe_allow_html=True)
                if isinstance(_d_vp,dict) and _d_vp.get("poc"):
                    st.markdown(f"**POC (Volume Profile):** Rp {_d_vp['poc']:,.0f}")
                # Divergences
                if _d_diverg:
                    st.markdown("**🔀 Divergensi**")
                    for _dv in _d_diverg[:5]:
                        st.markdown(f"<div style='font-size:0.82rem;color:#FF9800'>● {_dv.get('type','')} {_dv.get('indicator','')}</div>", unsafe_allow_html=True)
                # Pola Candlestick
                if _d_candle:
                    st.markdown("**🕯️ Pola Candlestick**")
                    for _pat in _d_candle[:8]:
                        _pn = _pat.get("pattern",""); _ps = _pat.get("signal","")
                        _pc = "#26A69A" if "Bullish" in _ps else "#EF5350"
                        st.markdown(f"<div style='font-size:0.82rem;color:{_pc}'>● {_pn} — {_ps}</div>", unsafe_allow_html=True)
                # Wyckoff & MTF
                if isinstance(_d_wyck,dict):
                    st.markdown(f"**Wyckoff Phase:** {_d_wyck.get('phase','—')}")
                if isinstance(_d_mtf,dict):
                    st.markdown("**Multi-Timeframe:**")
                    for _tf, _td in _d_mtf.items():
                        if isinstance(_td,dict):
                            _b = _td.get("bias","—")
                            _c = "#26A69A" if "Bull" in str(_b) else "#EF5350"
                            st.markdown(f"<span style='color:{_c}'>● {_tf.upper()}: {_b}</span>", unsafe_allow_html=True)

            with _ptab4:
                # Risk & Quant
                _r1, _r2 = st.columns(2)
                with _r1:
                    st.markdown("**📊 Performance Metrics**")
                    for _lbl, _key, _suf in [("Annual Return","annual_return","%"),("Sharpe Ratio","sharpe_ratio",""),("Sortino Ratio","sortino_ratio",""),("Max Drawdown","max_drawdown","%"),("Calmar Ratio","calmar_ratio","")]:
                        _v = _d_ratios.get(_key)
                        if _v is not None:
                            _vc = "#26A69A" if float(_v)>=0 else "#EF5350"
                            st.markdown(f"<div style='display:flex;justify-content:space-between;padding:3px 0;border-bottom:1px solid #21262D'><span style='color:#8B949E'>{_lbl}</span><span style='color:{_vc};font-weight:700'>{float(_v):.2f}{_suf}</span></div>", unsafe_allow_html=True)
                with _r2:
                    st.markdown("**📉 VaR & Kelly**")
                    _var_hist = _d_var.get("historical",{}) if isinstance(_d_var,dict) else {}
                    for _lbl, _key in [("VaR 95%","var_95"),("CVaR 95%","cvar_95")]:
                        _v = _var_hist.get(_key)
                        if _v is not None:
                            st.markdown(f"<div style='display:flex;justify-content:space-between;padding:3px 0;border-bottom:1px solid #21262D'><span style='color:#8B949E'>{_lbl}</span><span style='color:#EF5350;font-weight:700'>{float(_v):.2f}%</span></div>", unsafe_allow_html=True)
                    _kf = _d_kelly.get("kelly_fraction") if isinstance(_d_kelly,dict) else None
                    if _kf is not None:
                        st.markdown(f"<div style='display:flex;justify-content:space-between;padding:3px 0'><span style='color:#8B949E'>Kelly Fraction</span><span style='color:#2196F3;font-weight:700'>{float(_kf)*100:.1f}%</span></div>", unsafe_allow_html=True)
                # Monte Carlo
                st.markdown("---")
                try:
                    _mc_sim = _d_mc.get("simulations") if isinstance(_d_mc, dict) else None
                    _mc_ok  = isinstance(_mc_sim, pd.DataFrame) and not _mc_sim.empty
                    if _mc_ok:
                        _fig_mc = plot_monte_carlo(_d_mc, _d_ticker)
                        st.plotly_chart(_fig_mc, use_container_width=True, config={"displayModeBar":False})
                        _mc_m  = _d_mc.get("percentile_50")
                        _mc_bu = _d_mc.get("percentile_95")
                        _mc_be = _d_mc.get("percentile_5")
                        if _mc_m:
                            st.caption(f"Bear: Rp {_mc_be:,.0f} · Median: Rp {_mc_m:,.0f} · Bull: Rp {_mc_bu:,.0f}")
                    else:
                        st.info("Data Monte Carlo tidak tersedia")
                except Exception as _e:
                    st.warning(f"Monte Carlo error: {_e}")

            with _ptab5:
                # Fundamental
                _d_info2 = st.session_state.info
                _d_fin2  = st.session_state.get("financials", {})
                _d_met2  = get_key_metrics(_d_info2)
                _f1, _f2 = st.columns(2)
                with _f1:
                    st.markdown("**📋 Data Perusahaan**")
                    for _lbl, _key in [("Sektor","sector"),("Industri","industry"),("Market Cap","marketCap"),("Karyawan","fullTimeEmployees"),("Negara","country")]:
                        _v = _d_info2.get(_key,"—")
                        if _key == "marketCap" and _v and _v != "—":
                            _v = f"Rp {int(_v)/1e12:.2f} T" if _v > 1e12 else f"Rp {int(_v)/1e9:.1f} B"
                        st.markdown(f"<div style='display:flex;justify-content:space-between;padding:3px 0;border-bottom:1px solid #21262D'><span style='color:#8B949E'>{_lbl}</span><span style='color:#E8EAED'>{_v}</span></div>", unsafe_allow_html=True)
                with _f2:
                    st.markdown("**📊 Valuasi**")
                    for _lbl, _key in [("P/E Ratio","trailingPE"),("PBV","priceToBook"),("EPS","trailingEps"),("Dividen Yield","dividendYield"),("ROE","returnOnEquity")]:
                        _v = _d_info2.get(_key)
                        if _v is not None:
                            _vs = f"{float(_v):.2f}" if _key != "dividendYield" else f"{float(_v)*100:.2f}%"
                            st.markdown(f"<div style='display:flex;justify-content:space-between;padding:3px 0;border-bottom:1px solid #21262D'><span style='color:#8B949E'>{_lbl}</span><span style='color:#E8EAED'>{_vs}</span></div>", unsafe_allow_html=True)

            with _ptab6:
                # Berita & Sentimen
                _pop_news = st.session_state.get("news", [])
                if _pop_news:
                    from modules.news_analysis import aggregate_sentiment
                    _pagg = aggregate_sentiment(_pop_news)
                    _pn1, _pn2, _pn3, _pn4 = st.columns(4)
                    _pn1.metric("Sentimen", _pagg["label"])
                    _pn2.metric("🟢 Bullish", _pagg["bullish"])
                    _pn3.metric("🔴 Bearish", _pagg["bearish"])
                    _pn4.metric("⚪ Neutral",  _pagg["neutral"])
                    _ptot = _pagg["total"]
                    if _ptot > 0:
                        _pbull = _pagg["bullish"] / _ptot * 100
                        _pbear = _pagg["bearish"] / _ptot * 100
                        st.markdown(f"""<div style="background:#333;border-radius:6px;overflow:hidden;height:16px;margin:8px 0">
                            <div style="display:inline-block;background:#26A69A;width:{_pbull:.0f}%;height:100%"></div>
                            <div style="display:inline-block;background:#555;width:{100-_pbull-_pbear:.0f}%;height:100%"></div>
                            <div style="display:inline-block;background:#EF5350;width:{_pbear:.0f}%;height:100%"></div>
                        </div>""", unsafe_allow_html=True)
                    st.markdown("---")
                    _pnews_tabs = st.tabs([f"🟢 Bullish ({_pagg['bullish']})", f"🔴 Bearish ({_pagg['bearish']})", f"📋 Semua ({_ptot})"])
                    with _pnews_tabs[0]:
                        for _na in [n for n in _pop_news if n.get("sentiment",{}).get("label")=="Bullish"][:8]:
                            st.markdown(f"**[{_na.get('title','')}]({_na.get('url','#')})** — *{_na.get('source','')}*")
                    with _pnews_tabs[1]:
                        for _na in [n for n in _pop_news if n.get("sentiment",{}).get("label")=="Bearish"][:8]:
                            st.markdown(f"**[{_na.get('title','')}]({_na.get('url','#')})** — *{_na.get('source','')}*")
                    with _pnews_tabs[2]:
                        for _na in _pop_news[:15]:
                            _sl = _na.get("sentiment",{}).get("label","—")
                            _sc = "🟢" if _sl=="Bullish" else ("🔴" if _sl=="Bearish" else "⚪")
                            st.markdown(f"{_sc} **[{_na.get('title','')}]({_na.get('url','#')})** — *{_na.get('source','')}*")
                else:
                    st.info("Belum ada data berita. Analisis saham terlebih dahulu.")

            with _ptab7:
                # Makro Ekonomi
                _pop_macro = st.session_state.get("macro_env", {})
                if _pop_macro:
                    _pm1, _pm2 = st.columns(2)
                    with _pm1:
                        st.markdown("**🏦 Kondisi Makro**")
                        for _mk, _mv in list(_pop_macro.items())[:8]:
                            if isinstance(_mv, (int, float, str)):
                                st.markdown(f"<div style='display:flex;justify-content:space-between;padding:3px 0;border-bottom:1px solid #21262D'><span style='color:#8B949E;font-size:0.82rem'>{_mk}</span><span style='color:#E8EAED;font-size:0.82rem'>{_mv}</span></div>", unsafe_allow_html=True)
                    with _pm2:
                        st.markdown("**📊 Indikator Ekonomi**")
                        for _mk, _mv in list(_pop_macro.items())[8:16]:
                            if isinstance(_mv, (int, float, str)):
                                st.markdown(f"<div style='display:flex;justify-content:space-between;padding:3px 0;border-bottom:1px solid #21262D'><span style='color:#8B949E;font-size:0.82rem'>{_mk}</span><span style='color:#E8EAED;font-size:0.82rem'>{_mv}</span></div>", unsafe_allow_html=True)
                else:
                    st.info("Belum ada data makro. Analisis saham terlebih dahulu.")
                # Market summary
                _pop_markets = st.session_state.get("markets", [])
                if _pop_markets:
                    st.markdown("---")
                    st.markdown("**🌐 Pasar Global**")
                    _pm_cols = st.columns(4)
                    for _i, _mkt in enumerate(_pop_markets[:8]):
                        with _pm_cols[_i % 4]:
                            _mchg = _mkt.get("change", 0) or 0
                            _mc   = "#26A69A" if _mchg >= 0 else "#EF5350"
                            _marr = "▲" if _mchg >= 0 else "▼"
                            st.markdown(f"""<div style="background:#161B22;border:1px solid #30363D;border-radius:6px;padding:8px;margin:3px 0;text-align:center">
                                <div style="color:#8B949E;font-size:0.75rem">{_mkt.get('name','')}</div>
                                <div style="color:#E8EAED;font-weight:700">{_mkt.get('price','—')}</div>
                                <div style="color:{_mc};font-size:0.8rem">{_marr}{abs(_mchg):.2f}%</div>
                            </div>""", unsafe_allow_html=True)

            with _ptab8:
                # AI Analysis
                if st.session_state.ai_result:
                    st.markdown(st.session_state.ai_result)
                else:
                    st.info("Klik tombol di bawah untuk generate analisis mendalam dari Claude AI.")
                    if st.button("🤖 Generate AI Analisis Sekarang", type="primary", key="dlg_ai_gen"):
                        st.session_state["_idx_pending_ticker"] = active_ticker
                        st.session_state["_trigger_ai"] = True
                        st.session_state["idx_open_popup"] = True
                        st.rerun()

    # ── Tampilkan popup analisis otomatis ──
    if _active_ticker and st.session_state.get("idx_open_popup", False):
        st.session_state["idx_open_popup"] = False
        _show_analysis_popup(_active_ticker, _all_prices, _display_list)
    elif _active_ticker and st.session_state.last_analyzed == _active_ticker and not st.session_state.df.empty:
        _show_analysis_popup(_active_ticker, _all_prices, _display_list)

    if not _active_ticker:
        st.markdown("""
        <div style="background:#0D1117;border:1px dashed #30363D;border-radius:12px;
            padding:40px;text-align:center;margin-top:8px">
            <div style="font-size:2rem;margin-bottom:10px">👆</div>
            <div style="color:#C9D1D9;font-size:1.1rem;font-weight:600">Klik saham di atas untuk melihat analisis lengkap</div>
            <div style="color:#8B949E;font-size:0.85rem;margin-top:6px">Popup analisis otomatis muncul — Teknikal · SMC · Fibonacci · Risk · Chart</div>
        </div>
        """, unsafe_allow_html=True)


# ── Konten Live Price, Teknikal, SMC, Advanced TA, Risk, Fundamental, AI
# ── dipindahkan ke dalam popup dialog saat saham diklik
if False:  # placeholder — tidak dirender di main page
    _dummy_ctx = True
    st.markdown('<div class="section-header">⚡ Live Price & Intraday</div>', unsafe_allow_html=True)

    if not live_mode:
        st.info("🔴 Mode real-time belum aktif. Aktifkan toggle **Mode Real-Time** di sidebar.")
    else:
        # ── Live quote panel ──
        live_data = get_live_price(ticker)
        if live_data and live_data.get("price"):
            lp = live_data["price"]
            lc = live_data.get("change", 0) or 0
            lpc = live_data.get("pct_change", 0) or 0
            source = live_data.get("source", "yfinance")
            ts_str = format_timestamp(live_data.get("timestamp"))
            is_open = is_market_open(ticker)

            cl1, cl2, cl3, cl4, cl5 = st.columns(5)
            with cl1:
                st.metric("💵 Harga Live", format_price(lp), f"{lpc:+.2f}%")
            with cl2:
                st.metric("📈 High", format_price(live_data.get("high")))
            with cl3:
                st.metric("📉 Low", format_price(live_data.get("low")))
            with cl4:
                st.metric("🔓 Open", format_price(live_data.get("open")))
            with cl5:
                st.metric("Prev Close", format_price(live_data.get("prev_close")))

            col_info, col_status = st.columns([3, 1])
            with col_info:
                st.caption(f"Sumber: **{source}** · Update: **{ts_str}** · "
                           f"{'🟢 Pasar Sedang Buka' if is_open else '🔴 Pasar Tutup'}")
            with col_status:
                if FINNHUB_API_KEY and not ticker.endswith(".JK"):
                    fh_sent = finnhub_sentiment(ticker)
                    if fh_sent and fh_sent.get("companyNewsScore") is not None:
                        score = fh_sent.get("companyNewsScore", 0)
                        buzz  = fh_sent.get("buzz", {}).get("articlesInLastWeek", 0)
                        sentiment_label = "🟢 Positif" if score > 0.6 else ("🔴 Negatif" if score < 0.4 else "⚪ Netral")
                        st.metric("Finnhub Sentiment", sentiment_label, f"{buzz} artikel/minggu")
        else:
            st.warning("Harga live tidak tersedia. Periksa koneksi atau API key.")

        st.markdown("---")

        # ── Intraday chart ──
        if show_intraday:
            st.markdown(f"#### 📊 Chart Intraday ({intraday_interval})")
            with st.spinner("Memuat data intraday..."):
                df_intra = get_intraday_data(ticker, interval=intraday_interval, hours=8)

            if not df_intra.empty:
                from modules.technical_analysis import calculate_indicators as _calc
                df_intra = _calc(df_intra)

                fig_intra = make_subplots(
                    rows=3, cols=1, shared_xaxes=True,
                    row_heights=[0.6, 0.2, 0.2],
                    vertical_spacing=0.02,
                    subplot_titles=["", "Volume", "RSI"],
                )
                # Candle
                fig_intra.add_trace(go.Candlestick(
                    x=df_intra.index, open=df_intra["Open"], high=df_intra["High"],
                    low=df_intra["Low"], close=df_intra["Close"],
                    name="Harga", increasing_line_color="#26A69A", decreasing_line_color="#EF5350",
                ), row=1, col=1)
                # EMA
                for col_ema, color_ema in [("EMA9", "#FF9800"), ("EMA21", "#2196F3")]:
                    if col_ema in df_intra.columns:
                        fig_intra.add_trace(go.Scatter(
                            x=df_intra.index, y=df_intra[col_ema],
                            name=col_ema, line=dict(color=color_ema, width=1.2),
                        ), row=1, col=1)
                # VWAP (aproximasi)
                if "Volume" in df_intra.columns:
                    typical = (df_intra["High"] + df_intra["Low"] + df_intra["Close"]) / 3
                    cum_tp_v = (typical * df_intra["Volume"]).cumsum()
                    cum_v    = df_intra["Volume"].cumsum()
                    vwap     = cum_tp_v / cum_v
                    fig_intra.add_trace(go.Scatter(
                        x=df_intra.index, y=vwap, name="VWAP",
                        line=dict(color="#E91E63", width=1.5, dash="dot"),
                    ), row=1, col=1)
                # Volume
                vol_colors = ["#EF5350" if df_intra["Close"].iloc[i] < df_intra["Open"].iloc[i]
                              else "#26A69A" for i in range(len(df_intra))]
                fig_intra.add_trace(go.Bar(x=df_intra.index, y=df_intra["Volume"],
                                           marker_color=vol_colors, name="Volume"), row=2, col=1)
                # RSI
                if "RSI" in df_intra.columns:
                    fig_intra.add_trace(go.Scatter(
                        x=df_intra.index, y=df_intra["RSI"], name="RSI",
                        line=dict(color="#E91E63", width=1.5),
                    ), row=3, col=1)
                    fig_intra.add_hline(y=70, line_dash="dash", line_color="red", opacity=0.5, row=3, col=1)
                    fig_intra.add_hline(y=30, line_dash="dash", line_color="green", opacity=0.5, row=3, col=1)

                fig_intra.update_layout(
                    height=650, template="plotly_dark",
                    xaxis_rangeslider_visible=False,
                    title=f"<b>{ticker}</b> — Intraday {intraday_interval} (termasuk VWAP)",
                    paper_bgcolor="#0E1117", plot_bgcolor="#161B22",
                    showlegend=True,
                    legend=dict(orientation="h", y=1.02),
                )
                st.plotly_chart(fig_intra, use_container_width=True)
            else:
                st.warning("Data intraday tidak tersedia (kemungkinan pasar tutup atau data belum tersedia).")

        st.markdown("---")

        # ── Finnhub Extras ──
        if FINNHUB_API_KEY and not ticker.endswith(".JK"):
            col_e1, col_e2 = st.columns(2)

            with col_e1:
                st.markdown("#### 🎯 Rekomendasi Analis (Finnhub)")
                recs = finnhub_recommendation(ticker)
                if recs:
                    df_rec = pd.DataFrame(recs[:4])
                    show_cols = [c for c in ["period", "strongBuy", "buy", "hold", "sell", "strongSell"] if c in df_rec.columns]
                    if show_cols:
                        st.dataframe(df_rec[show_cols], use_container_width=True, hide_index=True)
                else:
                    st.info("Data rekomendasi tidak tersedia")

            with col_e2:
                st.markdown("#### 📅 Earnings Historis (Finnhub)")
                earnings = finnhub_earnings(ticker)
                if earnings:
                    df_earn = pd.DataFrame(earnings[:6])
                    show_cols = [c for c in ["period", "actual", "estimate", "surprise", "surprisePercent"] if c in df_earn.columns]
                    if show_cols:
                        st.dataframe(df_earn[show_cols], use_container_width=True, hide_index=True)
                else:
                    st.info("Data earnings tidak tersedia")

            # Finnhub news
            st.markdown("#### 📰 Berita Terkini (Finnhub)")
            fh_news = finnhub_news(ticker, days=3)
            if fh_news:
                for n in fh_news[:6]:
                    headline = n.get("headline", "")
                    source   = n.get("source", "")
                    url      = n.get("url", "#")
                    summary  = n.get("summary", "")[:200]
                    dt_str   = datetime.fromtimestamp(n.get("datetime", 0)).strftime("%d %b %Y %H:%M") if n.get("datetime") else ""
                    st.markdown(f"""<div class="news-card">
                        <b><a href="{url}" target="_blank" style="color:#E8EAED;text-decoration:none">{headline}</a></b>
                        <p style="color:#8B949E;font-size:0.85rem;margin:4px 0">{summary}</p>
                        <span style="color:#555;font-size:0.78rem">{source} · {dt_str}</span>
                    </div>""", unsafe_allow_html=True)
            else:
                st.info("Berita Finnhub tidak tersedia")
        else:
            st.info("💡 Tambahkan **FINNHUB_API_KEY** di file `.env` untuk fitur live berikut: "
                    "intraday Finnhub, rekomendasi analis real-time, earnings, berita Finnhub, dan sentimen.")

# ════════════════════════════════════════════════════════════════════════════════
# TAB 1: TECHNICAL ANALYSIS — masuk popup
# ════════════════════════════════════════════════════════════════════════════════
if False:
    st.markdown('<div class="section-header">📊 Analisis Teknikal</div>', unsafe_allow_html=True)

    # Chart
    fig = plot_candlestick_chart(df, ticker, show_ichimoku=show_ichimoku)
    st.plotly_chart(fig, use_container_width=True)

    col_sig, col_sr = st.columns([1, 1])

    with col_sig:
        st.markdown("#### 🎯 Sinyal Indikator")
        for key, val in signals.items():
            if key.startswith("_"):
                continue
            render_signal_badge(val.get("signal", ""), f"{key}: {val.get('note', '')}")

        st.markdown("---")
        score_pct = tech_overall.get("pct", 0)
        st.markdown("#### 📈 Skor Teknikal Keseluruhan")
        st.progress(max(0, min(100, int((score_pct + 100) / 2))),
                    text=f"Skor: {score_pct:+.1f}% → **{tech_overall.get('recommendation', 'N/A')}**")

    with col_sr:
        st.markdown("#### 🎯 Support & Resistance")
        current = sr.get("current", 0)

        res = sr.get("resistances", [])
        sup = sr.get("supports", [])

        st.markdown("**🔴 Resistance:**")
        if res:
            for r in res[:3]:
                dist = ((r - current) / current * 100) if current else 0
                st.markdown(f"  `{r:.2f}` (+{dist:.2f}%)")
        else:
            st.markdown("  Tidak ada data")

        st.markdown(f"**⚪ Harga Saat Ini:** `{current:.2f}`")

        st.markdown("**🟢 Support:**")
        if sup:
            for s in sup[:3]:
                dist = ((current - s) / current * 100) if current else 0
                st.markdown(f"  `{s:.2f}` (-{dist:.2f}%)")
        else:
            st.markdown("  Tidak ada data")

        st.markdown("---")
        st.markdown("**📐 Pivot Points (Daily):**")
        for label, key in [("Pivot", "pivot"), ("R1", "R1"), ("R2", "R2"), ("S1", "S1"), ("S2", "S2")]:
            val = sr.get(key)
            if val and not np.isnan(val):
                st.markdown(f"  **{label}:** `{val:.2f}`")

    # RSI & Stochastic chart
    st.markdown("---")
    st.markdown("#### 📉 RSI & Stochastic Oscillator")
    fig2 = plot_rsi_stochastic(df)
    st.plotly_chart(fig2, use_container_width=True)

    # Indicator table
    st.markdown("#### 📋 Nilai Indikator Terkini")
    last_row = df.iloc[-1] if not df.empty else {}
    ind_cols = {
        "MA20": "MA 20", "MA50": "MA 50", "MA200": "MA 200",
        "EMA21": "EMA 21", "RSI": "RSI (14)",
        "MACD": "MACD", "MACD_signal": "MACD Signal",
        "BB_upper": "BB Upper", "BB_lower": "BB Lower",
        "Stoch_K": "Stoch %K", "Stoch_D": "Stoch %D",
        "ATR": "ATR (14)", "ATR_pct": "ATR %",
    }
    ind_data = {}
    for col, label in ind_cols.items():
        val = last_row.get(col) if hasattr(last_row, "get") else None
        if val is not None and not (isinstance(val, float) and np.isnan(val)):
            ind_data[label] = round(float(val), 4)

    if ind_data:
        ind_df = pd.DataFrame(list(ind_data.items()), columns=["Indikator", "Nilai"])
        st.dataframe(ind_df, use_container_width=True, hide_index=True)


# ════════════════════════════════════════════════════════════════════════════════
# TAB 2: SMART MONEY CONCEPTS — masuk popup
# ════════════════════════════════════════════════════════════════════════════════
if False:
    st.markdown('<div class="section-header">🏦 Smart Money Concepts (SMC)</div>', unsafe_allow_html=True)

    # SMC Bias card
    if smc_bias:
        bias_color = smc_bias.get("color", "#888")
        st.markdown(f"""<div style="background:rgba(0,0,0,0.3);border:2px solid {bias_color};
            border-radius:12px;padding:16px;margin-bottom:12px">
            <div style="color:{bias_color};font-size:1.5rem;font-weight:800">{smc_bias.get('bias','N/A')}</div>
            <div style="color:#C9D1D9;font-size:0.9rem">Skor SMC: {smc_bias.get('score',0):+.0f}</div>
        </div>""", unsafe_allow_html=True)

        col_n1, col_n2 = st.columns(2)
        with col_n1:
            st.markdown("**📋 Analisis SMC:**")
            for note in smc_bias.get("notes", []):
                st.markdown(f"- {note}")

        with col_n2:
            if pd_zone:
                st.markdown("**🎯 Premium / Discount Zone:**")
                pz_color = pd_zone.get("color", "#888")
                st.markdown(f"""<div style="border:1px solid {pz_color};border-radius:8px;padding:12px">
                    <b style="color:{pz_color}">{pd_zone.get('zone','N/A')}</b><br>
                    <small>{pd_zone.get('bias','')}</small><br><br>
                    📊 Posisi: <b>{pd_zone.get('position_pct',0):.1f}%</b> dari range<br>
                    EQ (50%): <b>{pd_zone.get('equilibrium',0):.2f}</b><br>
                    OTE Zone: <b>{pd_zone.get('ote_bot',0):.2f} – {pd_zone.get('ote_top',0):.2f}</b>
                    {'<br>✅ <b>Harga di OTE Zone!</b>' if pd_zone.get('in_ote') else ''}
                </div>""", unsafe_allow_html=True)

    st.markdown("---")

    # SMC Chart
    if not df.empty:
        fig_smc = plot_smc_chart(df.tail(80), ticker, obs, fvgs, bos_events, pd_zone, liq)
        st.plotly_chart(fig_smc, use_container_width=True)

    # Detail panels
    col_ob, col_fvg, col_liq = st.columns(3)

    with col_ob:
        st.markdown("#### 📦 Order Blocks Aktif")
        if obs:
            for ob in obs:
                color = "#26A69A" if "Bullish" in ob["type"] else "#EF5350"
                st.markdown(f"""<div style="border-left:3px solid {color};padding:8px;margin:4px 0;background:rgba(0,0,0,0.2)">
                    <b style="color:{color}">{ob['type']}</b><br>
                    Top: {ob['top']:.2f} | Bot: {ob['bottom']:.2f}
                </div>""", unsafe_allow_html=True)
        else:
            st.info("Tidak ada OB aktif")

    with col_fvg:
        st.markdown("#### 🕳️ Fair Value Gaps Aktif")
        if fvgs:
            for fvg in fvgs:
                color = "#26A69A" if "Bullish" in fvg["type"] else "#EF5350"
                sz_pct = fvg["size"] / df["Close"].iloc[-1] * 100 if df["Close"].iloc[-1] > 0 else 0
                st.markdown(f"""<div style="border-left:3px solid {color};padding:8px;margin:4px 0;background:rgba(0,0,0,0.2)">
                    <b style="color:{color}">{fvg['type']}</b><br>
                    {fvg['bottom']:.2f} – {fvg['top']:.2f} ({sz_pct:.2f}%)
                </div>""", unsafe_allow_html=True)
        else:
            st.info("Tidak ada FVG aktif")

    with col_liq:
        st.markdown("#### 💧 Liquidity Targets")
        bsl = liq.get("buy_side_liquidity", [])
        ssl = liq.get("sell_side_liquidity", [])
        if bsl:
            st.markdown("**🔼 Buy-Side (Resistance Likuiditas):**")
            for z in bsl[:3]:
                dist = (z["level"] - df["Close"].iloc[-1]) / df["Close"].iloc[-1] * 100
                st.markdown(f"- `{z['level']:.2f}` (+{dist:.2f}%)")
        if ssl:
            st.markdown("**🔽 Sell-Side (Support Likuiditas):**")
            for z in ssl[:3]:
                dist = (df["Close"].iloc[-1] - z["level"]) / df["Close"].iloc[-1] * 100
                st.markdown(f"- `{z['level']:.2f}` (-{dist:.2f}%)")

    # BOS/CHOCH history
    st.markdown("---")
    st.markdown("#### 🔀 BOS & CHOCH History")
    if bos_events:
        bos_df = pd.DataFrame([{
            "Tanggal": str(e["index"])[:10],
            "Event": e["type"],
            "Level": round(e["level"], 2),
            "Arah": e["direction"],
        } for e in bos_events[-10:]])
        st.dataframe(bos_df, use_container_width=True, hide_index=True)


# ════════════════════════════════════════════════════════════════════════════════
# TAB 3: ADVANCED TECHNICAL ANALYSIS — masuk popup
# ════════════════════════════════════════════════════════════════════════════════
if False:
    st.markdown('<div class="section-header">📐 Advanced Technical Analysis</div>', unsafe_allow_html=True)

    adv_sub = st.tabs(["📐 Fibonacci", "📊 Volume Profile", "🔀 Divergence & Patterns", "⏱️ MTF & Wyckoff"])

    with adv_sub[0]:
        st.markdown("#### 📐 Auto Fibonacci Retracement & Extension")
        if fib:
            col_f1, col_f2 = st.columns([2, 1])
            with col_f1:
                fig_fib = plot_fibonacci(df.tail(100), fib, ticker)
                st.plotly_chart(fig_fib, use_container_width=True)
            with col_f2:
                st.markdown(f"**Arah:** {fib.get('direction','N/A')}")
                st.markdown(f"**Swing High:** `{fib.get('swing_high',0):.2f}`")
                st.markdown(f"**Swing Low:** `{fib.get('swing_low',0):.2f}`")
                near_s = fib.get("nearest_support")
                near_r = fib.get("nearest_resistance")
                if near_s:
                    st.success(f"🟢 Support Fib: **{near_s[0]:.3f}** = `{near_s[1]:.2f}`")
                if near_r:
                    st.error(f"🔴 Resistance Fib: **{near_r[0]:.3f}** = `{near_r[1]:.2f}`")
                st.markdown("---")
                st.markdown("**Level Retracement:**")
                for lvl, price in fib.get("levels", {}).items():
                    cur = df["Close"].iloc[-1]
                    marker = " ◀ HARGA" if abs(price - cur) / cur < 0.01 else ""
                    st.markdown(f"- `{lvl:.3f}` → **{price:.2f}**{marker}")
                st.markdown("**Level Extension:**")
                for lvl, price in fib.get("extensions", {}).items():
                    st.markdown(f"- `{lvl:.3f}` → **{price:.2f}**")
        else:
            st.info("Data Fibonacci tidak tersedia (butuh minimal 50 candle)")

    with adv_sub[1]:
        st.markdown("#### 📊 Volume Profile (VPVR)")
        if vp:
            col_v1, col_v2 = st.columns([3, 1])
            with col_v1:
                fig_vp = plot_volume_profile(df.tail(100), vp, ticker)
                st.plotly_chart(fig_vp, use_container_width=True)
            with col_v2:
                cur = df["Close"].iloc[-1]
                poc = vp.get("poc", 0)
                vah = vp.get("vah", 0)
                val = vp.get("val", 0)
                st.metric("POC 🟡", f"{poc:.2f}", f"{(cur-poc)/poc*100:+.2f}%")
                st.metric("VAH 🔵", f"{vah:.2f}")
                st.metric("VAL 🔴", f"{val:.2f}")
                if val < cur < vah:
                    st.success("✅ Harga dalam Value Area")
                elif cur > vah:
                    st.warning("⚠️ Di atas Value Area")
                else:
                    st.error("⚠️ Di bawah Value Area")
        else:
            st.info("Data Volume Profile tidak tersedia")

    with adv_sub[2]:
        col_div, col_pat = st.columns(2)
        with col_div:
            st.markdown("#### 🔀 Divergence Analysis")
            if divergences:
                for d in divergences:
                    color = "#26A69A" if d["signal"] == "BUY" else "#EF5350"
                    st.markdown(f"""<div style="border-left:3px solid {color};padding:8px;
                        margin:4px 0;background:rgba(0,0,0,0.2)">
                        <b style="color:{color}">{d['type']}</b><br>
                        <small>{d['desc']}</small><br>
                        <small>RSI: {d.get('rsi',0):.1f} | Harga: {d.get('price',0):.2f}</small>
                    </div>""", unsafe_allow_html=True)
            else:
                st.info("Tidak ada divergensi terdeteksi")

        with col_pat:
            st.markdown("#### 🕯️ Candlestick Patterns Terkini")
            if candle_pat:
                for p in candle_pat:
                    color = "#26A69A" if p["signal"] == "BUY" else ("#EF5350" if p["signal"] == "SELL" else "#FF9800")
                    st.markdown(f"""<div style="border-left:3px solid {color};padding:8px;
                        margin:4px 0;background:rgba(0,0,0,0.2)">
                        <b style="color:{color}">{p['name']}</b> [{p['signal']}]<br>
                        <small>{p['desc']}</small>
                    </div>""", unsafe_allow_html=True)
            else:
                st.info("Tidak ada pola candlestick signifikan")

    with adv_sub[3]:
        col_w, col_mtf = st.columns(2)
        with col_w:
            st.markdown("#### 📊 Wyckoff Phase")
            if wyckoff:
                wc = wyckoff.get("color", "#888")
                st.markdown(f"""<div style="border:2px solid {wc};border-radius:10px;padding:16px">
                    <h4 style="color:{wc};margin:0">{wyckoff.get('phase','N/A')}</h4>
                    <p style="color:#C9D1D9;margin:8px 0">{wyckoff.get('description','')}</p>
                    <p style="color:#FFD700"><b>💡 {wyckoff.get('action','')}</b></p>
                    <small style="color:#8B949E">
                    Tren 20H: {wyckoff.get('price_trend_20',0):+.1f}% |
                    Tren 60H: {wyckoff.get('price_trend_60',0):+.1f}% |
                    Vol trend: {wyckoff.get('vol_trend',0):+.1f}%
                    </small>
                </div>""", unsafe_allow_html=True)

        with col_mtf:
            st.markdown("#### ⏱️ Multi-Timeframe Bias")
            if mtf:
                overall = mtf.get("overall", {})
                oc = overall.get("color", "#888")
                st.markdown(f"**Overall: <span style='color:{oc}'>{overall.get('bias','N/A')}</span>**",
                            unsafe_allow_html=True)
                st.markdown("")
                for tf, data in mtf.items():
                    if tf == "overall":
                        continue
                    tc = data.get("color", "#888")
                    st.markdown(f"""<div style="display:flex;justify-content:space-between;
                        padding:6px;border-bottom:1px solid #30363D">
                        <span>{tf}</span>
                        <span style="color:{tc};font-weight:700">{data.get('trend','N/A')}</span>
                        <span style="color:#8B949E">MA: {data.get('ma','N/A')}</span>
                    </div>""", unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════════════════════════
# TAB 4: RISK & QUANTITATIVE — masuk popup
# ════════════════════════════════════════════════════════════════════════════════
if False:
    st.markdown('<div class="section-header">📉 Risk Management & Quantitative Analysis</div>', unsafe_allow_html=True)

    risk_sub = st.tabs(["📊 Performance", "🎲 Monte Carlo", "📉 VaR", "💰 Position Sizing"])

    with risk_sub[0]:
        if ratios:
            c1, c2, c3, c4, c5 = st.columns(5)
            metric_items = [
                (c1, "📈 Annual Return", f"{ratios.get('annualized_return',0):.1f}%"),
                (c2, "📊 Volatilitas", f"{ratios.get('annualized_vol',0):.1f}%"),
                (c3, "⚡ Sharpe Ratio", f"{ratios.get('sharpe_ratio',0):.3f}"),
                (c4, "🎯 Sortino Ratio", f"{ratios.get('sortino_ratio',0):.3f}"),
                (c5, "📉 Max Drawdown", f"{ratios.get('max_drawdown',0):.1f}%"),
            ]
            for col, label, val in metric_items:
                with col:
                    st.metric(label, val)

            c6, c7, c8, c9, c10 = st.columns(5)
            for col, label, val in [
                (c6,  "🏆 Calmar Ratio",  f"{ratios.get('calmar_ratio',0):.3f}"),
                (c7,  "✅ Win Rate",       f"{ratios.get('win_rate',0):.1f}%"),
                (c8,  "💎 Profit Factor",  str(ratios.get('profit_factor','N/A'))),
                (c9,  "📐 Beta",           str(ratios.get('beta','N/A'))),
                (c10, "📐 Skewness",       f"{ratios.get('skewness',0):.3f}"),
            ]:
                with col:
                    st.metric(label, val)

            # Interpretasi Sharpe
            sharpe = ratios.get("sharpe_ratio", 0)
            if sharpe > 2:
                st.success(f"✅ Sharpe Ratio {sharpe:.2f} — Excellent (>2)")
            elif sharpe > 1:
                st.success(f"✅ Sharpe Ratio {sharpe:.2f} — Good (>1)")
            elif sharpe > 0:
                st.warning(f"⚠️ Sharpe Ratio {sharpe:.2f} — Below average (<1)")
            else:
                st.error(f"❌ Sharpe Ratio {sharpe:.2f} — Negatif (tidak layak invest)")

            st.markdown("---")
            fig_perf = plot_performance_dashboard(df, ratios, ticker)
            st.plotly_chart(fig_perf, use_container_width=True)

    with risk_sub[1]:
        if mc_data:
            st.markdown(f"#### 🎲 Monte Carlo {mc_data.get('simulations',500)} Simulasi × {mc_data.get('days',30)} Hari")
            c1, c2, c3, c4 = st.columns(4)
            with c1:
                st.metric("Prob. Profit", f"{mc_data.get('prob_profit',0):.1f}%")
            with c2:
                st.metric("Median Target", f"{mc_data.get('median_price',0):.2f}")
            with c3:
                st.metric("Skenario Terbaik (P95)", f"{mc_data.get('p95_price',0):.2f}")
            with c4:
                st.metric("Skenario Terburuk (P5)", f"{mc_data.get('p5_price',0):.2f}")

            fig_mc = plot_monte_carlo(mc_data, ticker)
            st.plotly_chart(fig_mc, use_container_width=True)

            cur = mc_data.get("current_price", 1)
            med = mc_data.get("median_price", 1)
            st.info(f"Dari {mc_data.get('simulations')} simulasi: "
                    f"median harga dalam {mc_data.get('days')} hari = **{med:.2f}** "
                    f"({(med/cur-1)*100:+.2f}%)")

    with risk_sub[2]:
        if var_data:
            st.markdown("#### 📉 Value at Risk (VaR) — Investasi Rp 100 Juta")
            inv = var_data.get("investment", 100_000_000)
            conf = var_data.get("confidence", 95)
            st.info(f"**{conf:.0f}% Confidence Interval** — Dengan probabilitas {conf:.0f}%, "
                    f"kerugian TIDAK akan melebihi angka berikut dalam 1 hari trading.")

            c1, c2, c3, c4 = st.columns(4)
            for col, method, key in [
                (c1, "Historical", "historical"),
                (c2, "Parametric", "parametric"),
                (c3, "Monte Carlo", "monte_carlo"),
                (c4, "CVaR (Expected Shortfall)", "cvar"),
            ]:
                with col:
                    pct = var_data.get(key, {}).get("pct", 0)
                    idr = var_data.get(key, {}).get("idr", 0)
                    st.metric(method, f"{abs(pct):.2f}%",
                              f"Rp {abs(idr)/1e6:.2f}jt maks. loss")

            st.markdown("---")
            st.markdown("""**📖 Cara Membaca VaR:**
- **Historical**: Berdasarkan distribusi return masa lalu (paling konservatif)
- **Parametric**: Asumsi distribusi normal — cepat tapi underestimate fat tails
- **Monte Carlo**: Simulasi 10.000 skenario — paling komprehensif
- **CVaR**: Rata-rata kerugian di bawah VaR — ukuran risiko ekstrim (tail risk)""")

    with risk_sub[3]:
        st.markdown("#### 💰 Position Sizing — Kelly Criterion")
        if kelly:
            col_k1, col_k2 = st.columns(2)
            with col_k1:
                st.markdown(f"""**Berdasarkan data historis {ticker}:**

| Metrik | Nilai |
|--------|-------|
| Win Probability | {kelly.get('win_probability',0):.1f}% |
| Rata-rata Win | {kelly.get('avg_win_pct',0):.3f}% |
| Rata-rata Loss | {kelly.get('avg_loss_pct',0):.3f}% |
| Win/Loss Ratio | {kelly.get('win_loss_ratio',0):.2f} |
| Full Kelly | {kelly.get('kelly_full',0):.1f}% kapital |
| Half Kelly ✅ | **{kelly.get('kelly_half',0):.1f}% kapital** |
| Quarter Kelly | {kelly.get('kelly_quarter',0):.1f}% kapital |""")

                rec = kelly.get("recommendation", "")
                st.success(f"💡 Rekomendasi: **{rec}**")

            with col_k2:
                st.markdown("#### 🧮 Risk/Reward Calculator")
                cur_price = df["Close"].iloc[-1] if not df.empty else 0
                col_rr1, col_rr2, col_rr3 = st.columns(3)
                with col_rr1:
                    entry = st.number_input("Entry", value=float(cur_price), step=float(cur_price*0.001))
                with col_rr2:
                    sl = st.number_input("Stop Loss", value=float(cur_price * 0.97), step=float(cur_price*0.001))
                with col_rr3:
                    tp = st.number_input("Target", value=float(cur_price * 1.05), step=float(cur_price*0.001))

                cap = st.number_input("Modal (Rp)", value=100_000_000, step=10_000_000)
                risk_pct_input = st.slider("Risk per trade (%)", 0.5, 5.0, 2.0, 0.5) / 100

                rr = calculate_risk_reward(entry, sl, tp, cap, risk_pct_input)
                if rr:
                    rr_ratio = rr.get("rr_ratio", 0)
                    color_rr = "#26A69A" if rr_ratio >= 2 else ("#FF9800" if rr_ratio >= 1 else "#EF5350")
                    st.markdown(f"""
<div style="border:1px solid {color_rr};border-radius:8px;padding:12px;margin-top:8px">
<b style="color:{color_rr}">R:R = {rr_ratio:.2f}</b>
{"✅ Setup layak" if rr_ratio >= 2 else "⚠️ R:R rendah" if rr_ratio >= 1 else "❌ Jangan masuk"}<br><br>
💰 Lot yang disarankan: <b>{rr.get('shares',0):,}</b> lembar<br>
📊 Nilai posisi: Rp {rr.get('position_value',0)/1e6:.1f}jt<br>
✅ Potensi profit: Rp {rr.get('potential_profit',0)/1e6:.2f}jt<br>
❌ Maks. loss: Rp {rr.get('potential_loss',0)/1e6:.2f}jt<br>
🎯 Breakeven win rate: {rr.get('breakeven_winrate',0):.1f}%
</div>""", unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════════════════════════
# TAB 5: FUNDAMENTAL ANALYSIS — masuk popup
# ════════════════════════════════════════════════════════════════════════════════
if False:
    st.markdown('<div class="section-header">💰 Analisis Fundamental</div>', unsafe_allow_html=True)

    # Fundamental score
    f_color = {"green": "#26A69A", "orange": "#FF9800", "gray": "#8B949E", "red": "#EF5350"}
    fc = f_color.get(fund_score.get("color", "gray"), "#8B949E")
    col_fs, col_at = st.columns([1, 1])

    with col_fs:
        st.markdown(f"""<div style="background:rgba(0,0,0,0.3);border:2px solid {fc};border-radius:10px;
            padding:16px;text-align:center">
            <div style="color:{fc};font-size:1.4rem;font-weight:800">{fund_score.get('rating', 'N/A')}</div>
            <div style="color:#8B949E">Skor Fundamental: {fund_score.get('pct', 0):.1f}%</div>
        </div>""", unsafe_allow_html=True)

        st.markdown("**📝 Catatan Fundamental:**")
        for note in fund_score.get("notes", []):
            st.markdown(f"- {note}")

    with col_at:
        analyst = get_analyst_targets(info)
        if analyst.get("target_mean"):
            st.markdown("#### 🎯 Target Analis")
            c1, c2 = st.columns(2)
            with c1:
                st.metric("Target Rata-rata", fmt_num(analyst.get("target_mean")),
                          f"{analyst.get('upside_pct', 0):+.1f}% upside" if analyst.get("upside_pct") else None)
                st.metric("Target Tertinggi", fmt_num(analyst.get("target_high")))
            with c2:
                st.metric("Target Terendah", fmt_num(analyst.get("target_low")))
                rec_key = analyst.get("recommendation", "N/A")
                rec_map = {"buy": "🟢 BUY", "strong_buy": "🟢🟢 STRONG BUY",
                           "hold": "⚪ HOLD", "sell": "🔴 SELL", "underperform": "🔴 UNDERPERFORM"}
                st.metric("Rekomendasi Analis", rec_map.get(rec_key, rec_key.upper()))
                st.metric("Jumlah Analis", analyst.get("analyst_count", "N/A"))
        else:
            st.info("Data target analis tidak tersedia")

    st.markdown("---")

    # Key metrics grid
    st.markdown("#### 📊 Metrik Keuangan Kunci")
    metric_groups = {
        "💎 Valuasi": ["P/E Ratio (TTM)", "P/E Forward", "P/B Ratio", "P/S Ratio", "EV/EBITDA"],
        "📈 Profitabilitas": ["ROE (%)", "ROA (%)", "Profit Margin (%)", "Operating Margin (%)", "Gross Margin (%)"],
        "🚀 Pertumbuhan": ["Revenue Growth (YoY %)", "Earnings Growth (YoY %)", "Quarterly Revenue Growth", "Quarterly Earnings Growth"],
        "💪 Kesehatan Keuangan": ["Current Ratio", "Quick Ratio", "Debt/Equity", "Total Debt (B)", "Free Cashflow (B)"],
        "💸 Per Saham & Dividen": ["EPS (TTM)", "EPS Forward", "Book Value/Share", "Dividend Yield (%)", "Payout Ratio (%)"],
    }

    for group_name, metric_keys in metric_groups.items():
        with st.expander(group_name, expanded=True):
            g_cols = st.columns(5)
            for i, key in enumerate(metric_keys):
                val = metrics.get(key)
                with g_cols[i % 5]:
                    if val is not None:
                        suffix = "%" if "%" in key or "Ratio" in key and False else ""
                        st.metric(key.replace(" (%)", "").replace(" (B)", " B").replace(" (M)", " M"),
                                  fmt_num(val, 2))
                    else:
                        st.metric(key.replace(" (%)", "").replace(" (B)", " B"), "N/A")

    # Financial charts
    st.markdown("---")
    st.markdown("#### 📉 Laporan Keuangan Historis")
    fig_fin = plot_financials(financials, ticker)
    if fig_fin.data:
        st.plotly_chart(fig_fin, use_container_width=True)
    else:
        st.info("Data laporan keuangan tidak tersedia")

    fig_ratio = plot_financial_ratios(metrics)
    if fig_ratio.data:
        st.plotly_chart(fig_ratio, use_container_width=True)

    # Company description
    desc = info.get("longBusinessSummary")
    if desc:
        st.markdown("---")
        with st.expander("📖 Tentang Perusahaan"):
            st.markdown(desc)


# ════════════════════════════════════════════════════════════════════════════════
# TAB 3: BERITA & SENTIMEN — masuk popup
# ════════════════════════════════════════════════════════════════════════════════
if False:
    st.markdown('<div class="section-header">📰 Berita & Analisis Sentimen</div>', unsafe_allow_html=True)

    if news:
        agg = aggregate_sentiment(news)

        # Sentiment summary
        col_s1, col_s2, col_s3, col_s4 = st.columns(4)
        with col_s1:
            st.metric("📊 Sentimen Keseluruhan", agg["label"])
        with col_s2:
            st.metric("🟢 Bullish", agg["bullish"])
        with col_s3:
            st.metric("🔴 Bearish", agg["bearish"])
        with col_s4:
            st.metric("⚪ Neutral", agg["neutral"])

        # Sentiment bar
        total = agg["total"]
        if total > 0:
            bull_pct = agg["bullish"] / total * 100
            bear_pct = agg["bearish"] / total * 100
            st.markdown(f"""
            <div style="background:#333;border-radius:8px;overflow:hidden;height:20px;margin:10px 0">
                <div style="display:inline-block;background:#26A69A;width:{bull_pct:.0f}%;height:100%"></div>
                <div style="display:inline-block;background:#666;width:{100-bull_pct-bear_pct:.0f}%;height:100%"></div>
                <div style="display:inline-block;background:#EF5350;width:{bear_pct:.0f}%;height:100%"></div>
            </div>
            <div style="display:flex;justify-content:space-between;font-size:0.8rem">
                <span style="color:#26A69A">🟢 Bullish {bull_pct:.0f}%</span>
                <span style="color:#EF5350">🔴 Bearish {bear_pct:.0f}%</span>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("---")

        # News by category
        bull_news = [a for a in news if a.get("sentiment", {}).get("label") == "Bullish"]
        bear_news = [a for a in news if a.get("sentiment", {}).get("label") == "Bearish"]
        neu_news = [a for a in news if a.get("sentiment", {}).get("label") == "Neutral"]

        tab_bull, tab_bear, tab_neu, tab_all = st.tabs([
            f"🟢 Bullish ({len(bull_news)})",
            f"🔴 Bearish ({len(bear_news)})",
            f"⚪ Neutral ({len(neu_news)})",
            f"📋 Semua ({len(news)})",
        ])

        with tab_bull:
            if bull_news:
                for a in bull_news:
                    render_news_card(a)
            else:
                st.info("Tidak ada berita bullish")

        with tab_bear:
            if bear_news:
                for a in bear_news:
                    render_news_card(a)
            else:
                st.info("Tidak ada berita bearish")

        with tab_neu:
            for a in neu_news:
                render_news_card(a)

        with tab_all:
            for a in news:
                render_news_card(a)

    else:
        st.warning("Tidak ada berita yang ditemukan untuk saham ini.")

    # Macro news
    st.markdown("---")
    st.markdown("#### 🌍 Berita Makro Ekonomi")
    with st.spinner("Memuat berita makro..."):
        macro_news = get_macro_news()

    if macro_news:
        macro_agg = aggregate_sentiment(macro_news)
        st.markdown(f"**Sentimen Makro:** {macro_agg['label']} (Skor: {macro_agg['score']:+.3f})")
        st.markdown(summarize_news_sentiment(macro_news, context="macro"))

        news_by_cat = {}
        for a in macro_news:
            cat = a.get("category", "Umum")
            news_by_cat.setdefault(cat, []).append(a)

        for cat, articles in news_by_cat.items():
            with st.expander(f"📌 {cat} ({len(articles)} berita)"):
                for a in articles:
                    render_news_card(a)


# ════════════════════════════════════════════════════════════════════════════════
# TAB 2: MAKRO EKONOMI — masuk popup
# ════════════════════════════════════════════════════════════════════════════════
if False:
    st.markdown('<div class="section-header">🌍 Analisis Makro & Mikro Ekonomi</div>', unsafe_allow_html=True)

    # Macro environment assessment
    env = macro_env.get("environment", "N/A")
    env_color = "#26A69A" if "ON" in env or "POSITIVE" in env else ("#EF5350" if "OFF" in env or "NEGATIVE" in env else "#FF9800")

    st.markdown(f"""<div style="background:rgba(0,0,0,0.3);border:2px solid {env_color};border-radius:12px;
        padding:20px;margin:10px 0">
        <h3 style="color:{env_color};margin:0">{env}</h3>
        <p style="color:#C9D1D9;margin:8px 0 0 0">{macro_env.get('description', '')}</p>
    </div>""", unsafe_allow_html=True)

    col_opp, col_risk = st.columns(2)
    with col_opp:
        st.markdown("#### ✅ Peluang")
        for o in macro_env.get("opportunities", []):
            st.markdown(f"- 🟢 {o}")
        if not macro_env.get("opportunities"):
            st.info("Tidak ada peluang signifikan terdeteksi")

    with col_risk:
        st.markdown("#### ⚠️ Risiko")
        for r in macro_env.get("risk_factors", []):
            st.markdown(f"- 🔴 {r}")
        if not macro_env.get("risk_factors"):
            st.info("Tidak ada risiko signifikan terdeteksi")

    st.markdown("---")

    # Global markets table
    col_m1, col_m2 = st.columns(2)

    with col_m1:
        st.markdown("#### 📈 Indeks Saham Global")
        if markets:
            rows = []
            for m in markets:
                pct = m.get("pct_change")
                rows.append({
                    "Pasar": m["name"],
                    "Perubahan (%)": f"{pct:+.2f}%" if pct is not None else "N/A",
                    "Arah": "▲" if (pct or 0) >= 0 else "▼",
                })
            df_markets = pd.DataFrame(rows)
            st.dataframe(df_markets, use_container_width=True, hide_index=True)

    with col_m2:
        st.markdown("#### 💱 Nilai Tukar")
        if currencies:
            rows = []
            for c in currencies:
                pct = c.get("pct_change")
                rows.append({
                    "Pasangan": c["name"],
                    "Harga": fmt_num(c.get("price"), 4),
                    "Perubahan (%)": f"{pct:+.2f}%" if pct is not None else "N/A",
                })
            st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

    st.markdown("---")

    # Commodities
    st.markdown("#### ⚡ Harga Komoditi")
    if commodities:
        cols = st.columns(min(len(commodities), 4))
        for i, c in enumerate(commodities):
            pct = c.get("pct_change")
            color = "#26A69A" if (pct or 0) >= 0 else "#EF5350"
            arrow = "▲" if (pct or 0) >= 0 else "▼"
            with cols[i % 4]:
                st.markdown(f"""<div class="metric-card" style="text-align:center">
                    <div style="font-size:0.85rem;color:#8B949E">{c['name']}</div>
                    <div style="font-size:1rem;font-weight:700">{fmt_num(c.get('price'), 2)}</div>
                    <div style="color:{color}">{arrow} {abs(pct or 0):.2f}%</div>
                </div>""", unsafe_allow_html=True)

    st.markdown("---")

    # Macro historical chart
    st.markdown("#### 📉 Performa Makro Historis")
    with st.spinner("Memuat data historis makro..."):
        macro_hist = get_macro_data_history(period=TIMEFRAMES[timeframe])

    if macro_hist:
        fig_macro = plot_macro_overview(macro_hist)
        st.plotly_chart(fig_macro, use_container_width=True)

        fig_corr = plot_correlation_heatmap(macro_hist)
        if fig_corr.data:
            st.plotly_chart(fig_corr, use_container_width=True)

    st.markdown("---")

    # Sector rotation
    st.markdown("#### 🔄 Rotasi Sektor")
    sector_rotation = get_sector_rotation_view()
    cols = st.columns(4)
    for col, (phase, data) in zip(cols, sector_rotation.items()):
        color_map = {"green": "#26A69A", "red": "#EF5350", "blue": "#2196F3", "orange": "#FF9800"}
        c = color_map.get(data["color"], "#8B949E")
        with col:
            st.markdown(f"""<div style="border:1px solid {c};border-radius:8px;padding:12px">
                <div style="color:{c};font-weight:700;margin-bottom:6px">{phase}</div>
                <div style="font-size:0.8rem;color:#8B949E;margin-bottom:8px">{data['description']}</div>
                {''.join([f'<span style="background:{c}22;color:{c};border-radius:4px;padding:2px 6px;margin:2px;display:inline-block;font-size:0.75rem">{s}</span>' for s in data['sectors']])}
            </div>""", unsafe_allow_html=True)

    st.markdown("---")

    # BI Rate context
    st.markdown("#### 🏦 Konteks BI Rate & Dampaknya")
    bi_ctx = get_bi_rate_context()
    st.info(f"📌 **{bi_ctx['current_rate_assumption']}**")
    for sector_name, impact in bi_ctx["impact"].items():
        st.markdown(f"- **{sector_name}**: {impact}")
    st.caption(f"*{bi_ctx['note']}*")

    st.markdown("---")

    # Economic calendar
    st.markdown("#### 📅 Kalender Ekonomi Penting")
    events = get_economic_calendar()
    df_events = pd.DataFrame(events)
    if not df_events.empty:
        def style_impact(val):
            if val == "High":
                return "color: #EF5350; font-weight: bold"
            elif val == "Medium":
                return "color: #FF9800"
            return ""
        st.dataframe(df_events.style.map(style_impact, subset=["impact"]),
                     use_container_width=True, hide_index=True)


# ════════════════════════════════════════════════════════════════════════════════
# TAB 8: AI ANALYSIS — masuk popup
# ════════════════════════════════════════════════════════════════════════════════
if False:
    st.markdown('<div class="section-header">🤖 Analisis AI (Powered by Claude)</div>', unsafe_allow_html=True)

    if st.session_state.ai_result:
        st.markdown(st.session_state.ai_result)
    else:
        st.info("""
        ### 🤖 Analisis AI Belum Dihasilkan

        Klik tombol **"Generate AI Analysis"** di sidebar untuk mendapatkan:
        - ✅ Rekomendasi trading komprehensif (BUY/SELL/HOLD)
        - 📊 Analisis teknikal mendalam dari Claude
        - 💰 Penilaian fundamental saham
        - 📰 Dampak berita dan sentimen pasar
        - 🌍 Faktor makro ekonomi yang relevan
        - 🎯 Entry point, target harga & stop loss
        - ⚠️ Risiko dan katalis utama

        > **Catatan:** Membutuhkan Anthropic API Key. Set `ANTHROPIC_API_KEY` di file `.env`
        """)

    # Quick summary without AI
    st.markdown("---")
    st.markdown("### 📋 Ringkasan Cepat (Tanpa AI)")

    col_t, col_f = st.columns(2)
    with col_t:
        st.markdown("**🔵 Teknikal:**")
        for key, val in signals.items():
            if not key.startswith("_"):
                icon = "🟢" if "BUY" in val.get("signal", "") else ("🔴" if "SELL" in val.get("signal", "") else "⚪")
                st.markdown(f"- {icon} **{key}**: {val.get('note', '')}")

    with col_f:
        st.markdown("**💰 Fundamental:**")
        for note in fund_score.get("notes", []):
            st.markdown(f"- {note}")

        st.markdown("**📰 Sentimen Berita:**")
        if news:
            agg = aggregate_sentiment(news)
            st.markdown(summarize_news_sentiment(news))
        else:
            st.markdown("- Tidak ada data berita")


# ════════════════════════════════════════════════════════════════════════════════
# TAB 1: PASAR GLOBAL
# ════════════════════════════════════════════════════════════════════════════════
with tabs[1]:
    st.markdown('<div class="section-header">🗺️ Peta Pasar Global</div>', unsafe_allow_html=True)

    # Full market table
    col_idx, col_comm = st.columns(2)

    with col_idx:
        st.markdown("#### 🌐 Semua Indeks Saham")
        if markets:
            data = []
            for m in markets:
                pct = m.get("pct_change")
                data.append({
                    "Nama": m["name"],
                    "Ticker": m["ticker"],
                    "Harga": fmt_num(m.get("price"), 2),
                    "Δ%": f"{pct:+.2f}%" if pct is not None else "N/A",
                })
            df_m = pd.DataFrame(data)
            st.dataframe(df_m, use_container_width=True, hide_index=True)

    with col_comm:
        st.markdown("#### ⚡ Semua Komoditi")
        if commodities:
            data = []
            for c in commodities:
                pct = c.get("pct_change")
                data.append({
                    "Komoditi": c["name"],
                    "Harga": fmt_num(c.get("price"), 3),
                    "Δ%": f"{pct:+.2f}%" if pct is not None else "N/A",
                })
            st.dataframe(pd.DataFrame(data), use_container_width=True, hide_index=True)

    st.markdown("---")

    # All currencies
    st.markdown("#### 💱 Semua Kurs Mata Uang")
    if currencies:
        data = []
        for c in currencies:
            pct = c.get("pct_change")
            data.append({
                "Pasangan": c["name"],
                "Harga": fmt_num(c.get("price"), 4),
                "Δ%": f"{pct:+.2f}%" if pct is not None else "N/A",
            })
        st.dataframe(pd.DataFrame(data), use_container_width=True, hide_index=True)

    st.markdown("---")

    # IDX Sector performance
    st.markdown("#### 📊 Performa Sektor IDX")
    with st.spinner("Menghitung performa sektor..."):
        from modules.data_fetcher import get_sector_performance
        sector_data = []
        for sector_name, tickers in SECTOR_MAP.items():
            df_sect = get_sector_performance(tickers[:3], period="1mo")
            if not df_sect.empty:
                avg_ret = df_sect["return"].mean()
                sector_data.append({"Sektor": sector_name, "Return 1 Bulan (%)": round(avg_ret, 2)})

    if sector_data:
        df_sect = pd.DataFrame(sector_data).sort_values("Return 1 Bulan (%)", ascending=False)
        fig_sect = go.Figure(go.Bar(
            x=df_sect["Sektor"],
            y=df_sect["Return 1 Bulan (%)"],
            marker_color=["#26A69A" if v >= 0 else "#EF5350" for v in df_sect["Return 1 Bulan (%)"]],
            text=[f"{v:+.2f}%" for v in df_sect["Return 1 Bulan (%)"]],
            textposition="outside",
        ))
        fig_sect.update_layout(
            title="Performa Sektor IDX (1 Bulan)",
            template="plotly_dark",
            height=400,
            paper_bgcolor="#0E1117",
            plot_bgcolor="#161B22",
        )
        st.plotly_chart(fig_sect, use_container_width=True)

    # Disclaimer
    st.markdown("---")
    st.markdown("""
    <div style="background:#161B22;border:1px solid #30363D;border-radius:8px;padding:16px;margin:10px 0">
        <h4 style="color:#FF9800">⚠️ Disclaimer</h4>
        <p style="color:#8B949E;font-size:0.9rem">
        Informasi yang disajikan dalam aplikasi ini hanya untuk tujuan edukasi dan referensi semata.
        Bukan merupakan rekomendasi investasi. Selalu lakukan riset mandiri (<i>due diligence</i>) sebelum
        membuat keputusan investasi. Investasi di pasar modal mengandung risiko kerugian.
        Kinerja masa lalu tidak menjamin kinerja di masa mendatang.
        </p>
    </div>
    """, unsafe_allow_html=True)
