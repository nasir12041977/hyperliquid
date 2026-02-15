# ==========================================
# EDIT NUMBER: 08
# [OK] BALANCE MODE: Fixed & Stable.
# [UNDER PROGRESS] TRADE MODE: Syncing based on 4-Point Logic.
# ROADMAP:
# Step 1: Extra coins cleanup (जो लिस्ट में नहीं हैं उन्हें बंद करना).
# Step 2: Same Side check (अगर सब सही है तो स्किप करना).
# Step 3: Direction/Quantity Correction (Target - Current Logic).
# Step 4: Max Leverage & Cross Margin execution.
# ==========================================

import os
import json
import requests
from flask import Flask, request, jsonify
from eth_account import Account
from hyperliquid.utils import constants
from hyperliquid.exchange import Exchange
from hyperliquid.info import Info

app = Flask(__name__)

# --- FIXED SECTION: SETTINGS ---
HL_SECRET_KEY = os.getenv("HL_SECRET_KEY")
HL_ADDRESS = os.getenv("HL_ADDRESS")

account = Account.from_key(HL_SECRET_KEY)
info = Info(constants.MAINNET_API_URL)
exchange = Exchange(account, constants.MAINNET_API_URL)

HL_INFO_URL = "https://api.hyperliquid.xyz/info"

@app.route("/trade", methods=["POST"])
def handle_request():
    try:
        data = request.json
        action = data.get("action")

        # ---------------------------------------------------------
        # [FIXED] SECTION: BALANCE MODE
        # ---------------------------------------------------------
        if action == "BALANCE":
            margin_data = info.user_state(HL_ADDRESS)
            spot_data = info.spot_user_state(HL_ADDRESS)
            vault_payload = {"type": "userVaultEquities", "user": HL_ADDRESS}
            vault_res = requests.post(HL_INFO_URL, json=vault_payload, timeout=10)
            vault_data = vault_res.json()

            full_report = {
                "PERPETUAL_AND_MARGIN": margin_data,
                "SPOT_WALLET": spot_data,
                "VAULTS_DATA": vault_data
            }
            return jsonify({"msg": json.dumps(full_report)})

        # ---------------------------------------------------------
        # [UNDER PROGRESS] SECTION: TRADE MODE
        # ---------------------------------------------------------
        elif action == "TRADE":
            incoming_trades = data.get("trades", [])
            results = []
            
            # डेटा इकट्ठा करना (Fetch Initial Data)
            user_state = info.user_state(HL_ADDRESS)
            meta = info.meta_and_asset_ctxs()
            all_mids = info.all_mids()
            
            # एक्सचेंज की मौजूदा स्थिति (Active Positions Map)
            active_positions = {}
            for pos in user_state.get("assetPositions", []):
                p = pos["position"]
                active_positions[p["coin"]] = float(p["szi"])

            sheet_coins = []
            
            # --- STEP 1, 2 & 3: SYNC, SKIP & REVERSAL LOGIC ---
            for t in incoming_trades:
                idx = int(t["index"])
                coin_data = meta[0]["universe"][idx]
                coin_name = coin_data["name"]
                sheet_coins.append(coin_name)
                
                # Calculation (Target Quantity from Sheet)
                is_buy = t["isBuy"]
                target_usd = float(t["usdSize"])
                price = float(all_mids[coin_name])
                sz_decimals = coin_data["szDecimals"]
                
                target_sz = round(target_usd / price, sz_decimals)
                if not is_buy: target_sz = -target_sz

                current_sz = active_positions.get(coin_name, 0.0)
                
                # Logic: Check if direction is already correct (Step 2)
                if current_sz == target_sz:
                    results.append(f"{coin_name}: Skip (Already Same)")
                    continue

                # Logic: Position Reversal / Correction (Step 3)
                diff_sz = round(target_sz - current_sz, sz_decimals)

                if diff_sz != 0:
                    # Step 4: Apply Leverage & Margin before order
                    max_lev = coin_data["maxLeverage"]
                    exchange.update_leverage(max_lev, idx, is_cross=True)
                    
                    # Execute Order
                    order_side = diff_sz > 0
                    res = exchange.order(idx, order_side, abs(diff_sz), price, {"limitFee": 0.04})
                    results.append(f"{coin_name}: {res['status']} (Synced)")

            # --- STEP 1: CLEANUP (Ghost Positions Cleanup) ---
            for coin_on_exchange, sz_on_exchange in active_positions.items():
                if coin_on_exchange not in sheet_coins and sz_on_exchange != 0:
                    for i, m in enumerate(meta[0]["universe"]):
                        if m["name"] == coin_on_exchange:
                            close_side = sz_on_exchange < 0
                            exchange.order(i, close_side, abs(sz_on_exchange), float(all_mids[coin_on_exchange]), {"limitFee": 0.04})
                            results.append(f"CLEANED: {coin_on_exchange}")

            return jsonify({"msg": "\n".join(results) if results else "No Action"})

        return jsonify({"msg": "Invalid Action"})

    except Exception as e:
        return jsonify({"msg": f"System Error: {str(e)}"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
