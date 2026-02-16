# edit number 30
# [OK] BALANCE MODE: Stable & Isolated (112.50+).
# [under progress] TRADE MODE: Final Fix using market_open (No more Error 1).
# ------------------------------------------
# COMPULSORY: Cross Margin & Max Leverage.
# LOGIC STEPS: 1. Side Match = Skip | 2. Reverse/Entry.
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
        # [BALANCE MODE] - NO CHANGES HERE (WORKING)
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
        # [TRADE MODE] - REWRITTEN BASED ON SDK DOCUMENTATION
        # ---------------------------------------------------------
        elif action == "TRADE":
            incoming_trades = data.get("trades", [])
            results = []
            
            user_state = info.user_state(HL_ADDRESS)
            meta = info.meta()
            all_mids = info.all_mids()
            
            active_positions = {p["position"]["coin"]: float(p["position"]["szi"]) 
                               for p in user_state.get("assetPositions", []) 
                               if float(p["position"]["szi"]) != 0}

            for t in incoming_trades:
                idx = int(t["index"])
                coin_data = meta["universe"][idx]
                coin_name = coin_data["name"]
                
                is_buy = t["isBuy"]
                target_usd = float(t["usdSize"])
                price = float(all_mids[coin_name])
                sz_decimals = int(coin_data["szDecimals"])
                
                current_sz = active_positions.get(coin_name, 0.0)

                # 1. Side Match Skip (Same as your logic)
                if (is_buy and current_sz > 0) or (not is_buy and current_sz < 0):
                    results.append(f"{coin_name}: RUNNING")
                    continue

                # 2. Update Leverage (Fixed syntax)
                try:
                    exchange.update_leverage(int(coin_data["maxLeverage"]), coin_name, is_cross=True)
                except:
                    pass

                # 3. Market Order using market_open (Safe & Tested in Edit 56)
                sz = clean_sz(target_usd / price, sz_decimals)
                
                # Minimum size check (Hyperliquid needs ~$10 minimum)
                if (sz * price) < 10.1:
                    sz = clean_sz(10.1 / price, sz_decimals)

                # market_open use kar rahe hain jo direct SDK function hai
                res = exchange.market_open(coin_name, is_buy, sz, slippage=0.05)
                
                if res["status"] == "ok":
                    results.append(f"{coin_name}: ENTRY")
                else:
                    results.append(f"{coin_name}: ERROR")

            return jsonify({"msg": "\n".join(results) if results else "No Action"})

    except Exception as e:
        return jsonify({"msg": f"System Error: {str(e)}"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
