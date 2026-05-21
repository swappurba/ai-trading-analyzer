"""
Live Price Module
-----------------
Sumber data harga real-time:
  1. Finnhub REST API  — saham global (US, EU, dsb.), 60 req/mnt gratis
  2. Finnhub WebSocket — streaming tick-by-tick (digunakan via thread)
  3. yfinance polling  — fallback untuk IDX & saham lain (delay ~15 mnt)

Daftar gratis Finnhub: https://finnhub.io/register
"""

import requests
import threading
import queue
import json
import time
import datetime
from collections import deque
from typing import Optional
import yfinance as yf

try:
    import websocket
    WS_AVAILABLE = True
except ImportError:
    WS_AVAILABLE = False

import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import FINNHUB_API_KEY

FINNHUB_BASE = "https://finnhub.io/api/v1"
YAHOO_V8_BASE = "https://query1.finance.yahoo.com/v8/finance/chart"
YAHOO_V8_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "application/json",
}

# ── In-memory price cache ──────────────────────────────────────────────────────
_price_cache: dict[str, dict] = {}
_cache_lock = threading.Lock()

# ── WebSocket state ────────────────────────────────────────────────────────────
_ws_app: Optional[object] = None
_ws_thread: Optional[threading.Thread] = None
_ws_subscribed: set[str] = set()
_tick_queue: queue.Queue = queue.Queue(maxsize=500)


# ══════════════════════════════════════════════════════════════════════════════
# FINNHUB REST — harga snapshot, kuota, profil
# ══════════════════════════════════════════════════════════════════════════════

def _fh_get(endpoint: str, params: dict) -> dict:
    if not FINNHUB_API_KEY:
        return {}
    try:
        params["token"] = FINNHUB_API_KEY
        r = requests.get(f"{FINNHUB_BASE}/{endpoint}", params=params, timeout=5)
        if r.status_code == 200:
            return r.json()
    except Exception:
        pass
    return {}


def finnhub_quote(symbol: str) -> dict:
    """Harga real-time via Finnhub REST (refresh setiap ~1 detik di server)."""
    data = _fh_get("quote", {"symbol": symbol})
    if not data or data.get("c") is None:
        return {}
    return {
        "price":      data.get("c"),
        "change":     data.get("d"),
        "pct_change": data.get("dp"),
        "high":       data.get("h"),
        "low":        data.get("l"),
        "open":       data.get("o"),
        "prev_close": data.get("pc"),
        "timestamp":  data.get("t"),
        "source":     "Finnhub",
    }


def finnhub_company_profile(symbol: str) -> dict:
    return _fh_get("stock/profile2", {"symbol": symbol})


def finnhub_candles(symbol: str, resolution: str = "1", from_ts: int = None, to_ts: int = None) -> dict:
    """
    Ambil candlestick real-time.
    resolution: '1','5','15','30','60','D','W','M'
    """
    now = int(time.time())
    if to_ts is None:
        to_ts = now
    if from_ts is None:
        from_ts = now - 3600  # 1 jam terakhir
    return _fh_get("stock/candle", {
        "symbol":     symbol,
        "resolution": resolution,
        "from":       from_ts,
        "to":         to_ts,
    })


def finnhub_candles_to_df(symbol: str, resolution: str = "5", hours_back: int = 6):
    """Return DataFrame OHLCV dari Finnhub intraday."""
    import pandas as pd
    now = int(time.time())
    from_ts = now - hours_back * 3600
    data = finnhub_candles(symbol, resolution=resolution, from_ts=from_ts, to_ts=now)
    if not data or data.get("s") != "ok":
        return pd.DataFrame()
    df = pd.DataFrame({
        "Open":   data["o"],
        "High":   data["h"],
        "Low":    data["l"],
        "Close":  data["c"],
        "Volume": data["v"],
    }, index=pd.to_datetime(data["t"], unit="s"))
    df.index.name = "Datetime"
    return df


def finnhub_multiple_quotes(symbols: list) -> dict:
    """Ambil harga beberapa simbol sekaligus (perhatikan rate limit 60/mnt)."""
    results = {}
    for sym in symbols:
        q = finnhub_quote(sym)
        if q:
            results[sym] = q
        time.sleep(0.05)  # jaga rate limit
    return results


def finnhub_news(symbol: str, days: int = 3) -> list:
    """Berita terkini dari Finnhub."""
    to_dt   = datetime.date.today()
    from_dt = to_dt - datetime.timedelta(days=days)
    data = _fh_get("company-news", {
        "symbol": symbol,
        "from":   str(from_dt),
        "to":     str(to_dt),
    })
    return data if isinstance(data, list) else []


def finnhub_sentiment(symbol: str) -> dict:
    """Sentimen berita dari Finnhub (buzz + score)."""
    return _fh_get("news-sentiment", {"symbol": symbol})


def finnhub_earnings(symbol: str) -> list:
    data = _fh_get("stock/earnings", {"symbol": symbol, "limit": 8})
    return data if isinstance(data, list) else []


def finnhub_recommendation(symbol: str) -> list:
    data = _fh_get("stock/recommendation", {"symbol": symbol})
    return data if isinstance(data, list) else []


# ══════════════════════════════════════════════════════════════════════════════
# FINNHUB WEBSOCKET — streaming tick real-time
# ══════════════════════════════════════════════════════════════════════════════

def _on_ws_message(ws, message):
    try:
        data = json.loads(message)
        if data.get("type") == "trade":
            for trade in data.get("data", []):
                sym  = trade.get("s", "")
                price = trade.get("p")
                vol  = trade.get("v")
                ts   = trade.get("t")
                if sym and price:
                    with _cache_lock:
                        prev = _price_cache.get(sym, {})
                        prev_price = prev.get("price")
                        change = (price - prev_price) if prev_price else 0
                        pct    = (change / prev_price * 100) if prev_price else 0
                        _price_cache[sym] = {
                            "price":      price,
                            "change":     round(change, 4),
                            "pct_change": round(pct, 4),
                            "volume":     vol,
                            "timestamp":  ts,
                            "source":     "Finnhub WS",
                        }
                    try:
                        _tick_queue.put_nowait({"symbol": sym, "price": price, "ts": ts})
                    except queue.Full:
                        pass
    except Exception:
        pass


def _on_ws_error(ws, error):
    pass


def _on_ws_close(ws, *args):
    pass


def _on_ws_open(ws):
    for sym in list(_ws_subscribed):
        ws.send(json.dumps({"type": "subscribe", "symbol": sym}))


def start_websocket(symbols: list[str]):
    """Mulai WebSocket Finnhub di background thread."""
    global _ws_app, _ws_thread

    if not FINNHUB_API_KEY or not WS_AVAILABLE:
        return False

    _ws_subscribed.update(symbols)

    if _ws_thread and _ws_thread.is_alive():
        # Sudah berjalan — subscribe simbol baru saja
        if _ws_app:
            for sym in symbols:
                try:
                    _ws_app.send(json.dumps({"type": "subscribe", "symbol": sym}))
                except Exception:
                    pass
        return True

    def _run():
        global _ws_app
        url = f"wss://ws.finnhub.io?token={FINNHUB_API_KEY}"
        _ws_app = websocket.WebSocketApp(
            url,
            on_message=_on_ws_message,
            on_error=_on_ws_error,
            on_close=_on_ws_close,
            on_open=_on_ws_open,
        )
        _ws_app.run_forever(ping_interval=30, ping_timeout=10)

    _ws_thread = threading.Thread(target=_run, daemon=True)
    _ws_thread.start()
    return True


def stop_websocket():
    global _ws_app
    if _ws_app:
        try:
            _ws_app.close()
        except Exception:
            pass


def get_ws_price(symbol: str) -> dict:
    """Ambil harga terakhir dari cache WebSocket."""
    with _cache_lock:
        return _price_cache.get(symbol, {})


def get_recent_ticks(n: int = 50) -> list:
    """Ambil n tick terakhir dari queue."""
    ticks = []
    try:
        while not _tick_queue.empty() and len(ticks) < n:
            ticks.append(_tick_queue.get_nowait())
    except Exception:
        pass
    return ticks


# ══════════════════════════════════════════════════════════════════════════════
# YAHOO FINANCE v8 — real-time IDX (bypass yfinance library delay)
# ══════════════════════════════════════════════════════════════════════════════

def yahoo_v8_realtime(ticker: str) -> dict:
    """
    Direct call to Yahoo Finance v8 chart API — lebih real-time dari yfinance library.
    Mengembalikan regularMarketPrice yang di-update hampir real-time oleh Yahoo.
    """
    try:
        url = f"{YAHOO_V8_BASE}/{ticker}"
        params = {"interval": "1m", "range": "1d", "includePrePost": "false"}
        r = requests.get(url, params=params, headers=YAHOO_V8_HEADERS, timeout=6)
        if r.status_code != 200:
            return {}
        data = r.json()
        result = data.get("chart", {}).get("result", [])
        if not result:
            return {}
        meta = result[0].get("meta", {})
        price = meta.get("regularMarketPrice")
        if price is None:
            return {}
        prev_close = meta.get("chartPreviousClose") or meta.get("previousClose") or price
        change = price - prev_close
        pct = (change / prev_close * 100) if prev_close else 0

        # Ambil candle terakhir untuk OHLV jika tersedia
        indicators = result[0].get("indicators", {})
        quote_list = indicators.get("quote", [{}])
        q = quote_list[0] if quote_list else {}
        closes = q.get("close", [])
        opens  = q.get("open", [])
        highs  = q.get("high", [])
        lows   = q.get("low", [])
        vols   = q.get("volume", [])

        # Filter None values
        closes_clean = [x for x in closes if x is not None]
        highs_clean  = [x for x in highs  if x is not None]
        lows_clean   = [x for x in lows   if x is not None]
        opens_clean  = [x for x in opens  if x is not None]
        vols_clean   = [x for x in vols   if x is not None]

        return {
            "price":      float(price),
            "change":     round(change, 4),
            "pct_change": round(pct, 4),
            "high":       float(highs_clean[-1])  if highs_clean  else meta.get("regularMarketDayHigh", price),
            "low":        float(lows_clean[-1])   if lows_clean   else meta.get("regularMarketDayLow", price),
            "open":       float(opens_clean[0])   if opens_clean  else price,
            "prev_close": float(prev_close),
            "volume":     int(vols_clean[-1])     if vols_clean   else meta.get("regularMarketVolume", 0),
            "timestamp":  meta.get("regularMarketTime"),
            "source":     "Yahoo v8",
        }
    except Exception:
        return {}


def yahoo_v8_intraday(ticker: str, interval: str = "2m", hours: int = 8):
    """
    Ambil data intraday IDX via Yahoo Finance v8 langsung (lebih segar dari yfinance).
    interval: '1m','2m','5m','15m','30m','60m','90m'
    """
    import pandas as pd
    range_map = {1: "1d", 2: "1d", 5: "1d", 8: "1d", 24: "5d", 48: "5d", 72: "5d"}
    yf_range = "5d" if hours > 8 else "1d"

    try:
        url = f"{YAHOO_V8_BASE}/{ticker}"
        params = {"interval": interval, "range": yf_range, "includePrePost": "false"}
        r = requests.get(url, params=params, headers=YAHOO_V8_HEADERS, timeout=8)
        if r.status_code != 200:
            return pd.DataFrame()
        data = r.json()
        result = data.get("chart", {}).get("result", [])
        if not result:
            return pd.DataFrame()

        timestamps = result[0].get("timestamp", [])
        indicators = result[0].get("indicators", {}).get("quote", [{}])
        q = indicators[0] if indicators else {}

        df = pd.DataFrame({
            "Open":   q.get("open", []),
            "High":   q.get("high", []),
            "Low":    q.get("low", []),
            "Close":  q.get("close", []),
            "Volume": q.get("volume", []),
        }, index=pd.to_datetime(timestamps, unit="s"))
        df.index.name = "Datetime"
        df = df.dropna(subset=["Close"])
        return df
    except Exception:
        return pd.DataFrame()


# ══════════════════════════════════════════════════════════════════════════════
# UNIFIED get_live_price — otomatis pilih sumber terbaik
# ══════════════════════════════════════════════════════════════════════════════

def get_live_price(ticker: str) -> dict:
    """
    Prioritas:
    1. Cache WebSocket Finnhub (jika WS aktif & non-IDX)
    2. Finnhub REST (jika API key ada & bukan IDX)
    3. Yahoo Finance v8 direct HTTP (IDX — near real-time)
    4. yfinance fallback
    """
    is_idx = ticker.endswith(".JK")

    # 1. WebSocket cache (hanya untuk non-IDX karena Finnhub tidak cover IDX)
    if not is_idx:
        ws_data = get_ws_price(ticker)
        if ws_data and ws_data.get("price"):
            return ws_data

    # 2. Finnhub REST (untuk non-IDX)
    if FINNHUB_API_KEY and not is_idx:
        fh = finnhub_quote(ticker)
        if fh and fh.get("price"):
            return fh

    # 3. Yahoo Finance v8 direct (IDX & fallback global)
    yv8 = yahoo_v8_realtime(ticker)
    if yv8 and yv8.get("price"):
        return yv8

    # 4. yfinance fallback
    return _yfinance_live(ticker)


def _yfinance_live(ticker: str) -> dict:
    try:
        stk = yf.Ticker(ticker)
        hist = stk.history(period="2d", interval="1m")
        if hist.empty:
            hist = stk.history(period="2d")
        if hist.empty:
            return {}
        cur  = float(hist["Close"].iloc[-1])
        prev = float(hist["Close"].iloc[-2]) if len(hist) > 1 else cur
        change = cur - prev
        pct    = (change / prev * 100) if prev else 0
        return {
            "price":      cur,
            "change":     round(change, 4),
            "pct_change": round(pct, 4),
            "high":       float(hist["High"].iloc[-1]),
            "low":        float(hist["Low"].iloc[-1]),
            "open":       float(hist["Open"].iloc[-1]),
            "volume":     int(hist["Volume"].iloc[-1]),
            "timestamp":  int(hist.index[-1].timestamp()),
            "source":     "yfinance",
        }
    except Exception:
        return {}


# ══════════════════════════════════════════════════════════════════════════════
# INTRADAY CHART — ambil data menit-an untuk chart real-time
# ══════════════════════════════════════════════════════════════════════════════

def get_intraday_data(ticker: str, interval: str = "5m", hours: int = 6):
    """
    Ambil data intraday.
    - Yahoo v8 direct untuk IDX (near real-time, tidak delayed)
    - Finnhub untuk non-IDX
    - yfinance fallback
    """
    import pandas as pd
    is_idx = ticker.endswith(".JK")

    # IDX: Yahoo v8 direct — lebih segar dari yfinance library
    if is_idx:
        yv8_interval_map = {"1m": "1m", "2m": "2m", "5m": "5m", "15m": "15m", "30m": "30m", "1h": "60m"}
        yv8_iv = yv8_interval_map.get(interval, "5m")
        df = yahoo_v8_intraday(ticker, interval=yv8_iv, hours=hours)
        if not df.empty:
            return df

    # Finnhub candles untuk global
    if FINNHUB_API_KEY and not is_idx:
        res_map = {"1m": "1", "5m": "5", "15m": "15", "30m": "30", "1h": "60"}
        fh_res  = res_map.get(interval, "5")
        df = finnhub_candles_to_df(ticker, resolution=fh_res, hours_back=hours)
        if not df.empty:
            return df

    # yfinance fallback
    try:
        stk = yf.Ticker(ticker)
        period = "1d" if hours <= 8 else "5d"
        df  = stk.history(period=period, interval=interval)
        if not df.empty:
            df.index = pd.to_datetime(df.index)
            if df.index.tz is not None:
                df.index = df.index.tz_localize(None)
            return df
    except Exception:
        pass
    return pd.DataFrame()


# ══════════════════════════════════════════════════════════════════════════════
# MULTI-TICKER LIVE SCREENER
# ══════════════════════════════════════════════════════════════════════════════

def live_screener(tickers: list, use_finnhub: bool = True) -> list:
    """Ambil harga live untuk banyak ticker sekaligus."""
    results = []
    for ticker in tickers:
        data = get_live_price(ticker)
        if data:
            data["ticker"] = ticker
            results.append(data)
        time.sleep(0.05)
    return results


def batch_live_prices(tickers: list, max_workers: int = 10) -> dict:
    """
    Fetch live prices for many tickers in parallel threads.
    Returns dict: {ticker: price_dict}
    """
    result: dict = {}
    lock = threading.Lock()

    def _fetch(t):
        try:
            data = yahoo_v8_realtime(t) if t.endswith(".JK") else get_live_price(t)
            if data and data.get("price"):
                with lock:
                    result[t] = data
        except Exception:
            pass

    threads = []
    for t in tickers:
        th = threading.Thread(target=_fetch, args=(t,), daemon=True)
        threads.append(th)
        th.start()
        if len(threads) >= max_workers:
            for th2 in threads:
                th2.join(timeout=8)
            threads = []
    for th in threads:
        th.join(timeout=8)

    return result


def get_sparkline_data(ticker: str, days: int = 5) -> list:
    """Ambil closing prices N hari terakhir untuk mini sparkline."""
    try:
        url = f"{YAHOO_V8_BASE}/{ticker}"
        params = {"interval": "1d", "range": f"{days}d"}
        r = requests.get(url, params=params, headers=YAHOO_V8_HEADERS, timeout=5)
        if r.status_code != 200:
            return []
        data = r.json()
        result = data.get("chart", {}).get("result", [])
        if not result:
            return []
        closes = result[0].get("indicators", {}).get("quote", [{}])[0].get("close", [])
        return [c for c in closes if c is not None]
    except Exception:
        return []


# ══════════════════════════════════════════════════════════════════════════════
# HELPERS
# ══════════════════════════════════════════════════════════════════════════════

def is_market_open(ticker: str) -> bool:
    """Cek apakah pasar sedang buka (UTC-based, sederhana)."""
    now_utc = datetime.datetime.utcnow()
    weekday = now_utc.weekday()  # 0=Mon … 6=Sun

    if weekday >= 5:  # Sabtu/Minggu
        return False

    hour = now_utc.hour

    if ticker.endswith(".JK"):
        # IDX: 01:30 – 10:00 UTC (WIB = UTC+7, sesi: 09:00–16:15 WIB)
        return (1 <= hour < 10) or (3 <= hour < 10)
    else:
        # NYSE/NASDAQ: 13:30 – 20:00 UTC
        return 13 <= hour < 20


def format_price(price, decimals: int = 2) -> str:
    if price is None:
        return "N/A"
    try:
        return f"{float(price):,.{decimals}f}"
    except Exception:
        return str(price)


def format_timestamp(ts) -> str:
    if not ts:
        return ""
    try:
        dt = datetime.datetime.fromtimestamp(int(ts) / 1000 if int(ts) > 1e10 else int(ts))
        return dt.strftime("%H:%M:%S")
    except Exception:
        return ""
