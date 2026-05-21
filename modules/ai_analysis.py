"""
AI Analysis — powered by Claude Opus 4.7
------------------------------------------
Prompt dirancang seperti analis institusional tier-1:
mengintegrasikan SMC, Fibonacci, Wyckoff, VaR, MTF, Fundamental, dan Makro.
"""

import anthropic
from config import ANTHROPIC_API_KEY

MODEL = "claude-opus-4-7"   # Model terbaru dan terkuat


def get_ai_analysis(
    ticker: str,
    company_name: str,
    current_price: dict,
    tech_signals: dict,
    fund_metrics: dict,
    fund_score: dict,
    news_articles: list,
    macro_env: dict,
    sr_levels: dict,
    # Extended data (optional)
    smc_bias: dict = None,
    wyckoff: dict = None,
    fib: dict = None,
    mtf: dict = None,
    ratios: dict = None,
    var_data: dict = None,
    mc_data: dict = None,
    kelly: dict = None,
    candle_patterns: list = None,
    divergences: list = None,
    vp: dict = None,
) -> str:

    if not ANTHROPIC_API_KEY:
        return "⚠️ API Key Anthropic belum diset. Tambahkan ANTHROPIC_API_KEY di file .env"

    prompt = _build_prompt(
        ticker, company_name, current_price, tech_signals, fund_metrics,
        fund_score, news_articles, macro_env, sr_levels, smc_bias, wyckoff,
        fib, mtf, ratios, var_data, mc_data, kelly, candle_patterns, divergences, vp,
    )

    try:
        client  = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
        message = client.messages.create(
            model=MODEL,
            max_tokens=4096,
            system=_system_prompt(),
            messages=[{"role": "user", "content": prompt}],
        )
        return message.content[0].text

    except anthropic.AuthenticationError:
        return "❌ API Key tidak valid. Periksa ANTHROPIC_API_KEY di file .env"
    except anthropic.RateLimitError:
        return "❌ Rate limit tercapai. Coba lagi dalam beberapa menit."
    except Exception as e:
        return f"❌ Error: {str(e)}"


def _system_prompt() -> str:
    return """Anda adalah Chief Investment Analyst dengan spesialisasi di:
- Smart Money Concepts (SMC) dan institusional trading
- Analisis teknikal multi-timeframe (Wyckoff, Fibonacci, VSA)
- Kuantitatif finance (VaR, Monte Carlo, factor models)
- Fundamental analysis (DCF, relative valuation)
- Makro ekonomi global dan Indonesia

Gaya analisis Anda:
- Presisi dan berbasis data — setiap pernyataan didukung angka
- Prioritaskan confluensi sinyal (3+ sinyal searah = setup kuat)
- Selalu sertakan level konkret (harga entry, target, stop loss)
- Risk management sebagai prioritas utama
- Gunakan framework: Trend → Structure → Entry → Target → Stop

Anda menulis dalam Bahasa Indonesia profesional."""


def _build_prompt(
    ticker, company_name, current_price, tech_signals, fund_metrics,
    fund_score, news_articles, macro_env, sr_levels, smc_bias, wyckoff,
    fib, mtf, ratios, var_data, mc_data, kelly, candle_patterns, divergences, vp,
) -> str:

    price    = current_price.get("price", "N/A")
    pct      = current_price.get("pct_change", 0)
    tech_rec = tech_signals.get("_overall", {}).get("recommendation", "N/A")
    tech_pct = tech_signals.get("_overall", {}).get("pct", 0)

    sections = [f"""# ANALISIS SAHAM: {ticker} ({company_name})

## 📍 DATA HARGA
- Harga: **{_f(price)}**  |  Perubahan hari ini: **{_f(pct)}%**
- Volume rasio: {tech_signals.get('Volume', {}).get('note', 'N/A')}
"""]

    # ── SMC ──────────────────────────────────────────────────────────────────
    if smc_bias:
        sections.append(f"""## 🏦 SMART MONEY CONCEPTS (SMC)
- **Bias SMC:** {smc_bias.get('bias', 'N/A')} (Skor: {smc_bias.get('score', 0)})
{chr(10).join('- ' + n for n in smc_bias.get('notes', []))}
""")

    # ── Multi-Timeframe ───────────────────────────────────────────────────────
    if mtf:
        overall_mtf = mtf.pop("overall", {})
        mtf_lines = [f"- **Overall MTF:** {overall_mtf.get('bias', 'N/A')}"]
        for tf, data in mtf.items():
            mtf_lines.append(f"- {tf}: {data.get('trend', 'N/A')} (MA: {data.get('ma', 'N/A')})")
        mtf["overall"] = overall_mtf
        sections.append("## ⏱️ MULTI-TIMEFRAME ANALYSIS\n" + "\n".join(mtf_lines) + "\n")

    # ── Wyckoff ───────────────────────────────────────────────────────────────
    if wyckoff:
        sections.append(f"""## 📊 WYCKOFF PHASE
- **Fase:** {wyckoff.get('phase', 'N/A')}
- {wyckoff.get('description', '')}
- **Action:** {wyckoff.get('action', '')}
- Tren 20 hari: {wyckoff.get('price_trend_20', 0):+.1f}%  |  Tren 60 hari: {wyckoff.get('price_trend_60', 0):+.1f}%
""")

    # ── Fibonacci ─────────────────────────────────────────────────────────────
    if fib:
        near_sup = fib.get("nearest_support")
        near_res = fib.get("nearest_resistance")
        sections.append(f"""## 📐 FIBONACCI AUTO
- Arah: {fib.get('direction', 'N/A')}
- Swing High: {_f(fib.get('swing_high'))}  |  Swing Low: {_f(fib.get('swing_low'))}
- Support Fib terdekat: {f"{near_sup[0]:.3f} = {_f(near_sup[1])}" if near_sup else 'N/A'}
- Resistance Fib terdekat: {f"{near_res[0]:.3f} = {_f(near_res[1])}" if near_res else 'N/A'}
""")

    # ── Candlestick Patterns ──────────────────────────────────────────────────
    if candle_patterns:
        patt_lines = [f"- {p['name']}: {p['desc']} [{p['signal']}]" for p in candle_patterns[-3:]]
        sections.append("## 🕯️ POLA CANDLESTICK TERKINI\n" + "\n".join(patt_lines) + "\n")

    # ── Divergences ───────────────────────────────────────────────────────────
    if divergences:
        div_lines = [f"- {d['type']}: {d['desc']}" for d in divergences[-3:]]
        sections.append("## 🔀 DIVERGENCE\n" + "\n".join(div_lines) + "\n")

    # ── Volume Profile ────────────────────────────────────────────────────────
    if vp:
        sections.append(f"""## 📊 VOLUME PROFILE (VPVR)
- POC (Point of Control): {_f(vp.get('poc'))}
- VAH (Value Area High): {_f(vp.get('vah'))}
- VAL (Value Area Low):  {_f(vp.get('val'))}
- Posisi harga: {"di atas POC (bullish)" if (vp.get("current", 0) or 0) > (vp.get("poc", 0) or 0) else "di bawah POC (bearish)"}
""")

    # ── Classic Technical ─────────────────────────────────────────────────────
    sections.append(f"""## 📈 ANALISIS TEKNIKAL KLASIK
- Rekomendasi: **{tech_rec}** (Skor: {tech_pct:+.1f}%)
{_format_tech_signals(tech_signals)}

## 🎯 SUPPORT & RESISTANCE
- Support: {', '.join([_f(s) for s in sr_levels.get('supports', [])[:3]]) or 'N/A'}
- Resistance: {', '.join([_f(r) for r in sr_levels.get('resistances', [])[:3]]) or 'N/A'}
- 52W High: {_f(sr_levels.get('52w_high'))}  |  52W Low: {_f(sr_levels.get('52w_low'))}
""")

    # ── Quantitative Risk ─────────────────────────────────────────────────────
    if ratios:
        sections.append(f"""## 📉 QUANTITATIVE RISK METRICS
- Annual Return: {ratios.get('annualized_return', 'N/A')}%
- Annual Volatility: {ratios.get('annualized_vol', 'N/A')}%
- Sharpe Ratio: {ratios.get('sharpe_ratio', 'N/A')} {"🟢 Baik" if (ratios.get('sharpe_ratio') or 0) > 1 else "🔴 Rendah"}
- Sortino Ratio: {ratios.get('sortino_ratio', 'N/A')}
- Calmar Ratio: {ratios.get('calmar_ratio', 'N/A')}
- Max Drawdown: {ratios.get('max_drawdown', 'N/A')}%
- Win Rate: {ratios.get('win_rate', 'N/A')}%  |  Profit Factor: {ratios.get('profit_factor', 'N/A')}
- Beta: {ratios.get('beta', 'N/A')}  |  Skewness: {ratios.get('skewness', 'N/A')}
""")

    if var_data:
        sections.append(f"""## 🎰 VALUE AT RISK ({var_data.get('confidence', 95):.0f}% CI)
- Historical VaR: {_f(var_data.get('historical', {}).get('pct', 0))}%
- Parametric VaR: {_f(var_data.get('parametric', {}).get('pct', 0))}%
- Monte Carlo VaR: {_f(var_data.get('monte_carlo', {}).get('pct', 0))}%
- CVaR (Expected Shortfall): {_f(var_data.get('cvar', {}).get('pct', 0))}%
""")

    if mc_data:
        sections.append(f"""## 🎲 MONTE CARLO SIMULATION ({mc_data.get('days', 30)} hari)
- Probabilitas profit: **{mc_data.get('prob_profit', 0):.1f}%**
- Median target price: {_f(mc_data.get('median_price'))}
- P5 (worst 5%): {_f(mc_data.get('p5_price'))}
- P95 (best 5%): {_f(mc_data.get('p95_price'))}
""")

    if kelly:
        sections.append(f"""## 💰 KELLY CRITERION (Position Sizing)
- Full Kelly: {kelly.get('kelly_full', 0):.1f}% kapital
- Half Kelly (recommended): {kelly.get('kelly_half', 0):.1f}% kapital
- Win probability: {kelly.get('win_probability', 0):.1f}%
- W/L Ratio: {kelly.get('win_loss_ratio', 0):.2f}
- Rekomendasi: {kelly.get('recommendation', 'N/A')}
""")

    # ── Fundamental ───────────────────────────────────────────────────────────
    sections.append(f"""## 💰 FUNDAMENTAL
- Rating: **{fund_score.get('rating', 'N/A')}** (Skor: {fund_score.get('pct', 0):.1f}%)
- P/E: {_f(fund_metrics.get('P/E Ratio (TTM)'), 1)}x  |  P/B: {_f(fund_metrics.get('P/B Ratio'), 2)}x
- ROE: {_f(fund_metrics.get('ROE (%)'))}%  |  Net Margin: {_f(fund_metrics.get('Profit Margin (%)'))}%
- Revenue Growth: {_f(fund_metrics.get('Revenue Growth (YoY %)'))}%
- Earnings Growth: {_f(fund_metrics.get('Earnings Growth (YoY %)'))}%
- Debt/Equity: {_f(fund_metrics.get('Debt/Equity'), 1)}%
- Dividend Yield: {_f(fund_metrics.get('Dividend Yield (%)'))}%
""")

    # ── News & Macro ──────────────────────────────────────────────────────────
    news_summary = _summarize_news(news_articles)
    sections.append(f"""## 📰 BERITA & SENTIMEN
{news_summary}

## 🌍 MAKRO EKONOMI
- Environment: **{macro_env.get('environment', 'N/A')}**
- {macro_env.get('description', '')}
- Peluang: {'; '.join(macro_env.get('opportunities', [])[:3]) or 'Tidak ada'}
- Risiko: {'; '.join(macro_env.get('risk_factors', [])[:3]) or 'Tidak ada'}
""")

    # ── Request output ────────────────────────────────────────────────────────
    sections.append("""---
## INSTRUKSI OUTPUT

Berikan analisis komprehensif dalam format berikut (Bahasa Indonesia, profesional):

## 🎯 EXECUTIVE SUMMARY & REKOMENDASI
**[STRONG BUY / BUY / HOLD / SELL / STRONG SELL]**
[2-3 kalimat justifikasi utama berdasarkan confluensi sinyal]

## 🏦 ANALISIS SMART MONEY CONCEPTS
[Jelaskan kondisi struktur pasar, order blocks aktif, FVG, dan bias institusional]

## ⏱️ ANALISIS MULTI-TIMEFRAME
[Sinkronisasi tren dari weekly hingga intraday — apakah aligned?]

## 📊 WYCKOFF & MARKET STRUCTURE
[Fase Wyckoff saat ini dan implikasinya untuk trader]

## 📐 FIBONACCI & KEY LEVELS
[Level Fibonacci kritis sebagai support/resistance]

## 📈 TEKNIKAL & MOMENTUM
[RSI, MACD, BB — kondisi momentum dan divergensi]

## 🕯️ PRICE ACTION & PATTERNS
[Pola candlestick terkini dan maknanya]

## 💰 FUNDAMENTAL & VALUASI
[Apakah saham murah/mahal secara fundamental? Bandingkan dengan peers]

## 📉 RISK ASSESSMENT
- Sharpe/Sortino: [interpretasi]
- Max Drawdown: [berapa % risiko historis]
- VaR: [risiko per hari dalam Rupiah untuk investasi Rp 100jt]
- Monte Carlo: [probabilitas dan skenario]

## 🎲 STRATEGI TRADING

### Setup Entry:
- **Tipe:** [Breakout / Pullback / Reversal]
- **Entry Ideal:** [level harga spesifik]
- **Konfirmasi yang diperlukan:** [volume, candle close, dll]

### Target & Stop Loss:
| Level | Harga | % dari Entry |
|-------|-------|-------------|
| Stop Loss | Rp X | -X% |
| Target 1 | Rp X | +X% |
| Target 2 | Rp X | +X% |
| Target 3 | Rp X | +X% |

- **Risk/Reward Ratio:** X:1
- **Time Horizon:** [Intraday / Swing 3-5 hari / Position 2-4 minggu]

### Position Sizing (Modal Rp 100 juta):
- **Alokasi (Kelly):** [% dan nominal]
- **Jumlah lot:** [estimasi]

## ⚠️ RISIKO & KATALIS

### Risiko Utama:
1. [Risiko spesifik 1]
2. [Risiko spesifik 2]
3. [Risiko spesifik 3]

### Katalis Positif:
1. [Katalis 1]
2. [Katalis 2]
3. [Katalis 3]

## 📋 KESIMPULAN
[Ringkasan 3-4 kalimat: level kunci, setup, kondisi market, satu aksi konkret]
""")

    return "\n".join(sections)


def _f(val, decimals: int = 2) -> str:
    if val is None:
        return "N/A"
    try:
        return f"{float(val):.{decimals}f}"
    except Exception:
        return str(val)


def _format_tech_signals(signals: dict) -> str:
    lines = []
    for key, val in signals.items():
        if key.startswith("_"):
            continue
        s    = val.get("signal", "")
        note = val.get("note", "")
        icon = "🟢" if "BUY" in s else ("🔴" if "SELL" in s else "⚪")
        lines.append(f"  - {key}: {icon} {s} — {note}")
    return "\n".join(lines) or "  N/A"


def _summarize_news(articles: list) -> str:
    if not articles:
        return "Tidak ada berita tersedia."
    bull = sum(1 for a in articles if a.get("sentiment", {}).get("label") == "Bullish")
    bear = sum(1 for a in articles if a.get("sentiment", {}).get("label") == "Bearish")
    total = len(articles)
    headlines = [f"  {'🟢' if a.get('sentiment',{}).get('label')=='Bullish' else '🔴' if a.get('sentiment',{}).get('label')=='Bearish' else '⚪'} {(a.get('title_clean') or a.get('title',''))[:100]}"
                 for a in articles[:5]]
    return f"Total {total} berita: {bull} Bullish, {bear} Bearish\n" + "\n".join(headlines)
