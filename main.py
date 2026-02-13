from flask import Flask, render_template_string
from hyperliquid.info import Info
from hyperliquid.utils import constants
import os

app = Flask(__name__)
address = "0x3C00ECF3EaAecBC7F1D1C026DCb925Ac5D2a38C5"

# HTML Template (Screenshot 177 वाला डिज़ाइन)
DASHBOARD_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AQDAS SECURE TERMINAL</title>
    <style>
        body { background-color: #0d1117; color: white; font-family: sans-serif; text-align: center; margin: 0; padding: 20px; }
        .header { color: #ff00ff; font-size: 24px; font-weight: bold; font-style: italic; margin-bottom: 5px; }
        .sub-header { color: #ff00ff; font-size: 12px; margin-bottom: 20px; }
        .user-btn { background-color: #064e3b; color: #10b981; border: 1px solid #10b981; padding: 10px 30px; border-radius: 20px; font-weight: bold; margin-bottom: 30px; display: inline-block; }
        .stats-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 15px; max-width: 500px; margin: 0 auto 30px; }
        .stat-box { background: #161b22; padding: 20px; border-radius: 15px; border: 1px solid #30363d; }
        .stat-label { color: #8b949e; font-size: 10px; text-transform: uppercase; margin-bottom: 10px; }
        .stat-value { font-size: 20px; font-weight: bold; color: #58a6ff; }
        .pnl-red { color: #f85149; }
        table { width: 100%; max-width: 500px; margin: 0 auto; border-collapse: collapse; background: #161b22; border-radius: 15px; overflow: hidden; }
        th { color: #8b949e; font-size: 10px; padding: 15px; text-align: left; border-bottom: 1px solid #30363d; }
        td { padding: 15px; text-align: left; font-size: 14px; border-bottom: 1px solid #30363d; }
        .footer { color: #30363d; font-size: 10px; margin-top: 30px; letter-spacing: 2px; }
    </style>
</head>
<body>
    <div class="header">Presenting By Sir Nasir</div>
    <div class="sub-header">TRADING SOFTWARE = AQDAS<br>(ADAL+QADR+DASTAK+AMAL+SAFEER)</div>
    
    <div class="user-btn">SIR NASIR</div>

    <div class="stats-grid">
        <div class="stat-box">
            <div class="stat-label">Total Equity</div>
            <div class="stat-value">${{ "%.2f"|format(total_equity) }}</div>
        </div>
        <div class="stat-box">
            <div class="stat-label">Vault Equity</div>
            <div class="stat-value">$0.00</div>
        </div>
        <div class="stat-box">
            <div class="stat-label">Live PNL</div>
            <div class="stat-value pnl-red">${{ "%.4f"|format(total_pnl) }}</div>
        </div>
        <div class="stat-box">
            <div class="stat-label">Open Trades</div>
            <div class="stat-value">{{ positions|length }}</div>
        </div>
    </div>

    <table>
        <thead>
            <tr>
                <th>COIN</th>
                <th>SIZE</th>
                <th>ENTRY</th>
                <th>PNL</th>
            </tr>
        </thead>
        <tbody>
            {% for pos in positions %}
            <tr>
                <td><strong>{{ pos.coin }}</strong></td>
                <td>{{ pos.szi }}</td>
                <td>${{ pos.entryPx }}</td>
                <td class="pnl-red">{{ "%.4f"|format(pos.unrealizedPnl|float) }}</td>
            </tr>
            {% endfor %}
        </tbody>
    </table>

    <div class="footer">AQDAS SECURE TERMINAL</div>
</body>
</html>
"""

@app.route('/balance')
def dashboard():
    try:
        info = Info(constants.MAINNET_API_URL)
        # डेटा प्राप्त करना
        spot = info.spot_user_state(address)
        trades = info.user_state(address)
        
        # कैलकुलेशन
        total_equity = 0
        for b in spot.get('balances', []):
            if b['coin'] == 'USDC':
                total_equity = float(b['total'])
        
        positions = []
        total_pnl = 0
        for pos_wrapper in trades.get('assetPositions', []):
            p = pos_wrapper['position']
            positions.append({
                'coin': p['coin'],
                'szi': p['szi'],
                'entryPx': p['entryPx'],
                'unrealizedPnl': p['unrealizedPnl']
            })
            total_pnl += float(p['unrealizedPnl'])

        return render_template_string(DASHBOARD_HTML, 
                                    total_equity=total_equity, 
                                    total_pnl=total_pnl, 
                                    positions=positions)
    except Exception as e:
        return f"Error: {str(e)}"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
