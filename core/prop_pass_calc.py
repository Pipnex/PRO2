"""
Pipnex AI - Exact Instrument Specifications, Risk Calculator & PropPass™ Engine
Reconstructed directly from Pipnex AI's riskCalculator specification table.
Supports Forex, Metals, Crypto, Indices, and Deriv Synthetics.
"""

from typing import Dict, Any

INSTRUMENT_SPECS: Dict[str, Dict[str, Any]] = {
    # Forex Majors & Crosses
    "EURUSD": {"pipValue": 10.0, "pipSize": 0.0001, "minLot": 0.01, "lotStep": 0.01, "digits": 5, "category": "Forex", "label": "EUR/USD"},
    "GBPUSD": {"pipValue": 10.0, "pipSize": 0.0001, "minLot": 0.01, "lotStep": 0.01, "digits": 5, "category": "Forex", "label": "GBP/USD"},
    "AUDUSD": {"pipValue": 10.0, "pipSize": 0.0001, "minLot": 0.01, "lotStep": 0.01, "digits": 5, "category": "Forex", "label": "AUD/USD"},
    "NZDUSD": {"pipValue": 10.0, "pipSize": 0.0001, "minLot": 0.01, "lotStep": 0.01, "digits": 5, "category": "Forex", "label": "NZD/USD"},
    "USDCAD": {"pipValue": 7.5,  "pipSize": 0.0001, "minLot": 0.01, "lotStep": 0.01, "digits": 5, "category": "Forex", "label": "USD/CAD"},
    "USDCHF": {"pipValue": 11.0, "pipSize": 0.0001, "minLot": 0.01, "lotStep": 0.01, "digits": 5, "category": "Forex", "label": "USD/CHF"},
    "USDJPY": {"pipValue": 6.5,  "pipSize": 0.01,   "minLot": 0.01, "lotStep": 0.01, "digits": 3, "category": "Forex", "label": "USD/JPY"},
    "EURGBP": {"pipValue": 12.5, "pipSize": 0.0001, "minLot": 0.01, "lotStep": 0.01, "digits": 5, "category": "Forex", "label": "EUR/GBP"},
    "EURJPY": {"pipValue": 6.5,  "pipSize": 0.01,   "minLot": 0.01, "lotStep": 0.01, "digits": 3, "category": "Forex", "label": "EUR/JPY"},
    "GBPJPY": {"pipValue": 6.5,  "pipSize": 0.01,   "minLot": 0.01, "lotStep": 0.01, "digits": 3, "category": "Forex", "label": "GBP/JPY"},
    "AUDJPY": {"pipValue": 6.5,  "pipSize": 0.01,   "minLot": 0.01, "lotStep": 0.01, "digits": 3, "category": "Forex", "label": "AUD/JPY"},
    # Metals
    "XAUUSD": {"pipValue": 100.0, "pipSize": 0.01,  "minLot": 0.01, "lotStep": 0.01, "digits": 2, "category": "Metals", "label": "XAU/USD (Gold)"},
    "XAGUSD": {"pipValue": 50.0,  "pipSize": 0.001, "minLot": 0.01, "lotStep": 0.01, "digits": 3, "category": "Metals", "label": "XAG/USD (Silver)"},
    # Crypto
    "BTCUSD": {"pipValue": 1.0,   "pipSize": 1.0,   "minLot": 0.01, "lotStep": 0.01, "digits": 2, "category": "Crypto", "label": "BTC/USD"},
    "ETHUSD": {"pipValue": 1.0,   "pipSize": 0.1,   "minLot": 0.01, "lotStep": 0.01, "digits": 2, "category": "Crypto", "label": "ETH/USD"},
    # Indices
    "US30":   {"pipValue": 1.0,   "pipSize": 1.0,   "minLot": 0.01, "lotStep": 0.01, "digits": 2, "category": "Indices", "label": "US30 (Dow Jones)"},
    "NAS100": {"pipValue": 1.0,   "pipSize": 1.0,   "minLot": 0.01, "lotStep": 0.01, "digits": 2, "category": "Indices", "label": "NAS100 (Nasdaq)"},
    # Synthetics (Deriv)
    "V10":       {"pipValue": 0.01, "pipSize": 0.01, "minLot": 0.50, "lotStep": 0.01, "digits": 2, "category": "Synthetic", "label": "Volatility 10 Index"},
    "V25":       {"pipValue": 0.01, "pipSize": 0.01, "minLot": 0.50, "lotStep": 0.01, "digits": 2, "category": "Synthetic", "label": "Volatility 25 Index"},
    "V50":       {"pipValue": 0.01, "pipSize": 0.01, "minLot": 4.00, "lotStep": 0.01, "digits": 2, "category": "Synthetic", "label": "Volatility 50 Index"},
    "V75":       {"pipValue": 0.01, "pipSize": 0.01, "minLot": 0.01, "lotStep": 0.01, "digits": 2, "category": "Synthetic", "label": "Volatility 75 Index"},
    "V100":      {"pipValue": 0.01, "pipSize": 0.01, "minLot": 0.50, "lotStep": 0.01, "digits": 2, "category": "Synthetic", "label": "Volatility 100 Index"},
    "V75_1S":    {"pipValue": 0.01, "pipSize": 0.01, "minLot": 0.05, "lotStep": 0.01, "digits": 2, "category": "Synthetic", "label": "Volatility 75 (1s)"},
    "BOOM_500":  {"pipValue": 0.01, "pipSize": 0.01, "minLot": 0.20, "lotStep": 0.01, "digits": 2, "category": "Synthetic", "label": "Boom 500 Index"},
    "BOOM_1000": {"pipValue": 0.01, "pipSize": 0.01, "minLot": 0.20, "lotStep": 0.01, "digits": 2, "category": "Synthetic", "label": "Boom 1000 Index"},
    "CRASH_500": {"pipValue": 0.01, "pipSize": 0.01, "minLot": 0.20, "lotStep": 0.01, "digits": 2, "category": "Synthetic", "label": "Crash 500 Index"},
    "CRASH_1000":{"pipValue": 0.01, "pipSize": 0.01, "minLot": 0.20, "lotStep": 0.01, "digits": 2, "category": "Synthetic", "label": "Crash 1000 Index"},
    "STEP":      {"pipValue": 0.10, "pipSize": 0.10, "minLot": 0.10, "lotStep": 0.01, "digits": 2, "category": "Synthetic", "label": "Step Index"},
    "JUMP_50":   {"pipValue": 0.01, "pipSize": 0.01, "minLot": 0.01, "lotStep": 0.01, "digits": 2, "category": "Synthetic", "label": "Jump 50 Index"},
}

PROP_FIRM_PROFILES = {
    "FTMO": {"max_daily_loss_pct": 5.0, "max_total_loss_pct": 10.0, "profit_target_pct": 10.0},
    "FundedNext": {"max_daily_loss_pct": 5.0, "max_total_loss_pct": 10.0, "profit_target_pct": 8.0},
    "AlphaCapital": {"max_daily_loss_pct": 4.0, "max_total_loss_pct": 8.0, "profit_target_pct": 8.0},
    "The5ers": {"max_daily_loss_pct": 5.0, "max_total_loss_pct": 10.0, "profit_target_pct": 8.0},
    "Standard": {"max_daily_loss_pct": 5.0, "max_total_loss_pct": 10.0, "profit_target_pct": 10.0},
}


def get_instrument_spec(symbol: str) -> Dict[str, Any]:
    s = str(symbol or "XAUUSD").upper().rstrip("M")
    spec = None
    if s in INSTRUMENT_SPECS:
        spec = dict(INSTRUMENT_SPECS[s])
    else:
        s_clean = s.replace("_", "")
        for k, v in INSTRUMENT_SPECS.items():
            if k.replace("_", "") == s_clean:
                spec = dict(v)
                break
    if spec is None:
        if "JPY" in s:
            spec = {"pipValue": 6.5, "pipSize": 0.01, "minLot": 0.01, "lotStep": 0.01, "digits": 3, "category": "Forex", "label": s}
        elif "XAU" in s or "GOLD" in s:
            spec = {"pipValue": 100.0, "pipSize": 0.01, "minLot": 0.01, "lotStep": 0.01, "digits": 2, "category": "Metals", "label": s}
        elif s.startswith("V") or any(w in s for w in ["BOOM", "CRASH", "JUMP", "STEP", "RANGE", "DEX", "DSI"]):
            spec = {"pipValue": 0.01, "pipSize": 0.01, "minLot": 0.01, "lotStep": 0.01, "digits": 2, "category": "Synthetic", "label": s}
        else:
            spec = {"pipValue": 10.0, "pipSize": 0.0001, "minLot": 0.01, "lotStep": 0.01, "digits": 5, "category": "Forex", "label": s}

    spec["pip_size"] = spec["pipSize"]
    spec["pip_value"] = spec["pipValue"]
    return spec


def get_symbol_digits(symbol: str) -> int:
    return get_instrument_spec(symbol)["digits"]


def calculate_prop_pass_risk(
    account_balance: float = 10000.0,
    risk_pct: float = None,
    entry_price: float = 2735.0,
    stop_loss: float = 2728.0,
    symbol: str = "XAUUSD",
    daily_dd_limit_pct: float = 5.0,
    current_daily_dd_pct: float = 0.0,
    risk_percent: float = None,
    prop_firm: str = "FTMO",
) -> Dict[str, Any]:
    """
    Exact Pipnex riskCalculator math across Forex, Metals, Crypto, Indices, and Synthetics.
    """
    effective_risk_pct = float(risk_pct if risk_pct is not None else (risk_percent if risk_percent is not None else 1.0))
    spec = get_instrument_spec(symbol)
    profile = PROP_FIRM_PROFILES.get(prop_firm, PROP_FIRM_PROFILES["Standard"])

    risk_amount = account_balance * (effective_risk_pct / 100.0)
    sl_distance = abs(entry_price - stop_loss)
    if sl_distance <= 0:
        sl_distance = spec["pipSize"] * 50.0

    sl_pips = sl_distance / spec["pipSize"]

    if spec["category"] == "Synthetic":
        raw_lot = risk_amount / (sl_pips * spec["pipValue"])
    elif spec["category"] == "Metals" and "XAU" in symbol.upper():
        raw_lot = risk_amount / (sl_distance * 100.0)
    else:
        raw_lot = risk_amount / (sl_pips * spec["pipValue"])

    lot_step = spec["lotStep"]
    rounded_lot = round(raw_lot / lot_step) * lot_step
    is_min_lot = rounded_lot < spec["minLot"]
    final_lot = max(spec["minLot"], min(100.0, rounded_lot))
    decimals = 3 if lot_step < 0.01 else 2
    final_lot = round(final_lot, decimals)

    max_daily_loss_dollars = account_balance * (daily_dd_limit_pct / 100.0)
    max_total_loss_dollars = account_balance * (profile["max_total_loss_pct"] / 100.0)
    remaining_dd_pct = max(0.0, daily_dd_limit_pct - current_daily_dd_pct - effective_risk_pct)

    is_safe = (current_daily_dd_pct + effective_risk_pct) <= (daily_dd_limit_pct * 0.85)
    safety_status = "SAFE FOR PROP CHALLENGE" if is_safe else "HIGH DRAWDOWN WARNING"

    return {
        "symbol": symbol,
        "account_balance": round(account_balance, 2),
        "risk_pct": effective_risk_pct,
        "risk_percent": effective_risk_pct,
        "risk_amount_usd": round(risk_amount, 2),
        "risk_dollar_amount": round(risk_amount, 2),
        "stop_loss_pips": round(sl_pips, 1),
        "sl_pips": round(sl_pips, 1),
        "recommended_lot_size": final_lot,
        "max_daily_loss_allowed_usd": round(max_daily_loss_dollars, 2),
        "Drawdown_Buffer_Remaining": f"{round(remaining_dd_pct, 2)}%",
        "safety_status": safety_status,
        "spec": spec,
        "limits": {
            "max_daily_loss": round(max_daily_loss_dollars, 2),
            "max_total_loss": round(max_total_loss_dollars, 2),
        },
    }
