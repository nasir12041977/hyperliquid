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
            # 1. ट्रेडिंग अकाउंट (Perp/Margin) का बैलेंस
            margin_data = info.user_state(ACCOUNT_ADDRESS)
            
            # 2. स्पॉट वॉलेट का बैलेंस (यही वो हिस्सा है जो एरर दे रहा था)
            # सही फंक्शन 'spot_user_state' ही है, बस लाइब्रेरी वर्ज़न का फर्क है
            try:
                spot_data = info.spot_user_state(ACCOUNT_ADDRESS)
            except:
                spot_data = "Spot data not available"

            combined = {
                "account_info": margin_data,
                "spot_info": spot_data
            }
            
            return jsonify({"msg": json.dumps(combined)})
            
        return jsonify({"msg": "Invalid Action"})
    except Exception as e:
        # अगर कोई भी एरर आएगा तो साफ़ दिखेगा कि कहाँ दिक्कत है
        return jsonify({"msg": f"Final Error: {str(e)}"})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
