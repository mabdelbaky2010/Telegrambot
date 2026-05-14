from flask import Flask, request
import requests
app = Flask(__name__)

TELEGRAM_TOKEN = "8784816733:AAF2FpH9EqJ85BzVUjSXH1UI4McDIhSbNvI"
CHAT_ID = "1003940485703"

def send_telegram(message):
    url = f"https://api.telegram.org/bot8784816733:AAF2FpH9EqJ85BzVUjSXH1UI4McDIhSbNvI/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": message
    }
    requests.post(url, data=payload)


@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.json
    
    symbol   = data.get("symbol", "غير محدد")
    price    = data.get("price", "غير محدد")
    action   = data.get("action", "غير محدد")
    ema10    = data.get("ema10", "")
    ema20    = data.get("ema20", "")
    interval = data.get("interval", "")
    time     = data.get("time", "")
    
 # تقريب EMA لرقمين بعد العلامة العشرية
    ema10_raw = data.get("ema10", "")
    ema20_raw = data.get("ema20", "")
    try:
        ema10 = f"{float(ema10_raw):.2f}"
    except:
        ema10 = ema10_raw
    try:
        ema20 = f"{float(ema20_raw):.2f}"
    except:
        ema20 = ema20_raw
        pass

    icon = "🟢" if action == "BUY" else "🔴"
    
    msg = (
        f"{icon}  {'صاعد' if action == 'BUY' else 'هابط'}\n"
        f"📊 السهم: {symbol}\n"
        f"💰 السعر: {price} ر.س\n"
        f"EMA10: {ema10} | EMA20: {ema20}\n"
        f"⏱ الفريم: {interval}\n"
        f" القرار: {action}\n"
        f"🕐 {time}"
    )
    
    send_telegram(msg)
    return {"status": "ok"}, 200
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
