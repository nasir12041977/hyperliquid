import os
from flask import Flask, request, jsonify
from hyperliquid.utils import constants
from hyperliquid.exchange import Exchange
from hyperliquid.info import Info
from eth_account import Account

app = Flask(__name__)

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
            return jsonify({"error": "No Data Received"}), 400

        # PING चेक
        if data.get("type") == "ping":
            return jsonify({"msg": "pong"}), 200

        # ORDER चेक
        if data.get("type") == "order":
            exchange = get_exchange()
            if not exchange:
                return jsonify({"error": "Environment Variables not set"}), 500
            
            info = Info(constants.MAINNET_API_URL, skip_ws=True)
            meta = info.meta()
            universe = meta['universe']

            orders = data.get("orders", [])
            hl_orders = []

            for o in orders:
                asset_index = int(o["asset"])
                if asset_index < len(universe):
                    coin_name = universe[asset_index]['name']
                    hl_orders.append({
                        "coin": coin_name,
                        "is_buy": bool(o["isBuy"]),
                        "sz": float(o["sz"]),
                        "limit_px": float(o["limitPx"]),
                        "order_type": {"limit": {"tif": "Gtc"}},
                        "reduce_only": bool(o["reduceOnly"])
                    })

            if hl_orders:
                response = exchange.bulk_orders(hl_orders)
                return jsonify(response), 200
            else:
                return jsonify({"error": "No valid orders in list"}), 400

        # अगर ऊपर का कुछ भी मैच न हो, तो यह जवाब देगा (ताकि 500 एरर न आए)
        return jsonify({"msg": "Request received but no action taken", "data_received": data}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
