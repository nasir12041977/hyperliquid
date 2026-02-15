import os
import json
from flask import Flask, request, jsonify
from eth_account import Account
from hyperliquid.utils import constants
from hyperliquid.exchange import Exchange
from hyperliquid.info import Info

app = Flask(__name__)

SECRET_KEY = os.getenv("HL_PRIVATE_KEY")
ACCOUNT_ADDRESS = os.getenv("HL_WALLET_ADDRESS")

info = Info(constants.MAINNET_API_URL)
exchange = Exchange(Account.from_key(SECRET_KEY), constants.MAINNET_API_URL)

@app.route('/trade', methods=['POST'])
def handle_request():
    try:
        data = request.json or {}
        action = data.get("action")

        if action == "BALANCE":
            user_state = info.user_state(ACCOUNT_ADDRESS)
            balance = user_state.get("marginSummary", {}).get("accountValue", "0.0")
            return jsonify({"msg": f"Total Balance: {balance}"})

        elif action == "TRADE":
            trades = data.get("trades", [])
            if not trades:
                return jsonify({"msg": "No trade data found"})

            meta = info.meta()
            sz_decimals = {asset["name"]: asset["szDecimals"] for asset in meta["universe"]}

            output_logs = []
            for trade in trades:
                coin = trade[0]
                side = trade[1]
                order_diff_sz = float(trade[2])

                coin_decimals = sz_decimals.get(coin, 4)
                final_sz = abs(round(order_diff_sz, coin_decimals))

                is_buy = True if side.lower() == "buy" else False
                order_result = exchange.market_open(coin, is_buy, final_sz)

                output_logs.append(f"{coin} {side}: {json.dumps(order_result)}")

            return jsonify({"msg": "\n".join(output_logs)})

        else:
            return jsonify({"msg": "Invalid Action"})

    except Exception as e:
        return jsonify({"msg": f"System Error: {str(e)}"})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
