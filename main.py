import os
import json
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
            return "No Data Received", 400

        # Apps Script से आने वाला 'ping'
        if data.get("type") == "ping":
            return "pong", 200

        # Apps Script से आने वाला 'order'
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
                    
                    # यहाँ सुधार किया गया है: 'px' की जगह 'limit_px'
                    hl_orders.append({
                        "coin": coin_name,
                        "is_buy": bool(o["isBuy"]),
                        "sz": float(o["sz"]),
                        "limit_px": float(o["limitPx"]), # सही कीवर्ड 'limit_px' है
                        "order_type": {"limit": {"tif": "Gtc"}},
                        "reduce_only": bool(o["reduceOnly"])
                    })

            if hl_orders:
                # बल्क ऑर्डर्स भेजना
                response = exchange.bulk_orders(hl_orders)
                return jsonify(response), 200
            else:
                return jsonify({"error": "Invalid Asset Index"}), 400

    except Exception as e:
        # अगर कोई चाभी (जैसे limitPx) नहीं मिली, तो यहाँ एरर दिखेगा
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
