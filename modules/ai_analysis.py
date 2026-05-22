"""
AI Analysis — powered by Claude claude-opus-4-5 (latest)
------------------------------------------
Prompt dirancang seperti analis institusional tier-1:
mengintegrasikan SMC, Fibonacci, Wyckoff, VaR, MTF, Fundamental, dan Makro.
"""

import anthropic
from config import ANTHROPIC_API_KEY

MODEL = "claude-opus-4-5"   # Model terkuat Claude


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
        client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

        # Gunakan streaming untuk response lebih cepat dan stabil
        full_text = ""
        with client.messages.stream(
            model=MODEL,
            max_tokens=8192,
            system=_system_prompt(),
            messages=[{"role": "user", "content": prompt}],
        ) as stream:
            for text in stream.text_stream:
                full_text += text

        return full_text

    except anthropic.AuthenticationError:
        return "❌ API Key tidak valid. Periksa ANTHROPIC_API_KEY di file .env"
    except anthropic.RateLimitError:
        return "❌ Rate limit tercapai. Coba lagi dalam beberapa menit."
    except anthropic.BadRequestError as e:
        # Fallback ke claude-sonnet-4-5 jika model tidak tersedia
        try:
            client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
            full_text = ""
            with client.messages.stream(
                model="claude-sonnet-4-5",
                max_tokens=8192,
                system=_system_prompt(),
                messages=[{"role": "user", "content": prompt}],
            ) as stream:
                for text in stream.text_stream:
                    full_text += text
            return full_text
        except Exception as e2:
            return f"❌ Error: {str(e2)}"
    except Exception as e:
        return f"❌ Error: {str(e)}"


def _system_prompt() -> str:
    return """Anda adalah **Chief Investment Analyst** kelas dunia dengan keahlian:

**TEKNIKAL & PRICE ACTION:**
- Smart Money Concepts (SMC): Order Blocks, FVG, BOS/CHoCH, Liquidity Sweep
- Wyckoff Method: Accumulation/Distribution phase detection
- Multi-Timeframe Analysis: alignment dari Monthly → Weekly → Daily → H4
- Fibonacci: retracement, extension, dan confluensi level kritis
- Volume Spread Analysis (VSA) dan Volume Profile (VPVR)
- Pola candlestick institusional dan divergensi RSI/MACD

**KUANTITATIF:**
- Value at Risk (VaR, CVaR) dengan confidence interval
- Monte Carlo simulation untuk probabilistik harga
- Kelly Criterion untuk optimal position sizing
- Sharpe, Sortino, Calmar Ratio untuk risk-adjusted return
- Factor models: momentum, value, quality

**FUNDAMENTAL:**
- DCF valuation dan relative valuation (P/E, P/B, EV/EBITDA)
- Quality screening: ROE, ROIC, margin trends
- Growth vs value assessment

**MAKRO & SENTIMEN:**
- Siklus ekonomi Indonesia dan global
- Dampak USD/IDR, komoditas terhadap sektor IDX
- Flow analysis: asing vs domestik
- Sentiment positioning

**GAYA ANALISIS:**
- Setiap klaim WAJIB didukung angka spesifik dari data
- Identifikasi confluensi 3+ sinyal searah = HIGH CONVICTION setup
- Risk/Reward minimum 1:2 untuk setiap rekomendasi
- Berikan level harga KONKRET untuk entry, stop loss, dan target
- Framework: Context → Structure → Setup → Execution → Management

Tulis dalam **Bahasa Indonesia profesional**, gunakan format markdown yang rapi.
Jadilah BERANI dalam rekomendasi — analis yang baik bukan yang selalu "HOLD"."""


def _build_prompt(
    ticker, company_name, current_price, tech_signals, fund_metrics,
    fund_score, news_articles, macro_env, sr_levels, smc_bias, wyckoff,
    fib, mtf, ratios, var_data, mc_data, kelly, candle_patterns, divergences, vp,
) -> str:

    price    = current_price.get("price", "N/A")
    chg      = current_price.get("change", 0) or 0
    pct      = current_price.get("pct_change", 0) or 0
    vol      = current_price.get("volume", 0) or 0
    high     = current_price.get("high")
    low      = current_price.get("low")
    tech_rec = tech_signals.get("_overall", {}).get("recommendation", "N/A")
    tech_pct = tech_signals.get("_overall", {}).get("pct", 0)

    sections = [f"""# DATA INPUT ANALISIS: {ticker} ({company_name})

## 📍 DATA HARGA TERKINI
| Metrik | Nilai |
|--------|-------|
| Harga | **Rp {_f(price, 0)}** |
| Perubahan | **{chg:+.0f} ({pct:+.2f}%)** |
| High Hari Ini | Rp {_f(high, 0)} |
| Low Hari Ini | Rp {_f(low, 0)} |
| Volume | {vol:,.0f} |
"""]

    # ── SMC ──────────────────────────────────────────────────────────────────
    if smc_bias:
        _bs = smc_bias if isinstance(smc_bias, dict) else {}
        _score = _bs.get("score", 0)
        _bias  = "BULLISH" if _score > 0 else ("BEARISH" if _score < 0 else "NEUTRAL")
        sections.append(f"""## 🏦 SMART MONEY CONCEPTS (SMC)
- **Bias Institusional:** {_bias} (Skor: {_score})
- **Order Blocks Aktif:** {_bs.get('order_blocks', 'N/A')}
- **FVG Unfilled:** {_bs.get('fvg_count', 'N/A')}
- **BOS/CHoCH:** {_bs.get('bos_choch', 'N/A')}
{chr(10).join('- ' + n for n in _bs.get('notes', [])[:5])}
""")

    # ── Multi-Timeframe ───────────────────────────────────────────────────────
    if mtf:
        _mtf_copy = dict(mtf)
        overall_mtf = _mtf_copy.pop("overall", {})
        sections.append(f"""## ⏱️ MULTI-TIMEFRAME ANALYSIS
- **Overall Bias:** {overall_mtf.get('bias', 'N/A')} (Skor: {overall_mtf.get('score', 0)})
""" + "\n".join(
            f"- **{tf.upper()}:** Trend={data.get('trend','N/A')} | MA={data.get('ma','N/A')} | Bias={data.get('bias','N/A')}"
            for tf, data in _mtf_copy.items() if isinstance(data, dict)
        ) + "\n")

    # ── Wyckoff ───────────────────────────────────────────────────────────────
    if wyckoff and isinstance(wyckoff, dict):
        sections.append(f"""## 📊 WYCKOFF PHASE ANALYSIS
- **Fase:** {wyckoff.get('phase', 'N/A')}
- **Deskripsi:** {wyckoff.get('description', 'N/A')}
- **Action:** {wyckoff.get('action', 'N/A')}
- Tren 20H: {wyckoff.get('price_trend_20', 0):+.2f}% | Tren 60H: {wyckoff.get('price_trend_60', 0):+.2f}%
- Volume Trend: {wyckoff.get('vol_trend', 'N/A')}
""")

    # ── Fibonacci ─────────────────────────────────────────────────────────────
    if fib and isinstance(fib, dict):
        near_sup = fib.get("nearest_support")
        near_res = fib.get("nearest_resistance")
        fib_levels = fib.get("levels", {})
        sections.append(f"""## 📐 FIBONACCI AUTO-LEVELS
- **Arah:** {fib.get('direction', 'N/A')}
- **Swing High:** Rp {_f(fib.get('swing_high'), 0)} | **Swing Low:** Rp {_f(fib.get('swing_low'), 0)}
- **Support Fib Terdekat:** {f"{near_sup[0]:.3f} = Rp {_f(near_sup[1], 0)}" if near_sup else 'N/A'}
- **Resistance Fib Terdekat:** {f"{near_res[0]:.3f} = Rp {_f(near_res[1], 0)}" if near_res else 'N/A'}
- **Semua Level:** {' | '.join(f"{k}=Rp{_f(v,0)}" for k,v in list(fib_levels.items())[:6])}
""")

    # ── Volume Profile ────────────────────────────────────────────────────────
    if vp and isinstance(vp, dict):
        poc = vp.get('poc')
        cur = vp.get('current', 0) or 0
        pos = "DI ATAS POC (bullish pressure)" if cur > (poc or 0) else "DI BAWAH POC (bearish pressure)"
        sections.append(f"""## 📊 VOLUME PROFILE (VPVR)
- **POC (Point of Control):** Rp {_f(poc, 0)} — level dengan volume tertinggi
- **VAH (Value Area High):** Rp {_f(vp.get('vah'), 0)}
- **VAL (Value Area Low):**  Rp {_f(vp.get('val'), 0)}
- **Posisi Harga:** {pos}
""")

    # ── Candlestick Patterns ──────────────────────────────────────────────────
    if candle_patterns:
        sections.append("## 🕯️ POLA CANDLESTICK TERKINI\n" +
            "\n".join(f"- **{p.get('name','?')}** ({p.get('date','')}) — {p.get('desc','')} → Signal: {p.get('signal','?')}"
                      for p in candle_patterns[-5:]) + "\n")

    # ── Divergences ───────────────────────────────────────────────────────────
    if divergences:
        sections.append("## 🔀 DIVERGENCE SIGNALS\n" +
            "\n".join(f"- **{d.get('type','?')}** pada {d.get('indicator','?')}: {d.get('desc','')}"
                      for d in divergences[-4:]) + "\n")

    # ── Classic Technical ─────────────────────────────────────────────────────
    sections.append(f"""## 📈 ANALISIS TEKNIKAL KLASIK
- **Rekomendasi Agregat:** **{tech_rec}** (Skor Bullish: {tech_pct:+.1f}%)
{_format_tech_signals(tech_signals)}

## 🎯 SUPPORT & RESISTANCE
- **Support:** {', '.join([f"Rp {_f(s,0)}" for s in (sr_levels.get('support') or sr_levels.get('supports', []))[:3]]) or 'N/A'}
- **Resistance:** {', '.join([f"Rp {_f(r,0)}" for r in (sr_levels.get('resistance') or sr_levels.get('resistances', []))[:3]]) or 'N/A'}
- **52W High:** Rp {_f(sr_levels.get('52w_high'), 0)} | **52W Low:** Rp {_f(sr_levels.get('52w_low'), 0)}
""")

    # ── Quantitative Risk ─────────────────────────────────────────────────────
    if ratios:
        sections.append(f"""## 📉 QUANTITATIVE RISK METRICS
| Metrik | Nilai | Interpretasi |
|--------|-------|--------------|
| Annual Return | {_f(ratios.get('annual_return'))}% | {'🟢 Positif' if (ratios.get('annual_return') or 0) > 0 else '🔴 Negatif'} |
| Sharpe Ratio | {_f(ratios.get('sharpe_ratio'))} | {'🟢 Excellent' if (ratios.get('sharpe_ratio') or 0) > 2 else '🟡 Good' if (ratios.get('sharpe_ratio') or 0) > 1 else '🔴 Poor'} |
| Sortino Ratio | {_f(ratios.get('sortino_ratio'))} | Downside-adjusted return |
| Max Drawdown | {_f(ratios.get('max_drawdown'))}% | Risiko penurunan historis |
| Calmar Ratio | {_f(ratios.get('calmar_ratio'))} | Return per unit drawdown |
| Win Rate | {_f(ratios.get('win_rate'))}% | Hari dengan return positif |
| Beta | {_f(ratios.get('beta'))} | Sensitivitas vs market |
""")

    if var_data and isinstance(var_data, dict):
        _vh = var_data.get('historical', {}) or {}
        _vp2 = var_data.get('parametric', {}) or {}
        sections.append(f"""## 🎰 VALUE AT RISK (95% Confidence)
- **Historical VaR:** {_f(_vh.get('var_95'))}% per hari
- **CVaR (Expected Shortfall):** {_f(_vh.get('cvar_95'))}% — rata-rata kerugian di skenario terburuk
- **Parametric VaR:** {_f(_vp2.get('var_95'))}%
- *Untuk modal Rp 100 juta: VaR = Rp {abs(float(_vh.get('var_95') or 0)) * 1_000_000:,.0f} per hari*
""")

    if mc_data and isinstance(mc_data, dict):
        sections.append(f"""## 🎲 MONTE CARLO ({mc_data.get('days', 30)} Hari ke Depan)
- **Probabilitas Profit:** **{mc_data.get('prob_profit', 0):.1f}%**
- **Skenario Bear (P5):** Rp {_f(mc_data.get('percentile_5') or mc_data.get('p5_price'), 0)}
- **Skenario Base (P50):** Rp {_f(mc_data.get('percentile_50') or mc_data.get('median_price'), 0)}
- **Skenario Bull (P95):** Rp {_f(mc_data.get('percentile_95') or mc_data.get('p95_price'), 0)}
""")

    if kelly and isinstance(kelly, dict):
        sections.append(f"""## 💰 KELLY CRITERION (Optimal Position Sizing)
- **Full Kelly:** {_f(float(kelly.get('kelly_fraction', kelly.get('kelly_full', 0)) or 0) * 100, 1)}% kapital
- **Half Kelly (rekomendasi):** {_f(float(kelly.get('kelly_fraction', kelly.get('kelly_half', 0)) or 0) * 50, 1)}% kapital
- **Win Rate:** {_f(kelly.get('win_probability', kelly.get('win_rate', 0)))}%
- **Rekomendasi:** {kelly.get('recommendation', 'N/A')}
""")

    # ── Fundamental ───────────────────────────────────────────────────────────
    sections.append(f"""## 💰 FUNDAMENTAL ANALYSIS
- **Rating:** **{fund_score.get('rating', 'N/A')}** (Skor: {fund_score.get('pct', 0):.1f}%)
| Metrik | Nilai |
|--------|-------|
| P/E Ratio | {_f(fund_metrics.get('P/E Ratio (TTM)'), 1)}x |
| P/B Ratio | {_f(fund_metrics.get('P/B Ratio'), 2)}x |
| ROE | {_f(fund_metrics.get('ROE (%)'))}% |
| Net Margin | {_f(fund_metrics.get('Profit Margin (%)'))}% |
| Revenue Growth | {_f(fund_metrics.get('Revenue Growth (YoY %)'))}% YoY |
| Earnings Growth | {_f(fund_metrics.get('Earnings Growth (YoY %)'))}% YoY |
| Debt/Equity | {_f(fund_metrics.get('Debt/Equity'), 1)} |
| Dividend Yield | {_f(fund_metrics.get('Dividend Yield (%)'))}% |
""")

    # ── News & Macro ──────────────────────────────────────────────────────────
    news_summary = _summarize_news(news_articles)
    macro_ops  = '; '.join(macro_env.get('opportunities', [])[:3]) or 'Tidak ada'
    macro_risk = '; '.join(macro_env.get('risk_factors', [])[:3]) or 'Tidak ada'
    sections.append(f"""## 📰 BERITA & SENTIMEN PASAR
{news_summary}

## 🌍 KONDISI MAKRO EKONOMI
- **Environment:** **{macro_env.get('environment', 'N/A')}**
- **Deskripsi:** {macro_env.get('description', 'N/A')}
- **Peluang:** {macro_ops}
- **Risiko Makro:** {macro_risk}
""")

    # ── Instruction ───────────────────────────────────────────────────────────
    sections.append(f"""---
# INSTRUKSI: BERIKAN ANALISIS KOMPREHENSIF

Berdasarkan SEMUA data di atas untuk **{ticker} ({company_name})** pada harga **Rp {_f(price, 0)}**,
berikan analisis mendalam dan rekomendasi konkret dalam format LENGKAP berikut:

---

## 🎯 EXECUTIVE SUMMARY
**REKOMENDASI: [STRONG BUY / BUY / HOLD / SELL / STRONG SELL]**
**Conviction Level: [HIGH / MEDIUM / LOW]**

> [2-3 kalimat ringkas paling penting — apa setup-nya, mengapa sekarang, berapa target]

---

## 🏦 SMART MONEY & STRUKTUR PASAR
[Analisis mendalam: Di mana institusi mengakumulasi/distribusi? Order block mana yang kritis?
Apakah ada liquidity sweep baru-baru ini? Apa implikasi FVG yang belum terisi?]

---

## ⏱️ MULTI-TIMEFRAME CONFLUENCE
[Apakah semua timeframe aligned? Jika tidak, timeframe mana yang dominan?
Apa yang harus terjadi di H4/Daily untuk konfirmasi entry?]

---

## 📊 WYCKOFF & MARKET PHASE
[Fase Wyckoff saat ini, implikasinya, dan estimasi berapa lama fase ini berlangsung]

---

## 📐 LEVEL KRITIS FIBONACCI & S/R
[Level-level Fibonacci yang menjadi support/resistance kuat + confluensi dengan S/R klasik]

---

## 📈 MOMENTUM & INDIKATOR TEKNIKAL
[RSI, MACD, Stochastic — apakah overbought/oversold? Ada divergensi?
Bollinger Band squeeze atau expansion?]

---

## 💰 FUNDAMENTAL & VALUASI
[Apakah harga saat ini murah/wajar/mahal? Bandingkan P/E dengan rata-rata sektor.
Apakah growth mendukung valuasi saat ini?]

---

## 📰 KATALIS & RISIKO

### ✅ Katalis Positif:
1. [Katalis fundamental/teknikal/makro terkuat]
2. [Katalis kedua]
3. [Katalis ketiga]

### ⚠️ Risiko Utama:
1. [Risiko terbesar yang bisa membatalkan setup]
2. [Risiko kedua]
3. [Risiko makro/eksternal]

---

## 🎲 STRATEGI TRADING KONKRET

### Setup & Entry:
- **Tipe Setup:** [Breakout / Pullback ke support / Reversal / Accumulation]
- **Entry Ideal:** **Rp {_f(price, 0)} area** — [kondisi konfirmasi yang harus terpenuhi]
- **Validitas Setup:** Sampai [level/kondisi invalidasi]

### Level Target & Stop Loss:
| Level | Harga | % dari Entry | Alasan |
|-------|-------|-------------|--------|
| 🛑 Stop Loss | Rp _____ | -X% | [S/R kritis yang tidak boleh ditembus] |
| 🎯 Target 1 | Rp _____ | +X% | [Resistance pertama / Fib level] |
| 🎯 Target 2 | Rp _____ | +X% | [Resistance kedua / FVG] |
| 🎯 Target 3 | Rp _____ | +X% | [Target maksimal / Swing high] |

**Risk/Reward Ratio: X:1**
**Time Horizon: [Scalping <1H / Swing 3-7 hari / Position 2-8 minggu]**

### Position Sizing (Modal Rp 100 Juta):
- **Alokasi Kelly:** {_f(float(kelly.get('kelly_fraction', 0.1) if kelly and isinstance(kelly,dict) else 0.1) * 100, 1)}% = **Rp {_f(float(kelly.get('kelly_fraction', 0.1) if kelly and isinstance(kelly,dict) else 0.1) * 100_000_000 / 2, 0)}**
- **Estimasi Lot:** [hitung berdasarkan harga dan lot size IDX]
- **Max Risk per Trade:** 2% = Rp 2.000.000

---

## 📋 KESIMPULAN & NEXT STEPS
[3-4 kalimat konkret: apa yang harus dilakukan trader SEKARANG,
level mana yang harus diawasi hari ini, dan kondisi apa yang akan mengubah rekomendasi ini]
""")

    return "\n".join(sections)


def _f(val, decimals: int = 2) -> str:
    if val is None:
        return "N/A"
    try:
        v = float(val)
        if decimals == 0:
            return f"{v:,.0f}"
        return f"{v:,.{decimals}f}"
    except Exception:
        return str(val)


def _format_tech_signals(signals: dict) -> str:
    lines = []
    for key, val in signals.items():
        if key.startswith("_") or not isinstance(val, dict):
            continue
        s    = val.get("signal", "")
        note = val.get("note", "")
        icon = "🟢" if "BUY" in str(s) else ("🔴" if "SELL" in str(s) else "⚪")
        lines.append(f"  - **{key}:** {icon} {s} — {note}")
    return "\n".join(lines) or "  Tidak ada sinyal"


def _summarize_news(articles: list) -> str:
    if not articles:
        return "Tidak ada berita tersedia untuk saham ini."
    bull  = sum(1 for a in articles if a.get("sentiment", {}).get("label") == "Bullish")
    bear  = sum(1 for a in articles if a.get("sentiment", {}).get("label") == "Bearish")
    neu   = len(articles) - bull - bear
    total = len(articles)
    score_avg = sum(a.get("sentiment", {}).get("score", 0) for a in articles) / max(total, 1)
    overall = "BULLISH" if score_avg > 0.1 else ("BEARISH" if score_avg < -0.1 else "NETRAL")
    headlines = [
        f"  {'🟢' if a.get('sentiment',{}).get('label')=='Bullish' else '🔴' if a.get('sentiment',{}).get('label')=='Bearish' else '⚪'} {(a.get('title_clean') or a.get('title',''))[:120]}"
        for a in articles[:8]
    ]
    return (
        f"**Sentimen Keseluruhan: {overall}** (Skor avg: {score_avg:+.3f})\n"
        f"Total {total} berita: 🟢 {bull} Bullish | 🔴 {bear} Bearish | ⚪ {neu} Neutral\n\n"
        + "\n".join(headlines)
    )
