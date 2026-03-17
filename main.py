import os
from flask import Flask, request, jsonify
from hyperliquid.utils import constants
from hyperliquid.exchange import Exchange
from hyperliquid.info import Info
from eth_account import Account

app = Flask(__name__)

_exchange = None
_info = None
_universe = None

def get_exchange():
    global _exchange
    if _exchange is None:
        address = os.getenv("HL_ADDRESS")
        secret_key = os.getenv("HL_SECRET_KEY")
        if not address or not secret_key:
            return None
        account = Account.from_key(secret_key)
        _exchange = Exchange(account, constants.MAINNET_API_URL)
    return _exchange

def get_universe():
    global _info, _universe
    if _universe is None:
        _info = Info(constants.MAINNET_API_URL, skip_ws=True)
        _universe = _info.meta()['universe']
    return _universe

@app.route('/trade', methods=['POST'])
def trade():
    try:
        data = request.json
        if not data:
            return jsonify({"error": "No Data Received"}), 400

        if data.get("type") == "ping":
            return jsonify({"msg": "pong"}), 200

        if data.get("type") == "order":
            exchange = get_exchange()
            if not exchange:
                return jsonify({"error": "Environment Variables not set"}), 500

            universe = get_universe()
            orders = data.get("orders", [])
            hl_orders = []

            for o in orders:
                asset_index = int(o["asset"])
                if asset_index < len(universe):
                    hl_orders.append({
                        "coin": universe[asset_index]['name'],
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
                return jsonify({"error": "No valid orders"}), 400

        return jsonify({"msg": "No action taken"}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
