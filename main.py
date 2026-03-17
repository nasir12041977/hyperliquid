# 2. ORDER HANDLER
if data.get("type") == "order":
    exchange = get_exchange()
    if not exchange:
        return jsonify({"error": "Environment Variables not set"}), 500
    
    # मार्केट मेटा डेटा लेना ताकि इंडेक्स से नाम मिल सके
    info = exchange.info
    meta = info.meta()
    universe = meta['universe'] # यहाँ सारे कॉइन्स की लिस्ट होती है

    orders = data.get("orders", [])
    hl_orders = []

    for o in orders:
        # यहाँ इंडेक्स का इस्तेमाल करके कॉइन का नाम ढूँढना
        asset_index = int(o["asset"])
        if asset_index < len(universe):
            coin_name = universe[asset_index]['name']
            
            hl_orders.append({
                "coin": coin_name, # अब यहाँ असली नाम जाएगा (जैसे "BTC")
                "is_buy": bool(o["isBuy"]),
                "sz": float(o["sz"]),
                "px": float(o["limitPx"]),
                "order_type": {"limit": {"tif": "Gtc"}},
                "reduce_only": bool(o["reduceOnly"])
            })

    if hl_orders:
        response = exchange.bulk_orders(hl_orders)
        return jsonify(response), 200
