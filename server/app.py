import os
import sys
import json
import base64
from aiohttp import web
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def default_json_serializer(obj):
    if isinstance(obj, (np.integer,)):
        return int(obj)
    if isinstance(obj, (np.floating,)):
        return float(obj)
    if isinstance(obj, (np.bool_,)):
        return bool(obj)
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    return str(obj)


def json_response(data, status=200):
    return web.Response(
        text=json.dumps(data, default=default_json_serializer),
        status=status,
        content_type="application/json",
    )


from core.confidence_engine import ConfidenceEngine
from core.prop_pass_calc import calculate_prop_pass_risk, get_symbol_digits
from core.chart_vision import ChartVisionEngine
from core.auto_trader import AutoTraderDaemon
from core.newsiq_engine import NewsIQEngine
from core.momo_engine import momo_engine, PACKAGES
from mt5.mt5_bridge import MT5Bridge

bridge = MT5Bridge()
confidence_engine = ConfidenceEngine()
vision_engine = ChartVisionEngine()
newsiq_engine = NewsIQEngine()
auto_trader = AutoTraderDaemon(bridge=bridge, confidence_engine=confidence_engine, newsiq_engine=newsiq_engine)

WEB_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "web")

PULSE_CATALOG = [
    {"symbol": "XAUUSD", "category": "Metals", "name": "Gold vs US Dollar"},
    {"symbol": "EURUSD", "category": "Forex", "name": "Euro vs US Dollar"},
    {"symbol": "GBPUSD", "category": "Forex", "name": "British Pound vs USD"},
    {"symbol": "USDJPY", "category": "Forex", "name": "US Dollar vs Yen"},
    {"symbol": "GBPJPY", "category": "Forex", "name": "Pound vs Japanese Yen"},
    {"symbol": "BTCUSD", "category": "Crypto", "name": "Bitcoin vs USD"},
    {"symbol": "ETHUSD", "category": "Crypto", "name": "Ethereum vs USD"},
    {"symbol": "NAS100", "category": "Indices", "name": "Nasdaq 100 Tech Index"},
    {"symbol": "US30", "category": "Indices", "name": "Dow Jones 30 Index"},
    {"symbol": "V75", "category": "Synthetics", "name": "Deriv Volatility 75 Index"},
    {"symbol": "BOOM1000", "category": "Synthetics", "name": "Deriv Boom 1000 Index"},
    {"symbol": "CRASH1000", "category": "Synthetics", "name": "Deriv Crash 1000 Index"},
]


async def index_handler(request):
    return web.FileResponse(os.path.join(WEB_DIR, "index.html"))


async def api_status(request):
    status = bridge.initialize()
    return json_response(status)


async def api_accounts_list(request):
    return json_response(bridge.list_accounts())


async def api_accounts_connect(request):
    data = await request.json()
    login = data.get("login", "")
    password = data.get("password", "")
    server = data.get("server", "")
    label = data.get("label", "")
    res = bridge.connect_account(login=login, password=password, server=server, label=label)
    return json_response(res)


async def api_accounts_switch(request):
    data = await request.json()
    login = data.get("login", 0)
    res = bridge.switch_account(login=login)
    return json_response(res)


async def api_accounts_remove(request):
    data = await request.json()
    login = data.get("login", 0)
    res = bridge.remove_account(login=login)
    return json_response(res)


async def api_positions(request):
    positions = bridge.get_open_positions()
    history = bridge.get_trade_history(days=30)
    status = bridge.initialize()
    return json_response({
        "account": status.get("account"),
        "open_positions": positions,
        "history": history,
    })


async def api_positions_close(request):
    data = await request.json()
    ticket = int(data.get("ticket", 0))
    res = bridge.close_position(ticket)
    return json_response(res)


async def api_analyze(request):
    symbol = request.query.get("symbol", "XAUUSD").upper()
    timeframe = request.query.get("timeframe", "M15").upper()
    execution_mode = request.query.get("execution_mode", "smart").lower()
    strategy_style = request.query.get("strategy_style", "auto").lower()

    df = bridge.get_candles(symbol=symbol, timeframe=timeframe, count=220)
    analysis = confidence_engine.analyze(
        df,
        symbol=symbol,
        timeframe=timeframe,
        execution_mode=execution_mode,
        strategy_style=strategy_style,
    )
    digits = get_symbol_digits(symbol)

    candles = []
    for _, row in df.iterrows():
        candles.append({
            "time": int(row["time"]),
            "open": round(float(row["open"]), digits),
            "high": round(float(row["high"]), digits),
            "low": round(float(row["low"]), digits),
            "close": round(float(row["close"]), digits),
        })

    return json_response({"candles": candles, "analysis": analysis})


async def api_pulse_signals(request):
    timeframe = request.query.get("timeframe", "M15").upper()
    category_filter = request.query.get("category", "ALL").upper()

    signals = []
    for item in PULSE_CATALOG:
        if category_filter != "ALL" and item["category"].upper() != category_filter:
            continue
        sym = item["symbol"]
        df = bridge.get_candles(symbol=sym, timeframe=timeframe, count=140)
        res = confidence_engine.analyze(df, symbol=sym, timeframe=timeframe, execution_mode="smart")
        signals.append({
            "symbol": sym,
            "name": item["name"],
            "category": item["category"],
            "timeframe": timeframe,
            "digits": res["digits"],
            "current_price": res["current_price"],
            "direction": res["direction"],
            "order_type": res["execution"]["order_type"],
            "execution_decision": res["execution"]["decision"],
            "confidence": res["confidence"],
            "grade": res["grade"],
            "entry": res["entry"],
            "stop_loss": res["stop_loss"],
            "take_profit_1": res["take_profit_1"],
            "take_profit_2": res["take_profit_2"],
            "risk_reward": res["risk_reward"],
            "trend": res["market_structure"]["trend"],
            "zone": res["market_structure"]["dealing_range"]["zone"],
            "strategy_engine": res["strategy_intent"]["label"],
            "top_reason": res["reasons"][0] if res["reasons"] else "Institutional Confluence",
        })

    signals.sort(key=lambda x: x["confidence"], reverse=True)
    return json_response({"signals": signals})


async def api_trish_chat(request):
    data = await request.json()
    question = str(data.get("question", "")).strip()
    symbol = str(data.get("symbol", "XAUUSD")).upper()
    timeframe = str(data.get("timeframe", "M15")).upper()

    df = bridge.get_candles(symbol=symbol, timeframe=timeframe, count=180)
    a = confidence_engine.analyze(df, symbol=symbol, timeframe=timeframe, execution_mode="smart")
    q_low = question.lower()

    if any(k in q_low for k in ("entry", "buy", "sell", "trade", "signal", "setup")):
        reply = (
            f"**Trish AI Trade Plan for {symbol} ({timeframe}):**\n"
            f"• **Action:** `{a['execution']['order_type']}` ({a['grade']} Setup — {a['confidence']}% Confidence)\n"
            f"• **Entry Price:** `{a['entry']}` (Current: `{a['current_price']}`)\n"
            f"• **Stop Loss:** `{a['stop_loss']}` | **TP1:** `{a['take_profit_1']}` | **TP2:** `{a['take_profit_2']}` ({a['risk_reward']}:1 R:R)\n"
            f"• **Execution Logic:** {a['execution']['reasons'][0] if a['execution']['reasons'] else 'Smart Mode active.'}"
        )
    elif any(k in q_low for k in ("risk", "lot", "prop", "drawdown", "balance")):
        acc = bridge.account_info or {"balance": 10000}
        bal = float(acc.get("balance", 10000))
        rk = calculate_prop_pass_risk(bal, 1.0, a["entry"], a["stop_loss"], symbol)
        reply = (
            f"**Trish AI Risk & PropPass™ Check ({symbol}):**\n"
            f"• **Active Balance:** `${bal:,.2f}`\n"
            f"• **1% Safe Lot Size:** `{rk['recommended_lot_size']} lots` (Risking `${rk['risk_amount_usd']}` over `{rk['stop_loss_pips']} pips`)\n"
            f"• **Prop Status:** `{rk['safety_status']}` ({rk['Drawdown_Buffer_Remaining']} buffer remaining before daily limit)."
        )
    elif any(k in q_low for k in ("news", "cpi", "nfp", "fomc", "calendar", "event")):
        guard = newsiq_engine.get_guard_status()
        signals = newsiq_engine.generate_news_signals()
        top_sig = signals[0] if signals else None
        if top_sig:
            inst = top_sig.get("institutional_prediction", {})
            sig_text = (
                f"• **Top Institutional Setup:** {top_sig['event_title']} ({top_sig['country']})\n"
                f"• **Consensus Prediction:** `{inst.get('direction', 'SELL')}` on `{top_sig['primary_symbol']}` with **{inst.get('confidence', 80)}% Institutional Confidence**\n"
                f"• **Global Sources:** {inst.get('sources', 'Wall Street Consensus')}\n"
                f"• **Execution Strategy:** `{top_sig['strategy']['action']}` ({top_sig['strategy']['name']} {top_sig['strategy']['timeframe']})\n"
                f"• **Scenario Trigger:** {inst.get('hot_scenario', '')}"
            )
        else:
            sig_text = "• No imminent high-impact setups."
        reply = (
            f"**Trish AI NewsIQ™ Institutional Macro Intelligence:**\n"
            f"• **Auto-Guard Status:** {guard.get('badge', 'SAFE')}\n"
            f"• **Macro Window:** {guard.get('reason')}\n"
            f"{sig_text}\n"
            f"• **Institutional Rule:** Avoid entries 15-30m before and after high-impact USD events; fade the spike exhaustion after liquidity sweep."
        )
    elif any(k in q_low for k in ("why", "structure", "smc", "ob", "fvg", "reason", "trend")):
        reasons_bullets = "\n".join([f"• {r}" for r in a["reasons"][:4]])
        reply = (
            f"**Trish AI Institutional Confluence Breakdown ({symbol} {timeframe}):**\n"
            f"• **Market Structure:** `{a['market_structure']['trend']}` in `{a['market_structure']['dealing_range']['zone']}` (EQ: `{a['market_structure']['dealing_range']['equilibrium']}`)\n"
            f"• **Active Engine:** {a['strategy_intent']['icon']} {a['strategy_intent']['label']}\n"
            f"{reasons_bullets}"
        )
    else:
        reply = (
            f"**Trish AI Live Summary ({symbol} {timeframe}):**\n"
            f"{a['trish_summary']}\n\n"
            f"Key Confluences: {'; '.join(a['reasons'][:3])}. You can ask me about **Entry/TP levels**, **Lot Size & Risk**, or **Why this SMC setup formed**."
        )

    return json_response({"reply": reply, "analysis": a})


async def api_prop_pass(request):
    data = await request.json()
    res = calculate_prop_pass_risk(
        account_balance=float(data.get("balance", 10000)),
        risk_pct=float(data.get("risk_pct", 1.0)),
        entry_price=float(data.get("entry", 2735.0)),
        stop_loss=float(data.get("stop_loss", 2728.0)),
        symbol=data.get("symbol", "XAUUSD"),
        daily_dd_limit_pct=float(data.get("daily_dd_limit_pct", 5.0)),
        current_daily_dd_pct=float(data.get("current_daily_dd_pct", 0.0)),
    )
    return json_response(res)


async def api_execute(request):
    data = await request.json()
    symbol = data.get("symbol", "XAUUSD").upper()
    timeframe = data.get("timeframe", "M15").upper()
    lot_size = float(data.get("lots", 0.01))
    execution_mode = data.get("execution_mode", "smart").lower()

    df = bridge.get_candles(symbol=symbol, timeframe=timeframe, count=220)
    setup = confidence_engine.analyze(df, symbol=symbol, timeframe=timeframe, execution_mode=execution_mode)
    result = bridge.execute_signal(setup, lot_size=lot_size)
    return json_response({"execution": result, "setup": setup})


async def api_vision(request):
    data = await request.json()
    b64_str = data.get("image_base64", "")
    filename = data.get("filename", "uploaded_chart.png")

    if "," in b64_str:
        b64_str = b64_str.split(",", 1)[1]

    img_bytes = base64.b64decode(b64_str)
    result = vision_engine.analyze_image(img_bytes, filename=filename)
    return json_response(result)


async def api_autotrade_status(request):
    return json_response(auto_trader.get_status())


async def api_autotrade_config(request):
    data = await request.json()
    status = auto_trader.update_config(data)
    return json_response(status)


async def api_autotrade_test_trade(request):
    data = await request.json()
    symbol = data.get("symbol", "XAUUSD").upper()
    res = auto_trader.execute_test_trade(symbol=symbol)
    return json_response(res)


async def api_autotrade_clear_history(request):
    res = auto_trader.clear_history()
    return json_response(res)


async def api_newsiq_events(request):
    force = request.query.get("refresh", "0") in ("1", "true")
    events = newsiq_engine.fetch_calendar(force_refresh=force)
    return json_response({"events": events, "count": len(events)})


async def api_newsiq_signals(request):
    signals = newsiq_engine.generate_news_signals()
    return json_response({"signals": signals, "count": len(signals)})


async def api_newsiq_guard(request):
    guard = newsiq_engine.get_guard_status()
    return json_response(guard)


# =============================================================================
# MOBILE MONEY (UGX) SUBSCRIPTION & PAYMENT ENDPOINTS (MTN / Airtel Uganda)
# =============================================================================
async def api_subscribe_packages(request):
    return json_response({"packages": PACKAGES})


async def api_subscribe(request):
    try:
        data = await request.json()
        phone_number = data.get("phoneNumber")
        package_id = data.get("packageId")
        email = data.get("email")

        if not phone_number or not package_id:
            return json_response({"message": "phoneNumber and packageId are required"}, status=400)

        selected_package = PACKAGES.get(package_id)
        if not selected_package:
            return json_response({"message": "Package not found"}, status=404)

        result = await momo_engine.initiate_mobile_money_payment(
            phone_number=phone_number,
            package_id=package_id,
            email=email
        )
        return json_response(result)
    except Exception as e:
        return json_response({"message": str(e)}, status=500)


async def api_subscribe_status(request):
    tx_ref = request.match_info.get("tx_ref")
    status_info = momo_engine.get_transaction_status(tx_ref)
    return json_response(status_info)


async def api_subscribe_simulate_approve(request):
    try:
        data = await request.json()
        tx_ref = data.get("tx_ref")
        result = momo_engine.simulate_approval(tx_ref)
        return json_response(result)
    except Exception as e:
        return json_response({"message": str(e)}, status=500)


async def api_subscribe_user_status(request):
    phone = request.query.get("phone", "")
    info = momo_engine.get_user_subscription(phone)
    return json_response(info)


async def api_payments_webhook(request):
    try:
        payload = await request.json()
        data = payload.get("data", {})
        tx_ref = data.get("tx_ref") or payload.get("tx_ref")
        if tx_ref:
            momo_engine.simulate_approval(tx_ref)
        return json_response({"status": "SUCCESS"})
    except Exception as e:
        return json_response({"error": str(e)}, status=500)


@web.middleware
async def cors_middleware(request, handler):
    if request.method == "OPTIONS":
        resp = web.Response()
    else:
        try:
            resp = await handler(request)
        except Exception as e:
            resp = json_response({"error": str(e)}, status=500)
    resp.headers["Access-Control-Allow-Origin"] = "*"
    resp.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    resp.headers["Access-Control-Allow-Headers"] = "Content-Type"
    return resp


def create_app():
    app = web.Application(middlewares=[cors_middleware], client_max_size=25 * 1024 * 1024)
    app.router.add_get("/", index_handler)
    app.router.add_get("/api/status", api_status)
    app.router.add_get("/api/accounts", api_accounts_list)
    app.router.add_post("/api/accounts/connect", api_accounts_connect)
    app.router.add_post("/api/accounts/switch", api_accounts_switch)
    app.router.add_post("/api/accounts/remove", api_accounts_remove)
    app.router.add_get("/api/positions", api_positions)
    app.router.add_post("/api/positions/close", api_positions_close)
    app.router.add_get("/api/analyze", api_analyze)
    app.router.add_get("/api/pulse-signals", api_pulse_signals)
    app.router.add_post("/api/trish-chat", api_trish_chat)
    app.router.add_post("/api/prop-pass", api_prop_pass)
    app.router.add_post("/api/execute", api_execute)
    app.router.add_post("/api/vision", api_vision)
    app.router.add_get("/api/autotrade/status", api_autotrade_status)
    app.router.add_post("/api/autotrade/config", api_autotrade_config)
    app.router.add_post("/api/autotrade/test-trade", api_autotrade_test_trade)
    app.router.add_post("/api/autotrade/clear-history", api_autotrade_clear_history)
    app.router.add_get("/api/newsiq/events", api_newsiq_events)
    app.router.add_get("/api/newsiq/signals", api_newsiq_signals)
    app.router.add_get("/api/newsiq/guard", api_newsiq_guard)
    app.router.add_get("/api/subscribe/packages", api_subscribe_packages)
    app.router.add_post("/api/subscribe", api_subscribe)
    app.router.add_get("/api/subscribe/status/{tx_ref}", api_subscribe_status)
    app.router.add_post("/api/subscribe/simulate-approve", api_subscribe_simulate_approve)
    app.router.add_get("/api/subscribe/user-status", api_subscribe_user_status)
    app.router.add_post("/api/payments/webhook", api_payments_webhook)
    app.router.add_static("/static", WEB_DIR)
    return app


if __name__ == "__main__":
    print("=" * 68)
    print("  PIPNEX AI — INSTITUTIONAL SMC & MULTI-ACCOUNT MT5 ENGINE")
    print("  Dashboard URL : http://localhost:8899")
    print("=" * 68)
    web.run_app(create_app(), host="0.0.0.0", port=8899)
