import yfinance as yf
import pandas as pd
import numpy as np
import requests
from datetime import datetime, timedelta
import feedparser
import time
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import NEWS_API_KEY


def get_stock_data(ticker: str, period: str = "1y", interval: str = "1d") -> pd.DataFrame:
    try:
        stock = yf.Ticker(ticker)
        df = stock.history(period=period, interval=interval)
        if df.empty:
            return pd.DataFrame()
        df.index = pd.to_datetime(df.index)
        if df.index.tz is not None:
            df.index = df.index.tz_localize(None)
        return df
    except Exception as e:
        return pd.DataFrame()


def get_stock_info(ticker: str) -> dict:
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        return info if info else {}
    except Exception:
        return {}


def get_financials(ticker: str) -> dict:
    try:
        stock = yf.Ticker(ticker)
        result = {
            "income_stmt": stock.financials,
            "balance_sheet": stock.balance_sheet,
            "cashflow": stock.cashflow,
            "quarterly_income": stock.quarterly_financials,
            "quarterly_balance": stock.quarterly_balance_sheet,
        }
        return result
    except Exception:
        return {}


def get_multiple_stocks(tickers: list, period: str = "1y") -> dict:
    data = {}
    for ticker in tickers:
        df = get_stock_data(ticker, period=period)
        if not df.empty:
            data[ticker] = df
        time.sleep(0.1)
    return data


def get_index_data(index_ticker: str, period: str = "1y") -> pd.DataFrame:
    return get_stock_data(index_ticker, period=period)


def get_commodity_data(commodity_ticker: str, period: str = "1y") -> pd.DataFrame:
    return get_stock_data(commodity_ticker, period=period)


def get_currency_data(pair_ticker: str, period: str = "1y") -> pd.DataFrame:
    return get_stock_data(pair_ticker, period=period)


def get_current_price(ticker: str) -> dict:
    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(period="2d")
        if hist.empty:
            return {}
        current = hist["Close"].iloc[-1]
        prev = hist["Close"].iloc[-2] if len(hist) > 1 else current
        change = current - prev
        pct_change = (change / prev) * 100
        return {
            "price": current,
            "change": change,
            "pct_change": pct_change,
            "volume": hist["Volume"].iloc[-1],
            "high": hist["High"].iloc[-1],
            "low": hist["Low"].iloc[-1],
            "open": hist["Open"].iloc[-1],
        }
    except Exception:
        return {}


def get_news_newsapi(query: str, language: str = "id", days: int = 7) -> list:
    if not NEWS_API_KEY:
        return []
    try:
        from_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
        url = "https://newsapi.org/v2/everything"
        params = {
            "q": query,
            "language": language,
            "from": from_date,
            "sortBy": "relevancy",
            "pageSize": 20,
            "apiKey": NEWS_API_KEY,
        }
        resp = requests.get(url, params=params, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            return data.get("articles", [])
    except Exception:
        pass
    return []


def get_news_rss(ticker: str, company_name: str = "") -> list:
    articles = []
    feeds = []

    # Yahoo Finance RSS
    feeds.append(f"https://feeds.finance.yahoo.com/rss/2.0/headline?s={ticker}&region=US&lang=en-US")

    # Google News RSS for company
    if company_name:
        query = company_name.replace(" ", "+")
        feeds.append(f"https://news.google.com/rss/search?q={query}&hl=id&gl=ID&ceid=ID:id")
        feeds.append(f"https://news.google.com/rss/search?q={query}+stock&hl=en&gl=US&ceid=US:en")

    # Ticker-based Google News
    feeds.append(f"https://news.google.com/rss/search?q={ticker}+saham&hl=id&gl=ID&ceid=ID:id")

    for feed_url in feeds:
        try:
            feed = feedparser.parse(feed_url)
            for entry in feed.entries[:5]:
                article = {
                    "title": entry.get("title", ""),
                    "description": entry.get("summary", ""),
                    "url": entry.get("link", ""),
                    "publishedAt": entry.get("published", ""),
                    "source": {"name": feed.feed.get("title", "RSS Feed")},
                }
                if article["title"]:
                    articles.append(article)
        except Exception:
            continue

    return articles[:20]


def get_macro_news_rss() -> list:
    articles = []
    feeds = [
        ("https://news.google.com/rss/search?q=ekonomi+Indonesia+makro&hl=id&gl=ID&ceid=ID:id", "Ekonomi Indonesia"),
        ("https://news.google.com/rss/search?q=Bank+Indonesia+suku+bunga&hl=id&gl=ID&ceid=ID:id", "Bank Indonesia"),
        ("https://news.google.com/rss/search?q=inflasi+Indonesia&hl=id&gl=ID&ceid=ID:id", "Inflasi Indonesia"),
        ("https://news.google.com/rss/search?q=Federal+Reserve+interest+rate&hl=en&gl=US&ceid=US:en", "Fed Policy"),
        ("https://news.google.com/rss/search?q=global+economy+recession&hl=en&gl=US&ceid=US:en", "Global Economy"),
        ("https://news.google.com/rss/search?q=China+economy+trade&hl=en&gl=US&ceid=US:en", "China Economy"),
        ("https://news.google.com/rss/search?q=commodity+prices+oil+gold&hl=en&gl=US&ceid=US:en", "Commodities"),
    ]
    for url, category in feeds:
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries[:3]:
                articles.append({
                    "title": entry.get("title", ""),
                    "description": entry.get("summary", ""),
                    "url": entry.get("link", ""),
                    "publishedAt": entry.get("published", ""),
                    "source": {"name": category},
                    "category": category,
                })
        except Exception:
            continue
    return articles


def get_economic_calendar() -> list:
    events = [
        {"event": "BI Rate Decision", "country": "🇮🇩 Indonesia", "impact": "High", "frequency": "Monthly"},
        {"event": "Inflasi CPI Indonesia", "country": "🇮🇩 Indonesia", "impact": "High", "frequency": "Monthly"},
        {"event": "PDB Indonesia", "country": "🇮🇩 Indonesia", "impact": "High", "frequency": "Quarterly"},
        {"event": "Fed Funds Rate", "country": "🇺🇸 USA", "impact": "High", "frequency": "Per 6 Minggu"},
        {"event": "US CPI (Inflasi)", "country": "🇺🇸 USA", "impact": "High", "frequency": "Monthly"},
        {"event": "US GDP", "country": "🇺🇸 USA", "impact": "High", "frequency": "Quarterly"},
        {"event": "Non-Farm Payrolls", "country": "🇺🇸 USA", "impact": "High", "frequency": "Monthly"},
        {"event": "China GDP", "country": "🇨🇳 China", "impact": "Medium", "frequency": "Quarterly"},
        {"event": "ECB Rate Decision", "country": "🇪🇺 EU", "impact": "High", "frequency": "Per 6 Minggu"},
        {"event": "Japan BoJ Rate", "country": "🇯🇵 Japan", "impact": "Medium", "frequency": "Monthly"},
    ]
    return events


def get_sector_performance(tickers: list, period: str = "1mo") -> pd.DataFrame:
    results = []
    for ticker in tickers:
        try:
            df = get_stock_data(ticker, period=period)
            if not df.empty and len(df) >= 2:
                ret = (df["Close"].iloc[-1] / df["Close"].iloc[0] - 1) * 100
                results.append({"ticker": ticker, "return": round(ret, 2)})
        except Exception:
            continue
        time.sleep(0.05)
    return pd.DataFrame(results) if results else pd.DataFrame()
