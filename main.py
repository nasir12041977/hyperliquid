# ==========================================
# EDIT NUMBER: 04
# [PASS] BALANCE MODE: Stable and Working.
# [PASS] SYNC & CLEANUP: Reversal logic implemented.
# [LIVE] MARGIN & LEVERAGE: Cross Mode + Max Leverage logic added.
# ==========================================

import json
from flask import Flask, request, jsonify
import eth_account
from hyperliquid.exchange import Exchange
from hyperliquid.info import Info
from hyperliquid.utils import constants

app = Flask(__name__)

# SETTINGS
SECRET_KEY = "YOUR_PRIVATE_KEY"
ACCOUNT_ADDRESS = "YOUR_WALLET_ADDRESS"
ACCOUNT = eth_account.account.from_key(SECRET_KEY)
INFO = Info(constants.MAINNET_API_URL, skip_ws=True)
EXCHANGE = Exchange(ACCOUNT, constants.MAINNET_API_URL)

@app.route('/trade', methods=['POST'])
def trade():
    try:
        data = request.get_json()
        action = data.get("action")

        # ------------------------------------------
        # STEP: BALANCE MODE (Jagaye rakhne ke liye)
        # ------------------------------------------
        if action == "BALANCE":
            user_state = INFO.user_state(ACCOUNT_ADDRESS)
            spot_state = INFO.spot_user_state(ACCOUNT_ADDRESS)
            vaults = INFO.user_vault_equities(ACCOUNT_ADDRESS)
            return jsonify({"msg": json.dumps({"PERPETUAL_AND_MARGIN": user_state, "SPOT_WALLET": spot_state, "VAULTS_DATA": vaults})})

        # ------------------------------------------
        # STEP: TRADE MODE (With Max Leverage & Cross Margin)
        # ------------------------------------------
        elif action == "TRADE":
            incoming_trades = data.get("trades", [])
            results = []
            
            user_state = INFO.user_state(ACCOUNT_ADDRESS)
            meta = INFO.meta_and_asset_ctxs()
            all_mids = INFO.all_mids()
            
            active_positions = {}
            for pos in user_state.get("assetPositions", []):
                p = pos["position"]
                active_positions[p["coin"]] = float(p["szi"])

            sheet_coins = []
            for t in incoming_trades:
                idx = int(t["index"])
                coin_data = meta[0]["universe"][idx]
                coin_name = coin_data["name"]
                sheet_coins.append(coin_name)
                
                # 1. MARGIN & LEVERAGE SETTING
                # Meta data se Max Leverage nikalna
                max_leverage = coin_data["maxLeverage"]
                # Cross Margin (is_leverage=True means Cross in SDK) and Max Leverage set karna
                EXCHANGE.update_leverage(max_leverage, idx, is_cross=True)
                
                # 2. QUANTITY CALCULATION
                is_buy = t["isBuy"]
                target_usd = float(t["usdSize"])
                price = float(all_mids[coin_name])
                sz_decimals = coin_data["szDecimals"]
                
                target_sz = round(target_usd / price, sz_decimals)
                if not is_buy: target_sz = -target_sz

                # 3. POSITION SYNC (Target - Current)
                current_sz = active_positions.get(coin_name, 0.0)
                diff_sz = round(target_sz - current_sz, sz_decimals)

                if diff_sz != 0:
                    order_side = diff_sz > 0
                    res = EXCHANGE.order(idx, order_side, abs(diff_sz), price, {"limitFee": 0.04})
                    results.append(f"{coin_name}: {res['status']} (at {max_leverage}x Cross)")
                else:
                    results.append(f"{coin_name}: Already Synced")

            # 4. CLEANUP (Jo list mein nahi hain unhe close karo)
            for coin_on_exchange, sz_on_exchange in active_positions.items():
                if coin_on_exchange not in sheet_coins and sz_on_exchange != 0:
                    for i, m in enumerate(meta[0]["universe"]):
                        if m["name"] == coin_on_exchange:
                            close_side = sz_on_exchange < 0
                            EXCHANGE.order(i, close_side, abs(sz_on_exchange), float(all_mids[coin_on_exchange]), {"limitFee": 0.04})
                            results.append(f"CLEANED: {coin_on_exchange}")

            return jsonify({"msg": "\n".join(results)})

    except Exception as e:
        return jsonify({"msg": f"ERROR: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
