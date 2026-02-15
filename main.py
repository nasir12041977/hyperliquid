import os
import json
from flask import Flask, request, jsonify
from eth_account import Account
from hyperliquid.utils import constants
from hyperliquid.exchange import Exchange
from hyperliquid.info import Info

app = Flask(__name__)

# एनवायरनमेंट वेरिएबल्स (ये Render से अपने आप जुड़ जाएंगे)
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

        # 1. बैलेंस का हिस्सा: जैसा एक्सचेंज से आएगा, वैसा ही भेज देगा
        if action == "BALANCE":
            user_state = info.user_state(ACCOUNT_ADDRESS)
            return jsonify({"msg": json.dumps(user_state)})

        # 2. ट्रेड का हिस्सा: आपके 0, TRUE, 11 वाले फॉर्मेट के लिए
        elif action == "TRADE":
            trades = data.get("trades", [])
            if not trades:
                return jsonify({"msg": "No trade data found"})

            meta = info.meta()
            universe_list = meta["universe"]
            
            output_logs = []
            for trade in trades:
                # आपके Google Sheet से आने वाला डेटा
                idx = int(trade.get("index"))
                is_buy = trade.get("isBuy")
                usd_size = float(trade.get("usdSize"))

                # इंडेक्स के जरिए सही कॉइन का नाम और डेसीमल ढूंढना
                coin_meta = universe_list[idx]
                coin = coin_meta["name"]
                sz_decimals = coin_meta["szDecimals"]

                # साइज को राउंड करना
                final_sz = abs(round(usd_size, sz_decimals))

                # ट्रेड मारना
                order_result = exchange.market_open(coin, is_buy, final_sz)
                output_logs.append(f"{coin}: {json.dumps(order_result)}")

            return jsonify({"msg": "\n".join(output_logs)})

        return jsonify({"msg": "Invalid Action"})

    except Exception as e:
        return jsonify({"msg": f"System Error: {str(e)}"})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
