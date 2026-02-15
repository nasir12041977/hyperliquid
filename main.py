import os
import json
from flask import Flask, request, jsonify
from eth_account import Account
from hyperliquid.utils import constants
from hyperliquid.exchange import Exchange
from hyperliquid.info import Info

app = Flask(__name__)

HL_SECRET_KEY = os.getenv("HL_SECRET_KEY")
HL_ADDRESS = os.getenv("HL_ADDRESS")

@app.route("/trade", methods=["POST"])
def handle_request():
    try:
        data = request.json or {}
        action = data.get("action")

        info = Info(constants.MAINNET_API_URL)

        if action == "BALANCE":
            user_state = info.user_state(HL_ADDRESS)

            # पूरा JSON return करेंगे
            return jsonify({
                "raw_user_state": user_state
            })

        return jsonify({"msg": "Send action = BALANCE only for debug"})

    except Exception as e:
        return jsonify({"msg": f"System Error: {str(e)}"})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
