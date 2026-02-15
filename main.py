import os
import json
from flask import Flask, request, jsonify
from eth_account import Account
from hyperliquid.utils import constants
from hyperliquid.exchange import Exchange
from hyperliquid.info import Info

app = Flask(__name__)

# ===== ENV VARS =====
SECRET_KEY = os.getenv("HL_SECRET_KEY")
ACCOUNT_ADDRESS = os.getenv("HL_ADDRESS")

if not SECRET_KEY or not ACCOUNT_ADDRESS:
    raise Exception("HL_SECRET_KEY or HL_ADDRESS missing")

account = Account.from_key(SECRET_KEY)

info = Info(constants.MAINNET_API_URL)
exchange = Exchange(account, constants.MAINNET_API_URL)

@app.route("/trade", methods=["POST"])
def handle_request():
    try:
        data = request.json
        action = data.get("action")

        # ================= BALANCE MODE =================
        if action == "BALANCE":
            user_state = info.user_state(ACCOUNT_ADDRESS)

            margin = user_state.get("marginSummary", {})
            total_equity = float(margin.get("accountValue", 0))

            return jsonify({
                "msg": f"Total Equity: {total_equity}"
            })

        # ================= TRADE MODE =================
        elif action == "TRADE":
            trades = data.get("trades", [])
            if not trades:
                return jsonify({"msg": "No trade data"})

            meta = info.meta()
            sz_decimals = {a["name"]: a["szDecimals"] for a in meta["universe"]}

            logs = []

            for trade in trades:
                coin = trade[0]
                side = trade[1]
                usd_size = float(trade[2])

                if usd_size <= 0:
                    continue

                decimals = sz_decimals.get(coin, 4)

                is_buy = True if str(side).lower() == "buy" else False
                size = round(abs(usd_size), decimals)

                result = exchange.market_open(coin, is_buy, size)

                logs.append(f"{coin} {side}: {json.dumps(result)}")

            return jsonify({"msg": "\n".join(logs)})

        else:
            return jsonify({"msg": "Invalid action"})

    except Exception as e:
        return jsonify({"msg": f"System Error: {str(e)}"})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
