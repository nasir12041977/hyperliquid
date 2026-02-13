import os
from flask import Flask, request, jsonify
from hyperliquid.exchange import Exchange
from hyperliquid.info import Info
from hyperliquid.utils import constants
import eth_account

app = Flask(__name__)

# Render की सेटिंग्स से हम ये चाबियाँ उठाएंगे
ADDRESS = os.getenv("HL_ADDRESS")
SECRET_KEY = os.getenv("HL_SECRET_KEY")

@app.route('/')
def home():
    return "<h1>Systumm Set Hai!</h1><p>Render engine is running.</p>"

@app.route('/balance', methods=['GET'])
def get_balance():
    try:
        info = Info(constants.MAINNET_API_URL, skip_ws=True)
        user_state = info.spot_user_state(ADDRESS)
        return jsonify(user_state)
    except Exception as e:
        return jsonify({"error": str(e)})

if __name__ == "__main__":
    # Render के लिए पोर्ट 10000 ज़रूरी है
    app.run(host='0.0.0.0', port=10000)
