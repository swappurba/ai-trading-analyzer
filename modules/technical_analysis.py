import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import ta
from config import RSI_OVERBOUGHT, RSI_OVERSOLD


def calculate_indicators(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty or len(df) < 20:
        return df

    df = df.copy()
    close = df["Close"]
    high = df["High"]
    low = df["Low"]
    volume = df["Volume"]

    # Moving Averages
    df["MA5"] = close.rolling(5).mean()
    df["MA10"] = close.rolling(10).mean()
    df["MA20"] = close.rolling(20).mean()
    df["MA50"] = close.rolling(50).mean()
    df["MA200"] = close.rolling(200).mean()

    # EMA
    df["EMA9"] = close.ewm(span=9, adjust=False).mean()
    df["EMA21"] = close.ewm(span=21, adjust=False).mean()
    df["EMA55"] = close.ewm(span=55, adjust=False).mean()

    # Bollinger Bands
    df["BB_mid"] = close.rolling(20).mean()
    bb_std = close.rolling(20).std()
    df["BB_upper"] = df["BB_mid"] + 2 * bb_std
    df["BB_lower"] = df["BB_mid"] - 2 * bb_std
    df["BB_width"] = (df["BB_upper"] - df["BB_lower"]) / df["BB_mid"] * 100
    df["BB_pct"] = (close - df["BB_lower"]) / (df["BB_upper"] - df["BB_lower"])

    # RSI
    try:
        df["RSI"] = ta.momentum.RSIIndicator(close, window=14).rsi()
    except Exception:
        delta = close.diff()
        gain = delta.where(delta > 0, 0).rolling(14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
        rs = gain / loss
        df["RSI"] = 100 - (100 / (1 + rs))

    # MACD
    ema12 = close.ewm(span=12, adjust=False).mean()
    ema26 = close.ewm(span=26, adjust=False).mean()
    df["MACD"] = ema12 - ema26
    df["MACD_signal"] = df["MACD"].ewm(span=9, adjust=False).mean()
    df["MACD_hist"] = df["MACD"] - df["MACD_signal"]

    # Stochastic Oscillator
    low14 = low.rolling(14).min()
    high14 = high.rolling(14).max()
    df["Stoch_K"] = 100 * (close - low14) / (high14 - low14 + 1e-10)
    df["Stoch_D"] = df["Stoch_K"].rolling(3).mean()

    # ATR (Average True Range)
    tr1 = high - low
    tr2 = abs(high - close.shift())
    tr3 = abs(low - close.shift())
    df["TR"] = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    df["ATR"] = df["TR"].rolling(14).mean()
    df["ATR_pct"] = df["ATR"] / close * 100

    # OBV (On Balance Volume)
    obv = [0]
    for i in range(1, len(df)):
        if close.iloc[i] > close.iloc[i - 1]:
            obv.append(obv[-1] + volume.iloc[i])
        elif close.iloc[i] < close.iloc[i - 1]:
            obv.append(obv[-1] - volume.iloc[i])
        else:
            obv.append(obv[-1])
    df["OBV"] = obv

    # Volume MA
    df["Vol_MA20"] = volume.rolling(20).mean()
    df["Vol_ratio"] = volume / df["Vol_MA20"]

    # Ichimoku Cloud (simplified)
    h9 = high.rolling(9).max()
    l9 = low.rolling(9).min()
    df["Ichi_tenkan"] = (h9 + l9) / 2

    h26 = high.rolling(26).max()
    l26 = low.rolling(26).min()
    df["Ichi_kijun"] = (h26 + l26) / 2

    df["Ichi_senkou_a"] = ((df["Ichi_tenkan"] + df["Ichi_kijun"]) / 2).shift(26)
    h52 = high.rolling(52).max()
    l52 = low.rolling(52).min()
    df["Ichi_senkou_b"] = ((h52 + l52) / 2).shift(26)
    df["Ichi_chikou"] = close.shift(-26)

    # Support & Resistance (pivot points)
    df["Pivot"] = (high.shift(1) + low.shift(1) + close.shift(1)) / 3
    df["R1"] = 2 * df["Pivot"] - low.shift(1)
    df["S1"] = 2 * df["Pivot"] - high.shift(1)
    df["R2"] = df["Pivot"] + (high.shift(1) - low.shift(1))
    df["S2"] = df["Pivot"] - (high.shift(1) - low.shift(1))

    # Price momentum
    df["ROC5"] = close.pct_change(5) * 100
    df["ROC20"] = close.pct_change(20) * 100

    return df


def get_signals(df: pd.DataFrame) -> dict:
    if df.empty or len(df) < 50:
        return {}

    last = df.iloc[-1]
    prev = df.iloc[-2]
    signals = {}
    score = 0
    total = 0

    # --- RSI ---
    rsi = last.get("RSI", np.nan)
    if not np.isnan(rsi):
        total += 1
        if rsi < RSI_OVERSOLD:
            signals["RSI"] = {"value": round(rsi, 2), "signal": "BUY", "note": f"Oversold ({rsi:.1f} < {RSI_OVERSOLD})"}
            score += 1
        elif rsi > RSI_OVERBOUGHT:
            signals["RSI"] = {"value": round(rsi, 2), "signal": "SELL", "note": f"Overbought ({rsi:.1f} > {RSI_OVERBOUGHT})"}
            score -= 1
        else:
            signals["RSI"] = {"value": round(rsi, 2), "signal": "NEUTRAL", "note": f"Netral ({rsi:.1f})"}

    # --- MACD ---
    macd = last.get("MACD", np.nan)
    macd_sig = last.get("MACD_signal", np.nan)
    macd_hist = last.get("MACD_hist", np.nan)
    prev_hist = prev.get("MACD_hist", np.nan)
    if not any(np.isnan(x) for x in [macd, macd_sig, macd_hist, prev_hist]):
        total += 1
        if macd_hist > 0 and prev_hist <= 0:
            signals["MACD"] = {"value": round(macd, 4), "signal": "BUY", "note": "Bullish crossover"}
            score += 1
        elif macd_hist < 0 and prev_hist >= 0:
            signals["MACD"] = {"value": round(macd, 4), "signal": "SELL", "note": "Bearish crossover"}
            score -= 1
        elif macd_hist > 0:
            signals["MACD"] = {"value": round(macd, 4), "signal": "BUY", "note": "Histogram positif"}
            score += 0.5
        else:
            signals["MACD"] = {"value": round(macd, 4), "signal": "SELL", "note": "Histogram negatif"}
            score -= 0.5

    # --- Bollinger Bands ---
    bb_pct = last.get("BB_pct", np.nan)
    close = last["Close"]
    bb_upper = last.get("BB_upper", np.nan)
    bb_lower = last.get("BB_lower", np.nan)
    if not any(np.isnan(x) for x in [bb_pct, bb_upper, bb_lower]):
        total += 1
        if bb_pct < 0.2:
            signals["Bollinger"] = {"value": round(bb_pct, 3), "signal": "BUY", "note": "Harga dekat lower band"}
            score += 1
        elif bb_pct > 0.8:
            signals["Bollinger"] = {"value": round(bb_pct, 3), "signal": "SELL", "note": "Harga dekat upper band"}
            score -= 1
        else:
            signals["Bollinger"] = {"value": round(bb_pct, 3), "signal": "NEUTRAL", "note": "Harga dalam rentang normal"}

    # --- Moving Average Crossover ---
    ma20 = last.get("MA20", np.nan)
    ma50 = last.get("MA50", np.nan)
    prev_ma20 = prev.get("MA20", np.nan)
    prev_ma50 = prev.get("MA50", np.nan)
    if not any(np.isnan(x) for x in [ma20, ma50, prev_ma20, prev_ma50]):
        total += 1
        if ma20 > ma50 and prev_ma20 <= prev_ma50:
            signals["MA_Cross"] = {"value": round(ma20, 2), "signal": "BUY", "note": "Golden Cross MA20/MA50"}
            score += 1
        elif ma20 < ma50 and prev_ma20 >= prev_ma50:
            signals["MA_Cross"] = {"value": round(ma20, 2), "signal": "SELL", "note": "Death Cross MA20/MA50"}
            score -= 1
        elif ma20 > ma50:
            signals["MA_Cross"] = {"value": round(ma20, 2), "signal": "BUY", "note": "MA20 di atas MA50 (bullish)"}
            score += 0.5
        else:
            signals["MA_Cross"] = {"value": round(ma20, 2), "signal": "SELL", "note": "MA20 di bawah MA50 (bearish)"}
            score -= 0.5

    # --- Price vs MA200 ---
    ma200 = last.get("MA200", np.nan)
    if not np.isnan(ma200):
        total += 1
        if close > ma200:
            signals["MA200"] = {"value": round(ma200, 2), "signal": "BUY", "note": "Harga di atas MA200 (bullish)"}
            score += 1
        else:
            signals["MA200"] = {"value": round(ma200, 2), "signal": "SELL", "note": "Harga di bawah MA200 (bearish)"}
            score -= 1

    # --- Stochastic ---
    stoch_k = last.get("Stoch_K", np.nan)
    stoch_d = last.get("Stoch_D", np.nan)
    if not any(np.isnan(x) for x in [stoch_k, stoch_d]):
        total += 1
        if stoch_k < 20 and stoch_k > stoch_d:
            signals["Stochastic"] = {"value": round(stoch_k, 2), "signal": "BUY", "note": f"Oversold & K > D ({stoch_k:.1f})"}
            score += 1
        elif stoch_k > 80 and stoch_k < stoch_d:
            signals["Stochastic"] = {"value": round(stoch_k, 2), "signal": "SELL", "note": f"Overbought & K < D ({stoch_k:.1f})"}
            score -= 1
        else:
            signals["Stochastic"] = {"value": round(stoch_k, 2), "signal": "NEUTRAL", "note": f"Netral ({stoch_k:.1f})"}

    # --- Volume ---
    vol_ratio = last.get("Vol_ratio", np.nan)
    if not np.isnan(vol_ratio):
        total += 1
        if vol_ratio > 1.5:
            signals["Volume"] = {"value": round(vol_ratio, 2), "signal": "WATCH", "note": f"Volume tinggi ({vol_ratio:.1f}x rata-rata)"}
        elif vol_ratio < 0.5:
            signals["Volume"] = {"value": round(vol_ratio, 2), "signal": "LOW", "note": f"Volume rendah ({vol_ratio:.1f}x rata-rata)"}
        else:
            signals["Volume"] = {"value": round(vol_ratio, 2), "signal": "NORMAL", "note": f"Volume normal ({vol_ratio:.1f}x rata-rata)"}

    # Overall
    if total > 0:
        score_pct = (score / total) * 100
        if score_pct > 40:
            overall = "STRONG BUY"
        elif score_pct > 15:
            overall = "BUY"
        elif score_pct < -40:
            overall = "STRONG SELL"
        elif score_pct < -15:
            overall = "SELL"
        else:
            overall = "NEUTRAL / HOLD"
        signals["_overall"] = {"score": round(score, 2), "total": total, "pct": round(score_pct, 1), "recommendation": overall}

    return signals


def get_support_resistance(df: pd.DataFrame, n: int = 5) -> dict:
    if df.empty or len(df) < 20:
        return {}

    close = df["Close"]
    high = df["High"]
    low = df["Low"]

    # Recent key levels
    recent = df.tail(60)
    highs = []
    lows = []

    for i in range(1, len(recent) - 1):
        if recent["High"].iloc[i] > recent["High"].iloc[i-1] and recent["High"].iloc[i] > recent["High"].iloc[i+1]:
            highs.append(recent["High"].iloc[i])
        if recent["Low"].iloc[i] < recent["Low"].iloc[i-1] and recent["Low"].iloc[i] < recent["Low"].iloc[i+1]:
            lows.append(recent["Low"].iloc[i])

    current = close.iloc[-1]

    resistances = sorted([h for h in highs if h > current], reverse=False)[:3]
    supports = sorted([l for l in lows if l < current], reverse=True)[:3]

    last = df.iloc[-1]
    return {
        "current": current,
        "resistances": resistances,
        "supports": supports,
        "pivot": last.get("Pivot", np.nan),
        "R1": last.get("R1", np.nan),
        "R2": last.get("R2", np.nan),
        "S1": last.get("S1", np.nan),
        "S2": last.get("S2", np.nan),
        "52w_high": high.tail(252).max(),
        "52w_low": low.tail(252).min(),
    }


def plot_candlestick_chart(df: pd.DataFrame, ticker: str, show_ichimoku: bool = False) -> go.Figure:
    if df.empty:
        return go.Figure()

    df = calculate_indicators(df)
    fig = make_subplots(
        rows=4, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.02,
        row_heights=[0.55, 0.15, 0.15, 0.15],
        subplot_titles=["", "Volume", "RSI (14)", "MACD"],
    )

    # Candlestick
    fig.add_trace(go.Candlestick(
        x=df.index, open=df["Open"], high=df["High"],
        low=df["Low"], close=df["Close"],
        name="Harga", increasing_line_color="#26A69A", decreasing_line_color="#EF5350",
    ), row=1, col=1)

    # Moving Averages
    colors_ma = {"MA20": "#FF9800", "MA50": "#2196F3", "MA200": "#9C27B0"}
    for ma, color in colors_ma.items():
        if ma in df.columns:
            fig.add_trace(go.Scatter(x=df.index, y=df[ma], name=ma, line=dict(color=color, width=1.2), opacity=0.8), row=1, col=1)

    # Bollinger Bands
    if "BB_upper" in df.columns:
        fig.add_trace(go.Scatter(x=df.index, y=df["BB_upper"], name="BB Upper",
                                  line=dict(color="gray", width=1, dash="dot"), opacity=0.6), row=1, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=df["BB_lower"], name="BB Lower",
                                  line=dict(color="gray", width=1, dash="dot"),
                                  fill="tonexty", fillcolor="rgba(128,128,128,0.08)", opacity=0.6), row=1, col=1)

    # Ichimoku
    if show_ichimoku and "Ichi_senkou_a" in df.columns:
        fig.add_trace(go.Scatter(x=df.index, y=df["Ichi_senkou_a"], name="Senkou A",
                                  line=dict(color="rgba(0,200,100,0.6)", width=1)), row=1, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=df["Ichi_senkou_b"], name="Senkou B",
                                  line=dict(color="rgba(200,50,50,0.6)", width=1),
                                  fill="tonexty", fillcolor="rgba(128,128,128,0.1)"), row=1, col=1)

    # Volume bars
    colors_vol = ["#EF5350" if df["Close"].iloc[i] < df["Open"].iloc[i] else "#26A69A" for i in range(len(df))]
    fig.add_trace(go.Bar(x=df.index, y=df["Volume"], name="Volume",
                          marker_color=colors_vol, opacity=0.7), row=2, col=1)
    if "Vol_MA20" in df.columns:
        fig.add_trace(go.Scatter(x=df.index, y=df["Vol_MA20"], name="Vol MA20",
                                  line=dict(color="orange", width=1)), row=2, col=1)

    # RSI
    if "RSI" in df.columns:
        fig.add_trace(go.Scatter(x=df.index, y=df["RSI"], name="RSI",
                                  line=dict(color="#E91E63", width=1.5)), row=3, col=1)
        fig.add_hline(y=RSI_OVERBOUGHT, line_dash="dash", line_color="red", opacity=0.5, row=3, col=1)
        fig.add_hline(y=RSI_OVERSOLD, line_dash="dash", line_color="green", opacity=0.5, row=3, col=1)
        fig.add_hline(y=50, line_dash="dot", line_color="gray", opacity=0.3, row=3, col=1)

    # MACD
    if "MACD" in df.columns:
        macd_colors = ["#26A69A" if v >= 0 else "#EF5350" for v in df["MACD_hist"].fillna(0)]
        fig.add_trace(go.Bar(x=df.index, y=df["MACD_hist"], name="MACD Hist",
                              marker_color=macd_colors, opacity=0.7), row=4, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=df["MACD"], name="MACD",
                                  line=dict(color="#2196F3", width=1.5)), row=4, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=df["MACD_signal"], name="Signal",
                                  line=dict(color="#FF9800", width=1.5)), row=4, col=1)

    fig.update_layout(
        title=dict(text=f"<b>{ticker}</b> - Analisis Teknikal", font=dict(size=16)),
        xaxis_rangeslider_visible=False,
        height=850,
        template="plotly_dark",
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(l=60, r=20, t=60, b=20),
        paper_bgcolor="#0E1117",
        plot_bgcolor="#161B22",
    )
    fig.update_xaxes(showgrid=True, gridcolor="#2D3748", gridwidth=0.5)
    fig.update_yaxes(showgrid=True, gridcolor="#2D3748", gridwidth=0.5)

    return fig


def plot_rsi_stochastic(df: pd.DataFrame) -> go.Figure:
    if df.empty:
        return go.Figure()

    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.05,
                        subplot_titles=["RSI (14)", "Stochastic Oscillator"])

    if "RSI" in df.columns:
        fig.add_trace(go.Scatter(x=df.index, y=df["RSI"], name="RSI", line=dict(color="#E91E63")), row=1, col=1)
        fig.add_hrect(y0=70, y1=100, fillcolor="red", opacity=0.1, row=1, col=1)
        fig.add_hrect(y0=0, y1=30, fillcolor="green", opacity=0.1, row=1, col=1)
        fig.add_hline(y=70, line_dash="dash", line_color="red", row=1, col=1)
        fig.add_hline(y=30, line_dash="dash", line_color="green", row=1, col=1)

    if "Stoch_K" in df.columns:
        fig.add_trace(go.Scatter(x=df.index, y=df["Stoch_K"], name="%K", line=dict(color="#2196F3")), row=2, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=df["Stoch_D"], name="%D", line=dict(color="#FF9800")), row=2, col=1)
        fig.add_hrect(y0=80, y1=100, fillcolor="red", opacity=0.1, row=2, col=1)
        fig.add_hrect(y0=0, y1=20, fillcolor="green", opacity=0.1, row=2, col=1)

    fig.update_layout(height=400, template="plotly_dark", paper_bgcolor="#0E1117", plot_bgcolor="#161B22")
    return fig
