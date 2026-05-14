#!/usr/bin/env python3
"""
TradingView EMA10/EMA20 Crossover Screener  —  5-minute timeframe
------------------------------------------------------------------
Scans US stocks every 3 minutes for EMA10 crossing above EMA20.
Only sends Telegram alerts for FRESH crossovers (new since last scan).

Deploy on Railway:  start command = python tvscreener.py
Requirements:       pip install requests
"""

import requests
import json
import os
import time
from datetime import datetime

# ── CONFIG ──────────────────────────────────────────────────────────────────
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN", "8784816733:AAF2FpH9EqJ85BzVUjSXH1UI4McDIhSbNvI")
CHAT_ID        = os.environ.get("CHAT_ID",        "1621604072")

STATE_FILE     = os.path.join(os.path.dirname(os.path.abspath(__file__)), "screener_state.json")

INTERVAL_SEC   = 180        # run every 3 minutes
MIN_PRICE      = 1.0        # skip stocks below $1
MIN_VOLUME     = 10_000     # skip 5-min bars with < 10k volume
MAX_RESULTS    = 100        # max stocks to pull from TradingView screener
# ────────────────────────────────────────────────────────────────────────────


def log(msg: str):
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {msg}", flush=True)


def fetch_signals() -> dict:
    """
    Query TradingView screener for US stocks where
    EMA10 (5-min) > EMA20 (5-min), filtered by price and volume.
    Returns {symbol: {field: value}}.
    """
    url     = "https://scanner.tradingview.com/america/scan"
    headers = {
        "Content-Type": "application/json",
        "User-Agent":   "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        "Origin":       "https://www.tradingview.com",
        "Referer":      "https://www.tradingview.com/",
    }

    columns = [
        "name",
        "description",
        "close|5",
        "change|5",
        "volume|5",
        "EMA10|5",
        "EMA20|5",
        "exchange",
    ]

    payload = {
        "filter": [
            {"left": "EMA10|5",  "operation": "greater", "right": "EMA20|5"},
            {"left": "close|5",  "operation": "greater", "right": MIN_PRICE},
            {"left": "volume|5", "operation": "greater", "right": MIN_VOLUME},
        ],
        "columns": columns,
        "sort":    {"sortBy": "volume|5", "sortOrder": "desc"},
        "range":   [0, MAX_RESULTS],
        "options": {"lang": "en"},
    }

    r = requests.post(url, json=payload, headers=headers, timeout=15)
    r.raise_for_status()
    rows = r.json().get("data", [])
    return {row["s"]: dict(zip(columns, row["d"])) for row in rows}


def load_state() -> dict:
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, encoding="utf-8") as f:
            return json.load(f)
    return {"symbols": []}


def save_state(symbols: list):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump({"symbols": symbols, "updated": datetime.now().isoformat()}, f, indent=2)


def send_telegram(text: str):
    url  = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data = {"chat_id": CHAT_ID, "text": text, "parse_mode": "HTML"}
    r    = requests.post(url, json=data, timeout=10)
    r.raise_for_status()


def fmt_vol(v) -> str:
    v = v or 0
    if v >= 1_000_000: return f"{v / 1_000_000:.1f}M"
    if v >= 1_000:     return f"{v / 1_000:.0f}K"
    return str(int(v))


def build_message(new_signals: dict, total_in_signal: int) -> str:
    now   = datetime.now().strftime("%Y-%m-%d  %H:%M:%S")
    count = len(new_signals)
    lines = [
        "📡 <b>EMA10 ✕ EMA20 Crossover Alert</b>",
        "⏱ 5-min chart  |  US Stocks",
        f"🕐 {now}",
        f"🆕 {count} new signal(s)  |  {total_in_signal} total in zone\n",
    ]
    for sym, d in new_signals.items():
        ticker = sym.split(":")[-1]
        name   = (d.get("description") or ticker)[:22]
        price  = d.get("close|5")  or 0
        chg    = d.get("change|5") or 0
        vol    = d.get("volume|5") or 0
        ema10  = d.get("EMA10|5")  or 0
        ema20  = d.get("EMA20|5")  or 0
        exch   = d.get("exchange") or ""
        icon   = "🟢" if chg >= 0 else "🔴"
        lines.append(
            f"{icon} <b>{ticker}</b>  <i>{name}</i>  [{exch}]\n"
            f"   💰 ${price:.2f}  ({chg:+.2f}%)\n"
            f"   📈 EMA10: {ema10:.3f}  →  EMA20: {ema20:.3f}\n"
            f"   📦 Vol: {fmt_vol(vol)}\n"
        )
    return "\n".join(lines)


def scan_once():
    log("Running screener scan…")
    try:
        current = fetch_signals()
        log(f"TradingView: {len(current)} stocks in EMA10>EMA20 signal.")
    except Exception as e:
        log(f"ERROR fetching screener: {e}")
        return

    state          = load_state()
    prev_symbols   = set(state.get("symbols", []))
    curr_symbols   = set(current.keys())
    new_crossovers = curr_symbols - prev_symbols

    log(f"New crossovers: {len(new_crossovers)} | Exited: {len(prev_symbols - curr_symbols)}")
    save_state(list(curr_symbols))

    if new_crossovers:
        new_signals = {s: current[s] for s in new_crossovers}
        msg = build_message(new_signals, total_in_signal=len(curr_symbols))
        try:
            send_telegram(msg)
            tickers = sorted(s.split(":")[-1] for s in new_crossovers)
            log(f"Alert sent → {tickers}")
        except Exception as e:
            log(f"ERROR sending Telegram: {e}")
    else:
        log("No new crossovers — no message sent.")


def main():
    log("=== TradingView EMA Screener started ===")
    log(f"Scanning every {INTERVAL_SEC // 60} minutes. Market: US Stocks | TF: 5-min")

    while True:
        try:
            scan_once()
        except Exception as e:
            log(f"Unexpected error: {e}")
        log(f"Sleeping {INTERVAL_SEC}s until next scan…\n")
        time.sleep(INTERVAL_SEC)


if __name__ == "__main__":
    main()
