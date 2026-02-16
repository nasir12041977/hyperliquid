# ==========================================
# EDIT NUMBER: 12
# [OK] BALANCE MODE: Fixed & Stable.
# [FIXED] ERROR 192: Proper szDecimals handling and strict rounding.
# [UNDER PROGRESS] TRADE MODE: Side-based Logic.
# ------------------------------------------
# COMPULSORY: Cross Margin & Max Leverage (Always Applied for every trade).
# LOGIC STEPS:
# 1. Side Match = Skip (सिर्फ साइड देखो, क्वांटिटी नहीं).
# 2. Side Opposite = Reverse (पुरानी काटो, नई शुरू करो).
# 3. Zero Position = Fresh Entry (सीधा नया ट्रेड).
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

# --- FIXED SETTINGS ---
HL_SECRET_KEY = os.getenv("HL_SECRET_KEY")
HL_ADDRESS = os.getenv("HL_ADDRESS")

account = Account.from_key(HL_SECRET_KEY)
info = Info(constants.MAINNET_API_URL)
exchange = Exchange(account, constants.MAINNET_API_URL)

# Precision Fix: डेसीमल की गड़बड़ दूर करने के लिए
def clean_sz(sz, decimals):
    factor = 10 ** decimals
    return math.floor(sz * factor) / factor if sz > 0 else math.ceil(sz * factor) / factor

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
            return jsonify({"msg": json.dumps(margin_data)})

        # ---------------------------------------------------------
        # [UNDER PROGRESS] SECTION: TRADE MODE
        # ---------------------------------------------------------
        elif action == "TRADE":
            incoming_trades = data.get("trades", [])
            results = []
            
            user_state = info.user_state(HL_ADDRESS)
            meta = info.meta_and_asset_ctxs()
            all_mids = info.all_mids()
            
            # मौजूदा पोजीशन्स का मैप
            active_positions = {}
            for pos in user_state.get("assetPositions", []):
                p = pos["position"]
                active_positions[p["coin"]] = float(p["szi"])

            for t in incoming_trades:
                idx = int(t["index"])
                coin_data = meta[0]["universe"][idx]
                coin_name = coin_data["name"]
                
                is_buy_signal = t["isBuy"]
                target_usd = float(t["usdSize"])
                price = float(all_mids[coin_name])
                sz_decimals = coin_data["szDecimals"]
                
                current_sz = active_positions.get(coin_name, 0.0)

                # --- STEP 1: Side Match (Skip) ---
                # अगर साइड एक ही है, तो छोड़ दो।
                if (is_buy_signal and current_sz > 0) or (not is_buy_signal and current_sz < 0):
                    results.append(f"{coin_name}: Skip (Side Match)")
                    continue

                # --- COMPULSORY SETTINGS ---
                # Max Leverage & Cross Margin हमेशा लागू होंगे।
                max_lev = coin_data["maxLeverage"]
                exchange.update_leverage(max_lev, idx, is_cross=True)

                # --- STEP 2: Side Opposite (Reverse) & STEP 3: Zero Entry ---
                # अगर साइड अलग है तो पलटो, अगर खाली है तो नया ट्रेड लो।
                
                # नई क्वांटिटी का हिसाब (Target Quantity)
                target_sz = clean_sz(target_usd / price, sz_decimals)
                if not is_buy_signal: target_sz = -target_sz

                # फाइनल अंतर (जितने का ऑर्डर मारना है)
                diff_sz = clean_sz(target_sz - current_sz, sz_decimals)

                if diff_sz != 0:
                    order_side = diff_sz > 0
                    res = exchange.order(idx, order_side, abs(diff_sz), price, {"limitFee": 0.04})
                    results.append(f"{coin_name}: {res['status']}")

            return jsonify({"msg": "\n".join(results) if results else "No Action"})

    except Exception as e:
        return jsonify({"msg": f"System Error: {str(e)}"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
