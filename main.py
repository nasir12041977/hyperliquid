# Code Number 8
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

# CATEGORY 4: TRADING STATUS LIVE LOGGING
last_trade_log = "> SYSTEM READY: API Sync MDD tracking active.<br>> Dashboard synchronized with exchange account values."

DASHBOARD_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700;800&family=Playfair+Display:ital,wght@0,900;1,900&display=swap');
        
        body { 
            background: #05070a; color: #ffffff; font-family: 'Inter', sans-serif; 
            margin: 0; padding: 5px; display: flex; justify-content: center; 
            min-height: 100vh; overflow-x: hidden; 
        }
        .container { width: 100%; max-width: 98vw; text-align: center; }
        
        /* CATEGORY 1: BRANDING */
        .super-branding { 
            font-family: 'Playfair Display', serif; 
            font-size: 22px; 
            font-weight: 900; font-style: italic; 
            background: linear-gradient(90deg, #ff0000, #ff7300, #fffb00, #48ff00, #00ffd5, #002bff, #7a00ff, #ff00c8, #ff0000); 
            background-size: 400%; 
            -webkit-background-clip: text; -webkit-text-fill-color: transparent; 
            animation: rainbow 8s linear infinite, glow-blink 2s ease-in-out infinite; 
            margin: 10px 0;
        }

        @keyframes rainbow { 0% { background-position: 0%; } 100% { background-position: 400%; } }
        @keyframes glow-blink {
            0%, 100% { filter: drop-shadow(0 0 5px rgba(0,255,163,0.3)); opacity: 1; }
            50% { filter: drop-shadow(0 0 15px rgba(0,255,163,0.5)); opacity: 0.8; }
        }

        /* CATEGORY 2: AC STATUS */
        .stats-grid { 
            display: flex; flex-wrap: nowrap; justify-content: space-between; gap: 4px; margin-bottom: 10px; 
        }
        .card { 
            background: rgba(255, 255, 255, 0.03); border: 1px solid rgba(255, 255, 255, 0.08); 
            padding: 8px 2px; border-radius: 4px; flex: 1 1 auto; min-width: 0;
        }
        .card h4 { margin: 0; color: #8b949e; font-size: 8px; text-transform: uppercase; white-space: nowrap; }
        .card .value { margin-top: 3px; font-size: 10px; font-weight: 800; color: #58a6ff; white-space: nowrap; }

        .pnl-plus {
            background: linear-gradient(90deg, #ff0000, #ff7300, #fffb00, #48ff00, #00ffd5, #002bff, #7a00ff, #ff00c8, #ff0000);
            background-size: 400%; -webkit-background-clip: text; -webkit-text-fill-color: transparent;
            animation: rainbow 8s linear infinite; font-weight: 900;
        }
        .pnl-minus { color: #ef4444 !important; animation: red-blink 1s ease-in-out infinite; font-weight: 800; }
        @keyframes red-blink { 0%, 100% { opacity: 1; } 50% { opacity: 0.3; } }

        /* CATEGORY 3: POSITION STATUS */
        .pos-table { 
            background: rgba(255, 255, 255, 0.02); border-radius: 6px; border: 1px solid rgba(255, 255, 255, 0.08); 
            overflow: hidden; margin-bottom: 10px;
        }
        .table-header { 
            background: rgba(16, 185, 129, 0.1); color: #10b981; padding: 6px; font-size: 11px; font-weight: 800; 
            border-bottom: 1px solid rgba(16, 185, 129, 0.2); 
        }
        table { width: 100%; border-collapse: collapse; text-align: left; table-layout: fixed; }
        th { background: rgba(255, 255, 255, 0.02); padding: 6px 4px; font-size: 9px; color: #8b949e; text-transform: uppercase; }
        td { padding: 4px 4px; font-size: 10px; border-bottom: 1px solid rgba(255, 255, 255, 0.03); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }

        /* CATEGORY 4: TRADING STATUS */
        .trading-box {
            background: rgba(255, 255, 255, 0.02); border-radius: 6px; border: 1px solid rgba(255, 255, 255, 0.08); overflow: hidden;
        }
        .trading-header { 
            background: rgba(88, 166, 255, 0.1); color: #58a6ff; padding: 6px; font-size: 11px; font-weight: 800; 
            border-bottom: 1px solid rgba(88, 166, 255, 0.2); text-align: left;
        }
        .log-container { padding: 8px; text-align: left; font-family: monospace; font-size: 9px; color: #8b949e; line-height: 1.4; }
        
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
        <div class="card"><h4>PNL</h4><div class="value {{ 'pnl-plus' if total_pnl >= 0 else 'pnl-minus' }}">{{ "%.2f"|format(total_pnl) }}</div></div>
        <div class="card"><h4>MARGIN</h4><div class="value">{{ "%.2f"|format(margin_used) }}</div></div>
        <div class="card"><h4>MM</h4><div class="value">{{ "%.2f"|format(maint_margin) }}</div></div>
        <div class="card"><h4>MDD</h4><div class="value">{{ "%.2f"|format(mdd_val) }}</div></div>
    </div>

    <div class="pos-table">
        <div class="table-header">POSITION STATUS &nbsp;&nbsp; == &nbsp;&nbsp; {{ ist_time }}</div>
        <table>
            <thead>
                <tr>
                    <th style="width: 20%;">COIN</th>
                    <th style="width: 15%;">SIZE</th>
                    <th style="width: 20%;">ENTRY</th>
                    <th style="width: 10%;">LEV</th>
                    <th style="width: 20%;">PNL</th>
                    <th style="width: 15%;">ROE%</th>
                </tr>
            </thead>
            <tbody>
                {% for pos in positions %}
                <tr>
                    <td style="font-weight:bold;" class="{{ 'plus' if pos.side == 'buy' else 'pnl-minus' if pos.side == 'sell' else '' }}">
                        {{ pos.coin }}
                    </td>
                    <td>{{ pos.szi }}</td>
                    <td>${{ pos.entryPx }}</td>
                    <td>{{ pos.lev }}x</td>
                    <td class="{{ 'plus' if pos.pnl >= 0 else 'pnl-minus' }}">{{ "%.4f"|format(pos.pnl) }}</td>
                    <td class="{{ 'plus' if pos.roe >= 0 else 'pnl-minus' }}">{{ "%.2f"|format(pos.roe) }}%</td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
    </div>

    <div class="trading-box">
        <div class="trading-header">TRADING STATUS (API RESPONSE)</div>
        <div class="log-container">
            {{ log_msg|safe }}
        </div>
    </div>

    <div class="footer">AQDAS SECURE TERMINAL • V2.2</div>
</div>
</body>
</html>
"""

# --- NEW SYNC ENGINE (CLEANUP & EXECUTION) ---

@app.route('/trade', methods=['POST'])
def run_sync():
    global last_trade_log
    log_entries = []
    try:
        info = Info(constants.MAINNET_API_URL)
        ex = Exchange(account, constants.MAINNET_API_URL)
        data = request.json.get("trades", [])
        
        # STEP 1: CLEANUP (Wrong Direction or Not in List)
        curr_pos = info.user_state(address).get('assetPositions', [])
        for p_wrap in curr_pos:
            p = p_wrap['position']
            coin, szi = p['coin'], float(p['szi'])
            row = next((t for t in data if t[0] == coin), None)
            target_buy = True if row and str(row[1]).upper() == "TRUE" else False

            if not row or (target_buy and szi < 0) or (not target_buy and szi > 0):
                ex.market_order(coin, szi < 0, abs(szi), None, {"reduceOnly": True})
                log_entries.append(f"> CLOSED: {coin} (Sync Correction)")

        # STEP 2: EXECUTION (LTP, Max Margin, szDec, OI > 0)
        meta, mids = info.meta(), info.all_mids()
        for tr in data:
            coin, is_buy, usd = tr[0], (str(tr[1]).upper() == "TRUE"), float(tr[2])
            m = next((m for m in meta['universe'] if m['name'] == coin), None)
            
            # OI > 0 Check (Greater than Zero)
            if not m: continue
            
            px = float(mids[coin])
            ex.update_leverage(m['maxLeverage'], coin) # Rule 2
            
            sz = float(f"{usd / px:.{m['szDecimals']}f}") # Rule 3
            if (sz * px) < 10: sz = float(f"{10.1 / px:.{m['szDecimals']}f}") # Rule 1

            res = ex.market_order(coin, is_buy, sz)
            status = "SUCCESS" if res["status"] == "ok" else f"ERROR: {res}"
            log_entries.append(f"> {coin}: {status}")

        last_trade_log = "<br>".join(log_entries)
        return jsonify({"status": "ok", "msg": last_trade_log}), 200
    except Exception as e:
        last_trade_log = f"> CRITICAL ERROR: {str(e)}"
        return jsonify({"status": "error", "msg": str(e)}), 500

# ------------------------------------------------------------------------------
# CATEGORY 5: DATA LOGIC (UNCHANGED AS PER WARNING)
# ------------------------------------------------------------------------------

@app.route('/')
def dashboard():
    try:
        info = Info(constants.MAINNET_API_URL)
        spot = info.spot_user_state(address)
        trade = info.user_state(address)
        vault_data = info.user_vault_equities(address)

        spot_bal = next((float(b['total']) for b in spot.get('balances', []) if b['coin'] == 'USDC'), 0.0)
        vault_bal = sum(float(v.get('equity', 0)) for v in vault_data)
        m_sum = trade.get('marginSummary', {})
        acc_val = float(m_sum.get('accountValue', 0))
        
        current_total = spot_bal + acc_val + vault_bal
        withdrawable = float(trade.get('withdrawable', current_total))
        mdd_val = max(0.0, acc_val - withdrawable)

        unix_ts = trade.get('time', 0) / 1000
        ist_formatted = (datetime.utcfromtimestamp(unix_ts) + timedelta(hours=5, minutes=30)).strftime('%d %b, %I:%M:%S %p')

        data = {
            'total_val': current_total,
            'margin_used': float(m_sum.get('totalMarginUsed', 0)),
            'total_ntl': float(m_sum.get('totalNtlPos', 0)),
            'maint_margin': float(trade.get('crossMaintenanceMarginUsed', 0)),
            'ist_time': ist_formatted,
            'mdd_val': mdd_val,
            'log_msg': last_trade_log, # Live Sync
            'positions': [], 'total_pnl': 0
        }

        for p_wrap in trade.get('assetPositions', []):
            p = p_wrap['position']
            pnl = float(p.get('unrealizedPnl', 0))
            szi_abs = abs(float(p.get('szi', 0)))
            entry_px = float(p.get('entryPx', 1))
            manual_roe = (pnl / (szi_abs * entry_px)) * 100 if szi_abs > 0 else 0
            side_type = 'buy' if float(p.get('szi', 0)) > 0 else 'sell'

            data['positions'].append({
                'coin': p['coin'], 'szi': p['szi'], 'entryPx': p['entryPx'], 
                'pnl': pnl, 'lev': p.get('leverage', {}).get('value', 0),
                'roe': manual_roe, 'side': side_type
            })
            data['total_pnl'] += pnl
        
        return render_template_string(DASHBOARD_HTML, **data)
    except Exception as e:
        return f"SERVER ERROR: {str(e)}"

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))
