# edit number 28
# [OK] BALANCE MODE: Stable (Edit 08 base).
# [under progress] TRADE MODE: Fixed Leverage Index Error (Error 1).
# ------------------------------------------
# COMPULSORY: Cross Margin & Max Leverage (Always Applied).
# LOGIC STEPS: 1. Cleanup | 2. Side Match = Skip | 3. Reverse/Entry.
# ==========================================

import os
import json
import math
import requests
from flask import Flask, request, jsonify
from eth_account import Account
from hyperliquid.utils import constants
from hyperliquid.exchange import Exchange
from hyperliquid.info import Info

app = Flask(__name__)

# --- SETTINGS ---
HL_SECRET_KEY = os.getenv("HL_SECRET_KEY")
HL_ADDRESS = os.getenv("HL_ADDRESS")

account = Account.from_key(HL_SECRET_KEY)
info = Info(constants.MAINNET_API_URL)
exchange = Exchange(account, constants.MAINNET_API_URL)
HL_INFO_URL = "https://api.hyperliquid.xyz/info"

def clean_sz(sz, decimals):
    factor = 10 ** decimals
    return math.floor(sz * factor) / factor if sz > 0 else math.ceil(sz * factor) / factor

@app.route("/trade", methods=["POST"])
def handle_request():
    try:
        data = request.json
        action = data.get("action")

        # ---------------------------------------------------------
        # [IF ACTION == BALANCE] - (Works Correct)
        # ---------------------------------------------------------
        if action == "BALANCE":
            user_state = info.user_state(HL_ADDRESS)
            spot_state = info.spot_user_state(HL_ADDRESS)
            
            vault_payload = {"type": "userVaultEquities", "user": HL_ADDRESS}
            vault_res = requests.post(HL_INFO_URL, json=vault_payload, timeout=10)
            vault_data = vault_res.json()

            full_report = {
                "PERPETUAL_AND_MARGIN": {
                    "marginSummary": user_state.get("marginSummary", {"accountValue": "0.0"})
                },
                "SPOT_WALLET": spot_state,
                "VAULTS_DATA": vault_data
            }
            return jsonify({"msg": json.dumps(full_report)})

        # ---------------------------------------------------------
        # [IF ACTION == TRADE] - (Fixed Leverage Parameter)
        # ---------------------------------------------------------
        elif action == "TRADE":
            incoming_trades = data.get("trades", [])
            results = []
            
            user_state = info.user_state(HL_ADDRESS)
            meta = info.meta()
            all_mids = info.all_mids()
            
            active_positions = {}
            for pos in user_state.get("assetPositions", []):
                p = pos["position"]
                if float(p["szi"]) != 0:
                    active_positions[p["coin"]] = float(p["szi"])

            for t in incoming_trades:
                # 'index' ko sahi tarah se use karna
                idx = int(t["index"])
                coin_data = meta["universe"][idx]
                coin_name = coin_data["name"]
                
                is_buy_signal = t["isBuy"]
                target_usd = float(t["usdSize"])
                price = float(all_mids[coin_name])
                sz_decimals = int(coin_data["szDecimals"])
                
                current_sz = active_positions.get(coin_name, 0.0)

                # Step 1: Side Match Skip
                if (is_buy_signal and current_sz > 0) or (not is_buy_signal and current_sz < 0):
                    results.append(f"{coin_name}: Skip (Side Match)")
                    continue

                # FIX: Leverage update needs 'idx' (integer), not 'coin_name'
                max_lev = int(coin_data["maxLeverage"])
                exchange.update_leverage(max_lev, idx, is_cross=True)

                # Order logic
                target_sz = clean_sz(target_usd / price, sz_decimals)
                if not is_buy_signal: target_sz = -target_sz
                
                diff_sz = clean_sz(target_sz - current_sz, sz_decimals)

                if diff_sz != 0:
                    order_side = diff_sz > 0
                    res = exchange.order(idx, order_side, abs(diff_sz), price, {"limitFee": 0.04})
                    results.append(f"{coin_name}: {res['status']}")

            return jsonify({"msg": "\n".join(results) if results else "No Action"})

    except Exception as e:
        # Error message detail mein dikhega
        return jsonify({"msg": f"System Error: {str(e)}"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
