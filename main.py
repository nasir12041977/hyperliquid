import os
import json
from flask import Flask, request, jsonify
from eth_account import Account
from hyperliquid.utils import constants
from hyperliquid.exchange import Exchange
from hyperliquid.info import Info

app = Flask(__name__)

HL_SECRET_KEY = os.getenv("HL_SECRET_KEY")
HL_ADDRESS = os.getenv("HL_ADDRESS")

@app.route("/trade", methods=["POST"])
def handle_request():
    try:
        data = request.json or {}
        action = data.get("action")

        info = Info(constants.MAINNET_API_URL)

        # ===== BALANCE MODE =====
        if action == "BALANCE":
            user_state = info.user_state(HL_ADDRESS)

            # Trading Equity (Perp)
            cross = user_state.get("crossMarginSummary", {})
            trading_equity = cross.get("accountValue", "0.0")

            # Vault Equity
            vaults = info.user_vaults(HL_ADDRESS)
            vault_equity = "0.0"
            if vaults and len(vaults) > 0:
                vault_equity = vaults[0].get("equity", "0.0")

            return jsonify({
                "Trading Equity": trading_equity,
                "Vault Equity": vault_equity,
                "Total Equity": "Dashboard Value"
            })

        # ===== TRADE MODE =====
        elif action == "TRADE":
            exchange = Exchange(Account.from_key(HL_SECRET_KEY), constants.MAINNET_API_URL)

            trades = data.get("trades", [])
            if not trades:
                return jsonify({"msg": "No trade data found"})

            meta = info.meta()
            sz_decimals = {a["name"]: a["szDecimals"] for a in meta["universe"]}

            output_logs = []

            for trade in trades:
                coin = trade[0]
                side = trade[1]
                order_diff_sz = float(trade[2])

                coin_decimals = sz_decimals.get(coin, 4)
                final_sz = abs(round(order_diff_sz, coin_decimals))

                is_buy = True if side.lower() == "buy" else False
                result = exchange.market_open(coin, is_buy, final_sz)

                output_logs.append(f"{coin} {side}: {json.dumps(result)}")

            return jsonify({"msg": "\n".join(output_logs)})

        else:
            return jsonify({"msg": "Invalid Action"})

    except Exception as e:
        return jsonify({"msg": f"System Error: {str(e)}"})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
