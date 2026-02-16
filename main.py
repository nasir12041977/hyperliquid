# ==========================================
# edit number 32
# [OK] BALANCE MODE: Stable (Dashboard confirmed).
# [under progress] TRADE MODE: Option B (Reversal) ONLY. No Cleanup.
# ------------------------------------------
# COMPULSORY: Cross Margin & Max Leverage (Always Applied).
# LOGIC STEPS: 1. Target Size Calculation | 2. Side Match = Skip | 3. Diff-based Reversal.
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
        # [OK] SECTION: BALANCE MODE
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
        # [UNDER PROGRESS] SECTION: TRADE MODE (Option B - Targeted Only)
        # ---------------------------------------------------------
        elif action == "TRADE":
            incoming_trades = data.get("trades", [])
            results = []
            
            user_state = info.user_state(HL_ADDRESS)
            meta = info.meta()
            all_mids = info.all_mids()
            
            # Maujuda positions ka map (Sirf data fetch karne ke liye)
            active_positions = {p["position"]["coin"]: float(p["szi"]) 
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

                # --- STEP 1: Side Match (Skip) ---
                if (is_buy and current_sz > 0) or (not is_buy and current_sz < 0):
                    results.append(f"{coin_name}: RUNNING")
                    continue

                # --- STEP 2: Leverage & Margin ---
                try:
                    exchange.update_leverage(int(coin_data["maxLeverage"]), coin_name, is_cross=True)
                except:
                    pass

                # --- STEP 3: OPTION B (Diff-based Reversal) ---
                target_sz = clean_sz(target_usd / price, sz_decimals)
                if not is_buy: target_sz = -target_sz
                
                # Formula: Diff = Target - Current
                # Agar -11 short hai aur +17 long chahiye, toh diff +28 banega.
                diff_sz = clean_sz(target_sz - current_sz, sz_decimals)

                if abs(diff_sz * price) >= 10.0:
                    order_side = diff_sz > 0
                    res = exchange.market_open(coin_name, order_side, abs(diff_sz), slippage=0.05)
                    
                    if res["status"] == "ok":
                        results.append(f"{coin_name}: SYNCED")
                    else:
                        results.append(f"{coin_name}: ERROR")
                else:
                    results.append(f"{coin_name}: SIZE_TOO_SMALL")

            # YAHAN SE CLEANUP WALA CHUTIYAPA HATA DIYA HAI.
            # Sirf upar waale loop ke coins hi touch honge.

            return jsonify({"msg": "\n".join(results) if results else "No Action"})

    except Exception as e:
        return jsonify({"msg": f"System Error: {str(e)}"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
