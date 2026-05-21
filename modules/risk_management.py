"""
Risk Management & Quantitative Analysis
-----------------------------------------
Model kuantitatif profesional:
  - Value at Risk (VaR) — Historical, Parametric, Monte Carlo
  - Expected Shortfall (CVaR)
  - Sharpe / Sortino / Calmar Ratio
  - Maximum Drawdown
  - Monte Carlo Price Simulation
  - Kelly Criterion (position sizing)
  - Beta & Correlation vs benchmark
  - Risk/Reward Calculator
"""

import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from scipy import stats


# ══════════════════════════════════════════════════════════════════════════════
# RETURN METRICS
# ══════════════════════════════════════════════════════════════════════════════

def calculate_returns(df: pd.DataFrame) -> pd.Series:
    return df["Close"].pct_change().dropna()


def annualized_return(returns: pd.Series, periods_per_year: int = 252) -> float:
    if len(returns) == 0:
        return 0.0
    total = (1 + returns).prod()
    n = len(returns)
    return (total ** (periods_per_year / n) - 1) * 100


def annualized_volatility(returns: pd.Series, periods_per_year: int = 252) -> float:
    return returns.std() * np.sqrt(periods_per_year) * 100


# ══════════════════════════════════════════════════════════════════════════════
# VALUE AT RISK (VaR) & CVaR
# ══════════════════════════════════════════════════════════════════════════════

def calculate_var(returns: pd.Series, confidence: float = 0.95,
                  investment: float = 100_000_000) -> dict:
    """
    3 metode VaR:
    1. Historical Simulation
    2. Parametric (Normal Distribution)
    3. Monte Carlo
    """
    if len(returns) < 30:
        return {}

    # 1. Historical VaR
    hist_var_pct = float(np.percentile(returns, (1 - confidence) * 100))
    hist_var_idr = abs(hist_var_pct) * investment

    # 2. Parametric VaR
    mu   = returns.mean()
    sigma = returns.std()
    z    = stats.norm.ppf(1 - confidence)
    para_var_pct = mu + z * sigma
    para_var_idr = abs(para_var_pct) * investment

    # 3. Monte Carlo VaR
    np.random.seed(42)
    mc_returns = np.random.normal(mu, sigma, 10_000)
    mc_var_pct = float(np.percentile(mc_returns, (1 - confidence) * 100))
    mc_var_idr = abs(mc_var_pct) * investment

    # CVaR (Expected Shortfall) — rata-rata loss di bawah VaR
    threshold    = np.percentile(returns, (1 - confidence) * 100)
    cvar_pct     = float(returns[returns <= threshold].mean())
    cvar_idr     = abs(cvar_pct) * investment

    return {
        "confidence":    confidence * 100,
        "investment":    investment,
        "historical":    {"pct": hist_var_pct * 100, "idr": hist_var_idr},
        "parametric":    {"pct": para_var_pct * 100, "idr": para_var_idr},
        "monte_carlo":   {"pct": mc_var_pct   * 100, "idr": mc_var_idr},
        "cvar":          {"pct": cvar_pct      * 100, "idr": cvar_idr},
    }


# ══════════════════════════════════════════════════════════════════════════════
# PERFORMANCE RATIOS
# ══════════════════════════════════════════════════════════════════════════════

def calculate_performance_ratios(returns: pd.Series,
                                  benchmark_returns: pd.Series = None,
                                  risk_free_rate: float = 0.06) -> dict:
    """
    Hitung semua rasio performa standar institusional.
    risk_free_rate: annualized (misal 0.06 = 6% per tahun BI Rate)
    """
    if len(returns) < 20:
        return {}

    rf_daily   = (1 + risk_free_rate) ** (1 / 252) - 1
    excess_ret = returns - rf_daily

    ann_ret = annualized_return(returns)
    ann_vol = annualized_volatility(returns)

    # Sharpe Ratio
    sharpe = (ann_ret / 100 - risk_free_rate) / (ann_vol / 100) if ann_vol != 0 else 0

    # Sortino Ratio (hanya downside deviation)
    downside = returns[returns < rf_daily]
    downside_std = downside.std() * np.sqrt(252) * 100
    sortino = (ann_ret / 100 - risk_free_rate) / (downside_std / 100) if downside_std != 0 else 0

    # Maximum Drawdown
    cumulative = (1 + returns).cumprod()
    rolling_max = cumulative.cummax()
    drawdown  = (cumulative - rolling_max) / rolling_max
    max_dd    = drawdown.min() * 100

    # Calmar Ratio
    calmar = (ann_ret / 100) / abs(max_dd / 100) if max_dd != 0 else 0

    # Win Rate & Profit Factor
    wins    = returns[returns > 0]
    losses  = returns[returns < 0]
    win_rate    = len(wins) / len(returns) * 100
    avg_win     = wins.mean() * 100  if len(wins)   > 0 else 0
    avg_loss    = losses.mean() * 100 if len(losses) > 0 else 0
    profit_factor = abs(avg_win / avg_loss) if avg_loss != 0 else float("inf")

    # Beta vs benchmark
    beta, alpha, corr = None, None, None
    if benchmark_returns is not None and len(benchmark_returns) > 20:
        aligned = pd.concat([returns, benchmark_returns], axis=1).dropna()
        if len(aligned) > 20:
            cov    = aligned.cov().iloc[0, 1]
            var_bm = aligned.iloc[:, 1].var()
            beta   = cov / var_bm if var_bm != 0 else None
            alpha  = ann_ret / 100 - (risk_free_rate + beta * (annualized_return(benchmark_returns) / 100 - risk_free_rate)) if beta else None
            corr   = aligned.corr().iloc[0, 1]

    # Skewness & Kurtosis
    skew = returns.skew()
    kurt = returns.kurt()

    return {
        "annualized_return":  round(ann_ret,  2),
        "annualized_vol":     round(ann_vol,  2),
        "sharpe_ratio":       round(sharpe,   3),
        "sortino_ratio":      round(sortino,  3),
        "calmar_ratio":       round(calmar,   3),
        "max_drawdown":       round(max_dd,   2),
        "win_rate":           round(win_rate, 1),
        "avg_win":            round(avg_win,  3),
        "avg_loss":           round(avg_loss, 3),
        "profit_factor":      round(profit_factor, 2) if profit_factor != float("inf") else "∞",
        "beta":               round(beta,  3) if beta  is not None else None,
        "alpha":              round(alpha * 100, 2) if alpha is not None else None,
        "correlation":        round(corr,  3) if corr  is not None else None,
        "skewness":           round(skew,  3),
        "kurtosis":           round(kurt,  3),
        "total_trading_days": len(returns),
    }


# ══════════════════════════════════════════════════════════════════════════════
# MONTE CARLO PRICE SIMULATION
# ══════════════════════════════════════════════════════════════════════════════

def monte_carlo_simulation(df: pd.DataFrame, days: int = 30,
                            simulations: int = 500) -> dict:
    """
    Simulasi harga masa depan menggunakan Geometric Brownian Motion (GBM).
    """
    returns = calculate_returns(df)
    if len(returns) < 20:
        return {}

    mu     = returns.mean()
    sigma  = returns.std()
    current_price = df["Close"].iloc[-1]

    np.random.seed(42)
    dt     = 1
    paths  = np.zeros((simulations, days + 1))
    paths[:, 0] = current_price

    for t in range(1, days + 1):
        z = np.random.standard_normal(simulations)
        paths[:, t] = paths[:, t - 1] * np.exp((mu - 0.5 * sigma ** 2) * dt + sigma * np.sqrt(dt) * z)

    final_prices = paths[:, -1]

    return {
        "paths":          paths,
        "days":           days,
        "simulations":    simulations,
        "current_price":  current_price,
        "mean_price":     float(final_prices.mean()),
        "median_price":   float(np.median(final_prices)),
        "p5_price":       float(np.percentile(final_prices, 5)),
        "p25_price":      float(np.percentile(final_prices, 25)),
        "p75_price":      float(np.percentile(final_prices, 75)),
        "p95_price":      float(np.percentile(final_prices, 95)),
        "prob_profit":    float((final_prices > current_price).mean() * 100),
        "max_upside":     float((final_prices.max() / current_price - 1) * 100),
        "max_downside":   float((final_prices.min() / current_price - 1) * 100),
    }


def plot_monte_carlo(mc: dict, ticker: str) -> go.Figure:
    if not mc:
        return go.Figure()

    paths = mc["paths"]
    days  = mc["days"]
    x_axis = list(range(days + 1))

    fig = go.Figure()

    # Plot sample paths (max 100 untuk performa)
    sample_paths = paths[:100]
    for path in sample_paths:
        fig.add_trace(go.Scatter(
            x=x_axis, y=path.tolist(),
            mode="lines", line=dict(width=0.4, color="rgba(33,150,243,0.15)"),
            showlegend=False, hoverinfo="skip",
        ))

    # Percentile bands
    p5  = np.percentile(paths, 5,  axis=0)
    p25 = np.percentile(paths, 25, axis=0)
    p50 = np.percentile(paths, 50, axis=0)
    p75 = np.percentile(paths, 75, axis=0)
    p95 = np.percentile(paths, 95, axis=0)

    for lower, upper, color, name in [
        (p5, p95, "rgba(239,83,80,0.15)",   "90% CI"),
        (p25, p75, "rgba(38,166,154,0.25)", "50% CI"),
    ]:
        fig.add_trace(go.Scatter(x=x_axis + x_axis[::-1],
                                  y=upper.tolist() + lower.tolist()[::-1],
                                  fill="toself", fillcolor=color,
                                  line=dict(width=0), name=name, showlegend=True))

    fig.add_trace(go.Scatter(x=x_axis, y=p50.tolist(), name="Median",
                              line=dict(color="#FFD700", width=2)))
    fig.add_hline(y=mc["current_price"], line=dict(color="white", width=1, dash="dot"),
                  annotation_text="Harga Saat Ini")

    fig.update_layout(
        title=(f"<b>{ticker}</b> — Monte Carlo {mc['simulations']} Simulasi × {days} Hari | "
               f"Prob. Profit: {mc['prob_profit']:.1f}%"),
        height=500, template="plotly_dark",
        xaxis_title="Hari ke depan",
        yaxis_title="Harga",
        paper_bgcolor="#0E1117", plot_bgcolor="#161B22",
    )
    return fig


# ══════════════════════════════════════════════════════════════════════════════
# KELLY CRITERION — Position Sizing
# ══════════════════════════════════════════════════════════════════════════════

def kelly_criterion(returns: pd.Series, risk_free_rate: float = 0.06) -> dict:
    """
    Kelly Criterion: ukuran posisi optimal berdasarkan statistik historis.
    Full Kelly sering terlalu agresif → gunakan Half/Quarter Kelly.
    """
    if len(returns) < 20:
        return {}

    rf_daily = (1 + risk_free_rate) ** (1 / 252) - 1
    wins     = returns[returns > rf_daily]
    losses   = returns[returns <= rf_daily]

    if len(losses) == 0:
        return {}

    win_prob  = len(wins) / len(returns)
    loss_prob = 1 - win_prob
    avg_win   = wins.mean()
    avg_loss  = abs(losses.mean())

    # Kelly % = W/L - (1-W)/W
    odds  = avg_win / avg_loss if avg_loss > 0 else 1
    kelly = win_prob - loss_prob / odds if odds > 0 else 0
    kelly = max(0, min(kelly, 1))  # clamp 0–100%

    return {
        "kelly_full":     round(kelly * 100, 2),
        "kelly_half":     round(kelly * 50,  2),
        "kelly_quarter":  round(kelly * 25,  2),
        "win_probability": round(win_prob * 100, 1),
        "avg_win_pct":    round(avg_win * 100,   3),
        "avg_loss_pct":   round(avg_loss * 100,  3),
        "win_loss_ratio": round(odds,             3),
        "recommendation": (
            "Full Kelly" if kelly > 0.3 else
            "Half Kelly (lebih aman)" if kelly > 0.15 else
            "Quarter Kelly (konservatif)"
        ),
    }


# ══════════════════════════════════════════════════════════════════════════════
# RISK / REWARD CALCULATOR
# ══════════════════════════════════════════════════════════════════════════════

def calculate_risk_reward(entry: float, stop_loss: float, target: float,
                           capital: float = 100_000_000,
                           risk_pct: float = 0.02) -> dict:
    """
    Hitung risk/reward dan ukuran posisi optimal.
    risk_pct: berapa % capital yang direlakan per trade (default 2%)
    """
    if entry <= 0 or stop_loss <= 0 or target <= 0:
        return {}

    risk_per_share   = abs(entry - stop_loss)
    reward_per_share = abs(target - entry)
    rr_ratio         = reward_per_share / risk_per_share if risk_per_share > 0 else 0

    max_loss_idr     = capital * risk_pct
    shares           = int(max_loss_idr / risk_per_share) if risk_per_share > 0 else 0
    position_value   = shares * entry
    potential_profit = shares * reward_per_share
    potential_loss   = shares * risk_per_share

    return {
        "entry":           entry,
        "stop_loss":       stop_loss,
        "target":          target,
        "risk_per_share":  risk_per_share,
        "reward_per_share": reward_per_share,
        "rr_ratio":        round(rr_ratio, 2),
        "risk_pct":        risk_pct * 100,
        "shares":          shares,
        "position_value":  position_value,
        "potential_profit": potential_profit,
        "potential_loss":  potential_loss,
        "breakeven_winrate": round(1 / (1 + rr_ratio) * 100, 1) if rr_ratio > 0 else 50,
    }


# ══════════════════════════════════════════════════════════════════════════════
# DRAWDOWN CHART
# ══════════════════════════════════════════════════════════════════════════════

def plot_performance_dashboard(df: pd.DataFrame, ratios: dict, ticker: str) -> go.Figure:
    returns    = calculate_returns(df)
    cumulative = (1 + returns).cumprod()
    rolling_max = cumulative.cummax()
    drawdown    = (cumulative - rolling_max) / rolling_max * 100

    fig = make_subplots(rows=3, cols=1, shared_xaxes=True,
                        row_heights=[0.4, 0.3, 0.3],
                        subplot_titles=["Cumulative Return (%)", "Drawdown (%)", "Daily Return (%)"],
                        vertical_spacing=0.06)

    # Cumulative return
    cum_pct = (cumulative - 1) * 100
    fig.add_trace(go.Scatter(x=cum_pct.index, y=cum_pct,
                              name="Cum. Return", line=dict(color="#2196F3", width=1.5),
                              fill="tozeroy", fillcolor="rgba(33,150,243,0.1)"), row=1, col=1)

    # Drawdown
    fig.add_trace(go.Scatter(x=drawdown.index, y=drawdown,
                              name="Drawdown", line=dict(color="#EF5350", width=1),
                              fill="tozeroy", fillcolor="rgba(239,83,80,0.15)"), row=2, col=1)

    # Daily returns
    ret_colors = ["#26A69A" if r >= 0 else "#EF5350" for r in returns]
    fig.add_trace(go.Bar(x=returns.index, y=returns * 100,
                          marker_color=ret_colors, name="Daily Return"), row=3, col=1)

    # Annotations
    sharpe = ratios.get("sharpe_ratio", 0)
    sortino = ratios.get("sortino_ratio", 0)
    max_dd  = ratios.get("max_drawdown",  0)
    ann_ret = ratios.get("annualized_return", 0)

    fig.update_layout(
        title=(f"<b>{ticker}</b> — Performance Dashboard | "
               f"Return: {ann_ret:.1f}% | Sharpe: {sharpe:.2f} | "
               f"Sortino: {sortino:.2f} | Max DD: {max_dd:.1f}%"),
        height=600, template="plotly_dark",
        paper_bgcolor="#0E1117", plot_bgcolor="#161B22",
        showlegend=False,
    )
    return fig
