from flask import Flask, render_template_string
from hyperliquid.info import Info
from hyperliquid.utils import constants
import os

app = Flask(__name__)
address = "0x3C00ECF3EaAecBC7F1D1C026DCb925Ac5D2a38C5"

DASHBOARD_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700;800&family=Playfair+Display:ital,wght@0,900;1,900&display=swap');
        body {
            background: #0b0f14; color: #ffffff; font-family: 'Inter', sans-serif; margin: 0; padding: 20px 0;
            display: flex; justify-content: center; min-height: 100vh;
            background-image: radial-gradient(circle at 50% 10%, #1a2333, #0b0f14);
        }
        .container { width: 95%; max-width: 600px; text-align: center; }
        .super-branding {
            font-family: 'Playfair Display', serif;
            font-size: 36px; font-weight: 900; font-style: italic;
            background: linear-gradient(90deg, #ff0000, #ff7300, #fffb00, #48ff00, #00ffd5, #002bff, #7a00ff, #ff00c8, #ff0000);
            background-size: 400%; -webkit-background-clip: text; -webkit-text-fill-color: transparent;
            animation: rainbow 10s linear infinite; margin-bottom: 5px;
        }
        @keyframes rainbow { 0% { background-position: 0%; } 100% { background-position: 400%; } }
        .software-header {
            font-size: 11px; font-weight: bold; margin: 15px 0; letter-spacing: 1px;
            animation: disco-glow 1.5s infinite linear; line-height: 1.6;
        }
        @keyframes disco-glow {
            0% { color: #ff0000; text-shadow: 0 0 5px #ff0000; }
            25% { color: #00ff00; text-shadow: 0 0 5px #00ff00; }
            50% { color: #0000ff; text-shadow: 0 0 5px #0000ff; }
            100% { color: #ff00ff; text-shadow: 0 0 5px #ff00ff; }
        }
        .user-tag {
            background: rgba(0, 255, 163, 0.05); color: #00ffa3; padding: 10px 30px; border-radius: 50px;
            display: inline-block; margin: 10px 0 25px; border: 1px solid rgba(0, 255, 163, 0.2);
            font-weight: bold; text-transform: uppercase;
        }
        .stats-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-bottom: 25px; }
        .card { background: rgba(255, 255, 255, 0.03); border: 1px solid rgba(255, 255, 255, 0.08); padding: 15px 5px; border-radius: 15px; }
        .card h4 { margin: 0; color: #8b949e; font-size: 9px; text-transform: uppercase; letter-spacing: 1px; }
        .card .value { margin-top: 8px; font-size: 18px; font-weight: 700; }
        .full-card { grid-column: span 2; background: rgba(88, 166, 255, 0.05); border: 1px solid #58a6ff44; }
        .pos-table { background: rgba(255, 255, 255, 0.02); border-radius: 20px; border: 1px solid rgba(255, 255, 255, 0.08); overflow: hidden; text-align: left; margin-top: 20px; }
        table { width: 100%; border-collapse: collapse; }
        th { background: rgba(255, 255, 255, 0.05); padding: 12px; font-size: 10px; color: #8b949e; }
        td { padding: 12px; font-size: 13px; border-bottom: 1px solid rgba(255, 255, 255, 0.03); }
        .plus { color: #3fb950; } .minus { color: #f85149; }
        .footer { margin-top: 30px; font-size: 10px; color: #30363d; letter-spacing: 3px; font-weight: bold; }
    </style>
</head>
<body>
<div class="container">
    <div class="super-branding">Presenting By SirNasir</div>
    <div class="software-header">TRADING SOFTWARE = AQDAS<br>(ADAL+QADR+DASTAK+AMAL+SAFEER)</div>
    <div class="user-tag">SIR NASIR</div>

    <div class="stats-grid">
        <div class="card full-card">
            <h4>Combined Total Equity</h4>
            <div class="value" style="color:#58a6ff">${{ "%.2f"|format(total_equity) }}</div>
        </div>
        <div class="card">
            <h4>Spot Balance (USDC)</h4>
            <div class="value">${{ "%.2f"|format(spot_bal) }}</div>
        </div>
        <div class="card">
            <h4>Trading Margin</h4>
            <div class="value">${{ "%.2f"|format(acc_value) }}</div>
        </div>
        <div class="card">
            <h4>Vault Equity</h4>
            <div class="value">$0.00</div>
        </div>
        <div class="card">
            <h4>Live PNL</h4>
            <div class="value {{ 'plus' if total_pnl >= 0 else 'minus' }}">
                {{ '+' if total_pnl >= 0 else '' }}${{ "%.4f"|format(total_pnl) }}
            </div>
        </div>
        <div class="card full-card">
            <h4>Open Trades Count</h4>
            <div class="value">{{ positions|length }}</div>
        </div>
    </div>

    <div class="pos-table">
        <div style="padding: 12px; font-size: 10px; color: #8b949e; font-weight: bold; border-bottom: 1px solid rgba(255, 255, 255, 0.08);">LIVE TRADE STATUS</div>
        <table>
            <thead>
                <tr><th>COIN</th><th>SIZE</th><th>ENTRY</th><th>PNL</th></tr>
            </thead>
            <tbody>
                {% if positions|length == 0 %}
                <tr><td colspan="4" style="text-align:center; padding:30px; color:#484f58;">WAITING FOR SIGNAL...</td></tr>
                {% else %}
                {% for pos in positions %}
                <tr>
                    <td style="font-weight:bold; color:#ffffff;">{{ pos.coin }}</td>
                    <td>{{ pos.szi }}</td>
                    <td>${{ pos.entryPx }}</td>
                    <td class="{{ 'plus' if pos.pnl >= 0 else 'minus' }}" style="font-weight:bold;">
                        {{ '+' if pos.pnl >= 0 else '' }}{{ "%.4f"|format(pos.pnl) }}
                    </td>
                </tr>
                {% endfor %}
                {% endif %}
            </tbody>
        </table>
    </div>
    <div class="footer">AQDAS SECURE TERMINAL</div>
</div>
</body>
</html>
"""

@app.route('/balance')
def dashboard():
    try:
        info = Info(constants.MAINNET_API_URL)
        spot_state = info.spot_user_state(address)
        trading_state = info.user_state(address)
        
        spot_bal = 0
        for b in spot_state.get('balances', []):
            if b['coin'] == 'USDC': spot_bal = float(b['total'])
        
        acc_value = float(trading_state.get('marginSummary', {}).get('accountValue', 0))
        
        positions = []
        total_pnl = 0
        for pos_wrapper in trading_state.get('assetPositions', []):
            p = pos_wrapper['position']
            pnl = float(p.get('unrealizedPnl', 0))
            positions.append({'coin': p['coin'], 'szi': abs(float(p['szi'])), 'entryPx': "{:,.1f}".format(float(p['entryPx'])), 'pnl': pnl})
            total_pnl += pnl
        
        return render_template_string(DASHBOARD_HTML, total_equity=spot_bal + acc_value, spot_bal=spot_bal, acc_value=acc_value, total_pnl=total_pnl, positions=positions)
    except Exception as e:
        return f"SYSTEM OFFLINE: {str(e)}"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
