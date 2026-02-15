import os
import json
from flask import Flask, request, jsonify
from eth_account import Account
from hyperliquid.utils import constants
from hyperliquid.exchange import Exchange
from hyperliquid.info import Info

app = Flask(__name__)

# एनवायरनमेंट वेरिएबल्स
SECRET_KEY = os.getenv("HL_PRIVATE_KEY")
ACCOUNT_ADDRESS = os.getenv("HL_WALLET_ADDRESS")

# Hyperliquid सेटअप
info = Info(constants.MAINNET_API_URL)
exchange = Exchange(Account.from_key(SECRET_KEY), constants.MAINNET_API_URL)

@app.route('/trade', methods=['POST'])
def handle_request():
    try:
        data = request.json
        action = data.get("action")

        # --- बैलेंस का हिस्सा (जैसा है वैसा ही भेज रहा है) ---
        if action == "BALANCE":
            user_state = info.user_state(ACCOUNT_ADDRESS)
            return jsonify({"msg": json.dumps(user_state)})

        # --- ट्रेड का हिस्सा (आपके नए डेटा फॉर्मेट के हिसाब से) ---
        elif action == "TRADE":
            trades = data.get("trades", [])
            if not trades:
                return jsonify({"msg": "No trade data found"})

            meta = info.meta()
            # सभी सिक्कों की लिस्ट इंडेक्स के हिसाब से
            universe_list = meta["universe"]
            
            output_logs = []
            for trade in trades:
                # आपके द्वारा भेजे गए Keys: index, isBuy, usdSize
                idx = int(trade.get("index"))
                is_buy = trade.get("isBuy")
                usd_size = float(trade.get("usdSize"))

                # इंडेक्स से सिक्के का नाम और डेसीमल निकालना
                coin_meta = universe_list[idx]
                coin = coin_meta["name"]
                sz_decimals = coin_meta["szDecimals"]

                # यहाँ मार्केट प्राइस लेकर USD को Coin Size में बदलना होगा (Market Open के लिए)
                # अभी के लिए यह आपके द्वारा भेजे गए साइज को राउंड करके ट्रेड करेगा
                final_sz = abs(round(usd_size, sz_decimals))

                # ट्रेड एग्जीक्यूट करना
                order_result = exchange.market_open(coin, is_buy, final_sz)
                output_logs.append(f"{coin}: {json.dumps(order_result)}")

            return jsonify({"msg": "\n".join(output_logs)})

        return jsonify({"msg": "Invalid Action"})

    except Exception as e:
        return jsonify({"msg": f"System Error: {str(e)}"})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
