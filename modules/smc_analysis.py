"""
Smart Money Concepts (SMC) Analysis
------------------------------------
Metode analisis institusional modern yang digunakan hedge fund & smart money:
  - Order Blocks (OB)
  - Fair Value Gaps / Imbalance (FVG)
  - Break of Structure (BOS) & Change of Character (CHOCH)
  - Liquidity Zones (Equal H/L, Stop Hunts)
  - Premium / Discount Zones
  - Mitigation Blocks
  - Inducement
"""

import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots


# ══════════════════════════════════════════════════════════════════════════════
# SWING HIGH / LOW  (building block untuk semua SMC)
# ══════════════════════════════════════════════════════════════════════════════

def find_swing_points(df: pd.DataFrame, left: int = 5, right: int = 5) -> pd.DataFrame:
    """Temukan swing high dan swing low."""
    df = df.copy()
    df["swing_high"] = np.nan
    df["swing_low"]  = np.nan

    for i in range(left, len(df) - right):
        window_h = df["High"].iloc[i - left : i + right + 1]
        window_l = df["Low"].iloc[i - left  : i + right + 1]

        if df["High"].iloc[i] == window_h.max():
            df.at[df.index[i], "swing_high"] = df["High"].iloc[i]
        if df["Low"].iloc[i] == window_l.min():
            df.at[df.index[i], "swing_low"] = df["Low"].iloc[i]

    return df


# ══════════════════════════════════════════════════════════════════════════════
# ORDER BLOCKS
# ══════════════════════════════════════════════════════════════════════════════

def find_order_blocks(df: pd.DataFrame, lookback: int = 50) -> list:
    """
    Order Block = candle terakhir berlawanan arah sebelum impuls kuat.
    Bullish OB : candle bearish terakhir sebelum impuls naik tajam
    Bearish OB : candle bullish terakhir sebelum impuls turun tajam
    """
    obs = []
    data = df.tail(lookback).copy()

    for i in range(2, len(data) - 1):
        c      = data.iloc[i]
        c_next = data.iloc[i + 1]
        c_prev = data.iloc[i - 1]

        body_size   = abs(c["Close"] - c["Open"])
        next_body   = abs(c_next["Close"] - c_next["Open"])
        avg_body    = data["Close"].sub(data["Open"]).abs().mean()

        # Bullish Order Block: candle bearish diikuti impuls bullish kuat
        if (c["Close"] < c["Open"]                  # candle bearish
                and c_next["Close"] > c_next["Open"]  # diikuti candle bullish
                and next_body > avg_body * 1.5):       # impuls kuat
            obs.append({
                "type":   "Bullish OB",
                "top":    max(c["Open"], c["Close"]),
                "bottom": min(c["Open"], c["Close"]),
                "wick_low": c["Low"],
                "index":  data.index[i],
                "mitigated": data["Low"].iloc[i + 1:].min() < min(c["Open"], c["Close"]),
                "color":  "rgba(38,166,154,0.25)",
                "border": "#26A69A",
            })

        # Bearish Order Block: candle bullish diikuti impuls bearish kuat
        elif (c["Close"] > c["Open"]
                and c_next["Close"] < c_next["Open"]
                and next_body > avg_body * 1.5):
            obs.append({
                "type":   "Bearish OB",
                "top":    max(c["Open"], c["Close"]),
                "bottom": min(c["Open"], c["Close"]),
                "wick_high": c["High"],
                "index":  data.index[i],
                "mitigated": data["High"].iloc[i + 1:].max() > max(c["Open"], c["Close"]),
                "color":  "rgba(239,83,80,0.25)",
                "border": "#EF5350",
            })

    # Return only last 6 unmitigated OBs
    active = [o for o in obs if not o["mitigated"]]
    return active[-6:]


# ══════════════════════════════════════════════════════════════════════════════
# FAIR VALUE GAPS (FVG / Imbalance)
# ══════════════════════════════════════════════════════════════════════════════

def find_fvg(df: pd.DataFrame, lookback: int = 60) -> list:
    """
    FVG terbentuk ketika ada gap antara candle 1 dan candle 3.
    Bullish FVG : Low[i+1] > High[i-1]  → gap di bawah candle ke-2
    Bearish FVG : High[i+1] < Low[i-1]  → gap di atas candle ke-2
    """
    fvgs = []
    data = df.tail(lookback)

    for i in range(1, len(data) - 1):
        high_prev = data["High"].iloc[i - 1]
        low_prev  = data["Low"].iloc[i - 1]
        high_next = data["High"].iloc[i + 1]
        low_next  = data["Low"].iloc[i + 1]
        close_cur = data["Close"].iloc[i]
        idx       = data.index[i]

        # Bullish FVG
        if low_next > high_prev:
            gap_size = low_next - high_prev
            filled   = data["Low"].iloc[i + 1:].min() <= high_prev
            fvgs.append({
                "type":   "Bullish FVG",
                "top":    low_next,
                "bottom": high_prev,
                "size":   gap_size,
                "index":  idx,
                "filled": filled,
                "color":  "rgba(38,166,154,0.15)",
                "border": "#26A69A",
            })

        # Bearish FVG
        elif high_next < low_prev:
            gap_size = low_prev - high_next
            filled   = data["High"].iloc[i + 1:].max() >= low_prev
            fvgs.append({
                "type":   "Bearish FVG",
                "top":    low_prev,
                "bottom": high_next,
                "size":   gap_size,
                "index":  idx,
                "filled": filled,
                "color":  "rgba(239,83,80,0.15)",
                "border": "#EF5350",
            })

    active = [f for f in fvgs if not f["filled"]]
    return active[-8:]


# ══════════════════════════════════════════════════════════════════════════════
# BREAK OF STRUCTURE (BOS) & CHANGE OF CHARACTER (CHOCH)
# ══════════════════════════════════════════════════════════════════════════════

def find_bos_choch(df: pd.DataFrame, swing_left: int = 5, swing_right: int = 5) -> list:
    """
    BOS   : Harga menembus swing high/low searah tren → kelanjutan
    CHOCH : Harga menembus swing high/low berlawanan tren → pembalikan
    """
    df_sw  = find_swing_points(df, left=swing_left, right=swing_right)
    events = []

    swing_highs = df_sw[df_sw["swing_high"].notna()]["swing_high"]
    swing_lows  = df_sw[df_sw["swing_low"].notna()]["swing_low"]

    closes = df_sw["Close"]

    prev_broken_high = None
    prev_broken_low  = None
    last_trend       = None   # "up" atau "down"

    for i in range(len(df_sw)):
        idx   = df_sw.index[i]
        close = closes.iloc[i]

        # Cek apakah menembus swing high terakhir
        recent_highs = swing_highs[swing_highs.index < idx].tail(3)
        recent_lows  = swing_lows[swing_lows.index < idx].tail(3)

        if not recent_highs.empty:
            last_sh = recent_highs.iloc[-1]
            if close > last_sh and last_sh != prev_broken_high:
                etype  = "BOS ▲" if last_trend == "up" else "CHOCH ▲"
                events.append({
                    "type":  etype,
                    "level": last_sh,
                    "index": idx,
                    "color": "#26A69A" if "▲" in etype else "#2196F3",
                    "direction": "bullish",
                })
                prev_broken_high = last_sh
                last_trend = "up"

        if not recent_lows.empty:
            last_sl = recent_lows.iloc[-1]
            if close < last_sl and last_sl != prev_broken_low:
                etype  = "BOS ▼" if last_trend == "down" else "CHOCH ▼"
                events.append({
                    "type":  etype,
                    "level": last_sl,
                    "index": idx,
                    "color": "#EF5350" if "▼" in etype else "#FF9800",
                    "direction": "bearish",
                })
                prev_broken_low = last_sl
                last_trend = "down"

    return events[-10:]


# ══════════════════════════════════════════════════════════════════════════════
# LIQUIDITY ZONES
# ══════════════════════════════════════════════════════════════════════════════

def find_liquidity_zones(df: pd.DataFrame, tolerance_pct: float = 0.002, lookback: int = 80) -> dict:
    """
    Equal Highs / Equal Lows → target likuiditas yang sering di-sweep smart money.
    """
    data = df.tail(lookback)
    highs  = data["High"].values
    lows   = data["Low"].values
    dates  = data.index

    eq_highs = []
    eq_lows  = []

    for i in range(len(data)):
        for j in range(i + 3, len(data)):
            tol_h = highs[i] * tolerance_pct
            tol_l = lows[i] * tolerance_pct
            if abs(highs[i] - highs[j]) <= tol_h:
                eq_highs.append({"level": (highs[i] + highs[j]) / 2,
                                  "idx1": dates[i], "idx2": dates[j]})
            if abs(lows[i] - lows[j]) <= tol_l:
                eq_lows.append({"level": (lows[i] + lows[j]) / 2,
                                 "idx1": dates[i], "idx2": dates[j]})

    # Gabungkan level yang berdekatan
    def merge_levels(zones, tol):
        if not zones:
            return []
        sorted_z = sorted(zones, key=lambda x: x["level"])
        merged = [sorted_z[0]]
        for z in sorted_z[1:]:
            if abs(z["level"] - merged[-1]["level"]) / merged[-1]["level"] < tol * 3:
                merged[-1]["level"] = (merged[-1]["level"] + z["level"]) / 2
            else:
                merged.append(z)
        return merged[-5:]

    current_price = data["Close"].iloc[-1]

    return {
        "buy_side_liquidity":  merge_levels([h for h in eq_highs if h["level"] > current_price], tolerance_pct),
        "sell_side_liquidity": merge_levels([l for l in eq_lows  if l["level"] < current_price], tolerance_pct),
        "current_price":       current_price,
    }


# ══════════════════════════════════════════════════════════════════════════════
# PREMIUM / DISCOUNT ZONES
# ══════════════════════════════════════════════════════════════════════════════

def get_premium_discount(df: pd.DataFrame, lookback: int = 50) -> dict:
    """
    Range = swing high ke swing low terakhir.
    Premium  = di atas 50% range → mahal, cocok untuk SELL/SHORT
    Discount = di bawah 50% range → murah, cocok untuk BUY/LONG
    Equilibrium = 50% (OTE zone: 0.618–0.786 Fibonacci)
    """
    data      = df.tail(lookback)
    high      = data["High"].max()
    low       = data["Low"].min()
    current   = data["Close"].iloc[-1]
    rng       = high - low

    if rng == 0:
        return {}

    position_pct = (current - low) / rng * 100
    equilibrium  = low + rng * 0.5
    ote_top      = low + rng * 0.786
    ote_bot      = low + rng * 0.618

    if current > equilibrium:
        zone  = "PREMIUM 🔴"
        bias  = "Harga di zona premium — waspadai reversal / cari entry SELL"
        color = "#EF5350"
    else:
        zone  = "DISCOUNT 🟢"
        bias  = "Harga di zona diskon — potensi entry BUY / akumulasi"
        color = "#26A69A"

    return {
        "zone":           zone,
        "bias":           bias,
        "color":          color,
        "current":        current,
        "range_high":     high,
        "range_low":      low,
        "equilibrium":    equilibrium,
        "ote_top":        ote_top,
        "ote_bot":        ote_bot,
        "position_pct":   round(position_pct, 1),
        "in_ote":         ote_bot <= current <= ote_top,
    }


# ══════════════════════════════════════════════════════════════════════════════
# SMC OVERALL BIAS
# ══════════════════════════════════════════════════════════════════════════════

def get_smc_bias(obs: list, fvgs: list, bos_events: list, pd_zone: dict, liq: dict) -> dict:
    """Hitung bias SMC keseluruhan."""
    score = 0
    notes = []

    # BOS/CHOCH terbaru
    if bos_events:
        last = bos_events[-1]
        if last["direction"] == "bullish":
            score += 2
            notes.append(f"✅ {last['type']} terakhir → bullish bias")
        else:
            score -= 2
            notes.append(f"⚠️ {last['type']} terakhir → bearish bias")

    # Premium/Discount
    if pd_zone:
        if "DISCOUNT" in pd_zone.get("zone", ""):
            score += 1
            notes.append("✅ Harga di zona Discount (buy zone)")
        else:
            score -= 1
            notes.append("⚠️ Harga di zona Premium (sell zone)")
        if pd_zone.get("in_ote"):
            score += 1
            notes.append("✅ Harga di OTE Zone (0.618–0.786) — zona entry optimal")

    # Order Blocks aktif
    current = pd_zone.get("current", 0)
    bull_obs = [o for o in obs if o["type"] == "Bullish OB" and o["bottom"] <= current <= o["top"] * 1.02]
    bear_obs = [o for o in obs if o["type"] == "Bearish OB" and o["bottom"] * 0.98 <= current <= o["top"]]

    if bull_obs:
        score += 2
        notes.append(f"✅ Harga di dalam Bullish Order Block")
    if bear_obs:
        score -= 2
        notes.append(f"⚠️ Harga di dalam Bearish Order Block")

    # FVG aktif
    bull_fvg = [f for f in fvgs if f["type"] == "Bullish FVG" and f["bottom"] <= current <= f["top"]]
    bear_fvg = [f for f in fvgs if f["type"] == "Bearish FVG" and f["bottom"] <= current <= f["top"]]

    if bull_fvg:
        score += 1
        notes.append("✅ Harga mengisi Bullish FVG")
    if bear_fvg:
        score -= 1
        notes.append("⚠️ Harga mengisi Bearish FVG")

    # Liquidity target
    bsl = liq.get("buy_side_liquidity", [])
    ssl = liq.get("sell_side_liquidity", [])
    if bsl:
        nearest_bsl = min(bsl, key=lambda x: abs(x["level"] - current))
        dist = (nearest_bsl["level"] - current) / current * 100
        notes.append(f"🎯 Buy-side liquidity target: {nearest_bsl['level']:.2f} (+{dist:.2f}%)")
    if ssl:
        nearest_ssl = min(ssl, key=lambda x: abs(x["level"] - current))
        dist = (current - nearest_ssl["level"]) / current * 100
        notes.append(f"🎯 Sell-side liquidity target: {nearest_ssl['level']:.2f} (-{dist:.2f}%)")

    if score >= 3:
        bias, color = "STRONG BULLISH 🟢🟢", "#26A69A"
    elif score >= 1:
        bias, color = "BULLISH 🟢", "#4CAF50"
    elif score <= -3:
        bias, color = "STRONG BEARISH 🔴🔴", "#EF5350"
    elif score <= -1:
        bias, color = "BEARISH 🔴", "#F44336"
    else:
        bias, color = "NEUTRAL ⚪", "#FF9800"

    return {"bias": bias, "score": score, "color": color, "notes": notes}


# ══════════════════════════════════════════════════════════════════════════════
# PLOTLY CHART — SMC FULL
# ══════════════════════════════════════════════════════════════════════════════

def plot_smc_chart(df: pd.DataFrame, ticker: str,
                   obs: list, fvgs: list, bos_events: list,
                   pd_zone: dict, liq: dict) -> go.Figure:

    fig = make_subplots(rows=2, cols=1, shared_xaxes=True,
                        row_heights=[0.8, 0.2], vertical_spacing=0.02)

    # Candlestick
    fig.add_trace(go.Candlestick(
        x=df.index, open=df["Open"], high=df["High"],
        low=df["Low"], close=df["Close"], name="Harga",
        increasing_line_color="#26A69A", decreasing_line_color="#EF5350",
    ), row=1, col=1)

    x_start = df.index[max(0, len(df) - 60)]
    x_end   = df.index[-1]

    # ── Order Blocks ──────────────────────────────────────────────────────────
    for ob in obs:
        label = "🟢 OB" if "Bullish" in ob["type"] else "🔴 OB"
        fig.add_shape(type="rect",
            x0=ob["index"], x1=x_end,
            y0=ob["bottom"], y1=ob["top"],
            fillcolor=ob["color"], line=dict(color=ob["border"], width=1),
            row=1, col=1)
        fig.add_annotation(x=ob["index"], y=ob["top"],
            text=f"<b>{label}</b>", showarrow=False,
            font=dict(size=9, color=ob["border"]),
            xanchor="left", yanchor="bottom", row=1, col=1)

    # ── Fair Value Gaps ───────────────────────────────────────────────────────
    for fvg in fvgs:
        label = "🟢 FVG" if "Bullish" in fvg["type"] else "🔴 FVG"
        fig.add_shape(type="rect",
            x0=fvg["index"], x1=x_end,
            y0=fvg["bottom"], y1=fvg["top"],
            fillcolor=fvg["color"], line=dict(color=fvg["border"], width=0.5, dash="dot"),
            row=1, col=1)

    # ── Liquidity Lines ───────────────────────────────────────────────────────
    for bsl in liq.get("buy_side_liquidity", [])[:3]:
        fig.add_hline(y=bsl["level"], line=dict(color="#FFD700", width=1, dash="dot"),
                      annotation_text=f"BSL {bsl['level']:.2f}",
                      annotation_font=dict(color="#FFD700", size=9),
                      row=1, col=1)
    for ssl in liq.get("sell_side_liquidity", [])[:3]:
        fig.add_hline(y=ssl["level"], line=dict(color="#FF6B6B", width=1, dash="dot"),
                      annotation_text=f"SSL {ssl['level']:.2f}",
                      annotation_font=dict(color="#FF6B6B", size=9),
                      row=1, col=1)

    # ── Premium / Discount / Equilibrium ─────────────────────────────────────
    if pd_zone:
        eq = pd_zone.get("equilibrium")
        rh = pd_zone.get("range_high")
        rl = pd_zone.get("range_low")
        ote_t = pd_zone.get("ote_top")
        ote_b = pd_zone.get("ote_bot")

        if eq:
            fig.add_hline(y=eq, line=dict(color="#888", width=1, dash="longdash"),
                          annotation_text="EQ 50%",
                          annotation_font=dict(color="#888", size=9), row=1, col=1)
        if ote_t and ote_b:
            fig.add_shape(type="rect",
                x0=x_start, x1=x_end, y0=ote_b, y1=ote_t,
                fillcolor="rgba(33,150,243,0.07)",
                line=dict(color="#2196F3", width=0.5, dash="dot"),
                row=1, col=1)
            fig.add_annotation(x=x_end, y=(ote_t + ote_b) / 2,
                text="OTE Zone", showarrow=False,
                font=dict(size=8, color="#2196F3"),
                xanchor="right", row=1, col=1)

    # ── BOS / CHOCH markers ───────────────────────────────────────────────────
    for ev in bos_events[-5:]:
        fig.add_annotation(
            x=ev["index"], y=ev["level"],
            text=f"<b>{ev['type']}</b>",
            showarrow=True, arrowhead=2, arrowsize=0.8,
            font=dict(size=9, color=ev["color"]),
            arrowcolor=ev["color"],
            ax=0, ay=-25 if "▲" in ev["type"] else 25,
            row=1, col=1)

    # ── Volume ────────────────────────────────────────────────────────────────
    vol_colors = ["#EF5350" if df["Close"].iloc[i] < df["Open"].iloc[i]
                  else "#26A69A" for i in range(len(df))]
    fig.add_trace(go.Bar(x=df.index, y=df["Volume"], marker_color=vol_colors,
                          name="Volume", opacity=0.7), row=2, col=1)

    fig.update_layout(
        title=f"<b>{ticker}</b> — Smart Money Concepts (SMC)",
        height=750, template="plotly_dark",
        xaxis_rangeslider_visible=False,
        paper_bgcolor="#0E1117", plot_bgcolor="#161B22",
        showlegend=False,
        margin=dict(l=60, r=20, t=60, b=20),
    )
    fig.update_xaxes(showgrid=True, gridcolor="#2D3748")
    fig.update_yaxes(showgrid=True, gridcolor="#2D3748")
    return fig
