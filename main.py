# CODE EDIT NUMBER : 06 ( PROBLEM : BALANCE PURA NAHI AA RAHA KUM DIKH RAHA HE - RESOLVED )
# ============================================================================================================
# 1. ⚠️ सख्त चेतावनी (STRICT WARNING): इन सभी निर्देशों का हर हाल में पालन करना अनिवार्य है।
# 2. कोड में किसी भी तरह का बदलाव करने से पहले, आपको लिखित में समस्या (Problem) और समाधान (Solution) दोनों बताने होंगे।
# 3. यदि आपको कोड बदलने के लिए कहा भी जाए, तब भी आपको प्रक्रिया शुरू करने से पहले एक बार अनुमति मांगनी होगी।
# 4. जब तक स्पष्ट अनुमति (Permission) न दी जाए, तब तक कोड को न तो लिखें और न ही उसमें कोई बदलाव करें।
# 5. जब भी आप कोड में कोई बदलाव करें, तो 'कोड एडिट नंबर' को जरूर बदलें अधूरा कोड बिल्कुल भी स्वीकार नहीं किया जाएगा।।
# 6. पूरे कोड के भीतर किसी भी चेतावनी कमेंट (Warning Comment) को न तो बदलें और न ही वहां से हटाएँ।
# 7. केवल उसी समस्या पर काम करें जो आपको बताई गई है, उसके अलावा कोड में अन्य कुछ भी न बदलें।
# 8. कोड में सुधार करने से पहले github hyperliquid-python-sdk और hyperliquid API Documentation जरूर पढ़ें।
# 9. निम्नलिखित हिस्से सुरक्षित हैं: 1. BRANDING, 2. AC STATUS, 3. POSITION STATUS, 4. TRADING STATUS, 5. DATA LOGIC।
# 10. यदि इन सुरक्षित हिस्सों में बदलाव किया गया, तो डैशबोर्ड खराब हो जाएगा या गलत डेटा दिखाएगा।
# ============================================================================================================

from flask import Flask, render_template_string, request, jsonify
from hyperliquid.info import Info
from hyperliquid.exchange import Exchange
from hyperliquid.utils import constants
from datetime import datetime, timedelta
import eth_account
import os
import re

app = Flask(__name__)

# --- [CHECK MARK: USER SETTINGS] ---
address = "0x3C00ECF3EaAecBC7F1D1C026DCb925Ac5D2a38C5"
secret_key = os.getenv("HL_SECRET_KEY")
account = eth_account.Account.from_key(secret_key) if secret_key else None

def clean_status(text):
    clean_text = re.sub(r'[{}()\[\]"\'/,_]', ' ', str(text))
    return " ".join(clean_text.split()).upper()

last_trade_log = """
<div class="trading-header" style="text-align: center;">TRADING STATUS == WAITING FOR SIGNAL</div>
<table>
    <thead><tr><th>COIN</th><th>DIRECTION</th><th>STATUS</th></tr></thead>
    <tbody><tr><td>SYSTEM</td><td>READY</td><td>WAITING FOR SIGNAL...</td></tr></tbody>
</table>
"""

DASHBOARD_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <script>setTimeout(function(){ location.reload(); }, 60000);</script>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700;800&family=Playfair+Display:ital,wght@0,900;1,900&display=swap');
        body { background: #05070a; color: #ffffff; font-family: 'Inter', sans-serif; margin: 0; padding: 5px; display: flex; justify-content: center; min-height: 100vh; overflow-x: hidden; }
        .container { width: 100%; max-width: 98vw; text-align: center; }
        .super-branding { font-family: 'Playfair Display', serif; font-size: 22px; font-weight: 900; font-style: italic; background: linear-gradient(90deg, #ff0000, #ff7300, #fffb00, #48ff00, #00ffd5, #002bff, #7a00ff, #ff00c8, #ff0000); background-size: 400%; -webkit-background-clip: text; -webkit-text-fill-color: transparent; animation: rainbow 8s linear infinite, glow-blink 2s ease-in-out infinite; margin: 10px 0; }
        .pnl-glow-rainbow { background: linear-gradient(90deg, #ff0000, #ff7300, #fffb00, #48ff00, #00ffd5, #002bff, #7a00ff, #ff00c8, #ff0000); background-size: 400%; -webkit-background-clip: text; -webkit-text-fill-color: transparent; animation: rainbow 8s linear infinite; font-weight: 800; }
        .blink-red { color: #ef4444 !important; animation: blinker 1s linear infinite; font-weight: 800; }
        .text-red { color: #ef4444 !important; font-weight: 800; }
        .text-green { color: #10b981 !important; font-weight: 800; }
        @keyframes rainbow { 0% { background-position: 0%; } 100% { background-position: 400%; } }
        @keyframes blinker { 50% { opacity: 0; } }
        .stats-grid { display: flex; flex-wrap: nowrap; justify-content: space-between; gap: 4px; margin-bottom: 10px; }
        .card { background: rgba(255, 255, 255, 0.03); border: 1px solid rgba(255, 255, 255, 0.08); padding: 8px 2px; border-radius: 4px; flex: 1 1 auto; min-width: 0; }
        .card h4 { margin: 0; color: #8b949e; font-size: 8px; text-transform: uppercase; white-space: nowrap; }
        .card .value { margin-top: 3px; font-size: 10px; font-weight: 800; color: #58a6ff; white-space: nowrap; }
        .pos-table, .trading-box { background: rgba(255, 255, 255, 0.02); border-radius: 6px; border: 1px solid rgba(255, 255, 255, 0.08); overflow: hidden; margin-bottom: 10px; }
        .table-header { background: rgba(16, 185, 129, 0.1); color: #10b981; padding: 6px; font-size: 11px; font-weight: 800; border-bottom: 1px solid rgba(16, 185, 129, 0.2); }
        .trading-header { background: rgba(88, 166, 255, 0.1); color: #58a6ff; padding: 6px; font-size: 11px; font-weight: 800; border-bottom: 1px solid rgba(88, 166, 255, 0.2); text-align: center !important; }
        table { width: 100%; border-collapse: collapse; text-align: left; table-layout: fixed; }
        th { background: rgba(255, 255, 255, 0.02); padding: 6px 4px; font-size: 9px; color: #8b949e; text-transform: uppercase; }
        td { padding: 4px 4px; font-size: 10px; border-bottom: 1px solid rgba(255, 255, 255, 0.03); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
        .plus { color: #10b981; font-weight: bold; }
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
        <div class="card">
            <h4>PNL</h4>
            <div class="value {% if total_pnl > 0 %}pnl-glow-rainbow{% elif total_pnl < 0 %}blink-red{% endif %}">
                {{ "%.2f"|format(total_pnl) }}
            </div>
        </div>
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
                    <td style="font-weight:bold;" class="{{ 'text-green' if pos.side == 'buy' else 'text-red' }}">{{ pos.coin }}</td>
                    <td>{{ pos.szi }}</td><td>${{ pos.entryPx }}</td><td>{{ pos.lev }}x</td>
                    <td class="{% if pos.pnl > 0 %}plus{% elif pos.pnl < 0 %}blink-red{% endif %}">{{ "%.4f"|format(pos.pnl) }}</td>
                    <td class="{% if pos.roe > 0 %}plus{% elif pos.roe < 0 %}blink-red{% endif %}">{{ "%.2f"|format(pos.roe) }}%</td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
    </div>
    <div class="trading-box">{{ log_msg|safe }}</div>
    <div class="footer">AQDAS SECURE TERMINAL • V2.2</div>
</div>
</body>
</html>
"""

@app.route('/trade', methods=['POST'])
def run_sync():
    global last_trade_log
    logs_data, table_rows = [], ""
    ist_now = (datetime.utcnow() + timedelta(hours=5, minutes=30)).strftime('%d %b, %I:%M:%S %p')
    
    try:
        info = Info(constants.MAINNET_API_URL)
        ex = Exchange(account, constants.MAINNET_API_URL)
        data = request.json.get("trades", [])
        meta = info.meta()
        mids = info.all_mids()
        user_state = info.user_state(address)
        
        active_pos = {p['position']['coin']: float(p['position']['szi']) for p in user_state.get('assetPositions', []) if float(p['position']['szi']) != 0}
        universe = [m['name'] for m in meta['universe']]
        target_names = [universe[int(tr[0])] for tr in data if int(tr[0]) < len(universe)]

        for coin, szi in list(active_pos.items()):
            row = next((t for t in data if universe[int(t[0])] == coin), None)
            target_buy = True if row and str(row[1]).upper() == "TRUE" else False
            
            if coin not in target_names or (target_buy and szi < 0) or (not target_buy and szi > 0):
                is_buy_to_close = szi < 0 
                ex.market_open(coin, is_buy_to_close, abs(szi), slippage=0.05)
                
                side = "SELL" if szi > 0 else "BUY"
                status_msg = "CLOSE"
                table_rows += f"<tr><td>{coin}</td><td>{side}</td><td>{status_msg}</td></tr>"
                logs_data.append(f"{coin}, {side}, {status_msg}")
                if coin in active_pos: del active_pos[coin]

        for tr in data:
            coin_idx = int(tr[0])
            if coin_idx >= len(universe): continue
            coin, is_buy, usd_val = universe[coin_idx], (str(tr[1]).upper() == "TRUE"), float(tr[2])
            side_text = "BUY" if is_buy else "SELL"
            cur_szi = active_pos.get(coin, 0)
            
            if (is_buy and cur_szi > 0) or (not is_buy and cur_szi < 0):
                status_msg = "RUNNING"
                table_rows += f"<tr><td>{coin}</td><td>{side_text}</td><td>{status_msg}</td></tr>"
                logs_data.append(f"{coin}, {side_text}, {status_msg}")
                continue
            
            try:
                m = next(m for m in meta['universe'] if m['name'] == coin)
                px = float(mids[coin])
                ex.update_leverage(m['maxLeverage'], coin)
                sz = float(f"{usd_val / px:.{m['szDecimals']}f}")
                
                if (sz * px) < 10.1: sz = float(f"{10.1 / px:.{m['szDecimals']}f}")
                
                res = ex.market_open(coin, is_buy, sz, slippage=0.05)
                
                if res["status"] == "ok":
                    status_msg = "ENTRY"
                    table_rows += f"<tr><td>{coin}</td><td>{side_text}</td><td>{status_msg}</td></tr>"
                    logs_data.append(f"{coin}, {side_text}, {status_msg}")
                else:
                    err = clean_status(res.get("response", "ERROR"))
                    table_rows += f"<tr><td>{coin}</td><td>{side_text}</td><td>{err}</td></tr>"
                    logs_data.append(f"{coin}, {side_text}, {err}")
            except Exception as e:
                err_clean = clean_status(e)
                table_rows += f"<tr><td>{coin}</td><td>{side_text}</td><td>{err_clean}</td></tr>"
                logs_data.append(f"{coin}, {side_text}, {err_clean}")

        last_trade_log = f"""
        <div class="trading-header">TRADING STATUS &nbsp;&nbsp; == &nbsp;&nbsp; {ist_now}</div>
        <table>
            <thead><tr><th>COIN</th><th>DIRECTION</th><th>STATUS</th></tr></thead>
            <tbody>{table_rows}</tbody>
        </table>
        """
        return jsonify({"status": "ok", "msg": "\\n".join(logs_data)}), 200

    except Exception as e:
        last_trade_log = f"<div class='trading-header' style='color:#ef4444;'>ERROR == {ist_now}</div>"
        return jsonify({"status": "error", "msg": clean_status(e)}), 500

@app.route('/')
def dashboard():
    try:
        info = Info(constants.MAINNET_API_URL)
        
        perp_state = info.user_state(address)
        spot_state = info.spot_user_state(address)
        vault_states = info.user_vault_equities(address)
        
        m_sum = perp_state.get('marginSummary', {})
        
        # --- DATA LOGIC: FINAL CORRECT BALANCE CALCULATION ---
        # 1. Perp Account Value (Settled Cash + Unrealized PnL)
        p_val = float(m_sum.get('accountValue', 0))
        
        # 2. Withdrawable Cash (Actual cash available, used to verify liquidity)
        w_cash = float(perp_state.get('withdrawable', 0))
        
        # 3. Spot Value (Current value of all spot holdings)
        s_val = sum(float(s.get('totalValue', 0)) for s in spot_state.get('balances', []))
        
        # 4. Vault Value (Equity in all subscribed vaults)
        v_val = sum(float(v.get('equity', 0)) for v in vault_states)
        
        # FINAL TOTAL BALANCE (Logic updated to ensure no fund is left out)
        # Using accountValue + spot + vault. 
        # If accountValue is less than withdrawable (rare cross-margin case), we adjust.
        acc_val = max(p_val, w_cash) + s_val + v_val

        total_pnl = 0
        positions_list = []
        for p_wrap in perp_state.get('assetPositions', []):
            p = p_wrap['position']
            if float(p['szi']) != 0:
                pnl, szi, entry_px = float(p.get('unrealizedPnl', 0)), float(p.get('szi', 0)), float(p.get('entryPx', 1))
                positions_list.append({
                    'coin': p['coin'], 'szi': p['szi'], 'entryPx': p['entryPx'], 'pnl': pnl, 
                    'lev': p.get('leverage', {}).get('value', 0),
                    'roe': (pnl / (abs(szi) * entry_px)) * 100 if szi != 0 else 0, 'side': 'buy' if szi > 0 else 'sell'
                })
                total_pnl += pnl

        data = {
            'total_val': acc_val, 
            'margin_used': float(m_sum.get('totalMarginUsed', 0)),
            'total_ntl': float(m_sum.get('totalNtlPos', 0)), 
            'maint_margin': float(perp_state.get('crossMaintenanceMarginUsed', 0)),
            'ist_time': (datetime.utcnow() + timedelta(hours=5, minutes=30)).strftime('%d %b, %I:%M:%S %p'),
            'mdd_val': max(0.0, acc_val - w_cash),
            'log_msg': last_trade_log, 
            'positions': positions_list, 
            'total_pnl': total_pnl
        }
        
        return render_template_string(DASHBOARD_HTML, **data)
    except Exception as e: return f"SERVER ERROR: {str(e)}"

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
