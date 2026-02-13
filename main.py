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
        body { background: #05070a; color: #ffffff; font-family: 'Inter', sans-serif; margin: 0; padding: 10px; display: flex; justify-content: center; min-height: 100vh; }
        .container { width: 100%; max-width: 950px; text-align: center; }
        
        .super-branding { font-family: 'Playfair Display', serif; font-size: 36px; font-weight: 900; font-style: italic; background: linear-gradient(90deg, #ff0000, #ff7300, #fffb00, #48ff00, #00ffd5, #002bff, #7a00ff, #ff00c8, #ff0000); background-size: 400%; -webkit-background-clip: text; -webkit-text-fill-color: transparent; animation: rainbow 10s linear infinite; margin-bottom: 15px; }
        @keyframes rainbow { 0% { background-position: 0%; } 100% { background-position: 400%; } }

        /* JABARDAST BLINKING LOGIC */
        .software-header { 
            font-size: 16px; 
            font-weight: 800; 
            margin: 20px 0; 
            padding: 15px;
            border: 1px solid rgba(0, 255, 163, 0.2);
            border-radius: 10px;
            background: rgba(0, 255, 163, 0.02);
            letter-spacing: 1px;
            text-transform: uppercase;
        }

        .neon-text {
            color: #00ffa3;
            animation: cyber-blink 1.5s infinite alternate;
            text-shadow: 0 0 5px #00ffa3, 0 0 10px #00ffa3, 0 0 20px #00ffa3;
        }

        @keyframes cyber-blink {
            0%, 100% { opacity: 1; text-shadow: 0 0 10px #00ffa3, 0 0 20px #00ffa3, 0 0 40px #00ffa3; transform: scale(1); }
            50% { opacity: 0.3; text-shadow: 0 0 2px #00ffa3; transform: scale(0.98); }
            80% { opacity: 1; transform: scale(1.02); }
        }

        .user-tag { background: #00ffa3; color: #000; padding: 5px 30px; border-radius: 5px; display: inline-block; margin-bottom: 25px; font-weight: 900; box-shadow: 0 0 20px rgba(0, 255, 163, 0.4); }

        .stats-grid { display: grid; grid-template-columns: repeat(5, 1fr); gap: 10px; margin-bottom: 25px; }
        .card { background: rgba(255, 255, 255, 0.03); border: 1px solid rgba(255, 255, 255, 0.08); padding: 15px 5px; border-radius: 8px; transition: 0.3s; }
        .card:hover { border-color: #00ffa3; background: rgba(0, 255, 163, 0.05); }
        .card h4 { margin: 0; color: #8b949e; font-size: 9px; text-transform: uppercase; }
        .card .value { margin-top: 8px; font-size: 13px; font-weight: 800; color: #58a6ff; }

        .pos-table { background: rgba(255, 255, 255, 0.02); border-radius: 12px; border: 1px solid rgba(255, 255, 255, 0.08); overflow: hidden; }
        table { width: 100%; border-collapse: collapse; text-align: left; }
        th { background: rgba(255, 255, 255, 0.05); padding: 15px; font-size: 10px; color: #8b949e; }
        td { padding: 15px; font-size: 12px; border-bottom: 1px solid rgba(255, 255, 255, 0.03); }
        .plus { color: #00ff88; font-weight: bold; } .minus { color: #ff4444; font-weight: bold; }
        .footer { margin-top: 30px; font-size: 10px; color: #444; letter-spacing: 2px; }
    </style>
</head>
<body>
<div class="container">
    <div class="super-branding">Presenting By SirNasir</div>
    
    <div class="software-header">
        <span class="neon-text">TRADING SOFTWARE = AQDAS (ADAL+QADR+DASTAK+AMAL+SAFEER)</span>
    </div>

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
        <div class="card"><h4>Account Time (IST)</h4><div class="value" style="font-size:11px; color:#00ffa3; font-weight:bold;">{{ ist_time }}</div></div>
    </div>

    <div class="pos-table">
        <div style="padding: 12px; font-size: 11px; color: #00ffa3; font-weight: 800; text-align:center; border-bottom: 1px solid rgba(255,255,255,0.1); background: rgba(0,255,163,0.05);">LIVE TERMINAL STATUS</div>
        <table>
            <thead><tr><th>COIN</th><th>SIZE</th><th>ENTRY</th><th>LEV</th><th>PNL</th><th>ROE%</th><th>LIQ.PX</th></tr></thead>
            <tbody>
                {% for pos in positions %}
                <tr>
                    <td style="font-weight:bold; color: #fff;">{{ pos.coin }}</td>
                    <td>{{ pos.szi }}</td>
                    <td>${{ pos.entryPx }}</td>
                    <td>{{ pos.lev }}x</td>
                    <td class="{{ 'plus' if pos.pnl >= 0 else 'minus' }}">{{ "%.4f"|format(pos.pnl) }}</td>
                    <td class="{{ 'plus' if pos.roe >= 0 else 'minus' }}">{{ "%.2f"|format(pos.roe * 100) }}%</td>
                    <td style="color: #ffa500; font-weight:bold;">{{ pos.liq if pos.liq else 'CROSS' }}</td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
    </div>
    <div class="footer">AQDAS SECURE TERMINAL • V2.2 • ENCRYPTED</div>
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
        
        # Time Logic: AM/PM format
        unix_ts = trade.get('time', 0) / 1000
        ist_formatted = (datetime.utcfromtimestamp(unix_ts) + timedelta(hours=5, minutes=30)).strftime('%d %b, %I:%M:%S %p')

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
