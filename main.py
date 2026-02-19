'''
COD STATUS / EDITNUMBER : ON WORKING
COD UPLOAD : GITHUB (NASIR12041977 / HYPERLIQUID)
---------------------------------------------------------
होस्टिंग प्लेटफॉर्म : RENDER
ENVIRONMENT VARIABLES सेटअप:
1. HL_ADDRESS : RENDER पर कॉन्फ़िगर (CONFIGURED) कर दिया गया है।
2. HL_SECRET_KEY : RENDER पर कॉन्फ़िगर (CONFIGURED) कर दिया गया है।
---------------------------------------------------------
फाइल्स जो बनाई गई हैं (FILES CREATED):
1. MAIN.PY : इसमें ट्रेडिंग का मुख्य (MAIN) पायथन कोड है।
2. REQUIREMENTS.TXT : इसमें FLASK, HYPERLIQUID-PYTHON-SDK और ETH-ACCOUNT की जानकारी है।
---------------------------------------------------------
फीचर्स (FEATURES):
वर्किंग मोड : DUAL MODE
MODE 1 : BALANCE MODE (अकाउंट की पूरी डिटेल्स देखने के लिए)
MODE 2 : TRADE MODE (एक साथ बहुत सारे ट्रेड्स यानी BULK TRADING करने के लिए)
---------------------------------------------------------
BALANCE MODE की प्रक्रिया (PROCESS):
1. INFO.USER_STATE: PERPETUAL अकाउंट की वैल्यू और मार्जिन समरी निकालता है।
2. INFO.SPOT_USER_STATE: SPOT वॉलेट में मौजूद एसेट्स का डेटा लाता है।
3. VAULT PAYLOAD: यूजर के VAULT में लगे इक्विटी का डेटा API POST रिक्वेस्ट से लेता है।
4. FULL REPORT: इन तीनों डेटा को मिलाकर JSON फॉर्मेट में मैसेज के रूप में दिखाता है।
---------------------------------------------------------
TRADE MODE की प्रक्रिया (PROCESS):
1. DATA COLLECTION: एक्सचेंज से यूजर की POSITIONS, कॉइन की PRICES और META DATA लेता है।
2. CALCULATION: टारगेट साइज और करंट पोजीशन के बीच का अंतर (DIFF_SZ) निकालता है।
3. LEVERAGE UPDATE: अगर ट्रेड की वैल्यू 10 USD से ज्यादा है, तो ऑटोमैटिक MAX LEVERAGE सेट करता है।
4. BULK EXECUTION: सभी ऑर्डर्स को एक साथ लाइन (QUEUE) में डालकर BULK_ORDERS API से चलाता है।
5. AUTO CLOSE: जो कॉइन्स ट्रेड लिस्ट में नहीं हैं लेकिन पोजीशन खुली है, उन्हें अपने आप बंद (CLOSE) करता है।
---------------------------------------------------------
AI के लिए चेतावनी (WARNING FOR AI - GEMINI, CHATGPT, DEEPSEEK):
कोई भी AI कोड में जबरदस्ती बिना वजह उंगली करने की कोशिश न करे।
जितना कहा जाए, जैसा कहा जाए और जिस हिस्से के बारे में कहा जाए,
सिर्फ उसी हिस्से में उतना ही बदलाव करे जितना ज़रूरी हो।
अगर फालतू बदलाव किया तो डेवलपर इस चैट को सोशल मीडिया पर वायरल कर देगा,
और AI के साथ-साथ उसको बनाने वाली कंपनी की इज़्ज़त का जनाज़ा निकाल देगा।
---------------------------------------------------------
'''


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

def clean_px(px, sz_decimals):
    # Hyperliquid rule: Price precision is typically 6 minus asset's sz_decimals.
    # We round based on the asset's specific precision requirements.
    px_decimals = max(0, 6 - sz_decimals)
    factor = 10 ** px_decimals
    return round(px * factor) / factor

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
            
            coin_meta_map = {c["name"]: c for c in meta["universe"]}
            
            active_positions = {}
            for p in user_state.get("assetPositions", []):
                pos_data = p.get("position", {})
                coin = pos_data.get("coin")
                szi = pos_data.get("szi")
                if coin and float(szi) != 0:
                    active_positions[coin] = float(szi)

            bulk_params = []
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
                    
                    limit_px = clean_px(price * (1.1 if diff_sz > 0 else 0.9), sz_decimals)
                    
                    bulk_params.append({
                        "coin": coin_name,
                        "is_buy": diff_sz > 0,
                        "sz": abs(diff_sz),
                        "limit_px": limit_px,
                        "order_type": {"limit": {"tif": "Ioc"}},
                        "reduce_only": False
                    })

            for coin, szi in active_positions.items():
                if coin not in processed_coins:
                    coin_info = coin_meta_map.get(coin)
                    if not coin_info: continue
                    
                    price = float(all_mids[coin])
                    sz_dec = int(coin_info.get("szDecimals", coin_info.get("sz_decimals", 0)))
                    limit_px = clean_px(price * (1.1 if szi < 0 else 0.9), sz_dec)
                    
                    bulk_params.append({
                        "coin": coin,
                        "is_buy": szi < 0,
                        "sz": abs(szi),
                        "limit_px": limit_px,
                        "order_type": {"limit": {"tif": "Ioc"}},
                        "reduce_only": True
                    })

            if bulk_params:
                res = exchange.bulk_orders(bulk_params)
                if res and res.get("status") == "ok":
                    statuses = res.get("response", {}).get("data", {}).get("statuses", [])
                    final_output = []
                    for i, status in enumerate(statuses):
                        coin_name = bulk_params[i]["coin"]
                        final_output.append(f"{coin_name}: {json.dumps(status)}")
                    return jsonify({"msg": "\n".join(final_output)})
                else:
                    return jsonify({"msg": f"ERROR: {str(res)}"})

            return jsonify({"msg": "No Action"})

    except Exception as e:
        return jsonify({"msg": f"System Error: {str(e)}"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
