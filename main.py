import os
import json
from flask import Flask, request, jsonify
from hyperliquid.utils import constants
from hyperliquid.info import Info

app = Flask(__name__)

ACCOUNT_ADDRESS = os.getenv("HL_WALLET_ADDRESS")
info = Info(constants.MAINNET_API_URL)

@app.route('/trade', methods=['POST'])
def handle_request():
    try:
        data = request.json
        action = data.get("action")
        
        if action == "BALANCE":
            # 1. ट्रेडिंग और मार्जिन अकाउंट का पूरा डेटा
            user_state = info.user_state(ACCOUNT_ADDRESS)
            # 2. स्पॉट वॉलेट (सिक्कों) का पूरा डेटा
            spot_state = info.spot_user_state(ACCOUNT_ADDRESS)
            
            # दोनों को एक साथ जोड़कर जैसा है वैसा ही भेज रहा हूँ
            combined_report = {
                "margin_and_trading": user_state,
                "spot_wallet": spot_state
            }
            
            return jsonify({"msg": json.dumps(combined_report)})
            
        return jsonify({"msg": "Invalid Action"})
    except Exception as e:
        return jsonify({"msg": f"System Error: {str(e)}"})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
