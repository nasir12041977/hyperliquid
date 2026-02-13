# Code Number 12
# ==============================================================================
# ⚠️ सख्त चेतावनी (WARNING) - AI और डेवलपर्स के लिए:
# नीचे दी गई कैटेगरी को किसी भी हाल में छेड़ना, बदलना या हटाना नहीं है।
# 1. BRANDING  2. AC STATUS  3. POSITION STATUS  4. TRADING STATUS  5. DATA LOGIC
# अगर इनमें से कोई भी हिस्सा बदला गया, तो डैशबोर्ड खराब हो जाएगा या गलत डेटा दिखाएगा।
# ==============================================================================

from flask import Flask, render_template_string, request, jsonify
from hyperliquid.info import Info
from hyperliquid.exchange import Exchange
from hyperliquid.utils import constants
from datetime import datetime, timedelta
import eth_account
import os

app = Flask(__name__)
address = "0x3C00ECF3EaAecBC7F1D1C026DCb925Ac5D2a38C5"
secret_key = os.getenv("HL_SECRET_KEY")
account = eth_account.Account.from_key(secret_key) if secret_key else None

last_trade_log = "> SYSTEM READY: Waiting for Index-Based Signal..."

DASHBOARD_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700;800&family=Playfair+Display:ital,wght@0,900;1,900&display=swap');
        body { background: #05070a; color: #ffffff; font-family: 'Inter', sans-serif; margin: 0; padding: 5px; display: flex; justify-content: center; min-height: 100vh; overflow-x: hidden; }
        .container { width: 100%; max-width: 98vw; text-align: center; }
        .super-branding { font-family: 'Playfair Display', serif; font-size: 22px; font-weight: 900; font-style: italic; background: linear-gradient(90deg, #ff0000, #ff7300, #fffb00, #48ff00, #00ffd5, #002bff, #7a00ff, #ff00c8, #ff0000); background-size: 400%; -webkit-background-clip: text; -webkit-text-fill-color: transparent; animation: rainbow 8s linear infinite, glow-blink 2s ease-in-out infinite; margin: 10px 0; }
        @keyframes rainbow { 0% { background-position: 0%; } 100% { background-position: 400%; } }
        .stats-grid { display: flex; flex-wrap: nowrap; justify-content: space-between; gap: 4px; margin-bottom: 10px; }
        .card { background: rgba(255, 255, 255, 0.03); border: 1px solid rgba(255, 255, 255, 0.08); padding: 8px 2px; border-radius: 4px; flex: 1 1 auto; min-width: 0; }
        .card h4 { margin: 0; color: #8b949e; font-size: 8px; text-transform: uppercase; white-space: nowrap; }
        .card .value { margin-top: 3px; font-size: 10px; font-weight: 800; color: #58a6ff; white-space: nowrap; }
        .pos-table { background: rgba(255, 255, 255, 0.02); border-radius: 6px; border: 1px solid rgba(255, 255, 255, 0.08); overflow: hidden; margin-bottom: 10px; }
        .table-header { background: rgba(16, 185, 129, 0.1); color: #10b981; padding: 6px; font-size: 11px; font-weight: 800; border-bottom: 1px solid rgba(16, 185, 129, 0.2); }
        table { width: 100%; border-collapse: collapse; text-align: left; table-layout: fixed; }
        th { background: rgba(255, 255, 255, 0.02); padding: 6px 4px; font-size: 9px; color: #8b949e; text-transform: uppercase; }
        td { padding: 4px 4px; font-size: 10px; border-bottom: 1px solid rgba(255, 255, 255, 0.03); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
        .trading-box { background: rgba(255, 255, 255, 0.02); border-radius: 6px; border: 1px solid rgba(255, 255, 255, 0.08); overflow: hidden; }
        .trading-header { background: rgba(88, 166, 255, 0.1); color: #58a6ff; padding: 6px; font-size: 11px; font-weight: 800; border-bottom: 1px solid rgba(88, 166, 255, 0.2); text-align: left; }
        .log-container { padding: 8px; text-align: left; font-family: monospace; font-size: 9px; color: #8b949e; line-height: 1.4; }
        .plus { color: #10b981; font-weight: bold; }
        .pnl-minus { color: #ef4444 !important; font-weight: 800; }
        .footer { margin-top: 10px; font-size: 8px; color: #334155; font-weight: bold; }
    </style>
</head>
<body>
<div class="container">
    <div class="super-branding">Presenting By SirNasir</div>
    <div class="stats-grid">
        <div class="card"><h4>BALANCE</h4><div class="value">{{ "%.2f"|format(total_val) }}</div></div>
        <div class="card"><h4>TR</h4><div class="value">{{ positions|length }}</div></div>
        <div class="card"><h4>TR VALUE</h4><div class="value">{{ "%.2f"|format(total_ntl) }}</div></div>
        <div class="card"><h4>PNL</h4><div class="value {{ 'plus' if total_pnl >= 0 else 'pnl-minus' }}">{{ "%.2f"|format(total_pnl) }}</div></div>
        <div class="card"><h4>MARGIN</h4><div class="value">{{ "%.2f"|format(margin_used) }}</div></div>
        <div class="card"><h4>MM</h4><div class="value">{{ "%.2f"|format(maint_margin) }}</div></div>
        <div class="card"><h4>MDD</h4><div class="value">{{ "%.2f"|format(mdd_val) }}</div></div>
    </div>
    <div class="pos-table">
        <div class="table-header">POSITION STATUS &nbsp;&nbsp; == &nbsp;&nbsp; {{ ist_time }}</div>
        <table>
            <thead><tr><th>COIN</th><th>SIZE</th><th>ENTRY</th><th>LEV</th><th>PNL</th><th>ROE%</th></tr></thead>
            <tbody>
                {% for pos in positions %}
                <tr>
                    <td style="font-weight:bold;" class="{{ 'plus' if pos.side == 'buy' else 'pnl-minus' }}">{{ pos.coin }}</td>
                    <td>{{ pos.szi }}</td><td>${{ pos.entryPx }}</td><td>{{ pos.lev }}x</td>
                    <td class="{{ 'plus' if pos.pnl >= 0 else 'pnl-minus' }}">{{ "%.4f"|format(pos.pnl) }}</td>
                    <td class="{{ 'plus' if pos.roe >= 0 else 'pnl-minus' }}">{{ "%.2f"|format(pos.roe) }}%</td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
    </div>
    <div class="trading-box"><div class="trading-header">TRADING STATUS (API RESPONSE)</div><div class="log-container">{{ log_msg|safe }}</div></div>
    <div class="footer">AQDAS SECURE TERMINAL • V2.2</div>
</div>
</body>
</html>
"""

# --- MASTER SYNC ENGINE (INDEX-BASED MILAN LOGIC) ---

@app.route('/trade', methods=['POST'])
def run_sync():
    global last_trade_log
    logs = []
    try:
        info = Info(constants.MAINNET_API_URL)
        ex = Exchange(account, constants.MAINNET_API_URL)
        data = request.json.get("trades", [])
        
        meta = info.meta()
        mids = info.all_mids()
        user_state = info.user_state(address)
        active_pos = {p['position']['coin']: float(p['position']['szi']) for p in user_state.get('assetPositions', [])}
        
        # Index to Name Mapping (0 -> BTC, 1 -> ETH)
        universe = [m['name'] for m in meta['universe']]

        # STEP 1: CLEANUP (Based on Target List)
        target_names = []
        for tr in data:
            idx = int(tr[0])
            if idx < len(universe): target_names.append(universe[idx])

        for coin, szi in list(active_pos.items()):
            row = next((t for t in data if universe[int(t[0])] == coin), None)
            target_buy = True if row and str(row[1]).upper() == "TRUE" else False
            
            if coin not in target_names or (target_buy and szi < 0) or (not target_buy and szi > 0):
                # Market Close (Futures)
                ex.market_close(coin, reduce_only=True)
                logs.append(f"> {coin}: MARKET CLOSED (Sync)")
                if coin in active_pos: del active_pos[coin]

        # STEP 2: EXECUTION (Direction Check & Market Order)
        for tr in data:
            coin_idx = int(tr[0])
            if coin_idx >= len(universe): continue
            
            coin = universe[coin_idx]
            is_buy = (str(tr[1]).upper() == "TRUE")
            usd_val = float(tr[2])
            
            # Skip if direction matches
            cur_szi = active_pos.get(coin, 0)
            if (is_buy and cur_szi > 0) or (not is_buy and cur_szi < 0):
                logs.append(f"> {coin}: MATCHED (Skipped)")
                continue
            
            # Get asset info for decimals
            m = next(m for m in meta['universe'] if m['name'] == coin)
            px = float(mids[coin])
            ex.update_leverage(m['maxLeverage'], coin)
            
            sz = float(f"{usd_val / px:.{m['szDecimals']}f}")
            if (sz * px) < 10: sz = float(f"{10.1 / px:.{m['szDecimals']}f}")

            # Real Market Order (Slippage included)
            res = ex.market_open(coin, is_buy, sz, slippage=0.01)
            
            if res["status"] == "ok":
                logs.append(f"> {coin}: MARKET {'BUY' if is_buy else 'SELL'} SUCCESS")
            else:
                logs.append(f"> {coin}: FAILED")

        if not logs: logs.append("> ALL POSITIONS IN PERFECT SYNC")
        last_trade_log = "<br>".join(logs)
        return jsonify({"status": "ok", "msg": last_trade_log}), 200
    except Exception as e:
        last_trade_log = f"> CRITICAL ERROR: {str(e)}"
        return jsonify({"status": "error", "msg": str(e)}), 500

# --- CATEGORY 5: DATA LOGIC (UNCHANGED) ---
@app.route('/')
def dashboard():
    try:
        info = Info(constants.MAINNET_API_URL)
        spot, trade = info.spot_user_state(address), info.user_state(address)
        m_sum = trade.get('marginSummary', {})
        acc_val = float(m_sum.get('accountValue', 0))
        spot_bal = next((float(b['total']) for b in spot.get('balances', []) if b['coin'] == 'USDC'), 0.0)
        vault_bal = sum(float(v.get('equity', 0)) for v in info.user_vault_equities(address))
        current_total = spot_bal + acc_val + vault_bal
        mdd_val = max(0.0, acc_val - float(trade.get('withdrawable', acc_val)))
        ist_formatted = (datetime.utcnow() + timedelta(hours=5, minutes=30)).strftime('%d %b, %I:%M:%S %p')
        data = {
            'total_val': current_total, 'margin_used': float(m_sum.get('totalMarginUsed', 0)),
            'total_ntl': float(m_sum.get('totalNtlPos', 0)), 'maint_margin': float(trade.get('crossMaintenanceMarginUsed', 0)),
            'ist_time': ist_formatted, 'mdd_val': mdd_val, 'log_msg': last_trade_log, 'positions': [], 'total_pnl': 0
        }
        for p_wrap in trade.get('assetPositions', []):
            p = p_wrap['position']
            pnl, szi, entry_px = float(p.get('unrealizedPnl', 0)), float(p.get('szi', 0)), float(p.get('entryPx', 1))
            data['positions'].append({
                'coin': p['coin'], 'szi': p['szi'], 'entryPx': p['entryPx'], 'pnl': pnl, 
                'lev': p.get('leverage', {}).get('value', 0),
                'roe': (pnl / (abs(szi) * entry_px)) * 100 if szi != 0 else 0, 'side': 'buy' if szi > 0 else 'sell'
            })
            data['total_pnl'] += pnl
        return render_template_string(DASHBOARD_HTML, **data)
    except Exception as e: return f"SERVER ERROR: {str(e)}"

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))
