from flask import Flask, render_template_string
from hyperliquid.info import Info
from hyperliquid.utils import constants
import os

app = Flask(__name__)
address = "0x3C00ECF3EaAecBC7F1D1C026DCb925Ac5D2a38C5"

# UI लेआउट जिसे मैंने फिक्स कर दिया है
DASHBOARD_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700;800&family=Playfair+Display:ital,wght@0,900;1,900&display=swap');
        body { background: #0b0f14; color: #ffffff; font-family: 'Inter', sans-serif; margin: 0; padding: 10px; display: flex; justify-content: center; min-height: 100vh; }
        .container { width: 100%; max-width: 900px; text-align: center; }
        
        /* ब्रांडिंग और नाम (Fixed) */
        .super-branding { font-family: 'Playfair Display', serif; font-size: 32px; font-weight: 900; font-style: italic; background: linear-gradient(90deg, #ff0000, #ff7300, #fffb00, #48ff00, #00ffd5, #002bff, #7a00ff, #ff00c8, #ff0000); background-size: 400%; -webkit-background-clip: text; -webkit-text-fill-color: transparent; animation: rainbow 10s linear infinite; margin-bottom: 5px; }
        @keyframes rainbow { 0% { background-position: 0%; } 100% { background-position: 400%; } }
        .software-header { font-size: 11px; font-weight: bold; margin: 10px 0; letter-spacing: 1px; color: #00ffa3; line-height: 1.4; }
        .user-tag { background: rgba(0, 255, 163, 0.1); color: #00ffa3; padding: 5px 20px; border-radius: 50px; display: inline-block; margin-bottom: 15px; font-weight: bold; border: 1px solid #00ffa344; }

        /* पैरामीटर्स ग्रिड (Fixed Map - 5 Box per row for desktop) */
        .stats-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(110px, 1fr)); gap: 8px; margin-bottom: 25px; }
        .card { background: rgba(255, 255, 255, 0.03); border: 1px solid rgba(255, 255, 255, 0.08); padding: 10px 5px; border-radius: 8px; transition: 0.3s; }
        .card:hover { border-color: #58a6ff; background: rgba(88, 166, 255, 0.05); }
        .card h4 { margin: 0; color: #8b949e; font-size: 8px; text-transform: uppercase; letter-spacing: 0.5px; }
        .card .value { margin-top: 5px; font-size: 13px; font-weight: 700; color: #58a6ff; }
        .highlight { grid-column: span 2; background: rgba(88, 166, 255, 0.1); border-color: #58a6ff44; }

        /* ट्रेड्स टेबल (Dynamic Section) */
        .pos-table { background: rgba(255, 255, 255, 0.02); border-radius: 12px; border: 1px solid rgba(255, 255, 255, 0.08); overflow-x: auto; text-align: left; }
        table { width: 100%; border-collapse: collapse; min-width: 500px; }
        th { background: rgba(255, 255, 255, 0.05); padding: 10px; font-size: 9px; color: #8b949e; text-transform: uppercase; }
        td { padding: 10px; font-size: 11px; border-bottom: 1px solid rgba(255, 255, 255, 0.03); }
        .plus { color: #3fb950; } .minus { color: #f85149; }
        .footer { margin-top: 20px; font-size: 9px; color: #30363d; letter-spacing: 2px; }
    </style>
</head>
<body>
<div class="container">
    <div class="super-branding">Presenting By SirNasir</div>
    <div class="software-header">TRADING SOFTWARE = AQDAS<br>(ADAL+QADR+DASTAK+AMAL+SAFEER)</div>
    <div class="user-tag">SIR NASIR</div>
    
    <div class="stats-grid">
        <div class="card highlight"><h4>Combined Net Worth</h4><div class="value" style="font-size:18px;">${{ "%.2f"|format(total_val) }}</div></div>
        <div class="card"><h4>Spot USDC</h4><div class="value">${{ "%.2f"|format(spot_bal) }}</div></div>
        <div class="card"><h4>Account Value</h4><div class="value">${{ "%.2f"|format(acc_val) }}</div></div>
        <div class="card"><h4>Withdrawable</h4><div class="value">${{ withdrawable }}</div></div>
        <div class="card"><h4>Margin Used</h4><div class="value">${{ margin_used }}</div></div>
        <div class="card"><h4>Maint. Margin</h4><div class="value">${{ maint_margin }}</div></div>
        <div class="card"><h4>Total Ntl Pos</h4><div class="value">${{ total_ntl }}</div></div>
        <div class="card"><h4>Raw USD</h4><div class="value">${{ raw_usd }}</div></div>
        <div class="card"><h4>Total PNL</h4><div class="value {{ 'plus' if total_pnl >= 0 else 'minus' }}">${{ "%.4f"|format(total_pnl) }}</div></div>
        <div class="card"><h4>Open Trades</h4><div class="value">{{ positions|length }}</div></div>
        <div class="card"><h4>Account Time</h4><div class="value" style="font-size:9px;">{{ acc_time }}</div></div>
    </div>

    <div class="pos-table">
        <div style="padding: 10px; font-size: 10px; color: #00ffa3; font-weight: bold; text-align:center;">LIVE TRADE STATUS</div>
        <table>
            <thead><tr><th>COIN</th><th>SIZE</th><th>ENTRY</th><th>LEV</th><th>PNL</th><th>ROE%</th><th>LIQ.PX</th></tr></thead>
            <tbody>
                {% for pos in positions %}
                <tr>
                    <td style="font-weight:bold;">{{ pos.coin }}</td>
                    <td>{{ pos.szi }}</td>
                    <td>${{ pos.entryPx }}</td>
                    <td>{{ pos.lev }}x</td>
                    <td class="{{ 'plus' if pos.pnl >= 0 else 'minus' }}">{{ "%.4f"|format(pos.pnl) }}</td>
                    <td class="{{ 'plus' if pos.roe >= 0 else 'minus' }}">{{ "%.2f"|format(pos.roe * 100) }}%</td>
                    <td style="color: #ffa500;">{{ pos.liq if pos.liq else 'CROSS' }}</td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
    </div>
    <div class="footer">AQDAS SECURE TERMINAL • V2.0</div>
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
        
        m_sum = trade.get('marginSummary', {})
        spot_bal = next((float(b['total']) for b in spot.get('balances', []) if b['coin'] == 'USDC'), 0.0)
        
        data = {
            'spot_bal': spot_bal,
            'acc_val': float(m_sum.get('accountValue', 0)),
            'margin_used': float(m_sum.get('totalMarginUsed', 0)),
            'total_ntl': float(m_sum.get('totalNtlPos', 0)),
            'raw_usd': float(m_sum.get('totalRawUsd', 0)),
            'maint_margin': float(trade.get('crossMaintenanceMarginUsed', 0)),
            'withdrawable': float(trade.get('withdrawable', 0)),
            'acc_time': trade.get('time', 'N/A'),
            'total_val': spot_bal + float(m_sum.get('accountValue', 0)),
            'positions': [],
            'total_pnl': 0
        }

        for p_wrap in trade.get('assetPositions', []):
            p = p_wrap['position']
            pnl = float(p.get('unrealizedPnl', 0))
            data['positions'].append({
                'coin': p['coin'], 'szi': p['szi'], 'entryPx': p['entryPx'], 
                'pnl': pnl, 'lev': p.get('leverage', {}).get('value', 0),
                'liq': p.get('liquidationPx'), 'roe': float(p.get('returnOnEquity', 0))
            })
            data['total_pnl'] += pnl
        
        return render_template_string(DASHBOARD_HTML, **data)
    except Exception as e:
        return f"OFFLINE: {str(e)}"

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))
