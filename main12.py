#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from flask import Flask, request
from apscheduler.schedulers.background import BackgroundScheduler
import requests
import os

app = Flask(__name__)

TELEGRAM_TOKEN = "8784816733:AAF2FpH9EqJ85BzVUjSXH1UI4McDIhSbNvI"
CHAT_ID        = "1621604072"

# =======================================
#  ارسال تليجرام
# =======================================
def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text":    message,
        "parse_mode": "HTML"
    }
    try:
        requests.post(url, json=payload, timeout=10)
    except Exception as e:
        print(f"ERROR Telegram: {e}")

# =======================================
#  المهمة التي تعمل كل 3 دقائق
# =======================================
def scheduled_task():
    print("تشغيل الفحص الدوري كل 3 دقائق...")
    send_telegram("الفحص الدوري يعمل - لا توجد اشارات جديدة")

# =======================================
#  Webhook - يستقبل اشارات TradingView
# =======================================
@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.json

    symbol   = data.get("symbol",   "غير محدد")
    price    = data.get("price",    "غير محدد")
    action   = data.get("action",   "غير محدد")
    ema10    = data.get("ema10",    "")
    ema20    = data.get("ema20",    "")
    interval = data.get("interval", "")
    time_val = data.get("time",     "")

    icon       = "BUY +" if action == "BUY" else "SELL -"
    direction  = "صاعد"  if action == "BUY" else "هابط"

    msg = (
        f"<b>{icon} {symbol}</b>\n"
        f"الاتجاه : {direction}\n"
        f"السعر   : {price}\n"
        f"EMA10   : {ema10}\n"
        f"EMA20   : {ema20}\n"
        f"الفريم  : {interval}\n"
        f"الوقت   : {time_val}"
    )

    send_telegram(msg)
    return {"status": "ok"}, 200

# =======================================
#  Health Check
# =======================================
@app.route("/", methods=["GET"])
def home():
    return {"status": "running"}, 200

# =======================================
#  تشغيل الموقت
# =======================================
scheduler = BackgroundScheduler()
scheduler.add_job(
    func=scheduled_task,
    trigger="interval",
    minutes=3,
    id="scan_job"
)
scheduler.start()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
