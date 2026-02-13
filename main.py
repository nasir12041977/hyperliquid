from flask import Flask, jsonify
from hyperliquid.info import Info
from hyperliquid.utils import constants
import os

app = Flask(__name__)
address = os.getenv("HL_ADDRESS")

@app.route('/balance')
def get_balance():
    try:
        info = Info(constants.MAINNET_API_URL)
        state = info.spot_user_state(address)
        return jsonify(state)
    except Exception as e:
        return jsonify({"error": str(e)})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
