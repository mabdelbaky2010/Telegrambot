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
    data = request.get_json(force=True, silent=True) or {}
    symbol = data.get("symbol", "غير محدد")
    price = data.get("price", "غير محدد")
    action = data.get("action", "غير محدد")
    message = data.get("message", "")
    text = (
        f"تنبيه TradingView\n"
        f"السهم: {symbol}\n"
        f"السعر: {price}\n"
        f"الاشارة: {action}\n"
        f"{message}"
    )
    send_telegram(text)
    return {"status": "ok"}, 200


@app.route("/")
def home():
    return "السيرفر يعمل!", 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
