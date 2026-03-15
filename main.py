import os
from flask import Flask, request, jsonify
from hyperliquid.utils import constants
from hyperliquid.exchange import Exchange
from eth_account import Account

app = Flask(__name__)

# वॉलेट और एक्सचेंज सेटअप (Render की Env Variables से)
address = os.getenv("HL_ADDRESS")
secret_key = os.getenv("HL_SECRET_KEY")
account = Account.from_key(secret_key)
exchange = Exchange(account, constants.MAINNET_API_URL)

@app.route('/trade', methods=['POST'])
def trade():
    data = request.json
    
    # 1. Ping Handling (सिर्फ जगाए रखने के लिए)
    if data.get("type") == "ping":
        return jsonify({"status": "active"}), 200

    # 2. Bulk Order Handling
    if data.get("type") == "order":
        orders_to_send = []
        for o in data.get("orders", []):
            orders_to_send.append({
                "coin": o["asset"],
                "is_buy": o["isBuy"], # Apps Script से TRUE/FALSE आएगा
                "sz": float(o["sz"]),
                "px": float(o["limitPx"]),
                "order_type": {"limit": {"tif": "Gtc"}}, # Default Gtc
                "reduce_only": o["reduceOnly"]
            })

        if orders_to_send:
            # एक साथ सारे ऑर्डर्स मारना (Bulk Execution)
            response = exchange.bulk_orders(orders_to_send)
            return jsonify(response), 200

    return jsonify({"status": "no_data"}), 400

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))
