import re
from datetime import datetime
import feedparser
import requests
from config import NEWS_API_KEY


POSITIVE_WORDS = [
    "naik", "meningkat", "tumbuh", "positif", "profit", "laba", "untung", "rekor",
    "ekspansi", "investasi", "akuisisi", "dividen", "surplus", "optimis", "bullish",
    "rally", "rebound", "breakout", "upgrade", "outperform", "buy", "strong",
    "growth", "rise", "gain", "beat", "exceed", "record", "high", "up", "boost",
    "recover", "improve", "positive", "upside", "momentum", "demand", "increase",
    "bagus", "baik", "kuat", "unggul", "berhasil", "sukses", "maju",
]

NEGATIVE_WORDS = [
    "turun", "merosot", "rugi", "kerugian", "anjlok", "jatuh", "krisis", "resesi",
    "inflasi", "deflasi", "defisit", "hutang", "bangkrut", "pailit", "korupsi",
    "skandal", "negatif", "bearish", "crash", "selloff", "downgrade", "underperform",
    "sell", "weak", "fall", "drop", "decline", "loss", "miss", "below", "low", "down",
    "cut", "risk", "concern", "worry", "fear", "uncertainty", "slowdown", "contraction",
    "buruk", "lemah", "gagal", "masalah", "hambatan", "tekanan", "susut",
]

NEUTRAL_WORDS = [
    "stabil", "tetap", "flat", "sideways", "hold", "neutral", "mixed", "stable",
    "konsolidasi", "wait", "cautious", "moderate",
]


def simple_sentiment(text: str) -> dict:
    if not text:
        return {"score": 0, "label": "Neutral", "confidence": 0}

    text_lower = text.lower()
    pos = sum(1 for w in POSITIVE_WORDS if w in text_lower)
    neg = sum(1 for w in NEGATIVE_WORDS if w in text_lower)
    neu = sum(1 for w in NEUTRAL_WORDS if w in text_lower)

    total = pos + neg + neu + 1
    score = (pos - neg) / total

    if score > 0.15:
        label = "Bullish"
        emoji = "🟢"
    elif score < -0.15:
        label = "Bearish"
        emoji = "🔴"
    else:
        label = "Neutral"
        emoji = "⚪"

    confidence = min(100, int(abs(score) * 200))
    return {"score": round(score, 3), "label": label, "emoji": emoji,
            "confidence": confidence, "pos": pos, "neg": neg}


def analyze_news_batch(articles: list) -> list:
    analyzed = []
    for article in articles:
        text = f"{article.get('title', '')} {article.get('description', '')}"
        sentiment = simple_sentiment(text)
        article["sentiment"] = sentiment
        article["title_clean"] = _clean_html(article.get("title", ""))
        article["desc_clean"] = _clean_html(article.get("description", ""))

        # Parse date
        pub_date = article.get("publishedAt", "")
        article["date_display"] = _parse_date(pub_date)

        analyzed.append(article)
    return analyzed


def _clean_html(text: str) -> str:
    if not text:
        return ""
    clean = re.sub(r"<[^>]+>", "", text)
    clean = re.sub(r"&amp;", "&", clean)
    clean = re.sub(r"&lt;", "<", clean)
    clean = re.sub(r"&gt;", ">", clean)
    clean = re.sub(r"&nbsp;", " ", clean)
    clean = re.sub(r"\s+", " ", clean).strip()
    return clean[:300]


def _parse_date(date_str: str) -> str:
    if not date_str:
        return "N/A"
    formats = [
        "%a, %d %b %Y %H:%M:%S %z",
        "%a, %d %b %Y %H:%M:%S GMT",
        "%Y-%m-%dT%H:%M:%SZ",
        "%Y-%m-%dT%H:%M:%S%z",
        "%Y-%m-%d",
    ]
    for fmt in formats:
        try:
            dt = datetime.strptime(date_str[:30].strip(), fmt)
            return dt.strftime("%d %b %Y")
        except Exception:
            continue
    return date_str[:10]


def aggregate_sentiment(articles: list) -> dict:
    if not articles:
        return {"label": "N/A", "score": 0, "bullish": 0, "bearish": 0, "neutral": 0, "total": 0}

    scores = [a.get("sentiment", {}).get("score", 0) for a in articles]
    avg = sum(scores) / len(scores) if scores else 0

    bullish = sum(1 for a in articles if a.get("sentiment", {}).get("label") == "Bullish")
    bearish = sum(1 for a in articles if a.get("sentiment", {}).get("label") == "Bearish")
    neutral = sum(1 for a in articles if a.get("sentiment", {}).get("label") == "Neutral")

    if avg > 0.1:
        label = "🟢 Bullish"
        color = "green"
    elif avg < -0.1:
        label = "🔴 Bearish"
        color = "red"
    else:
        label = "⚪ Neutral"
        color = "gray"

    return {
        "label": label, "score": round(avg, 3),
        "bullish": bullish, "bearish": bearish, "neutral": neutral,
        "total": len(articles), "color": color,
    }


def get_stock_news(ticker: str, company_name: str = "") -> list:
    from modules.data_fetcher import get_news_rss, get_news_newsapi
    articles = []

    # Try NewsAPI (ID)
    if company_name and NEWS_API_KEY:
        articles += get_news_newsapi(company_name, language="id", days=7)
        articles += get_news_newsapi(ticker, language="en", days=7)

    # RSS fallback
    rss_articles = get_news_rss(ticker, company_name)
    articles += rss_articles

    # Deduplicate by title
    seen = set()
    unique = []
    for a in articles:
        title = a.get("title", "")[:60]
        if title and title not in seen:
            seen.add(title)
            unique.append(a)

    analyzed = analyze_news_batch(unique[:25])
    return analyzed


def get_macro_news() -> list:
    from modules.data_fetcher import get_macro_news_rss
    articles = get_macro_news_rss()
    return analyze_news_batch(articles)


def summarize_news_sentiment(articles: list, context: str = "stock") -> str:
    if not articles:
        return "Tidak ada berita yang dapat dianalisis."

    agg = aggregate_sentiment(articles)
    bull = agg["bullish"]
    bear = agg["bearish"]
    neu = agg["neutral"]
    total = agg["total"]
    score = agg["score"]

    summary = f"Dari **{total} berita** yang dianalisis: "
    summary += f"**{bull} Bullish**, **{bear} Bearish**, **{neu} Netral**. "
    summary += f"Skor sentimen rata-rata: **{score:+.3f}** → {agg['label']}."

    if context == "macro":
        if score < -0.1:
            summary += " ⚠️ Sentimen makro negatif dapat memberi tekanan pada pasar secara keseluruhan."
        elif score > 0.1:
            summary += " ✅ Sentimen makro positif mendukung kondisi pasar yang baik."

    return summary
