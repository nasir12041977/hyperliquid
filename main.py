# ==========================================
# EDIT NUMBER: 06
# [PASS] BALANCE MODE: Stable and Working (Spot+Margin+Vaults OK).
# [LIVE] TRADING MODE: Integrated Sync, Cleanup, Reversal, and Max Leverage.
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

# सेटिंग्स (Environment Variables से)
HL_SECRET_KEY = os.getenv("HL_SECRET_KEY")
HL_ADDRESS = os.getenv("HL_ADDRESS")

account = Account.from_key(HL_SECRET_KEY)
info = Info(constants.MAINNET_API_URL, skip_ws=True)
exchange = Exchange(account, constants.MAINNET_API_URL)

HL_INFO_URL = "https://api.hyperliquid.xyz/info"

@app.route("/trade", methods=["POST"])
def handle_request():
    try:
        data = request.json
        action = data.get("action")

        # ------------------------------------------
        # 1. BALANCE MODE (Working OK - No Changes)
        # ------------------------------------------
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

        # ------------------------------------------
        # 2. TRADE MODE (New Logic Added)
        # ------------------------------------------
        elif action == "TRADE":
            incoming_trades = data.get("trades", [])
            results = []
            
            # Speed ke liye ek hi baar data fetch karna
            user_state = info.user_state(HL_ADDRESS)
            meta = info.meta_and_asset_ctxs()
            all_mids = info.all_mids()
            
            # Current Positions ka map banana (Exchange par kya khula hai)
            active_positions = {}
            for pos in user_state.get("assetPositions", []):
                p = pos["position"]
                active_positions[p["coin"]] = float(p["szi"])

            sheet_coins = []
            
            # A. SYNC LOGIC (Sheet ke coins ko set karna)
            for t in incoming_trades:
                idx = int(t["index"])
                coin_data = meta[0]["universe"][idx]
                coin_name = coin_data["name"]
                sheet_coins.append(coin_name)
                
                # Max Leverage aur Cross Margin set karna
                max_lev = coin_data["maxLeverage"]
                exchange.update_leverage(max_lev, idx, is_cross=True)
                
                # Quantity calculation
                is_buy = t["isBuy"]
                target_usd = float(t["usdSize"])
                price = float(all_mids[coin_name])
                sz_decimals = coin_data["szDecimals"]
                
                target_sz = round(target_usd / price, sz_decimals)
                if not is_buy: target_sz = -target_sz

                # MAGIC FORMULA: (Target - Current)
                current_sz = active_positions.get(coin_name, 0.0)
                diff_sz = round(target_sz - current_sz, sz_decimals)

                if diff_sz != 0:
                    order_side = diff_sz > 0
                    res = exchange.order(idx, order_side, abs(diff_sz), price, {"limitFee": 0.04})
                    results.append(f"{coin_name}: {res['status']} ({max_lev}x)")
                else:
                    results.append(f"{coin_name}: Synced")

            # B. CLEANUP LOGIC (Faltu positions band karna)
            for coin_on_exchange, sz_on_exchange in active_positions.items():
                if coin_on_exchange not in sheet_coins and sz_on_exchange != 0:
                    # Meta mein index dhoondhna
                    for i, m in enumerate(meta[0]["universe"]):
                        if m["name"] == coin_on_exchange:
                            close_side = sz_on_exchange < 0
                            exchange.order(i, close_side, abs(sz_on_exchange), float(all_mids[coin_on_exchange]), {"limitFee": 0.04})
                            results.append(f"CLEANED: {coin_on_exchange}")

            return jsonify({"msg": "\n".join(results) if results else "No Action Taken"})

        return jsonify({"msg": "Invalid Action"})

    except Exception as e:
        return jsonify({"msg": f"System Error: {str(e)}"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
