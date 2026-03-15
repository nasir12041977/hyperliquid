import os
from flask import Flask, request, jsonify
from hyperliquid.utils import constants
from hyperliquid.exchange import Exchange
from eth_account import Account

app = Flask(__name__)

# चाबियों को सुरक्षित तरीके से लोड करने का फंक्शन
def get_exchange():
    address = os.getenv("HL_ADDRESS")
    secret_key = os.getenv("HL_SECRET_KEY")
    if not address or not secret_key:
        return None
    account = Account.from_key(secret_key)
    return Exchange(account, constants.MAINNET_API_URL)

@app.route('/trade', methods=['POST'])
def trade():
    data = request.json
    if not data:
        return jsonify({"error": "No data"}), 400

    # 1. PING - सिर्फ सर्वर को जगाए रखने के लिए
    if data.get("type") == "ping":
        return jsonify({"status": "active", "msg": "Boss is awake"}), 200

    # 2. ORDER - असली ट्रेडिंग लॉजिक
    if data.get("type") == "order":
        exchange = get_exchange()
        if not exchange:
            return jsonify({"error": "Keys not configured on Render"}), 500
        
        orders = data.get("orders", [])
        hl_orders = []

        for o in orders:
            hl_orders.append({
                "coin": str(o["asset"]),
                "is_buy": bool(o["isBuy"]),
                "sz": float(o["sz"]),
                "px": float(o["limitPx"]),
                "order_type": {"limit": {"tif": "Gtc"}},
                "reduce_only": bool(o["reduceOnly"])
            })

        try:
            # बल्क में आर्डर मारना (Fastest)
            response = exchange.bulk_orders(hl_orders)
            return jsonify(response), 200
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    return jsonify({"error": "Invalid Type"}), 400

if __name__ == "__main__":
    # Render के लिए पोर्ट सेटअप
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
