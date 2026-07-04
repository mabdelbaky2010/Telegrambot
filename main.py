#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from flask import Flask, request
from apscheduler.schedulers.background import BackgroundScheduler
import requests
import os
import json

app = Flask(__name__)

TELEGRAM_TOKEN = "8784816733:AAF2FpH9EqJ85BzVUjSXH1UI4McDIhSbNvI"
CHAT_ID        = "-1003940485703"
USERS_FILE     = "users.json"
ADMIN_ID       = "1621604072"

# =======================================
#  ادارة المستخدمين
# =======================================
def load_users():
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE) as f:
            return json.load(f)
    return [ADMIN_ID]

def save_users(users):
    with open(USERS_FILE, "w") as f:
        json.dump(users, f)

def add_user(chat_id):
    users = load_users()
    chat_id = str(chat_id)
    if chat_id not in users:
        users.append(chat_id)
        save_users(users)
        return True
    return False

def remove_user(chat_id):
    users = load_users()
    chat_id = str(chat_id)
    if chat_id in users:
        users.remove(chat_id)
        save_users(users)
        return True
    return False

# =======================================
#  ارسال تليجرام
# =======================================
def send_telegram(message, chat_id=None):
    targets = [chat_id] if chat_id else load_users()
    for cid in targets:
        try:
            requests.post(
                f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
                json={
                    "chat_id":    cid,
                    "text":       message,
                    "parse_mode": "HTML"
                },
                timeout=10
            )
        except Exception as e:
            print(f"ERROR Telegram {cid}: {e}")

# =======================================
#  تنسيق الارقام
# =======================================
def fmt(val):
    try:
        return f"{float(val):.2f}"
    except:
        return str(val)

# =======================================
#  بناء رسالة فيبوناتشى
# =======================================
def build_fib_message(data):
    symbol   = data.get("symbol",   "N/A")
    action   = data.get("action",   "N/A")
    level    = data.get("level",    "N/A")
    price    = fmt(data.get("price",    "N/A"))
    interval = data.get("interval", "N/A")
    time_val = data.get("time",     "N/A")

    if action == "CALL":
        icon      = "CALL +"
        direction = "شراء عقد CALL"
        color_txt = "صاعد"
    else:
        icon      = "PUT  -"
        direction = "شراء عقد PUT"
        color_txt = "هابط"

    # تحديد الاهداف بناء على المستوى
    targets = get_targets(action, level, float(data.get("price", 0)))

    sep = "--------------------------------"
    msg = (
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
    return msg

# =======================================
#  حساب الاهداف من المستوى
# =======================================
def get_targets(action, level, price):
    # نسب فيبوناتشى للحساب
    fib_levels = {
        "CALL": {
            "78.6%": {"t1": 1.009, "t2": 1.018, "t3": 1.027, "stop": 0.985},
            "61.8%": {"t1": 1.009, "t2": 1.018, "t3": 1.027, "stop": 0.985},
            "50%":   {"t1": 1.009, "t2": 1.018, "t3": 1.027, "stop": 0.985},
            "38.2%": {"t1": 1.009, "t2": 1.018, "t3": 1.027, "stop": 0.985},
            "23.6%": {"t1": 1.009, "t2": 1.018, "t3": 1.027, "stop": 0.985},
        },
        "PUT": {
            "23.6%": {"t1": 0.991, "t2": 0.982, "t3": 0.973, "stop": 1.015},
            "38.2%": {"t1": 0.991, "t2": 0.982, "t3": 0.973, "stop": 1.015},
            "50%":   {"t1": 0.991, "t2": 0.982, "t3": 0.973, "stop": 1.015},
            "61.8%": {"t1": 0.991, "t2": 0.982, "t3": 0.973, "stop": 1.015},
            "78.6%": {"t1": 0.991, "t2": 0.982, "t3": 0.973, "stop": 1.015},
        }
    }

    try:
        ratios = fib_levels[action][level]
        return {
            "t1":   f"{price * ratios['t1']:.2f}",
            "t2":   f"{price * ratios['t2']:.2f}",
            "t3":   f"{price * ratios['t3']:.2f}",
            "stop": f"{price * ratios['stop']:.2f}",
        }
    except:
        return {"t1": "N/A", "t2": "N/A", "t3": "N/A", "stop": "N/A"}

# =======================================
#  بناء رسالة EMA
# =======================================
def build_ema_message(data):
    symbol   = data.get("symbol",   "N/A")
    action   = data.get("action",   "N/A")
    price    = fmt(data.get("price",    "N/A"))
    ema10    = fmt(data.get("ema10",    ""))
    ema20    = fmt(data.get("ema20",    ""))
    interval = data.get("interval", "N/A")
    time_val = data.get("time",     "N/A")

    icon      = "BUY +" if action == "BUY" else "SELL -"
    direction = "شراء"  if action == "BUY" else "بيع"

    sep = "--------------------------------"
    msg = (
        f"<b>{icon} {symbol}</b>\n"
        f"{sep}\n"
        f"التوصية  : {direction}\n"
        f"السعر    : {price}\n"
        f"EMA10    : {ema10}\n"
        f"EMA20    : {ema20}\n"
        f"الفريم   : {interval} دقيقة\n"
        f"{sep}\n"
        f"الوقت    : {time_val}"
    )
    return msg

# =======================================
//  Webhook - يستقبل اشارات TradingView
# =======================================
@app.route("/webhook", methods=["POST"])
def webhook():
    try:
        data = request.json

        if not data:
            return {"status": "error", "message": "no data"}, 400

        action = data.get("action", "")
        level  = data.get("level",  "")

        # اشارة فيبوناتشى
        if action in ["CALL", "PUT"]:
            msg = build_fib_message(data)

        # اشارة EMA
        elif action in ["BUY", "SELL"]:
            msg = build_ema_message(data)

        # اشارة غير معروفة
        else:
            msg = f"اشارة جديدة:\n{json.dumps(data, ensure_ascii=False, indent=2)}"

        send_telegram(msg)
        return {"status": "ok"}, 200

    except Exception as e:
        print(f"ERROR webhook: {e}")
        return {"status": "error", "message": str(e)}, 500

# =======================================
#  Webhook تليجرام - اوامر المستخدمين
# =======================================
@app.route("/telegram", methods=["POST"])
def telegram_update():
    data = request.json

    if "message" not in data:
        return {"ok": True}

    msg     = data["message"]
    chat_id = str(msg["chat"]["id"])
    text    = msg.get("text", "")

    if text == "/start":
        added = add_user(chat_id)
        if added:
            send_telegram(
                "<b>تم تسجيلك بنجاح</b>\n"
                "ستصلك اشارات التداول تلقائياً\n\n"
                "الاوامر:\n"
                "/start  - اشتراك\n"
                "/stop   - الغاء الاشتراك\n"
                "/status - حالة الاشتراك",
                chat_id
            )
        else:
            send_telegram("انت مشترك بالفعل", chat_id)

    elif text == "/stop":
        if chat_id == ADMIN_ID:
            send_telegram("لا يمكن الغاء اشتراك الادمن", chat_id)
        else:
            remove_user(chat_id)
            send_telegram("تم الغاء اشتراكك", chat_id)

    elif text == "/status":
        users = load_users()
        status = "مشترك" if chat_id in users else "غير مشترك"
        send_telegram(
            f"الحالة: {status}\n"
            f"اجمالي المشتركين: {len(users)}",
            chat_id
        )

    elif text == "/list" and chat_id == ADMIN_ID:
        users = load_users()
        msg_text = f"<b>المشتركون ({len(users)}):</b>\n"
        for u in users:
            msg_text += f"- {u}\n"
        send_telegram(msg_text, chat_id)

    elif text.startswith("/broadcast ") and chat_id == ADMIN_ID:
        broadcast_msg = text.replace("/broadcast ", "")
        send_telegram(f"<b>رسالة من الادمن:</b>\n{broadcast_msg}")

    return {"ok": True}

# =======================================
#  Health Check
# =======================================
@app.route("/", methods=["GET"])
def home():
    users = load_users()
    return {"status": "running", "subscribers": len(users)}, 200

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
