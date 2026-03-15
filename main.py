import os
from flask import Flask, request, jsonify
from hyperliquid.utils import constants
from hyperliquid.exchange import Exchange
from eth_account import Account

app = Flask(__name__)

# एक्सचेंज सेटअप करने का फंक्शन
def get_exchange():
    address = os.getenv("HL_ADDRESS")
    secret_key = os.getenv("HL_SECRET_KEY")
    if not address or not secret_key:
        return None
    account = Account.from_key(secret_key)
    return Exchange(account, constants.MAINNET_API_URL)

@app.route('/trade', methods=['POST'])
def trade():
    try:
        data = request.json
        if not data:
            return "No Data Received", 400

        # 1. PING HANDLER
        if data.get("type") == "ping":
            return "pong", 200

        # 2. ORDER HANDLER
        if data.get("type") == "order":
            exchange = get_exchange()
            if not exchange:
                return jsonify({"error": "Environment Variables not set"}), 500
            
            orders = data.get("orders", [])
            hl_orders = []

            # Apps Script के डेटा को Hyperliquid के फॉर्मेट में बदलना
            for o in orders:
                hl_orders.append({
                    "coin": str(o["asset"]),
                    "is_buy": bool(o["isBuy"]),
                    "sz": float(o["sz"]),
                    "px": float(o["limitPx"]),
                    "order_type": {"limit": {"tif": "Gtc"}},
                    "reduce_only": bool(o["reduceOnly"])
                })

            if hl_orders:
                # बल्क आर्डर मारना
                response = exchange.bulk_orders(hl_orders)
                # यह पूरा रिस्पॉन्स वापस भेजेगा जिसमें statuses[] मौजूद होंगे
                return jsonify(response), 200
            else:
                return jsonify({"error": "Empty orders list"}), 400

    except Exception as e:
        return jsonify({"error": str(e)}), 500

    return jsonify({"error": "Invalid request type"}), 400

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
