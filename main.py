import os
import json
import requests
from flask import Flask, request, jsonify
from eth_account import Account
from hyperliquid.utils import constants
from hyperliquid.exchange import Exchange
from hyperliquid.info import Info

app = Flask(__name__)

# सीधा आपके रेंडर वेरिएबल्स
HL_SECRET_KEY = os.getenv("HL_SECRET_KEY")
HL_ADDRESS = os.getenv("HL_ADDRESS")

account = Account.from_key(HL_SECRET_KEY)
info = Info(constants.MAINNET_API_URL)
exchange = Exchange(account, constants.MAINNET_API_URL)

HL_INFO_URL = "https://api.hyperliquid.xyz/info"

@app.route("/trade", methods=["POST"])
def handle_request():
    try:
        data = request.json
        action = data.get("action")

        if action == "BALANCE":
            # 1. फ्यूचर और मार्जिन
            margin_data = info.user_state(HL_ADDRESS)
            # 2. स्पॉट वॉलेट
            spot_data = info.spot_user_state(HL_ADDRESS)
            # 3. वॉल्ट्स डेटा
            vault_payload = {"type": "userVaultEquities", "user": HL_ADDRESS}
            vault_res = requests.post(HL_INFO_URL, json=vault_payload, timeout=10)
            vault_data = vault_res.json()

            full_report = {
                "PERPETUAL_AND_MARGIN": margin_data,
                "SPOT_WALLET": spot_data,
                "VAULTS_DATA": vault_data
            }
            return jsonify({"msg": json.dumps(full_report)})

        return jsonify({"msg": "Invalid Action"})

    except Exception as e:
        return jsonify({"msg": f"System Error: {str(e)}"})

if __name__ == "__main__":
    # अब कोई पोर्ट की जबरदस्ती नहीं, रेंडर इसे खुद संभालेगा
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
