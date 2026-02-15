import os
import json
import requests
from flask import Flask, request, jsonify
from eth_account import Account
from hyperliquid.utils import constants
from hyperliquid.exchange import Exchange
from hyperliquid.info import Info

app = Flask(__name__)

# ===== ENV VARS =====
HL_SECRET_KEY = os.getenv("HL_SECRET_KEY")
HL_ADDRESS = os.getenv("HL_ADDRESS")

if not HL_SECRET_KEY or not HL_ADDRESS:
    raise Exception("HL_SECRET_KEY or HL_ADDRESS missing")

account = Account.from_key(HL_SECRET_KEY)

info = Info(constants.MAINNET_API_URL)
exchange = Exchange(account, constants.MAINNET_API_URL)

HL_INFO_URL = "https://api.hyperliquid.xyz/info"

# -------- VAULT EQUITY (RAW API) --------
def get_vault_equity(address):
    payload = {
        "type": "userVaultEquities",
        "user": address
    }
    r = requests.post(HL_INFO_URL, json=payload, timeout=10)
    data = r.json()
    return sum(float(v.get("equity", 0)) for v in data)

@app.route("/trade", methods=["POST"])
def handle_request():
    try:
        data = request.json
        action = data.get("action")

        # ================= BALANCE MODE =================
        if action == "BALANCE":
            user_state = info.user_state(HL_ADDRESS)
            spot_state = info.spot_user_state(HL_ADDRESS)

            # Perp Trading Equity
            trading_equity = float(
                user_state.get("marginSummary", {}).get("accountValue", 0)
            )

            # Spot USDC
            spot_usdc = 0.0
            for b in spot_state.get("balances", []):
                if b.get("coin") == "USDC":
                    spot_usdc = float(b.get("total", 0))

            # Vault Equity
            vault_equity = get_vault_equity(HL_ADDRESS)

            # Final Total Equity
            total_equity = trading_equity + spot_usdc + vault_equity

            return jsonify({
                "msg": f"Total Equity: {round(total_equity, 2)}"
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
