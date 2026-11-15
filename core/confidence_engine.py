import pandas as pd
import numpy as np
from .market_structure import analyze_market_structure
from .order_blocks import find_order_blocks
from .fair_value_gaps import find_fair_value_gaps
from .liquidity_sweeps import find_liquidity_sweeps
from .prop_pass_calc import get_symbol_digits, get_instrument_spec


STRATEGY_ENGINES = {
    "trend": {
        "id": "trend",
        "label": "Trend Engine",
        "icon": "📈",
        "description": "Identifies directional momentum using multi-timeframe EMA alignment, BOS continuation, and pullback entries.",
    },
    "scalping": {
        "id": "scalping",
        "label": "Scalping Engine",
        "icon": "⚡",
        "description": "Captures rapid micro-movements on M1–M15 using tight stops, momentum bursts, and quick profit targets.",
    },
    "range": {
        "id": "range",
        "label": "Range Engine",
        "icon": "↔️",
        "description": "Trades mean-reversion within consolidated support/resistance channels using oscillator extremes and liquidity sweeps.",
    },
    "breakout": {
        "id": "breakout",
        "label": "Breakout Engine",
        "icon": "💥",
        "description": "Detects high-energy breaks of key structure levels validated by volume expansion and volatility spikes.",
    },
    "intraday": {
        "id": "intraday",
        "label": "Intraday Momentum Engine",
        "icon": "🔄",
        "description": "Combines session-based directional bias with FVG and Order Block confluence for M15–H1 setups.",
    },
    "swing": {
        "id": "swing",
        "label": "Swing Engine",
        "icon": "🏄",
        "description": "Targets multi-day structural moves on H4–D1 using institutional order flow and macro Fibonacci zones.",
    },
}


def classify_strategy_intent(timeframe: str = "M15", style: str = "auto", rr_ratio: float = 2.0) -> dict:
    """
    Exact Pipnex Strategy Intent Classifier (from strategyIntentEngine-DXIlHaQb.js).
    """
    tf = (timeframe or "M15").upper()
    style_lower = (style or "auto").lower()

    if style_lower in STRATEGY_ENGINES:
        engine = STRATEGY_ENGINES[style_lower]
        return {**engine, "confidence": 92}

    if tf in ("M1", "M5"):
        return {**STRATEGY_ENGINES["scalping"], "confidence": 90}
    if tf in ("H4", "D1"):
        if rr_ratio >= 2.5:
            return {**STRATEGY_ENGINES["swing"], "confidence": 89}
        return {**STRATEGY_ENGINES["trend"], "confidence": 86}
    if tf == "H1":
        return {**STRATEGY_ENGINES["trend"], "confidence": 88}
    return {**STRATEGY_ENGINES["intraday"], "confidence": 87}


class ConfidenceEngine:
    """
    Pipnex AI Multi-Factor Institutional Confidence Scoring Engine
    + Exact Pipnex Order Execution Decision Engine ($s from TradingChart-CyJfNxim.js)
    """

    def __init__(self, swing_length: int = 5):
        self.swing_length = swing_length

    def evaluate_execution_mode(
        self,
        df: pd.DataFrame,
        mode: str,
        direction: str,
        entry: float,
        stop_loss: float,
        tp1: float,
        timeframe: str,
        symbol: str,
        latest_price: float,
        atr: float,
    ) -> dict:
        """
        Reconstructs Pipnex's exact Order Execution Decision Engine (function $s in TradingChart-CyJfNxim.js).
        """
        mode_clean = (mode or "smart").lower()
        is_buy = direction in ("BUY", "BULLISH")

        if mode_clean == "precision":
            return {
                "mode": "precision",
                "decision": "LIMIT",
                "order_type": "BUY_LIMIT" if is_buy else "SELL_LIMIT",
                "reasons": ["Precision Mode active — waiting for exact limit entry at institutional zone"],
                "checks": {
                    "volatility": False,
                    "bos": False,
                    "zone": True,
                    "scalping": False,
                    "proximity": False,
                },
                "market_score": 0,
                "limit_score": 10,
            }

        if mode_clean == "aggressive":
            return {
                "mode": "aggressive",
                "decision": "MARKET",
                "order_type": "BUY" if is_buy else "SELL",
                "reasons": ["Aggressive Mode active — immediate market execution"],
                "checks": {
                    "volatility": True,
                    "bos": True,
                    "zone": False,
                    "scalping": True,
                    "proximity": True,
                },
                "market_score": 10,
                "limit_score": 0,
            }

        # Smart Mode: 5-Factor Scoring ($s)
        reasons = []
        market_score = 0
        limit_score = 0

        # 1. Price Proximity Check
        price_diff = abs(latest_price - entry)
        prox_threshold = atr * 0.3 if atr > 0 else abs(entry - stop_loss) * 0.25
        proximity_ok = bool(price_diff <= prox_threshold)
        if proximity_ok:
            market_score += 2
            reasons.append("Price at entry zone — immediate market execution favored")
        else:
            limit_score += 2
            reasons.append(f"Entry is {round(price_diff / max(atr, 1e-6), 1)}x ATR away — limit order awaits pullback")

        # 2. Scalping Override Check (As)
        spec = get_instrument_spec(symbol)
        pip_size = spec.get("pip_size", 0.0001)
        tp_pips = abs(tp1 - entry) / pip_size if pip_size > 0 else 50
        scalping_ok = bool(timeframe.upper() in ("M1", "M5") and tp_pips < 20)
        if scalping_ok:
            market_score += 3
            reasons.append(f"Scalping setup on {timeframe.upper()} ({round(tp_pips, 1)} pips TP) — fast market entry required")

        # 3. Volatility Gate Check (ws)
        atr_pct = (atr / latest_price) * 100.0 if latest_price > 0 else 0.0
        volatility_ok = bool(atr_pct > 0.15)
        if volatility_ok:
            market_score += 1
            reasons.append(f"High volatility (ATR {round(atr_pct, 2)}%) — momentum active")
        else:
            limit_score += 1
            reasons.append(f"Low volatility (ATR {round(atr_pct, 2)}%) — patient limit preferred")

        # 4. BOS Candle Check (Ss)
        bos_ok = False
        if len(df) >= 5:
            last = df.iloc[-1]
            prev3 = df.iloc[-4:-1]
            last_body = abs(float(last["close"]) - float(last["open"]))
            last_range = float(last["high"]) - float(last["low"])
            avg_body = float(np.mean(np.abs(prev3["close"].values - prev3["open"].values)))
            strong_body = last_body > (avg_body * 1.2) and last_range > 0
            if is_buy:
                close_pos = (float(last["close"]) - float(last["low"])) / last_range if last_range > 0 else 0
                broke_struct = float(last["close"]) > float(prev3["high"].max())
                bos_ok = bool(strong_body and close_pos >= 0.7 and broke_struct)
            else:
                close_pos = (float(last["high"]) - float(last["close"])) / last_range if last_range > 0 else 0
                broke_struct = float(last["close"]) < float(prev3["low"].min())
                bos_ok = bool(strong_body and close_pos >= 0.7 and broke_struct)

        if bos_ok:
            market_score += 2
            reasons.append("Strong BOS displacement candle detected — market entry")
        else:
            limit_score += 1
            reasons.append("No immediate displacement break — limit at structure level")

        # 5. Zone Confirmation Check (Ms)
        zone_ok = False
        if len(df) >= 2:
            last = df.iloc[-1]
            prev = df.iloc[-2]
            near_entry = abs(float(last["close"]) - entry) <= (atr * 0.5)
            if is_buy:
                zone_ok = bool(near_entry and float(last["close"]) > float(last["open"]) and float(last["close"]) > float(prev["high"]))
            else:
                zone_ok = bool(near_entry and float(last["close"]) < float(last["open"]) and float(last["close"]) < float(prev["low"]))

        if zone_ok:
            market_score += 1
            reasons.append("Zone rejection confirmed — market entry valid")
        else:
            limit_score += 1
            reasons.append("Awaiting zone confirmation — limit order safer")

        decision = "MARKET" if market_score > limit_score else "LIMIT"
        if decision == "MARKET":
            order_type = "BUY" if is_buy else "SELL"
        else:
            if is_buy and entry >= latest_price:
                order_type = "BUY"
                decision = "MARKET"
                reasons.append("Entry is at/above current price — upgraded to Market Buy")
            elif (not is_buy) and entry <= latest_price:
                order_type = "SELL"
                decision = "MARKET"
                reasons.append("Entry is at/below current price — upgraded to Market Sell")
            else:
                order_type = "BUY_LIMIT" if is_buy else "SELL_LIMIT"

        return {
            "mode": "smart",
            "decision": decision,
            "order_type": order_type,
            "reasons": reasons,
            "checks": {
                "volatility": volatility_ok,
                "bos": bos_ok,
                "zone": zone_ok,
                "scalping": scalping_ok,
                "proximity": proximity_ok,
            },
            "market_score": market_score,
            "limit_score": limit_score,
        }

    def analyze(
        self,
        df: pd.DataFrame,
        symbol: str = "XAUUSD",
        timeframe: str = "M15",
        execution_mode: str = "smart",
        strategy_style: str = "auto",
    ) -> dict:
        digits = get_symbol_digits(symbol)
        current_price = float(df["close"].iloc[-1])

        # Calculate ATR (14)
        high_low = df["high"] - df["low"]
        high_close = np.abs(df["high"] - df["close"].shift())
        low_close = np.abs(df["low"] - df["close"].shift())
        tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        atr_val = float(tr.rolling(14).mean().iloc[-1])
        if np.isnan(atr_val) or atr_val <= 0:
            atr_val = float(high_low.mean())

        ms_raw = analyze_market_structure(df, window=self.swing_length)
        obs = find_order_blocks(df, lookback=150)
        fvgs = find_fair_value_gaps(df, min_gap_points=atr_val * 0.12, lookback=150)
        sweeps_raw = find_liquidity_sweeps(df, ms_raw.get("swing_highs", []), ms_raw.get("swing_lows", []))

        # Compute Dealing Range (Last 80 bars High/Low & 50% Equilibrium)
        lookback_df = df.iloc[-80:] if len(df) >= 80 else df
        range_high = float(lookback_df["high"].max())
        range_low = float(lookback_df["low"].min())
        eq = (range_high + range_low) / 2.0
        zone_name = "DISCOUNT" if current_price <= eq else "PREMIUM"

        structure_breaks = sorted(
            ms_raw.get("bos", []) + ms_raw.get("choch", []),
            key=lambda x: x.get("index", 0),
        )

        ms = {
            "trend": ms_raw.get("trend", "BULLISH"),
            "structure_breaks": structure_breaks[-6:],
            "swing_highs": ms_raw.get("swing_highs", []),
            "swing_lows": ms_raw.get("swing_lows", []),
            "dealing_range": {
                "high": round(range_high, digits),
                "low": round(range_low, digits),
                "equilibrium": round(eq, digits),
                "zone": zone_name,
            },
        }

        # Normalize sweeps
        sweeps = []
        for s in sweeps_raw:
            stype = "BULLISH_SWEEP" if s.get("direction") == "BULLISH" else "BEARISH_SWEEP"
            sweeps.append({
                "type": stype,
                "index": int(s.get("index", 0)),
                "time": s.get("time", ""),
                "swept_level": round(float(s.get("swept_level", current_price)), digits),
                "sweep_wick": round(float(s.get("wick_low", s.get("wick_high", current_price))), digits),
            })

        # EMA 20 / 50 / 200 Institutional Filter
        ema20 = float(df["close"].ewm(span=20, adjust=False).mean().iloc[-1])
        ema50 = float(df["close"].ewm(span=50, adjust=False).mean().iloc[-1])
        ema200 = float(df["close"].ewm(span=200, adjust=False).mean().iloc[-1])

        # RSI (14)
        delta = df["close"].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss.replace(0, np.nan)
        rsi = float(100 - (100 / (1 + rs.iloc[-1])))
        if np.isnan(rsi):
            rsi = 50.0

        # Score Calculation
        bull_score = 0
        bear_score = 0
        reasons = []

        # 1. Market Structure Trend & Breaks (30 pts)
        if ms["trend"] == "BULLISH":
            bull_score += 20
            reasons.append("Market Structure is Bullish (Higher Highs & Higher Lows)")
        elif ms["trend"] == "BEARISH":
            bear_score += 20
            reasons.append("Market Structure is Bearish (Lower Highs & Lower Lows)")

        if ms["structure_breaks"]:
            last_break = ms["structure_breaks"][-1]
            if "BULLISH" in last_break["type"]:
                bull_score += 12
                reasons.append(f"Recent {last_break['type'].replace('_', ' ')} confirmed at {round(float(last_break['level']), digits)}")
            else:
                bear_score += 12
                reasons.append(f"Recent {last_break['type'].replace('_', ' ')} confirmed at {round(float(last_break['level']), digits)}")

        # 2. Dealing Range Premium / Discount (15 pts)
        if zone_name == "DISCOUNT":
            bull_score += 15
            reasons.append(f"Price in Institutional DISCOUNT Zone (< {round(eq, digits)} EQ)")
        else:
            bear_score += 15
            reasons.append(f"Price in Institutional PREMIUM Zone (> {round(eq, digits)} EQ)")

        # 3. Unmitigated Order Block Proximity (20 pts)
        unmitigated_bull_obs = [o for o in obs if o["type"] == "BULLISH_OB" and not o["mitigated"]]
        unmitigated_bear_obs = [o for o in obs if o["type"] == "BEARISH_OB" and not o["mitigated"]]

        active_ob = None
        for ob in reversed(unmitigated_bull_obs):
            if ob["bottom"] - atr_val <= current_price <= ob["top"] + (atr_val * 1.5):
                bull_score += 20
                active_ob = ob
                reasons.append(f"Price tapping Unmitigated Bullish Order Block ({round(float(ob['bottom']), digits)} - {round(float(ob['top']), digits)})")
                break

        for ob in reversed(unmitigated_bear_obs):
            if ob["bottom"] - (atr_val * 1.5) <= current_price <= ob["top"] + atr_val:
                bear_score += 20
                if not active_ob:
                    active_ob = ob
                reasons.append(f"Price rejecting Unmitigated Bearish Order Block ({round(float(ob['bottom']), digits)} - {round(float(ob['top']), digits)})")
                break

        # 4. Fair Value Gap (FVG) Confluence (15 pts)
        open_bull_fvgs = [g for g in fvgs if g["type"] == "BULLISH_FVG" and not g["mitigated"]]
        open_bear_fvgs = [g for g in fvgs if g["type"] == "BEARISH_FVG" and not g["mitigated"]]

        if open_bull_fvgs:
            bull_score += 12
            reasons.append(f"{len(open_bull_fvgs)} Unfilled Bullish FVG Imbalance(s) acting as magnet/support")
        if open_bear_fvgs:
            bear_score += 12
            reasons.append(f"{len(open_bear_fvgs)} Unfilled Bearish FVG Imbalance(s) overhead")

        # 5. Liquidity Sweeps (15 pts)
        recent_sweeps = [s for s in sweeps if s["index"] >= len(df) - 25]
        for s in recent_sweeps:
            if s["type"] == "BULLISH_SWEEP":
                bull_score += 15
                reasons.append(f"Sell-Side Liquidity (SSL) Swept at {round(float(s['swept_level']), digits)} — Smart Money Accumulation")
            elif s["type"] == "BEARISH_SWEEP":
                bear_score += 15
                reasons.append(f"Buy-Side Liquidity (BSL) Swept at {round(float(s['swept_level']), digits)} — Smart Money Distribution")

        # 6. EMA Institutional Orderflow & RSI (10 pts)
        if current_price > ema50 > ema200:
            bull_score += 10
            reasons.append("Bullish Institutional EMA Stack (Price > EMA 50 > EMA 200)")
        elif current_price < ema50 < ema200:
            bear_score += 10
            reasons.append("Bearish Institutional EMA Stack (Price < EMA 50 < EMA 200)")

        if rsi < 35:
            bull_score += 8
            reasons.append(f"RSI Oversold Exhaustion ({round(rsi, 1)})")
        elif rsi > 65:
            bear_score += 8
            reasons.append(f"RSI Overbought Exhaustion ({round(rsi, 1)})")

        # Final Direction & Confidence
        if bull_score >= bear_score:
            direction = "BUY"
            raw_conf = min(98, max(56, 50 + int(bull_score * 0.55)))
        else:
            direction = "SELL"
            raw_conf = min(98, max(56, 50 + int(bear_score * 0.55)))

        # Calculate Optimal Entry, SL, TP1, TP2, TP3
        if direction == "BUY":
            if active_ob and active_ob["type"] == "BULLISH_OB" and active_ob["top"] <= current_price:
                entry = float((active_ob["top"] + active_ob["bottom"]) / 2.0)
                sl = float(active_ob["bottom"] - (atr_val * 0.6))
            else:
                pullback_ob = unmitigated_bull_obs[-1] if unmitigated_bull_obs else None
                if pullback_ob and (current_price - pullback_ob["top"]) <= atr_val * 1.2 and pullback_ob["top"] < current_price:
                    entry = float(pullback_ob["top"])
                    sl = float(pullback_ob["bottom"] - (atr_val * 0.5))
                else:
                    entry = current_price
                    sl = current_price - (atr_val * 1.5)
            risk = max(abs(entry - sl), atr_val * 0.5)
            tp1 = entry + (risk * 1.5)
            tp2 = entry + (risk * 2.5)
            tp3 = entry + (risk * 4.0)
        else:
            if active_ob and active_ob["type"] == "BEARISH_OB" and active_ob["bottom"] >= current_price:
                entry = float((active_ob["top"] + active_ob["bottom"]) / 2.0)
                sl = float(active_ob["top"] + (atr_val * 0.6))
            else:
                pullback_ob = unmitigated_bear_obs[-1] if unmitigated_bear_obs else None
                if pullback_ob and (pullback_ob["bottom"] - current_price) <= atr_val * 1.2 and pullback_ob["bottom"] > current_price:
                    entry = float(pullback_ob["bottom"])
                    sl = float(pullback_ob["top"] + (atr_val * 0.5))
                else:
                    entry = current_price
                    sl = current_price + (atr_val * 1.5)
            risk = max(abs(sl - entry), atr_val * 0.5)
            tp1 = entry - (risk * 1.5)
            tp2 = entry - (risk * 2.5)
            tp3 = entry - (risk * 4.0)

        rr_ratio = round(abs(tp2 - entry) / max(risk, 1e-9), 2)

        # Evaluate Execution Mode ($s from TradingChart-CyJfNxim.js)
        exec_decision = self.evaluate_execution_mode(
            df=df,
            mode=execution_mode,
            direction=direction,
            entry=entry,
            stop_loss=sl,
            tp1=tp1,
            timeframe=timeframe,
            symbol=symbol,
            latest_price=current_price,
            atr=atr_val,
        )

        if exec_decision["decision"] == "MARKET" and abs(entry - current_price) > 0:
            entry = current_price
            if direction == "BUY":
                sl = entry - risk
                tp1 = entry + (risk * 1.5)
                tp2 = entry + (risk * 2.5)
                tp3 = entry + (risk * 4.0)
            else:
                sl = entry + risk
                tp1 = entry - (risk * 1.5)
                tp2 = entry - (risk * 2.5)
                tp3 = entry - (risk * 4.0)

        strategy_intent = classify_strategy_intent(timeframe=timeframe, style=strategy_style, rr_ratio=rr_ratio)

        # Build SMC Elements matching LightweightChart-Bi42fpkQ.js (Le function)
        support_zones = [
            {
                "high": round(float(o["top"]), digits),
                "low": round(float(o["bottom"]), digits),
                "strength": "strong" if not o["mitigated"] else "moderate",
                "touches": 2 if not o["mitigated"] else 1,
            }
            for o in unmitigated_bull_obs[-3:]
        ]
        resistance_zones = [
            {
                "high": round(float(o["top"]), digits),
                "low": round(float(o["bottom"]), digits),
                "strength": "strong" if not o["mitigated"] else "moderate",
                "touches": 2 if not o["mitigated"] else 1,
            }
            for o in unmitigated_bear_obs[-3:]
        ]
        liquidity_zones = [
            {
                "level": round(float(s["swept_level"]), digits),
                "type": "sell_side" if s["type"] == "BULLISH_SWEEP" else "buy_side",
                "swept": True,
                "description": "SSL Swept" if s["type"] == "BULLISH_SWEEP" else "BSL Swept",
            }
            for s in sweeps[-4:]
        ]
        structure_breaks_ui = [
            {
                "type": "CHoCH" if "CHOCH" in b["type"] else "BOS",
                "direction": "bullish" if "BULLISH" in b["type"] else "bearish",
                "level": round(float(b["level"]), digits),
            }
            for b in ms["structure_breaks"][-4:]
        ]

        for o in obs:
            o["top"] = round(float(o["top"]), digits)
            o["bottom"] = round(float(o["bottom"]), digits)
        for g in fvgs:
            g["top"] = round(float(g["top"]), digits)
            g["bottom"] = round(float(g["bottom"]), digits)

        trish_summary = (
            f"Trish AI Analysis on {symbol} ({timeframe}): Market structure is {ms['trend']} in the "
            f"{zone_name} zone. {strategy_intent['label']} recommends a "
            f"{exec_decision['order_type']} at {round(entry, digits)} with SL at {round(sl, digits)} "
            f"and TP2 at {round(tp2, digits)} ({rr_ratio}:1 R:R, {raw_conf}% confidence)."
        )

        return {
            "symbol": symbol,
            "timeframe": timeframe,
            "digits": digits,
            "current_price": round(current_price, digits),
            "direction": direction,
            "confidence": raw_conf,
            "grade": "A+" if raw_conf >= 85 else ("A" if raw_conf >= 75 else "B+"),
            "entry": round(entry, digits),
            "stop_loss": round(sl, digits),
            "take_profit_1": round(tp1, digits),
            "take_profit_2": round(tp2, digits),
            "take_profit_3": round(tp3, digits),
            "risk_reward": rr_ratio,
            "atr": round(atr_val, digits),
            "rsi": round(rsi, 1),
            "ema20": round(ema20, digits),
            "ema50": round(ema50, digits),
            "ema200": round(ema200, digits),
            "execution": exec_decision,
            "strategy_intent": strategy_intent,
            "trish_summary": trish_summary,
            "reasons": reasons,
            "market_structure": ms,
            "order_blocks": obs[-8:],
            "fair_value_gaps": fvgs[-8:],
            "liquidity_sweeps": sweeps[-6:],
            "smc_elements": {
                "supportZones": support_zones,
                "resistanceZones": resistance_zones,
                "liquidityZones": liquidity_zones,
                "structureBreaks": structure_breaks_ui,
            },
        }
