from flask import Flask, render_template_string
from hyperliquid.info import Info
from hyperliquid.utils import constants
from datetime import datetime, timedelta
import os

# ==========================================================
# WARNING: "Presenting By SirNasir" AUR ISSE JUDI GLOW/BLINK 
# SETTINGS KO KUCH BHI NAHI BADALNA YA HATANA HE.
# ==========================================================

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
        
        /* ------------------------------------------------------------
           DO NOT TOUCH: SIR NASIR BRANDING & GLOW BLINK EFFECT
           ------------------------------------------------------------ */
        .super-branding { 
            font-family: 'Playfair Display', serif; 
            font-size: 38px; 
            font-weight: 900; 
            font-style: italic; 
            background: linear-gradient(90deg, #ff0000, #ff7300, #fffb00, #48ff00, #00ffd5, #002bff, #7a00ff, #ff00c8, #ff0000); 
            background-size: 400%; 
            -webkit-background-clip: text; 
            -webkit-text-fill-color: transparent; 
            animation: rainbow 8s linear infinite, glow-blink 2s ease-in-out infinite; 
            margin: 30px 0; 
        }

        @keyframes rainbow { 0% { background-position: 0%; } 100% { background-position: 400%; } }
        @keyframes glow-blink {
            0%, 100% { filter: drop-shadow(0 0 10px rgba(0,255,163,0.5)); opacity: 1; }
            50% { filter: drop-shadow(0 0 25px rgba(0,255,163,0.8)); opacity: 0.8; }
        }
        /* ------------------------------------------------------------ */

        .stats-grid { display: grid; grid-template-columns: repeat(5, 1fr); gap: 12px; margin-bottom: 25px; }
        .card { background: rgba(255, 255, 255, 0.03); border: 1px solid rgba(255, 255, 255, 0.08); padding: 18px 5px; border-radius: 8px; }
        .card h4 { margin: 0; color: #8b949e; font-size: 8px; text-transform: uppercase; font-weight: 800; }
        .card .value { margin-top: 8px; font-size: 13px; font-weight: 800; color: #58a6ff; }

        .time-card { border: 1px solid #10b981 !important; background: rgba(16, 185, 129, 0.1) !important; box-shadow: 0 0 10px rgba(16, 185, 129, 0.2); }
        .time-value { color: #10b981 !important; font-size: 10px !important; }

        .pos-table { background: rgba(255, 255, 255, 0.02); border-radius: 12px; border: 1px solid rgba(255, 255, 255, 0.08); overflow: hidden; }
        .table-header { background: rgba(16, 185, 129, 0.1); color: #10b981; padding: 12px; font-size: 11px; font-weight: 800; border-bottom: 1px solid rgba(16, 185, 129, 0.2); text-transform: uppercase; }
        table { width: 100%; border-collapse: collapse; text-align: left; }
        th { background: rgba(255, 255, 255, 0.02); padding: 15px; font-size: 10px; color: #8b949e; text-transform: uppercase; }
        td { padding: 15px; font-size: 12px; border-bottom: 1px solid rgba(255, 255, 255, 0.03); }
        
        .plus { color: #10b981; font-weight: bold; } 
        .minus { color: #ef4444; font-weight: bold; }
        .liq-price { color: #f59e0b; font-weight: bold; }
        
        .footer { margin-top: 30px; font-size: 10px; color: #334155; letter-spacing: 2px; font-weight: bold; }
    </style>
</head>
<body>
<div class="container">
    <div class="super-branding">Presenting By SirNasir</div>
    
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
        
        <div class="card time-card">
            <h4>DATE TIME</h4>
            <div class="value time-value">{{ ist_time }}</div>
        </div>
    </div>

    <div class="pos-table">
        <div class="table-header">LIVE TERMINAL STATUS</div>
        <table>
            <thead>
                <tr>
                    <th>COIN</th><th>SIZE</th><th>ENTRY</th><th>LEV</th><th>PNL</th><th>ROE%</th><th>LIQ.PX</th>
                </tr>
            </thead>
            <tbody>
                {% for pos in positions %}
                <tr>
                    <td style="font-weight:bold;">{{ pos.coin }}</td>
                    <td>{{ pos.szi }}</td>
                    <td>${{ pos.entryPx }}</td>
                    <td>{{ pos.lev }}x</td>
                    <td class="{{ 'plus' if pos.pnl >= 0 else 'minus' }}">{{ "%.4f"|format(pos.pnl) }}</td>
                    <td class="{{ 'plus' if pos.roe >= 0 else 'minus' }}">{{ "%.2f"|format(pos.roe * 100) }}%</td>
                    <td class="liq-price">{{ pos.liq if pos.liq else 'CROSS' }}</td>
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

@app.route('/')
def dashboard():
    try:
        info = Info(constants.MAINNET_API_URL)
        spot = info.spot_user_state(address)
        trade = info.user_state(address)
        m_sum = trade.get('marginSummary', {})
        spot_bal = next((float(b['total']) for b in spot.get('balances', []) if b['coin'] == 'USDC'), 0.0)
        
        unix_ts = trade.get('time', 0) / 1000
        ist_formatted = (datetime.utcfromtimestamp(unix_ts) + timedelta(hours=5, minutes=30)).strftime('%d %b, %I:%M:%S %p')

        data = {
            'spot_bal': spot_bal, 'acc_val': float(m_sum.get('accountValue', 0)),
            'margin_used': float(m_sum.get('totalMarginUsed', 0)),
            'total_ntl': float(m_sum.get('totalNtlPos', 0)),
            'raw_usd': float(m_sum.get('totalRawUsd', 0)),
            'maint_margin': float(trade.get('crossMaintenanceMarginUsed', 0)),
            'ist_time': ist_formatted,
            'total_val': spot_bal + float(m_sum.get('accountValue', 0)),
            'positions': [], 'total_pnl': 0
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
        return f"SERVER ERROR: {str(e)}"

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))
