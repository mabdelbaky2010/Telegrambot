from flask import Flask, request
import requests

app = Flask(__name__)

# ── CONFIG ────────────────────────────────────────────────────────────────────
TELEGRAM_TOKEN = "8784816733:AAF2FpH9EqJ85BzVUjSXH1UI4McDIhSbNvI"

# ✏️ أضف أو احذف chat_id هنا
RECIPIENTS = [
   # "-1003940485703",  # 📢 القناة الرئيسية
  #  "1621604072",      # 👤 محمود (شخصي)
    "1312946434",      # 👤 مستخدم 2
]
# ─────────────────────────────────────────────────────────────────────────────


def send_to_all(message: str):
    """يرسل الرسالة لجميع المستقبلين في RECIPIENTS."""
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    for chat_id in RECIPIENTS:
        try:
            r = requests.post(
                url,
                json={
                    "chat_id":    chat_id,
                    "text":       message,
                    "parse_mode": "HTML",
                },
                timeout=10,
            )
            r.raise_for_status()
            print(f"  ✅ Sent to {chat_id}", flush=True)
        except Exception as e:
            print(f"  ❌ Failed → {chat_id}: {e}", flush=True)


@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.json or {}

    # DEBUG — يظهر في Railway logs كل ما يصل من TradingView
    print("DATA RECEIVED:", data, flush=True)

    # ── استخراج البيانات ──────────────────────────────────────────────────────
    symbol     = data.get("symbol",   "غير محدد")
    price      = data.get("price",    "غير محدد")
    action     = data.get("action",   "غير محدد")
    interval   = data.get("interval", "")
    alert_time = data.get("time",     "")   # ✅ تم تغيير الاسم من time → alert_time

    # EMA10 — يبحث في عدة مفاتيح محتملة
    ema10_raw = data.get("ema10") or data.get("plot_0") or data.get("EMA10") or 0
    try:
        ema10 = f"{float(ema10_raw):.2f}"
    except (ValueError, TypeError):
        ema10 = str(ema10_raw)

    # EMA20 — يبحث في عدة مفاتيح محتملة
    ema20_raw = data.get("ema20") or data.get("plot_1") or data.get("EMA20") or 0
    try:
        ema20 = f"{float(ema20_raw):.2f}"
    except (ValueError, TypeError):
        ema20 = str(ema20_raw)

    # ── بناء الرسالة ─────────────────────────────────────────────────────────
    is_buy    = str(action).upper() == "BUY"
    icon      = "🟢" if is_buy else "🔴"
    direction = "صاعد 📈" if is_buy else "هابط 📉"

    msg = (
        f"{icon}  <b>{direction}</b>\n"
        f"📊 السهم: <b>{symbol}</b>\n"
        f"💰 السعر: {price} ر.س\n"
        f"📐 EMA10: {ema10}  |  EMA20: {ema20}\n"
        f"⏱ الفريم: {interval}\n"
        f"القرار: <b>{action}</b>\n"
        f"🕐 {alert_time}"
    )

    # ── إرسال لجميع المستقبلين ───────────────────────────────────────────────
    print(f"Sending to {len(RECIPIENTS)} recipient(s)...", flush=True)
    send_to_all(msg)
    return {"status": "ok"}, 200


@app.route("/health", methods=["GET"])
def health():
    """اختبار سريع — افتح الرابط في المتصفح للتأكد أن السيرفر شغّال."""
    send_to_all("✅ <b>Webhook يعمل بشكل صحيح</b>\nجاهز لاستقبال تنبيهات TradingView.")
    return {"status": "ok", "recipients": len(RECIPIENTS)}, 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
