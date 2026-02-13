from flask import Flask, jsonify
from hyperliquid.info import Info
from hyperliquid.utils import constants
import os

app = Flask(__name__)
address = "0x3C00ECF3EaAecBC7F1D1C026DCb925Ac5D2a38C5"

@app.route('/balance')
def get_all_data():
    try:
        info = Info(constants.MAINNET_API_URL)
        spot = info.spot_user_state(address)
        trades = info.user_state(address)
        return jsonify({"spot_balance": spot, "open_positions": trades})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
