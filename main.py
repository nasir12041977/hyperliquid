from flask import Flask, render_template_string
from hyperliquid.info import Info
from hyperliquid.utils import constants
from datetime import datetime, timedelta
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
        body { background: #0b0f14; color: #ffffff; font-family: 'Inter', sans-serif; margin: 0; padding: 10px; display: flex; justify-content: center; min-height: 100vh; }
        .container { width: 100%; max-width: 950px; text-align: center; }
        
        .super-branding { font-family: 'Playfair Display', serif; font-size: 32px; font-weight: 900; font-style: italic; background: linear-gradient(90deg, #ff0000, #ff7300, #fffb00, #48ff00, #00ffd5, #002bff, #7a00ff, #ff00c8, #ff0000); background-size: 400%; -webkit-background-clip: text; -webkit-text-fill-color: transparent; animation: rainbow 10s linear infinite; margin-bottom: 5px; }
        @keyframes rainbow { 0% { background-position: 0%; } 100% { background-position: 400%; } }

        /* 5-Step AQDAS Animation */
        .software-header { font-size: 13px; font-weight: 800; margin: 15px 0; letter-spacing: 1px; color: #00ffa3; }
        .aqdas-blink::after {
            content: "TRADING SOFTWARE = AQDAS";
            animation: aqdas-steps 8s infinite linear;
        }
        @keyframes aqdas-steps {
            0%, 15% { content: "TRADING SOFTWARE = AQDAS (A + ADAL)"; color: #ff0000; text-shadow: 0 0 10px #ff0000; }
            20%, 35% { content: "TRADING SOFTWARE = AQDAS (Q + QADR)"; color: #00ff00; text-shadow: 0 0 10px #00ff00; }
            40%, 55% { content: "TRADING SOFTWARE = AQDAS (D + DASTAK)"; color: #0000ff; text-shadow: 0 0 10px #0000ff; }
            60%, 75% { content: "TRADING SOFTWARE = AQDAS (A + AMAL)"; color: #ffff00; text-shadow: 0 0 10px #ffff00; }
            80%, 100% { content: "TRADING SOFTWARE = AQDAS (S + SAFEER)"; color: #ff00ff; text-shadow: 0 0 10px #ff00ff; }
        }

        .user-tag { background: rgba(0, 255, 163, 0.1); color: #00ffa3; padding: 5px 25px; border-radius: 50px; display: inline-block; margin-bottom: 20px; font-weight: bold; border: 1px solid #00ffa344; }

        /* 10 Box Grid (5+5) */
        .stats-grid { display: grid; grid-template-columns: repeat(5, 1fr); gap: 8px; margin-bottom: 25px; }
        .card { background: rgba(255, 255, 255, 0.03); border: 1px solid rgba(255, 255, 255, 0.08); padding: 12px 5px; border-radius: 8px; }
        .card h4 { margin: 0; color: #8b949e; font-size: 8px; text-transform: uppercase; }
        .card .value { margin-top: 5px; font-size: 12px; font-weight: 700; color: #58a6ff; }
        .wide-card { grid-column: span 1; background: rgba(88, 166, 255, 0.05); }

        .pos-table { background: rgba(255, 255, 255, 0.02); border-radius: 12px; border: 1px solid rgba(255, 255, 255, 0.08); overflow-x: auto; }
        table { width: 100%; border-collapse: collapse; min-width: 600px; text-align: left; }
        th { background: rgba(255, 255, 255, 0.05); padding: 12px; font-size: 9px; color: #8b949e; text-transform: uppercase; }
        td { padding: 12px; font-size: 11px; border-bottom: 1px solid rgba(255, 255, 255, 0.03); }
        .plus { color: #3fb950; } .minus { color: #f85149; }
        .footer { margin-top: 30px; font-size: 9px; color: #30363d; font-weight: bold; }
    </style>
</head>
<body>
<div class="container">
    <div class="super-branding">Presenting By SirNasir</div>
    <div class="software-header"><span class="aqdas-blink"></span></div>
    <div class="user-tag">SIR NASIR</div>
    
    <div class="stats-grid">
        <div class="card"><h4>Combined Net Worth</h4><div class="value">${{ "%.2f"|format(total_val) }}</div></div>
        <div class="card"><h4>Spot USDC</h4><div class="value">${{ "%.2f"|format(spot_bal) }}</div></div>
        <div class="card"><h4>Account Value</h4><div class="value">${{ "%.2f"|format(acc_val) }}</div></div>
        <div class="card"><h4>Margin Used</h4><div class="value">${{ "%.4f"|format(margin_used) }}</div></div>
        <div class="card"><h4>Maint. Margin</h4><div class="value">${{ "%.4f"|format(maint_margin) }}</div></div>
        
        <div class="card"><h4>Total Ntl Pos</h4><div class="value">${{ "%.2f"|format(total_ntl) }}</div></div>
        <div class="card"><h4>Raw USD</h4><div class="value">${{ "%.2f"|format(raw_usd) }}</div></div>
        <div class="card"><h4>Total PNL</h4><div class="value {{ 'plus' if total_pnl >= 0 else 'minus' }}">${{ "%.4f"|format(total_pnl) }}</div></div>
        <div class="card"><h4>Open Trades</h4><div class="value">{{ positions|length }}</div></div>
        <div class="card"><h4>Account Time (IST)</h4><div class="value" style="font-size:10px; color:#00ffa3;">{{ ist_time }}</div></div>
    </div>

    <div class="pos-table">
        <div style="padding: 10px; font-size: 10px; color: #00ffa3; font-weight: bold; text-align:center; border-bottom: 1px solid rgba(255,255,255,0.1);">LIVE TRADE STATUS</div>
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
    <div class="footer">AQDAS SECURE TERMINAL • V2.1</div>
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
        
        # Time Conversion (Unix to IST)
        unix_ts = trade.get('time', 0) / 1000
        ist_dt = datetime.fromtimestamp(unix_ts) + timedelta(hours=0, minutes=0) # Server time conversion check
        # नोट: Render सर्वर अक्सर UTC पर होते हैं, इसलिए +5:30 जोड़ना सुनिश्चित करता है कि कोलकाता टाइम दिखे
        ist_formatted = (datetime.utcfromtimestamp(unix_ts) + timedelta(hours=5, minutes=30)).strftime('%d %b, %H:%M:%S')

        data = {
            'spot_bal': spot_bal,
            'acc_val': float(m_sum.get('accountValue', 0)),
            'margin_used': float(m_sum.get('totalMarginUsed', 0)),
            'total_ntl': float(m_sum.get('totalNtlPos', 0)),
            'raw_usd': float(m_sum.get('totalRawUsd', 0)),
            'maint_margin': float(trade.get('crossMaintenanceMarginUsed', 0)),
            'ist_time': ist_formatted,
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
