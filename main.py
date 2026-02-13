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
        body { background: #0b0f14; color: #ffffff; font-family: 'Inter', sans-serif; margin: 0; padding: 10px; display: flex; justify-content: center; min-height: 100vh; background-image: radial-gradient(circle at 50% 10%, #1a2333, #0b0f14); }
        .container { width: 100%; max-width: 600px; text-align: center; }
        .super-branding { font-family: 'Playfair Display', serif; font-size: 28px; font-weight: 900; font-style: italic; background: linear-gradient(90deg, #ff0000, #ff7300, #fffb00, #48ff00, #00ffd5, #002bff, #7a00ff, #ff00c8, #ff0000); background-size: 400%; -webkit-background-clip: text; -webkit-text-fill-color: transparent; animation: rainbow 10s linear infinite; margin-bottom: 5px; }
        @keyframes rainbow { 0% { background-position: 0%; } 100% { background-position: 400%; } }
        .software-header { font-size: 10px; font-weight: bold; margin: 10px 0; letter-spacing: 1px; animation: disco-glow 1.5s infinite linear; line-height: 1.4; }
        @keyframes disco-glow { 0% { color: #ff0000; text-shadow: 0 0 5px #ff0000; } 50% { color: #00ff00; text-shadow: 0 0 5px #00ff00; } 100% { color: #ff00ff; text-shadow: 0 0 5px #ff00ff; } }
        .stats-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 8px; margin-bottom: 20px; }
        .card { background: rgba(255, 255, 255, 0.03); border: 1px solid rgba(255, 255, 255, 0.08); padding: 10px; border-radius: 12px; }
        .card h4 { margin: 0; color: #8b949e; font-size: 8px; text-transform: uppercase; letter-spacing: 0.5px; }
        .card .value { margin-top: 5px; font-size: 14px; font-weight: 700; color: #58a6ff; }
        .full-width { grid-column: span 2; background: rgba(0, 255, 163, 0.05); }
        .pos-table { background: rgba(255, 255, 255, 0.02); border-radius: 15px; border: 1px solid rgba(255, 255, 255, 0.08); overflow: hidden; text-align: left; }
        table { width: 100%; border-collapse: collapse; }
        th { background: rgba(255, 255, 255, 0.05); padding: 10px; font-size: 9px; color: #8b949e; text-transform: uppercase; }
        td { padding: 10px; font-size: 11px; border-bottom: 1px solid rgba(255, 255, 255, 0.03); }
        .plus { color: #3fb950; } .minus { color: #f85149; }
        .footer { margin-top: 20px; font-size: 9px; color: #30363d; letter-spacing: 2px; font-weight: bold; }
    </style>
</head>
<body>
<div class="container">
    <div class="super-branding">Presenting By SirNasir</div>
    <div class="software-header">TRADING SOFTWARE = AQDAS<br>(ADAL+QADR+DASTAK+AMAL+SAFEER)</div>
    
    <div class="stats-grid">
        <div class="card full-width">
            <h4>Combined Net Worth (Spot + Trading)</h4>
            <div class="value" style="font-size: 20px;">${{ "%.2f"|format(total_val) }}</div>
        </div>
        <div class="card">
            <h4>Spot USDC Total</h4>
            <div class="value">${{ "%.2f"|format(spot_bal) }}</div>
        </div>
        <div class="card">
            <h4>Trading Account Value</h4>
            <div class="value">${{ "%.2f"|format(acc_val) }}</div>
        </div>
        <div class="card">
            <h4>Withdrawable Cash</h4>
            <div class="value">${{ withdrawable }}</div>
        </div>
        <div class="card">
            <h4>Total Margin Used</h4>
            <div class="value">${{ margin_used }}</div>
        </div>
        <div class="card">
            <h4>Total Ntl Position</h4>
            <div class="value">${{ total_ntl }}</div>
        </div>
        <div class="card">
            <h4>Maint. Margin Used</h4>
            <div class="value">${{ maint_margin }}</div>
        </div>
        <div class="card">
            <h4>Total Live PNL</h4>
            <div class="value {{ 'plus' if total_pnl >= 0 else 'minus' }}">{{ '+' if total_pnl >= 0 else '' }}${{ "%.4f"|format(total_pnl) }}</div>
        </div>
        <div class="card">
            <h4>Open Positions</h4>
            <div class="value">{{ positions|length }}</div>
        </div>
    </div>

    <div class="pos-table">
        <div style="padding: 10px; font-size: 9px; color: #8b949e; font-weight: bold; text-align:center;">LIVE TRADE STATUS</div>
        <table>
            <thead><tr><th>COIN</th><th>SIZE</th><th>ENTRY</th><th>PNL</th></tr></thead>
            <tbody>
                {% for pos in positions %}
                <tr>
                    <td style="font-weight:bold;">{{ pos.coin }}</td>
                    <td>{{ pos.szi }}</td>
                    <td>${{ pos.entryPx }}</td>
                    <td class="{{ 'plus' if pos.pnl >= 0 else 'minus' }}">{{ "%.4f"|format(pos.pnl) }}</td>
                </tr>
                {% endfor %}
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
        spot = info.spot_user_state(address)
        trade = info.user_state(address)
        
        m_summary = trade.get('marginSummary', {})
        spot_bal = next((float(b['total']) for b in spot.get('balances', []) if b['coin'] == 'USDC'), 0.0)
        
        data = {
            'spot_bal': spot_bal,
            'acc_val': float(m_summary.get('accountValue', 0)),
            'margin_used': float(m_summary.get('totalMarginUsed', 0)),
            'total_ntl': float(m_summary.get('totalNtlPos', 0)),
            'maint_margin': float(trade.get('crossMaintenanceMarginUsed', 0)),
            'withdrawable': float(trade.get('withdrawable', 0)),
            'total_val': spot_bal + float(m_summary.get('accountValue', 0)),
            'positions': [],
            'total_pnl': 0
        }

        for pos_wrapper in trade.get('assetPositions', []):
            p = pos_wrapper['position']
            pnl = float(p.get('unrealizedPnl', 0))
            data['positions'].append({'coin': p['coin'], 'szi': abs(float(p['szi'])), 'entryPx': p['entryPx'], 'pnl': pnl})
            data['total_pnl'] += pnl
        
        return render_template_string(DASHBOARD_HTML, **data)
    except Exception as e:
        return f"ERROR: {str(e)}"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
