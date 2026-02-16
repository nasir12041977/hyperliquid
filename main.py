# edit number 18
# [OK] BALANCE MODE: worck sucsessful.
# [under progress] TRADE MODE: Side-based Logic (3 Steps).
# ------------------------------------------
# COMPULSORY: Cross Margin & Max Leverage (Always Applied).
# LOGIC STEPS: 1. Side Match = Skip | 2. Side Opposite = Reverse | 3. Zero = Entry.
# ==========================================

import os
import json
import math
from flask import Flask, request, jsonify
from eth_account import Account
from hyperliquid.utils import constants
from hyperliquid.exchange import Exchange
from hyperliquid.info import Info

app = Flask(__name__)

# --- अनिवार्य सेटिंग्स (Fixed Settings) ---
HL_SECRET_KEY = os.getenv("HL_SECRET_KEY")
HL_ADDRESS = os.getenv("HL_ADDRESS")

account = Account.from_key(HL_SECRET_KEY)
info = Info(constants.MAINNET_API_URL)
exchange = Exchange(account, constants.MAINNET_API_URL)

# Precision Fix: डेसीमल की सटीकता के लिए
def clean_sz(sz, decimals):
    factor = 10 ** decimals
    return math.floor(sz * factor) / factor if sz > 0 else math.ceil(sz * factor) / factor

@app.route("/trade", methods=["POST"])
def handle_request():
    try:
        data = request.json
        action = data.get("action")

        # ---------------------------------------------------------
        # [OK] SECTION: BALANCE MODE (Edit 08 Stable Version - Fixed Format)
        # ---------------------------------------------------------
        if action == "BALANCE":
            margin_data = info.user_state(HL_ADDRESS)
            # यहाँ json.dumps हटाकर सीधा डेटा भेज रहे हैं ताकि 'marginSummary' वाला एरर न आए
            return jsonify(margin_data)

        # ---------------------------------------------------------
        # [UNDER PROGRESS] SECTION: TRADE MODE (New 3-Step Logic)
        # ---------------------------------------------------------
        elif action == "TRADE":
            incoming_trades = data.get("trades", [])
            results = []
            
            user_state = info.user_state(HL_ADDRESS)
            meta = info.meta_and_asset_ctxs()
            all_mids = info.all_mids()
            
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

                # --- चरण 1: साइड मैच (Skip Logic) ---
                if (is_buy_signal and current_sz > 0) or (not is_buy_signal and current_sz < 0):
                    results.append(f"{coin_name}: Skip (Side Match)")
                    continue

                # --- अनिवार्य सेटिंग (Compulsory) ---
                max_lev = coin_data["maxLeverage"]
                exchange.update_leverage(max_lev, idx, is_cross=True)

                # --- चरण 2: साइड अपोजिट (Reverse) & चरण 3: फ्रेश एंट्री ---
                target_sz = clean_sz(target_usd / price, sz_decimals)
                if not is_buy_signal: target_sz = -target_sz
                
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
