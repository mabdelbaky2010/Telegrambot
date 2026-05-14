from flask import Flask, request
import requests

app = Flask(__name__)

TELEGRAM_TOKEN = "8784816733:AAF2FpH9EqJ85BzVUjSXH1UI4McDIhSbNvI"
CHAT_ID = "1621604072"


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

    icon = "🟢" if action == "BUY" else "🔴"
    
    msg = (
        f"{icon} <b>تقاطع {'صاعد' if action == 'BUY' else 'هابط'}</b>\n"
        f"📊 السهم: <b>{symbol}</b>\n"
        f"💰 السعر: {price} ر.س\n"
        f"📈 EMA10: {ema10}  |  EMA20: {ema20}\n"
        f"⏱ الفريم: {interval}\n"
        f"🕐 {time}"
    )
    
    send_telegram(msg)
    return {"status": "ok"}, 200
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
