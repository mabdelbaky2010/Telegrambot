from flask import Flask, request
import requests

app = Flask(__name__)

# ← ضع بياناتك هنا
# ✅ صح — التوكن يروح داخل علامات التنصيص
TELEGRAM_TOKEN = "8784816733:AAF2FpH9EqJ85BzVUjSXH1UI4McDIhSbNvI"
CHAT_ID        = "1621604072"

def send_telegram(message):
    url = f"https://api.telegram.org/bot8784816733:AAF2FpH9EqJ85BzVUjSXH1UI4McDIhSbNvI/sendMessage"
    data = {
        "chat_id": CHAT_ID,
        "text": message,
        "parse_mode": "HTML"
    }
    requests.post(url, data=data)

@app.route("/webhook", methods=["POST"])
def webhook():
    try:
        # استقبال البيانات من TradingView
        data = request.get_json(force=True)

        # تنسيق الرسالة
        symbol  = data.get("symbol",  "غير محدد")
        price   = data.get("price",   "غير محدد")
        action  = data.get("action",  "غير محدد")
        message = data.get("message", "")

        text = (
            f"📊 <b>تنبيه TradingView</b>\n"
            f"━━━━━━━━━━━━━━\n"
            f"📌 السهم : <b>{symbol}</b>\n"
            f"💰 السعر : <b>{price}</b>\n"
            f"🚦 الإشارة: <b>{action}</b>\n"
            f"📝 {message}"
        )

        send_telegram(text)
        return {"status": "ok"}, 200

    except Exception as e:
        send_telegram(f"⚠️ خطأ: {str(e)}")
        return {"status": "error"}, 500

@app.route("/")
def home():
    return "✅ السيرفر يعمل!", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
