"""
Astronacci Analysis Module
==========================
Implementasi metode analisis Astronacci International:
- Fibonacci Retracement & Extension
- Astronacci Cycle (siklus berbasis Fibonacci)
- Elliott Wave Count sederhana
- Fibonacci Time Zones
- Fibonacci Fan Lines
- Level Target berbasis Golden Ratio
"""

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from typing import Dict, List, Tuple, Optional

# ── Konstanta Fibonacci ───────────────────────────────────────────────────────
PHI = 1.618033988749895  # Golden Ratio

FIB_RETRACEMENT_LEVELS = {
    "0.0%":   0.000,
    "23.6%":  0.236,
    "38.2%":  0.382,
    "50.0%":  0.500,
    "61.8%":  0.618,
    "78.6%":  0.786,
    "88.6%":  0.886,
    "100%":   1.000,
}

FIB_EXTENSION_LEVELS = {
    "100%":   1.000,
    "127.2%": 1.272,
    "138.2%": 1.382,
    "161.8%": 1.618,
    "200%":   2.000,
    "261.8%": 2.618,
    "423.6%": 4.236,
}

# Fibonacci sequence untuk Astronacci Cycle
FIB_SEQUENCE = [3, 5, 8, 13, 21, 34, 55, 89, 144, 233]

# Warna level Fibonacci
FIB_COLORS = {
    "0.0%":   "#555555",
    "23.6%":  "#4FC3F7",
    "38.2%":  "#29B6F6",
    "50.0%":  "#FFD700",
    "61.8%":  "#FF9800",  # Golden Ratio — level paling kuat
    "78.6%":  "#F44336",
    "88.6%":  "#B71C1C",
    "100%":   "#555555",
    "127.2%": "#26A69A",
    "138.2%": "#2E7D32",
    "161.8%": "#00E676",  # Golden Ratio Extension — target utama
    "200%":   "#69F0AE",
    "261.8%": "#B9F6CA",
    "423.6%": "#CCFF90",
}


def _find_swing_points(df: pd.DataFrame, lookback: int = 10) -> Tuple[pd.Series, pd.Series]:
    """Temukan swing high dan swing low dalam data."""
    highs = df["High"].values
    lows  = df["Low"].values
    n     = len(df)

    swing_highs = []
    swing_lows  = []

    for i in range(lookback, n - lookback):
        window_h = highs[i - lookback: i + lookback + 1]
        window_l = lows[i - lookback: i + lookback + 1]
        if highs[i] == max(window_h):
            swing_highs.append((i, highs[i]))
        if lows[i] == min(window_l):
            swing_lows.append((i, lows[i]))

    return swing_highs, swing_lows


def calculate_fibonacci_retracement(df: pd.DataFrame) -> Dict:
    """
    Hitung level Fibonacci Retracement dari swing high & low terbaru.
    Metode: cari swing high/low terakhir yang signifikan.
    """
    if df.empty or len(df) < 20:
        return {}

    recent = df.tail(120)  # Gunakan 120 bar terakhir
    swing_high = recent["High"].max()
    swing_low  = recent["Low"].min()
    idx_high   = recent["High"].idxmax()
    idx_low    = recent["Low"].idxmin()

    # Tentukan arah tren (untuk menentukan retracement vs extension)
    is_uptrend = idx_low < idx_high  # Low dulu baru High = uptrend

    price_range = swing_high - swing_low
    levels = {}

    if is_uptrend:
        # Retracement dari High ke bawah
        for label, ratio in FIB_RETRACEMENT_LEVELS.items():
            levels[label] = swing_high - (price_range * ratio)
        direction = "uptrend"
        ext_levels = {}
        for label, ratio in FIB_EXTENSION_LEVELS.items():
            ext_levels[label] = swing_low + (price_range * ratio)
    else:
        # Downtrend — retracement dari Low ke atas
        for label, ratio in FIB_RETRACEMENT_LEVELS.items():
            levels[label] = swing_low + (price_range * ratio)
        direction = "downtrend"
        ext_levels = {}
        for label, ratio in FIB_EXTENSION_LEVELS.items():
            ext_levels[label] = swing_high - (price_range * ratio)

    current_price = float(df["Close"].iloc[-1])

    # Tentukan posisi harga saat ini
    level_vals = sorted(levels.values())
    nearest_support    = max([v for v in level_vals if v <= current_price], default=None)
    nearest_resistance = min([v for v in level_vals if v > current_price], default=None)

    # Tentukan zona (Premium / Discount ala Astronacci)
    mid_price = (swing_high + swing_low) / 2
    zone = "Premium Zone 🔴" if current_price > mid_price else "Discount Zone 🟢"

    # Hitung fibonacci target utama (golden ratio)
    golden_target   = swing_low + (price_range * 1.618) if is_uptrend else swing_high - (price_range * 1.618)
    golden_support  = levels.get("61.8%")
    golden_ext      = ext_levels.get("161.8%")

    return {
        "retracement":        levels,
        "extension":          ext_levels,
        "swing_high":         swing_high,
        "swing_low":          swing_low,
        "direction":          direction,
        "zone":               zone,
        "nearest_support":    nearest_support,
        "nearest_resistance": nearest_resistance,
        "golden_target":      golden_target,
        "golden_support":     golden_support,
        "golden_ext_161":     golden_ext,
        "price_range":        price_range,
        "current_price":      current_price,
        "is_uptrend":         is_uptrend,
    }


def calculate_astronacci_cycles(df: pd.DataFrame) -> Dict:
    """
    Hitung Astronacci Cycle — siklus waktu berbasis Fibonacci.
    Identifikasi bar-bar penting berdasarkan jarak Fibonacci dari titik pivot terakhir.
    """
    if df.empty or len(df) < 20:
        return {}

    n = len(df)
    dates = df.index.tolist()
    closes = df["Close"].values

    # Cari pivot point terakhir (swing high atau low yang paling baru)
    tail_size = min(60, n)
    high_pos = int(df["High"].tail(tail_size).values.argmax()) + (n - tail_size)
    low_pos  = int(df["Low"].tail(tail_size).values.argmin())  + (n - tail_size)

    pivot_pos = max(high_pos, low_pos)
    pivot_date = dates[pivot_pos] if pivot_pos < len(dates) else dates[-1]
    pivot_type = "High" if high_pos > low_pos else "Low"
    pivot_price = float(df["High"].iloc[pivot_pos] if pivot_type == "High" else df["Low"].iloc[pivot_pos])

    # Hitung siklus Fibonacci dari pivot
    cycle_bars = {}
    for fib in FIB_SEQUENCE:
        target_pos = pivot_pos + fib
        if target_pos < n:
            target_date = dates[target_pos]
            target_close = float(closes[target_pos])
            cycle_bars[fib] = {
                "bars_from_pivot": fib,
                "date": target_date,
                "price": target_close,
                "passed": True,
            }
        else:
            bars_remaining = target_pos - n + 1
            cycle_bars[fib] = {
                "bars_from_pivot": fib,
                "bars_remaining": bars_remaining,
                "passed": False,
            }

    # Cycle yang akan datang (belum dilewati)
    upcoming_cycles = {k: v for k, v in cycle_bars.items() if not v.get("passed", True)}
    next_cycle = min(upcoming_cycles.items(), key=lambda x: x[1].get("bars_remaining", 999)) if upcoming_cycles else None

    return {
        "pivot_pos":       pivot_pos,
        "pivot_date":      pivot_date,
        "pivot_type":      pivot_type,
        "pivot_price":     pivot_price,
        "cycles":          cycle_bars,
        "upcoming":        upcoming_cycles,
        "next_cycle":      next_cycle,
        "fib_sequence":    FIB_SEQUENCE,
        "total_bars":      n,
    }


def detect_elliott_wave(df: pd.DataFrame) -> Dict:
    """
    Deteksi pola Elliott Wave sederhana.
    Identifikasi: Wave 1-5 (impulsif) atau Wave A-B-C (korektif)
    """
    if df.empty or len(df) < 50:
        return {"wave_count": "Insufficient data", "pattern": "Unknown"}

    closes = df["Close"].values
    n = len(closes)
    recent = closes[-60:]  # Analisis 60 bar terakhir

    # Cari extrema lokal
    extrema = []
    for i in range(2, len(recent) - 2):
        if recent[i] > recent[i-1] and recent[i] > recent[i-2] and recent[i] > recent[i+1] and recent[i] > recent[i+2]:
            extrema.append(("H", i, recent[i]))
        elif recent[i] < recent[i-1] and recent[i] < recent[i-2] and recent[i] < recent[i+1] and recent[i] < recent[i+2]:
            extrema.append(("L", i, recent[i]))

    # Deduplicate — hapus yang terlalu dekat
    filtered = []
    min_gap = 5
    for ext in extrema:
        if not filtered or ext[1] - filtered[-1][1] >= min_gap:
            filtered.append(ext)

    # Identifikasi pattern berdasarkan alternating H-L
    alternating = []
    for i, ext in enumerate(filtered):
        if i == 0:
            alternating.append(ext)
        elif ext[0] != alternating[-1][0]:  # Alternating H dan L
            alternating.append(ext)

    wave_count = len(alternating)

    # Tentukan fase
    current_price = float(closes[-1])

    if wave_count >= 5:
        last_5 = alternating[-5:]
        if last_5[0][0] == "L":  # Dimulai dari Low = uptrend impulsive
            wave_labels = ["Wave 1 End", "Wave 2 End", "Wave 3 End", "Wave 4 End", "Wave 5 End"]
            pattern = "5-Wave Impulsive (Uptrend)"
            outlook = "Bearish" if last_5[4][0] == "H" else "Bullish"
        else:  # Dimulai dari High = downtrend
            wave_labels = ["Wave A End", "Wave B End", "Wave C End", "Wave D End", "Wave E End"]
            pattern = "5-Wave Corrective"
            outlook = "Bullish" if last_5[4][0] == "L" else "Bearish"

        waves = []
        for i, (label, (t, idx, price)) in enumerate(zip(wave_labels, last_5)):
            waves.append({"label": label, "price": price, "idx": idx})

    elif wave_count >= 3:
        last_3 = alternating[-3:]
        if last_3[0][0] == "L":
            pattern = "ABC Corrective (upward)"
            outlook = "Bearish"  # Setelah ABC up biasanya reversal
        else:
            pattern = "ABC Corrective (downward)"
            outlook = "Bullish"  # Setelah ABC down biasanya reversal
        waves = []
        labels = ["Wave A", "Wave B", "Wave C"]
        for label, (t, idx, price) in zip(labels, last_3):
            waves.append({"label": label, "price": price, "idx": idx})
    else:
        pattern = "Wave 1-2 (awal tren baru)"
        outlook = "Bullish" if len(alternating) > 0 and alternating[-1][0] == "L" else "Bearish"
        waves = []

    # Fibonacci ratio antar wave (validasi)
    wave_ratio_valid = False
    wave_analysis = ""
    if len(alternating) >= 4:
        w1 = abs(alternating[1][2] - alternating[0][2])
        w2 = abs(alternating[2][2] - alternating[1][2])
        w3 = abs(alternating[3][2] - alternating[2][2]) if len(alternating) > 3 else 0
        if w1 > 0:
            r1 = w2 / w1
            r2 = w3 / w1 if w3 > 0 and w1 > 0 else 0
            wave_ratio_valid = 0.3 < r1 < 0.9  # Wave 2 biasanya 38.2%-78.6% dari Wave 1
            wave_analysis = f"Wave ratio: W2/W1={r1:.2f}, W3/W1={r2:.2f}"
            if r2 >= 1.618:
                wave_analysis += " ✅ W3 Extended (Golden Ratio)"
            elif r2 >= 1.0:
                wave_analysis += " ✅ W3 Normal"

    # Perkiraan wave berikutnya
    next_wave = ""
    current_position = "—"
    if wave_count >= 2:
        last_ext = alternating[-1]
        if last_ext[0] == "H":
            current_position = f"Setelah High @ {last_ext[2]:,.0f} — menunggu reversal/koreksi"
            next_wave = "Koreksi (Wave Down)"
        else:
            current_position = f"Setelah Low @ {last_ext[2]:,.0f} — menunggu bounce/impulse"
            next_wave = "Impulse (Wave Up)"

    return {
        "pattern":           pattern,
        "outlook":           outlook,
        "wave_count":        wave_count,
        "waves":             waves,
        "alternating":       alternating,
        "wave_ratio_valid":  wave_ratio_valid,
        "wave_analysis":     wave_analysis,
        "current_position":  current_position,
        "next_wave":         next_wave,
        "extrema_count":     len(filtered),
    }


def fibonacci_time_zones(df: pd.DataFrame) -> Dict:
    """
    Hitung Fibonacci Time Zones dari titik awal trend.
    Menggunakan barisan Fibonacci untuk prediksi tanggal penting.
    """
    if df.empty or len(df) < 10:
        return {}

    n = len(df)
    dates = df.index.tolist()
    closes = df["Close"].values

    # Cari titik awal tren (low signifikan dalam 100 bar)
    lookback = min(100, n)
    start_pos_idx = int(df["Low"].tail(lookback).values.argmin()) + (n - lookback)

    time_zones = []
    for fib in FIB_SEQUENCE + [233, 377]:
        zone_pos = start_pos_idx + fib
        if zone_pos < n:
            time_zones.append({
                "fib": fib,
                "date": dates[zone_pos],
                "price": float(closes[zone_pos]),
                "status": "passed",
            })
        else:
            bars_left = zone_pos - n + 1
            time_zones.append({
                "fib": fib,
                "bars_remaining": bars_left,
                "status": "upcoming",
            })

    upcoming = [tz for tz in time_zones if tz["status"] == "upcoming"]
    next_zone = upcoming[0] if upcoming else None

    return {
        "start_pos": start_pos_idx,
        "start_date": dates[start_pos_idx] if start_pos_idx < len(dates) else None,
        "time_zones": time_zones,
        "upcoming": upcoming,
        "next_zone": next_zone,
    }


def get_astronacci_signal(fib_data: Dict, elliott: Dict, cycles: Dict, current_price: float) -> Dict:
    """
    Generate overall Astronacci signal dari semua komponen.
    """
    signals = []
    score   = 0

    # 1. Fibonacci zone
    zone = fib_data.get("zone", "")
    if "Discount" in zone:
        signals.append("✅ Harga di Discount Zone — area beli potensial")
        score += 2
    elif "Premium" in zone:
        signals.append("⚠️ Harga di Premium Zone — area jual potensial")
        score -= 1

    # 2. Level 61.8% (Golden Ratio) sebagai support/resistance kunci
    golden_sup = fib_data.get("golden_support")
    if golden_sup:
        if current_price > golden_sup * 1.01:
            signals.append(f"✅ Di atas Golden Ratio 61.8% support (Rp {golden_sup:,.0f})")
            score += 2
        elif abs(current_price - golden_sup) / golden_sup < 0.02:
            signals.append(f"🎯 Menyentuh area Golden Ratio 61.8% (Rp {golden_sup:,.0f}) — level kunci!")
            score += 1

    # 3. Elliott Wave outlook
    ew_outlook = elliott.get("outlook", "")
    ew_pattern = elliott.get("pattern", "")
    if ew_outlook == "Bullish":
        signals.append(f"🌊 Elliott Wave: {ew_pattern} → Outlook BULLISH")
        score += 2
    elif ew_outlook == "Bearish":
        signals.append(f"🌊 Elliott Wave: {ew_pattern} → Outlook BEARISH")
        score -= 2

    # 4. Astronacci Cycle
    next_cyc = cycles.get("next_cycle")
    if next_cyc:
        fib_n, cyc_data = next_cyc
        bars_left = cyc_data.get("bars_remaining", 0)
        if bars_left <= 5:
            signals.append(f"⏰ Siklus Fibonacci {fib_n}-bar akan segera terjadi ({bars_left} bar lagi) — waspada reversal!")
            score += 1

    # 5. Extension target
    golden_ext = fib_data.get("golden_ext_161")
    if golden_ext and fib_data.get("is_uptrend"):
        signals.append(f"🎯 Target Fibonacci 161.8%: Rp {golden_ext:,.0f}")

    # Overall signal
    if score >= 3:
        overall = "STRONG BUY 🚀"
        color = "#26A69A"
    elif score >= 1:
        overall = "BUY 📈"
        color = "#4CAF50"
    elif score <= -3:
        overall = "STRONG SELL 💥"
        color = "#EF5350"
    elif score <= -1:
        overall = "SELL 📉"
        color = "#F44336"
    else:
        overall = "NEUTRAL ⚪"
        color = "#FF9800"

    return {
        "overall":  overall,
        "color":    color,
        "score":    score,
        "signals":  signals,
    }


def plot_astronacci_chart(
    df: pd.DataFrame,
    ticker: str,
    fib_data: Dict,
    elliott: Dict,
    cycles: Dict,
) -> go.Figure:
    """
    Buat chart Astronacci lengkap:
    - Candlestick
    - Fibonacci Retracement & Extension lines
    - Astronacci Cycle markers
    - Elliott Wave labels
    """
    if df.empty:
        return go.Figure()

    fig = make_subplots(
        rows=2, cols=1,
        shared_xaxes=True,
        row_heights=[0.75, 0.25],
        vertical_spacing=0.03,
    )

    # ── Candlestick ──
    fig.add_trace(go.Candlestick(
        x=df.index,
        open=df["Open"], high=df["High"],
        low=df["Low"],   close=df["Close"],
        name=ticker,
        increasing_line_color="#26A69A",
        decreasing_line_color="#EF5350",
        showlegend=False,
    ), row=1, col=1)

    # ── Fibonacci Retracement Lines ──
    retracement = fib_data.get("retracement", {})
    for label, price in retracement.items():
        color = FIB_COLORS.get(label, "#555")
        width = 2.5 if label in ("61.8%", "38.2%", "50.0%") else 1
        dash  = "dot" if label in ("0.0%", "100%") else "dash"
        fig.add_hline(
            y=price,
            line=dict(color=color, width=width, dash=dash),
            annotation_text=f" {label} Rp {price:,.0f}",
            annotation_position="right",
            annotation_font_size=9,
            annotation_font_color=color,
            row=1, col=1,
        )

    # ── Fibonacci Extension Lines ──
    extension = fib_data.get("extension", {})
    for label, price in extension.items():
        if label in ("161.8%", "127.2%", "261.8%"):
            color = FIB_COLORS.get(label, "#26A69A")
            fig.add_hline(
                y=price,
                line=dict(color=color, width=1.5, dash="dashdot"),
                annotation_text=f" Ext {label} Rp {price:,.0f}",
                annotation_position="right",
                annotation_font_size=8,
                annotation_font_color=color,
                row=1, col=1,
            )

    # ── Fibonacci Time Zones (vertical lines) ──
    pivot_pos = cycles.get("pivot_pos", len(df) - 1)
    cycle_data = cycles.get("cycles", {})
    dates = df.index.tolist()

    for fib_n, cyc in cycle_data.items():
        if cyc.get("passed") and "date" in cyc:
            fig.add_vline(
                x=cyc["date"],
                line=dict(color="#2196F3", width=0.8, dash="dot"),
                annotation_text=f"F{fib_n}",
                annotation_position="top",
                annotation_font_size=7,
                annotation_font_color="#2196F3",
                row=1, col=1,
            )

    # ── Elliott Wave Labels ──
    alternating = elliott.get("alternating", [])
    if len(df) >= 60:
        offset = len(df) - 60
        waves_plot = elliott.get("waves", [])
        labels_ew = ["1", "2", "3", "4", "5"] if "Impulsive" in elliott.get("pattern","") else ["A", "B", "C"]
        for i, wave in enumerate(waves_plot[:5]):
            try:
                idx_plot = offset + wave["idx"]
                if 0 <= idx_plot < len(dates):
                    wdate = dates[idx_plot]
                    wprice = wave["price"]
                    wlabel = labels_ew[i] if i < len(labels_ew) else f"W{i+1}"
                    wcolor = "#FFD700" if wlabel in ("1","3","5","A","C") else "#FF9800"
                    fig.add_annotation(
                        x=wdate, y=wprice,
                        text=f"<b>({wlabel})</b>",
                        showarrow=True, arrowhead=2,
                        arrowsize=0.8, arrowcolor=wcolor,
                        font=dict(color=wcolor, size=11),
                        ax=0, ay=-30 if i % 2 == 0 else 30,
                        row=1, col=1,
                    )
            except Exception:
                pass

    # ── Volume bar ──
    if "Volume" in df.columns:
        vol_colors = ["#26A69A" if float(df["Close"].iloc[i]) >= float(df["Open"].iloc[i])
                      else "#EF5350" for i in range(len(df))]
        fig.add_trace(go.Bar(
            x=df.index, y=df["Volume"],
            name="Volume",
            marker_color=vol_colors,
            opacity=0.6,
            showlegend=False,
        ), row=2, col=1)

    # ── Layout ──
    direction = fib_data.get("direction", "uptrend")
    zone      = fib_data.get("zone", "")
    fig.update_layout(
        title=dict(
            text=f"🌀 Astronacci Chart — {ticker} | {direction.upper()} | {zone}",
            font=dict(size=14, color="#E8EAED"),
        ),
        template="plotly_dark",
        plot_bgcolor="#0D1117",
        paper_bgcolor="#0D1117",
        height=550,
        margin=dict(l=10, r=160, t=50, b=10),
        xaxis_rangeslider_visible=False,
        showlegend=False,
    )
    fig.update_yaxes(gridcolor="#21262D", row=1, col=1)
    fig.update_yaxes(gridcolor="#21262D", row=2, col=1)
    fig.update_xaxes(gridcolor="#21262D")

    return fig


def run_astronacci_analysis(df: pd.DataFrame) -> Dict:
    """
    Jalankan seluruh pipeline Astronacci dan return semua hasil.
    """
    if df.empty or len(df) < 30:
        return {}

    fib_data = calculate_fibonacci_retracement(df)
    elliott  = detect_elliott_wave(df)
    cycles   = calculate_astronacci_cycles(df)
    tz       = fibonacci_time_zones(df)

    current_price = float(df["Close"].iloc[-1])
    signal = get_astronacci_signal(fib_data, elliott, cycles, current_price)

    return {
        "fibonacci":    fib_data,
        "elliott":      elliott,
        "cycles":       cycles,
        "time_zones":   tz,
        "signal":       signal,
        "current_price": current_price,
    }
