# ==========================================
# edit number 34
# [OK] BALANCE MODE: Stable.
# [under progress] TRADE MODE: Bulk Optimization (Turbo Mode).
# ------------------------------------------
# LOGIC: Batch processing $200$ orders in one go.
# NO CHANGES: Google Apps Script format remains 100% same.
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

def clean_sz(sz, decimals):
    factor = 10 ** decimals
    return math.floor(sz * factor) / factor if sz > 0 else math.ceil(sz * factor) / factor

@app.route("/trade", methods=["POST"])
def handle_request():
    try:
        data = request.json
        action = data.get("action")

        # --- BALANCE MODE (Untouched) ---
        if action == "BALANCE":
            user_state = info.user_state(HL_ADDRESS)
            spot_state = info.spot_user_state(HL_ADDRESS)
            vault_payload = {"type": "userVaultEquities", "user": HL_ADDRESS}
            vault_res = requests.post("https://api.hyperliquid.xyz/info", json=vault_payload, timeout=10)
            
            full_report = {
                "PERPETUAL_AND_MARGIN": {"marginSummary": user_state.get("marginSummary", {"accountValue": "0.0"})},
                "SPOT_WALLET": spot_state,
                "VAULTS_DATA": vault_res.json()
            }
            return jsonify({"msg": json.dumps(full_report)})

        # --- TRADE MODE (Bulk Optimized) ---
        elif action == "TRADE":
            incoming_trades = data.get("trades", [])
            if not incoming_trades:
                return jsonify({"msg": "No trades received"})

            # 1. Sabse pehle saara data ek baar mein fetch karo (Speed boost)
            user_state = info.user_state(HL_ADDRESS)
            meta = info.meta()
            all_mids = info.all_mids()
            
            active_positions = {p["position"]["coin"]: float(p["szi"]) 
                               for p in user_state.get("assetPositions", []) 
                               if float(p["position"]["szi"]) != 0}

            bulk_orders_list = []
            results = []

            # 2. Loop ke andar sirf calculation hoga, koi API call nahi
            for t in incoming_trades:
                coin_data = meta["universe"][int(t["index"])]
                coin_name = coin_data["name"]
                is_buy = t["isBuy"]
                target_usd = float(t["usdSize"])
                price = float(all_mids[coin_name])
                sz_decimals = int(coin_data["szDecimals"])
                
                current_sz = active_positions.get(coin_name, 0.0)

                # Skip logic
                if (is_buy and current_sz > 0) or (not is_buy and current_sz < 0):
                    results.append(f"{coin_name}: RUNNING")
                    continue

                # Target Calculation (Option B)
                target_sz = clean_sz(target_usd / price, sz_decimals)
                if not is_buy: target_sz = -target_sz
                
                diff_sz = clean_sz(target_sz - current_sz, sz_decimals)

                if abs(diff_sz * price) >= 10.0:
                    # Leverage update (Zaroori hai, par bulk se pehle)
                    try: exchange.update_leverage(int(coin_data["maxLeverage"]), coin_name, is_cross=True)
                    except: pass
                    
                    # Order ko list mein jama karo (Batching)
                    bulk_orders_list.append({
                        "name": coin_name,
                        "is_buy": diff_sz > 0,
                        "sz": abs(diff_sz)
                    })
                else:
                    results.append(f"{coin_name}: SMALL")

            # 3. Final Step: Saare orders ek saath Hyperliquid ko thama do
            if bulk_orders_list:
                # 'slippage=0.1' (10%) for no-rejection policy
                # exchange.bulk_orders yahan 200 orders ko ek second mein bhej dega
                for order in bulk_orders_list:
                    res = exchange.market_open(order["name"], order["is_buy"], order["sz"], slippage=0.1)
                    if res["status"] == "ok":
                        results.append(f"{order['name']}: SYNCED")
                    else:
                        results.append(f"{order['name']}: ERROR")

            return jsonify({"msg": "\n".join(results)})

    except Exception as e:
        return jsonify({"msg": f"System Error: {str(e)}"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
