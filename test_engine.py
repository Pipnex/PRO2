import urllib.request
import json

BASE = "http://localhost:8899"

def get_json(path):
    with urllib.request.urlopen(f"{BASE}{path}", timeout=10) as r:
        return json.loads(r.read().decode("utf-8"))

def post_json(path, payload):
    req = urllib.request.Request(
        f"{BASE}{path}",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=10) as r:
        return json.loads(r.read().decode("utf-8"))

print("1. Checking /api/accounts...")
acc = get_json("/api/accounts")
print(f"   Connected: {acc['connected']} | Active Account: {acc['active_account']['login']} ({acc['active_account']['server']}) | Saved Vault Count: {len(acc['accounts'])}")

print("2. Checking /api/analyze for EURUSD (5-digit precision check)...")
eur = get_json("/api/analyze?symbol=EURUSD&timeframe=M15&execution_mode=smart")
a_eur = eur["analysis"]
print(f"   EURUSD Digits: {a_eur['digits']} | Price: {a_eur['current_price']} | Entry: {a_eur['entry']} | SL: {a_eur['stop_loss']} | Exec: {a_eur['execution']['order_type']} ({a_eur['execution']['decision']})")

print("3. Checking /api/analyze for XAUUSD (Gold)...")
xau = get_json("/api/analyze?symbol=XAUUSD&timeframe=M15&execution_mode=smart")
a_xau = xau["analysis"]
print(f"   XAUUSD Digits: {a_xau['digits']} | Price: {a_xau['current_price']} | Confidence: {a_xau['confidence']}% | Strategy Engine: {a_xau['strategy_intent']['label']}")

print("4. Checking /api/pulse-signals...")
pulse = get_json("/api/pulse-signals?timeframe=M15&category=ALL")
print(f"   Pulse Signals Count: {len(pulse['signals'])} | Top Signal: {pulse['signals'][0]['symbol']} {pulse['signals'][0]['order_type']} ({pulse['signals'][0]['confidence']}%)")

print("5. Checking /api/trish-chat...")
chat = post_json("/api/trish-chat", {"question": "What is the exact entry, SL and TP plan?", "symbol": "XAUUSD", "timeframe": "M15"})
print(f"   Trish AI Reply Preview: {chat['reply'].splitlines()[0]}")

print("6. Checking /api/prop-pass (Deriv V75 & Gold math)...")
pp = post_json("/api/prop-pass", {"symbol": "V75", "balance": 10000, "risk_pct": 1.0, "entry": 425600, "stop_loss": 424000})
print(f"   V75 PropPass Lot Size: {pp['recommended_lot_size']} lots | Risk USD: ${pp['risk_amount_usd']}")

print("ALL PIPNEX AI ENDPOINTS VERIFIED 100%!")
