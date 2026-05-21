"""
Advanced Technical Analysis
-----------------------------
Model analisis teknikal lanjutan:
  - Auto Fibonacci Retracement & Extension
  - RSI & MACD Divergence (Regular + Hidden)
  - Volume Profile (VPVR)
  - Multi-Timeframe Trend Analysis
  - Candlestick Pattern Recognition
  - Wyckoff Phase Detection
  - Market Structure Analysis
"""

import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from modules.smc_analysis import find_swing_points


# ══════════════════════════════════════════════════════════════════════════════
# AUTO FIBONACCI RETRACEMENT & EXTENSION
# ══════════════════════════════════════════════════════════════════════════════

FIBO_LEVELS = [0.0, 0.236, 0.382, 0.5, 0.618, 0.705, 0.786, 1.0]
FIBO_EXT    = [1.272, 1.414, 1.618, 2.0, 2.618]
FIBO_COLORS = {
    0.0:   "#FFFFFF", 0.236: "#FF9800", 0.382: "#4CAF50",
    0.5:   "#2196F3", 0.618: "#E91E63", 0.705: "#9C27B0",
    0.786: "#F44336", 1.0:   "#FFFFFF",
    1.272: "#00BCD4", 1.414: "#8BC34A", 1.618: "#FFD700",
    2.0:   "#FF5722", 2.618: "#FF1744",
}


def auto_fibonacci(df: pd.DataFrame, lookback: int = 100) -> dict:
    """
    Otomatis deteksi swing high/low terkini dan hitung Fibonacci levels.
    """
    data = df.tail(lookback)
    sw   = find_swing_points(data, left=5, right=5)

    highs = sw[sw["swing_high"].notna()].tail(3)
    lows  = sw[sw["swing_low"].notna()].tail(3)

    if highs.empty or lows.empty:
        return {}

    swing_high_val = highs["swing_high"].iloc[-1]
    swing_high_idx = highs.index[-1]
    swing_low_val  = lows["swing_low"].iloc[-1]
    swing_low_idx  = lows.index[-1]

    # Tentukan arah tren: jika swing high lebih baru → tren naik, hitung dari bawah
    if swing_high_idx > swing_low_idx:
        # Uptrend: retracement dari high ke low (hitung dari bawah)
        direction = "uptrend"
        high = swing_high_val
        low  = swing_low_val
    else:
        # Downtrend: retracement dari high ke low
        direction = "downtrend"
        high = swing_high_val
        low  = swing_low_val

    rng    = high - low
    levels = {}

    for lvl in FIBO_LEVELS:
        if direction == "uptrend":
            price = high - rng * lvl
        else:
            price = low + rng * lvl
        levels[lvl] = price

    ext_levels = {}
    for ext in FIBO_EXT:
        if direction == "uptrend":
            price = low - rng * (ext - 1)
        else:
            price = high + rng * (ext - 1)
        ext_levels[ext] = price

    current = data["Close"].iloc[-1]

    # Nearest support & resistance dari Fibonacci
    all_levels = {**levels, **ext_levels}
    supports    = {k: v for k, v in all_levels.items() if v < current}
    resistances = {k: v for k, v in all_levels.items() if v > current}

    nearest_sup = max(supports.items(),  key=lambda x: x[1]) if supports    else None
    nearest_res = min(resistances.items(), key=lambda x: x[1]) if resistances else None

    return {
        "direction":     direction,
        "swing_high":    swing_high_val,
        "swing_high_idx": swing_high_idx,
        "swing_low":     swing_low_val,
        "swing_low_idx": swing_low_idx,
        "levels":        levels,
        "extensions":    ext_levels,
        "current":       current,
        "nearest_support":    nearest_sup,
        "nearest_resistance": nearest_res,
    }


def plot_fibonacci(df: pd.DataFrame, fib: dict, ticker: str) -> go.Figure:
    if not fib:
        return go.Figure()

    fig = go.Figure()

    fig.add_trace(go.Candlestick(
        x=df.index, open=df["Open"], high=df["High"],
        low=df["Low"], close=df["Close"], name="Harga",
        increasing_line_color="#26A69A", decreasing_line_color="#EF5350",
    ))

    x_start = df.index[max(0, len(df) - 80)]
    x_end   = df.index[-1]

    all_levels = {**fib["levels"], **fib["extensions"]}
    for lvl, price in all_levels.items():
        color = FIBO_COLORS.get(lvl, "#888")
        is_ext = lvl in FIBO_EXT
        dash   = "dot" if is_ext else "solid"
        width  = 0.8 if is_ext else 1.2

        fig.add_shape(type="line",
            x0=x_start, x1=x_end, y0=price, y1=price,
            line=dict(color=color, width=width, dash=dash))

        label = f"{'EXT' if is_ext else 'FIB'} {lvl:.3f} — {price:.2f}"
        fig.add_annotation(x=x_end, y=price, text=label,
            showarrow=False, xanchor="right",
            font=dict(size=8, color=color))

    # Swing markers
    fig.add_trace(go.Scatter(
        x=[fib["swing_high_idx"]], y=[fib["swing_high"]],
        mode="markers+text", marker=dict(symbol="triangle-down", size=12, color="#EF5350"),
        text=["SH"], textposition="top center", name="Swing High",
    ))
    fig.add_trace(go.Scatter(
        x=[fib["swing_low_idx"]], y=[fib["swing_low"]],
        mode="markers+text", marker=dict(symbol="triangle-up", size=12, color="#26A69A"),
        text=["SL"], textposition="bottom center", name="Swing Low",
    ))

    fig.update_layout(
        title=f"<b>{ticker}</b> — Auto Fibonacci ({fib['direction']})",
        height=600, template="plotly_dark",
        xaxis_rangeslider_visible=False,
        paper_bgcolor="#0E1117", plot_bgcolor="#161B22",
    )
    return fig


# ══════════════════════════════════════════════════════════════════════════════
# DIVERGENCE ANALYSIS
# ══════════════════════════════════════════════════════════════════════════════

def find_divergences(df: pd.DataFrame) -> list:
    """
    Regular Divergence  → pembalikan arah
    Hidden Divergence   → kelanjutan tren
    """
    if "RSI" not in df.columns or len(df) < 30:
        return []

    divs  = []
    close = df["Close"]
    rsi   = df["RSI"]
    macd  = df.get("MACD", pd.Series(dtype=float))

    window = 5

    for i in range(window * 2, len(df) - window):
        # Cari local extrema harga dan RSI
        price_window_l = close.iloc[i - window : i + window + 1]
        rsi_window_l   = rsi.iloc[i  - window : i + window + 1]

        # ── BULLISH Regular: price lower low, RSI higher low (reversal bullish)
        if close.iloc[i] == price_window_l.min() and rsi.iloc[i] == rsi_window_l.min():
            prev_lows_p = [close.iloc[j] for j in range(max(0, i - 30), i - window)
                           if close.iloc[j] <= close.iloc[j - 1] and close.iloc[j] <= close.iloc[j + 1]]
            prev_lows_r = [rsi.iloc[j]   for j in range(max(0, i - 30), i - window)
                           if rsi.iloc[j]   <= rsi.iloc[j - 1]   and rsi.iloc[j]   <= rsi.iloc[j + 1]]

            if prev_lows_p and prev_lows_r:
                if close.iloc[i] < min(prev_lows_p) and rsi.iloc[i] > min(prev_lows_r):
                    divs.append({
                        "type":      "Bullish Regular Divergence",
                        "indicator": "RSI",
                        "index":     df.index[i],
                        "price":     close.iloc[i],
                        "rsi":       rsi.iloc[i],
                        "color":     "#26A69A",
                        "signal":    "BUY",
                        "desc":      "Harga lower low, RSI higher low → potensi reversal naik",
                    })

        # ── BEARISH Regular: price higher high, RSI lower high (reversal bearish)
        if close.iloc[i] == price_window_l.max() and rsi.iloc[i] == rsi_window_l.max():
            prev_highs_p = [close.iloc[j] for j in range(max(0, i - 30), i - window)
                            if close.iloc[j] >= close.iloc[j - 1] and close.iloc[j] >= close.iloc[j + 1]]
            prev_highs_r = [rsi.iloc[j]   for j in range(max(0, i - 30), i - window)
                            if rsi.iloc[j]   >= rsi.iloc[j - 1]   and rsi.iloc[j]   >= rsi.iloc[j + 1]]

            if prev_highs_p and prev_highs_r:
                if close.iloc[i] > max(prev_highs_p) and rsi.iloc[i] < max(prev_highs_r):
                    divs.append({
                        "type":      "Bearish Regular Divergence",
                        "indicator": "RSI",
                        "index":     df.index[i],
                        "price":     close.iloc[i],
                        "rsi":       rsi.iloc[i],
                        "color":     "#EF5350",
                        "signal":    "SELL",
                        "desc":      "Harga higher high, RSI lower high → potensi reversal turun",
                    })

    return divs[-6:]


# ══════════════════════════════════════════════════════════════════════════════
# VOLUME PROFILE (VPVR)
# ══════════════════════════════════════════════════════════════════════════════

def calculate_volume_profile(df: pd.DataFrame, bins: int = 30) -> dict:
    """
    Volume Profile: distribusi volume per level harga.
    POC = Point of Control (level harga dengan volume terbanyak)
    VAH = Value Area High (70% volume)
    VAL = Value Area Low
    """
    if df.empty or "Volume" not in df.columns:
        return {}

    price_min = df["Low"].min()
    price_max = df["High"].max()
    price_bins = np.linspace(price_min, price_max, bins + 1)
    vol_profile = np.zeros(bins)

    for _, row in df.iterrows():
        # Distribusikan volume candle ke bin harga yang dicakupnya
        candle_low  = row["Low"]
        candle_high = row["High"]
        candle_vol  = row["Volume"]

        for b in range(bins):
            bin_low  = price_bins[b]
            bin_high = price_bins[b + 1]
            overlap  = max(0, min(candle_high, bin_high) - max(candle_low, bin_low))
            if overlap > 0 and (candle_high - candle_low) > 0:
                vol_profile[b] += candle_vol * overlap / (candle_high - candle_low)

    bin_centers = (price_bins[:-1] + price_bins[1:]) / 2
    poc_idx     = np.argmax(vol_profile)
    poc         = bin_centers[poc_idx]

    # Value Area (70% total volume)
    total_vol  = vol_profile.sum()
    target_vol = total_vol * 0.70
    cum_vol    = 0
    vah_idx    = poc_idx
    val_idx    = poc_idx

    for step in range(1, bins):
        up_vol   = vol_profile[min(poc_idx + step, bins - 1)]
        down_vol = vol_profile[max(poc_idx - step, 0)]
        if up_vol >= down_vol:
            cum_vol += up_vol
            vah_idx  = min(poc_idx + step, bins - 1)
        else:
            cum_vol += down_vol
            val_idx  = max(poc_idx - step, 0)
        if cum_vol >= target_vol:
            break

    return {
        "bins":        bin_centers.tolist(),
        "volumes":     vol_profile.tolist(),
        "poc":         poc,
        "vah":         bin_centers[vah_idx],
        "val":         bin_centers[val_idx],
        "max_vol":     vol_profile.max(),
        "current":     df["Close"].iloc[-1],
    }


def plot_volume_profile(df: pd.DataFrame, vp: dict, ticker: str) -> go.Figure:
    if not vp:
        return go.Figure()

    fig = make_subplots(rows=1, cols=2, column_widths=[0.8, 0.2],
                        shared_yaxes=True, horizontal_spacing=0.01)

    # Candlestick
    fig.add_trace(go.Candlestick(
        x=df.index, open=df["Open"], high=df["High"],
        low=df["Low"], close=df["Close"],
        increasing_line_color="#26A69A", decreasing_line_color="#EF5350",
        name="Harga",
    ), row=1, col=1)

    # POC / VAH / VAL lines
    for level, label, color, dash in [
        (vp["poc"], "POC", "#FFD700", "solid"),
        (vp["vah"], "VAH", "#2196F3", "dash"),
        (vp["val"], "VAL", "#E91E63", "dash"),
    ]:
        fig.add_hline(y=level, line=dict(color=color, width=1.2, dash=dash),
                      annotation_text=f"{label} {level:.2f}",
                      annotation_font=dict(color=color, size=9),
                      row=1, col=1)

    # Volume Profile bars
    poc   = vp["poc"]
    bins  = vp["bins"]
    vols  = vp["volumes"]
    max_v = vp["max_vol"]
    bar_colors = []
    for b in bins:
        if abs(b - poc) < (bins[1] - bins[0]) * 0.5:
            bar_colors.append("#FFD700")
        elif b >= vp["val"] and b <= vp["vah"]:
            bar_colors.append("#2196F3")
        else:
            bar_colors.append("#555")

    normalized = [v / max_v for v in vols]
    fig.add_trace(go.Bar(
        x=normalized, y=bins,
        orientation="h",
        marker_color=bar_colors,
        opacity=0.8,
        name="Volume Profile",
        showlegend=False,
    ), row=1, col=2)

    fig.update_layout(
        title=f"<b>{ticker}</b> — Volume Profile (VPVR)",
        height=600, template="plotly_dark",
        xaxis_rangeslider_visible=False,
        paper_bgcolor="#0E1117", plot_bgcolor="#161B22",
        bargap=0.05,
    )
    return fig


# ══════════════════════════════════════════════════════════════════════════════
# CANDLESTICK PATTERN RECOGNITION
# ══════════════════════════════════════════════════════════════════════════════

def detect_candlestick_patterns(df: pd.DataFrame) -> list:
    """Deteksi pola candlestick klasik yang relevan untuk trading."""
    patterns = []
    data = df.tail(10)

    for i in range(2, len(data)):
        c  = data.iloc[i]      # current
        p  = data.iloc[i - 1]  # previous
        pp = data.iloc[i - 2]  # 2 bars ago

        o, h, l, cl = c["Open"], c["High"], c["Low"], c["Close"]
        body   = abs(cl - o)
        range_ = h - l
        avg_body = data["Close"].sub(data["Open"]).abs().mean()

        if range_ == 0:
            continue

        # ── Doji ──
        if body <= range_ * 0.1:
            patterns.append({"name": "Doji ⚖️", "index": data.index[i],
                             "signal": "NEUTRAL", "desc": "Indikasi ketidakpastian pasar",
                             "color": "#FF9800"})

        # ── Hammer / Hanging Man ──
        lower_wick = min(o, cl) - l
        upper_wick = h - max(o, cl)
        if lower_wick >= body * 2 and upper_wick <= body * 0.5:
            if cl > p["Close"]:
                patterns.append({"name": "Hammer 🔨", "index": data.index[i],
                                 "signal": "BUY", "desc": "Potensi reversal naik setelah downtrend",
                                 "color": "#26A69A"})
            else:
                patterns.append({"name": "Hanging Man 📊", "index": data.index[i],
                                 "signal": "SELL", "desc": "Potensi reversal turun setelah uptrend",
                                 "color": "#EF5350"})

        # ── Shooting Star ──
        if upper_wick >= body * 2 and lower_wick <= body * 0.3 and cl < o:
            patterns.append({"name": "Shooting Star ⭐", "index": data.index[i],
                             "signal": "SELL", "desc": "Potensi reversal turun",
                             "color": "#EF5350"})

        # ── Bullish Engulfing ──
        if (cl > o and p["Close"] < p["Open"]
                and cl > p["Open"] and o < p["Close"]):
            patterns.append({"name": "Bullish Engulfing 🟢", "index": data.index[i],
                             "signal": "BUY", "desc": "Candle bullish menelan candle bearish",
                             "color": "#26A69A"})

        # ── Bearish Engulfing ──
        if (cl < o and p["Close"] > p["Open"]
                and cl < p["Open"] and o > p["Close"]):
            patterns.append({"name": "Bearish Engulfing 🔴", "index": data.index[i],
                             "signal": "SELL", "desc": "Candle bearish menelan candle bullish",
                             "color": "#EF5350"})

        # ── Morning Star (3 candle) ──
        if (pp["Close"] < pp["Open"]                      # bearish
                and abs(p["Close"] - p["Open"]) < avg_body * 0.5  # doji/small
                and cl > o                                 # bullish
                and cl > (pp["Open"] + pp["Close"]) / 2): # recover >50%
            patterns.append({"name": "Morning Star 🌅", "index": data.index[i],
                             "signal": "BUY", "desc": "Pola pembalikan bullish 3 candle",
                             "color": "#26A69A"})

        # ── Evening Star (3 candle) ──
        if (pp["Close"] > pp["Open"]
                and abs(p["Close"] - p["Open"]) < avg_body * 0.5
                and cl < o
                and cl < (pp["Open"] + pp["Close"]) / 2):
            patterns.append({"name": "Evening Star 🌆", "index": data.index[i],
                             "signal": "SELL", "desc": "Pola pembalikan bearish 3 candle",
                             "color": "#EF5350"})

        # ── Marubozu ──
        if body >= avg_body * 2 and lower_wick <= body * 0.05 and upper_wick <= body * 0.05:
            if cl > o:
                patterns.append({"name": "Bullish Marubozu 🟩", "index": data.index[i],
                                 "signal": "BUY", "desc": "Candle bullish kuat tanpa shadow",
                                 "color": "#26A69A"})
            else:
                patterns.append({"name": "Bearish Marubozu 🟥", "index": data.index[i],
                                 "signal": "SELL", "desc": "Candle bearish kuat tanpa shadow",
                                 "color": "#EF5350"})

    return patterns[-5:]


# ══════════════════════════════════════════════════════════════════════════════
# WYCKOFF PHASE DETECTION (simplified)
# ══════════════════════════════════════════════════════════════════════════════

def detect_wyckoff_phase(df: pd.DataFrame) -> dict:
    """
    Wyckoff Method: 4 fase utama pasar
    Accumulation → Markup → Distribution → Markdown
    """
    if len(df) < 60:
        return {}

    data  = df.tail(60)
    close = data["Close"]
    vol   = data["Volume"]

    # Indikator sederhana
    price_trend_20  = close.iloc[-1] / close.iloc[-20] - 1
    price_trend_60  = close.iloc[-1] / close.iloc[0]   - 1
    vol_trend       = vol.tail(10).mean() / vol.head(10).mean() - 1
    volatility      = close.pct_change().std() * 100
    price_range_pct = (data["High"].max() - data["Low"].min()) / data["Low"].min() * 100
    is_sideways     = price_range_pct < 8 and abs(price_trend_20) < 0.03

    if is_sideways and vol_trend < 0:
        phase = "Accumulation (Phase B/C)"
        desc  = "Smart money sedang akumulasi. Volume rendah, harga sideways → potensi markup segera."
        action = "Pantau tanda spring/test. Entry saat volume naik & harga break resistance."
        color  = "#26A69A"
    elif price_trend_60 > 0.15 and price_trend_20 > 0:
        phase  = "Markup (Uptrend)"
        desc   = "Fase kenaikan harga. Smart money sudah akumulasi, retail mulai masuk."
        action = "Ikuti tren, buy on pullback ke support. Waspada tanda distribusi di atas."
        color  = "#4CAF50"
    elif is_sideways and vol_trend > 0.2:
        phase  = "Distribution (Phase B/C)"
        desc   = "Smart money sedang distribusi. Volume tinggi tapi harga sideways → potensi markdown."
        action = "Kurangi posisi long. Persiapkan short saat harga break support."
        color  = "#FF9800"
    elif price_trend_60 < -0.15 and price_trend_20 < 0:
        phase  = "Markdown (Downtrend)"
        desc   = "Fase penurunan harga. Smart money sudah exit, retail panik jual."
        action = "Hindari buy. Tunggu tanda akumulasi ulang di support kuat."
        color  = "#EF5350"
    else:
        phase  = "Transition / Uncertain"
        desc   = "Fase transisi. Butuh konfirmasi lebih lanjut."
        action = "Tunggu konfirmasi arah sebelum entry."
        color  = "#9E9E9E"

    return {
        "phase":          phase,
        "description":    desc,
        "action":         action,
        "color":          color,
        "price_trend_20": round(price_trend_20 * 100, 2),
        "price_trend_60": round(price_trend_60 * 100, 2),
        "vol_trend":      round(vol_trend * 100, 2),
        "volatility":     round(volatility, 2),
        "is_sideways":    is_sideways,
    }


# ══════════════════════════════════════════════════════════════════════════════
# MULTI-TIMEFRAME TREND (MTF)
# ══════════════════════════════════════════════════════════════════════════════

def multi_timeframe_bias(df_daily: pd.DataFrame) -> dict:
    """
    Simulasi MTF dari data daily:
    - Weekly trend  (MA 20 weekly ≈ MA 100 daily)
    - Daily trend   (MA 20 daily)
    - 4H trend      (MA 20 × 4H ≈ MA 5 daily)
    """
    close = df_daily["Close"]
    result = {}

    timeframes = {
        "Weekly (MA100)":   close.rolling(100).mean(),
        "Daily (MA20)":     close.rolling(20).mean(),
        "4H (MA5)":         close.rolling(5).mean(),
    }

    cur = close.iloc[-1]
    overall_bull = 0

    for tf, ma in timeframes.items():
        last_ma = ma.iloc[-1]
        if pd.isna(last_ma):
            continue
        if cur > last_ma:
            result[tf] = {"trend": "Bullish ▲", "ma": round(last_ma, 2), "color": "#26A69A"}
            overall_bull += 1
        else:
            result[tf] = {"trend": "Bearish ▼", "ma": round(last_ma, 2), "color": "#EF5350"}

    total = len(result)
    if total == 0:
        result["overall"] = {"bias": "N/A", "color": "#888"}
    elif overall_bull == total:
        result["overall"] = {"bias": "FULL BULLISH 🟢🟢🟢", "color": "#26A69A"}
    elif overall_bull >= total * 0.6:
        result["overall"] = {"bias": "BULLISH 🟢", "color": "#4CAF50"}
    elif overall_bull == 0:
        result["overall"] = {"bias": "FULL BEARISH 🔴🔴🔴", "color": "#EF5350"}
    elif overall_bull <= total * 0.4:
        result["overall"] = {"bias": "BEARISH 🔴", "color": "#F44336"}
    else:
        result["overall"] = {"bias": "MIXED ⚪", "color": "#FF9800"}

    return result
