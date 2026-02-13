<!DOCTYPE html>
<html lang="hi">
<head>
    <meta charset="UTF-8">
    <style>
        body { background-color: #020202; color: #ffffff; font-family: 'Segoe UI', sans-serif; padding: 40px; margin: 0; }
        
        /* AQDAS BRANDING SECTION */
        .aqdas-container {
            border: 1px solid #1a1a1a;
            padding: 50px;
            background: linear-gradient(145deg, #0a0a0a, #111);
            box-shadow: 0 0 40px rgba(0, 255, 204, 0.05);
            margin-bottom: 40px;
        }
        .header { margin-bottom: 40px; border-bottom: 2px solid #00ffcc; display: inline-block; }
        
        /* ब्लिंकिंग एनीमेशन */
        @keyframes blinker {
            50% { opacity: 0.3; text-shadow: none; }
        }

        .title { 
            font-size: 5rem; font-weight: 900; letter-spacing: 20px; color: #00ffcc; margin: 0;
            animation: blinker 1.5s linear infinite;
            text-shadow: 0 0 20px #00ffcc;
        }
        .subtitle { font-size: 2rem; letter-spacing: 10px; opacity: 0.8; margin-top: -10px; }

        /* SYMMETRY LOGIC - AQDAS (पाकीज़ा) */
        .logic-row { display: flex; align-items: center; margin-bottom: 15px; }
        .initial { font-size: 2.5rem; font-weight: 900; color: #00ffcc; width: 60px; text-shadow: 0 0 10px #00ffcc; }
        .word { font-size: 1.8rem; font-weight: 700; width: 280px; border-right: 1px solid #333; }
        .meaning { font-size: 1.2rem; padding-left: 25px; color: #888; letter-spacing: 1.5px; }

        /* TRADING DATA & PARAMETERS */
        .dashboard { display: grid; grid-template-columns: repeat(4, 1fr); gap: 20px; margin-top: 50px; }
        .card { background: #0d0d0d; border: 1px solid #222; padding: 25px; border-radius: 5px; }
        .card-label { color: #555; font-size: 0.9rem; font-weight: bold; text-transform: uppercase; display: block; margin-bottom: 10px; }
        .card-value { font-size: 2.2rem; font-family: monospace; font-weight: bold; color: #fff; }
        .highlight { color: #00ffcc; }
    </style>
</head>
<body>

    <div class="aqdas-container">
        <div class="header">
            <h1 class="title">AQDAS</h1>
            <div class="subtitle">(पाकीज़ा) =</div>
        </div>

        <div class="logic-list">
            <div class="logic-row">
                <div class="initial">A</div>
                <div class="word">ADAL (अदल)</div>
                <div class="meaning">: ANALYSIS & DATA ARCHIVE LOGIC</div>
            </div>
            <div class="logic-row">
                <div class="initial">Q</div>
                <div class="word">QADR (क़द्र)</div>
                <div class="meaning">: QUALITY CHECK & DEPLOYMENT RATING</div>
            </div>
            <div class="logic-row">
                <div class="initial">D</div>
                <div class="word">DASTAK (दस्तक)</div>
                <div class="meaning">: DATA ANALYSIS & STRATEGY TRACKING</div>
            </div>
            <div class="logic-row">
                <div class="initial">A</div>
                <div class="word">AMAL (अमल)</div>
                <div class="meaning">: ASSET MATCHING & ARBITRATION LOGIC</div>
            </div>
            <div class="logic-row">
                <div class="initial">S</div>
                <div class="word">SAFEER (सफ़ीर)</div>
                <div class="meaning">: SECURE AUDIT & FINAL EXECUTION REPORT</div>
            </div>
        </div>
    </div>

    <div class="dashboard">
        <div class="card">
            <span class="card-label">EQUITY</span>
            <div class="card-value">$42,500.85</div>
        </div>
        <div class="card">
            <span class="card-label">CANDLE DATA</span>
            <div class="card-value">14,400 PTS</div>
        </div>
        <div class="card">
            <span class="card-label">NET QTY (DASTAK)</span>
            <div class="card-value highlight">+1.45820</div>
        </div>
        <div class="card">
            <span class="card-label">GAP (SAFEER)</span>
            <div class="card-value" style="color: #00ff00;">0.00000</div>
        </div>
    </div>

</body>
</html>
