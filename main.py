# ==========================================
# edit number 49
# [OK] BALANCE MODE: Original & Locked (Syntax Fix).
# [under progress] TRADE MODE: Validated Bulk Execution (Raw API Format).
# ------------------------------------------
# LOGIC: Removed accidental text 'Matt' causing SyntaxError. No other changes.
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

def clean_px(px):
    px = float(px)
    if px == 0: return 0
    precision = 5 - int(math.floor(math.log10(abs(px)))) - 1
    rounded_px = round(px, precision)
    return float('{:g}'.format(float('{:.5g}'.format(rounded_px))))

@app.route("/trade", methods=["POST"])
def handle_request():
    try:
        data = request.json
        action = data.get("action")

        # --- 1. BALANCE MODE (Fixed Syntax - Back to Original) ---
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

        # --- 2. TRADE MODE (The Bulk Engine) ---
        elif action == "TRADE":
            incoming_trades = data.get("trades", [])
            user_state = info.user_state(HL_ADDRESS)
            meta = info.meta()
            all_mids = info.all_mids()
            
            active_positions = {}
            for p in user_state.get("assetPositions", []):
                pos_data = p.get("position", {})
                coin = pos_data.get("coin")
                szi = pos_data.get("szi")
                if coin and float(szi) != 0:
                    active_positions[coin] = float(szi)

            bulk_params = []
            results = []
            processed_coins = set()

            for t in incoming_trades:
                idx = int(t["index"])
                coin_data = meta["universe"][idx]
                coin_name = coin_data["name"]
                is_buy = t["isBuy"]
                target_usd = float(t["usdSize"])
                price = float(all_mids[coin_name])
                sz_decimals = int(coin_data.get("szDecimals", coin_data.get("sz_decimals", 0)))
                
                processed_coins.add(coin_name)
                current_sz = active_positions.get(coin_name, 0.0)

                target_sz = clean_sz(target_usd / price, sz_decimals)
                if not is_buy: target_sz = -target_sz
                
                diff_sz = clean_sz(target_sz - current_sz, sz_decimals)

                if abs(diff_sz * price) >= 10.0:
                    try: exchange.update_leverage(int(coin_data["maxLeverage"]), coin_name, is_cross=True)
                    except: pass
                    
                    limit_px = clean_px(price * (1.1 if diff_sz > 0 else 0.9))
                    
                    bulk_params.append({
                        "coin": coin_name,
                        "is_buy": diff_sz > 0,
                        "sz": abs(diff_sz),
                        "limit_px": limit_px,
                        "order_type": {"limit": {"tif": "Ioc"}},
                        "reduce_only": False
                    })
                    results.append(f"{coin_name}: QUEUED")
                else:
                    results.append(f"{coin_name}: RUNNING")

            for coin, szi in active_positions.items():
                if coin not in processed_coins:
                    price = float(all_mids[coin])
                    limit_px = clean_px(price * (1.1 if szi < 0 else 0.9))
                    
                    bulk_params.append({
                        "coin": coin,
                        "is_buy": szi < 0,
                        "sz": abs(szi),
                        "limit_px": limit_px,
                        "order_type": {"limit": {"tif": "Ioc"}},
                        "reduce_only": True
                    })
                    results.append(f"{coin}: CLOSING")

            if bulk_params:
                res = exchange.bulk_orders(bulk_params)
                if res and res.get("status") == "ok":
                    return jsonify({"msg": "BULK_SUCCESS\n" + "\n".join(results)})
                else:
                    return jsonify({"msg": f"BULK_ERROR: {str(res)}"})

            return jsonify({"msg": "\n".join(results) if results else "No Action"})

    except Exception as e:
        return jsonify({"msg": f"System Error: {str(e)}"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
