#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from flask import Flask, request
from apscheduler.schedulers.background import BackgroundScheduler
import requests
import os
import json
app = Flask(__name__)
TELEGRAM_TOKEN = "8784816733:AAF2FpH9EqJ85BzVUjSXH1UI4McDIhSbNvI"
CHANNEL_ID     = os.environ.get("CHANNEL_ID", "-1003940485703")
ADMIN_ID       = "1621604072"
# =======================================
#  ارسال للقناة
# =======================================
def send_telegram(message, chat_id=None):
    target = chat_id if chat_id else CHANNEL_ID
    try:
        r = requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
            json={
                "chat_id":    target,
                "text":       message,
                "parse_mode": "HTML"
            },
            timeout=10
        )
        print(f"Telegram response: {r.status_code} | {r.text}")
    except Exception as e:
        print(f"ERROR Telegram: {e}")
# =======================================
#  تنسيق الارقام
# =======================================
def fmt(val):
    try:
        return f"{float(val):.2f}"
    except:
        return str(val)
# =======================================
#  حساب الاهداف
# =======================================
def get_targets(action, price):
    try:
        p = float(price)
    except:
        return {"t1": "N/A", "t2": "N/A", "t3": "N/A", "stop": "N/A"}
    if action == "CALL":
        return {
            "t1":   f"{p * 1.009:.2f}",
            "t2":   f"{p * 1.018:.2f}",
            "t3":   f"{p * 1.027:.2f}",
            "stop": f"{p * 0.985:.2f}",
        }
    else:
        return {
            "t1":   f"{p * 0.991:.2f}",
            "t2":   f"{p * 0.982:.2f}",
            "t3":   f"{p * 0.973:.2f}",
            "stop": f"{p * 1.015:.2f}",
        }
# =======================================
#  بناء رسالة فيبوناتشى
# =======================================
def build_fib_message(data):
    symbol   = data.get("symbol",   "N/A")
    action   = data.get("action",   "N/A")
    level    = data.get("level",    "N/A")
    price    = fmt(data.get("price", 0))
    interval = data.get("interval", "N/A")
    time_val = data.get("time",     "N/A")
    targets  = get_targets(action, data.get("price", 0))
    if action == "CALL":
        icon      = "CALL +"
        direction = "شراء عقد CALL"
        color_txt = "صاعد"
    else:
        icon      = "PUT  -"
        direction = "شراء عقد PUT"
        color_txt = "هابط"
    sep = "--------------------------------"
    return (
        f"<b>{icon} {symbol}</b>\n"
        f"{sep}\n"
        f"النوع    : {direction}\n"
        f"الاتجاه  : {color_txt}\n"
        f"المستوى  : فيبوناتشى {level}\n"
        f"السعر    : {price}\n"
        f"الفريم   : {interval} دقيقة\n"
        f"{sep}\n"
        f"هدف 1   : {targets['t1']}\n"
        f"هدف 2   : {targets['t2']}\n"
        f"هدف 3   : {targets['t3']}\n"
        f"{sep}\n"
        f"وقف خسارة: {targets['stop']}\n"
        f"{sep}\n"
        f"الوقت    : {time_val}"
    )
# =======================================
#  بناء رسالة EMA (تم التعديل: اهداف بدل EMA10/EMA20)
# =======================================
def build_ema_message(data):
    symbol   = data.get("symbol",   "N/A")
    action   = data.get("action",   "N/A")
    price    = fmt(data.get("price",  0))
    interval = data.get("interval", "N/A")
    time_val = data.get("time",     "N/A")
    # BUY تتحسب زي CALL و SELL تتحسب زي PUT
    targets  = get_targets("CALL" if action == "BUY" else "PUT", data.get("price", 0))
    icon      = "BUY +" if action == "BUY" else "SELL -"
    direction = "شراء"  if action == "BUY" else "بيع"
    sep = "--------------------------------"
    return (
        f"<b>{icon} {symbol}</b>\n"
        f"{sep}\n"
        f"التوصية  : {direction}\n"
        f"السعر    : {price}\n"
        f"الفريم   : {interval} دقيقة\n"
        f"{sep}\n"
        f"هدف 1   : {targets['t1']}\n"
        f"هدف 2   : {targets['t2']}\n"
        f"هدف 3   : {targets['t3']}\n"
        f"{sep}\n"
        f"وقف خسارة: {targets['stop']}\n"
        f"{sep}\n"
        f"الوقت    : {time_val}"
    )
# =======================================
#  Webhook - اشارات TradingView
# =======================================
@app.route("/webhook", methods=["POST"])
def webhook():
    try:
        # ✅ يقبل اي نوع content-type
        data = request.get_json(force=True, silent=True)
        if not data:
            data = request.form.to_dict()
        if not data:
            print("ERROR: no data received")
            return {"status": "error", "message": "no data"}, 400
        print(f"Webhook received: {data}")
        action = data.get("action", "")
        if action in ["CALL", "PUT"]:
            msg = build_fib_message(data)
        elif action in ["BUY", "SELL"]:
            msg = build_ema_message(data)
        else:
            msg = f"اشارة جديدة:\n{json.dumps(data, ensure_ascii=False, indent=2)}"
        # ✅ يبعت للقناة دائماً
        send_telegram(msg)
        return {"status": "ok"}, 200
    except Exception as e:
        print(f"ERROR webhook: {e}")
        return {"status": "error", "message": str(e)}, 500
# =======================================
#  Webhook - اوامر تليجرام
# =======================================
@app.route("/telegram", methods=["POST"])
def telegram_update():
    try:
        # ✅ يقبل اي نوع content-type
        data = request.get_json(force=True, silent=True)
        if not data or "message" not in data:
            return {"ok": True}
        msg     = data["message"]
        chat_id = str(msg["chat"]["id"])
        text    = msg.get("text", "")
        print(f"Telegram command: {text} from {chat_id}")
        if text == "/start":
            send_telegram(
                "<b>مرحباً بك في WolfStock</b>\n\n"
                "اشترك في القناة لتصلك الاشارات:\n"
                "@wofl7stocks\n\n"
                "الاشارات تصل تلقائياً للقناة",
                chat_id
            )
        elif text == "/help":
            send_telegram(
                "<b>مساعدة WolfStock</b>\n\n"
                "الاشارات تصل للقناة تلقائياً\n"
                "اشترك في القناة: @wofl7stocks\n\n"
                "/start - رسالة ترحيب\n"
                "/help  - المساعدة",
                chat_id
            )
        elif text == "/test" and chat_id == ADMIN_ID:
            # ✅ يبعت للقناة مش للأدمن فقط
            send_telegram(
                "<b>CALL + SPX</b>\n"
                "--------------------------------\n"
                "النوع    : شراء عقد CALL\n"
                "المستوى  : فيبوناتشى 61.8%\n"
                "السعر    : 5250.00\n"
                "الفريم   : 15 دقيقة\n"
                "--------------------------------\n"
                "هدف 1   : 5297.25\n"
                "هدف 2   : 5344.50\n"
                "هدف 3   : 5391.75\n"
                "--------------------------------\n"
                "وقف خسارة: 5171.25\n"
                "--------------------------------\n"
                "الوقت    : 2026-07-04 15:00"
            )
            send_telegram("تم ارسال رسالة تجريبية للقناة", chat_id)
        elif text == "/stats" and chat_id == ADMIN_ID:
            send_telegram(
                f"<b>احصائيات البوت</b>\n"
                f"القناة: {CHANNEL_ID}\n"
                f"البوت يعمل بشكل صحيح",
                chat_id
            )
        return {"ok": True}
    except Exception as e:
        print(f"ERROR telegram_update: {e}")
        return {"ok": True}
# =======================================
#  Health Check
# =======================================
@app.route("/", methods=["GET"])
def home():
    return {"status": "running", "channel": CHANNEL_ID}, 200
# =======================================
#  الموقت
# =======================================
def scheduled_task():
    print("الفحص الدوري...")
scheduler = BackgroundScheduler()
scheduler.add_job(func=scheduled_task, trigger="interval", minutes=3, id="scan_job")
scheduler.start()
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
