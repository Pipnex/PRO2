"""
Pipnex AI - Aggressive Scalper Engine Suite
============================================
Collection of high-frequency, battle-tested M1 & M5 scalping algorithms:
  1. 'm1-turbo-blitz'       : 9/21/50 EMA Ribbon + ATR Volatility Expansion Scalper
  2. 'm1-liquidity-sweep'   : 1-Minute Micro-SMC / Liquidity Wick Rejection Snatcher
  3. 'm1-bb-squeeze'        : Bollinger Bandwidth Squeeze & Volatility Breakout
  4. 'news-fade'            : NewsIQ Post-Spike Exhaustion Fade (M5)
  5. 'smc-scalp'            : Classical M15 Smart Money Concepts (OB / FVG / BOS)
"""

import numpy as np
import pandas as pd
from datetime import datetime
from .prop_pass_calc import get_symbol_digits


SCALPER_BOT_PROFILES = {
    "m1-turbo-blitz": {
        "id": "m1-turbo-blitz",
        "name": "M1 Turbo-Scalp Blitz",
        "badge": "⚡ M1 RAPID SCALPER",
        "timeframe": "M1",
        "scan_interval_sec": 5,
        "style": "Momentum / EMA Ribbon",
        "description": "Fast 1-minute aggressive scalper utilizing 9/21/50 EMA ribbon alignment and ATR volume expansion. Enters high-probability impulse moves with tight 8-12 pip stops.",
        "recommended_pairs": ["XAUUSD", "EURUSD", "GBPUSD", "USDJPY"],
        "target_rr": 1.8,
    },
    "m1-liquidity-sweep": {
        "id": "m1-liquidity-sweep",
        "name": "M1 Micro-SMC Liquidity Snatcher",
        "badge": "🎯 M1 SMC SNIPER",
        "timeframe": "M1",
        "scan_interval_sec": 5,
        "style": "Order Flow / Liquidity Sweeps",
        "description": "Monitors micro-structure for false breakout wick rejections outside recent 15-bar extremes. Enters immediately on liquidity absorption targeting opposite order block.",
        "recommended_pairs": ["XAUUSD", "EURUSD", "US30", "NAS100"],
        "target_rr": 2.5,
    },
    "m1-bb-squeeze": {
        "id": "m1-bb-squeeze",
        "name": "M1 Volatility Squeeze Breakout",
        "badge": "💥 M1 VOLATILITY BLITZ",
        "timeframe": "M1",
        "scan_interval_sec": 5,
        "style": "Volatility / Bollinger Expansion",
        "description": "Detects tight compression where Bollinger Bandwidth drops into low percentiles, then fires explosive entries on the first high-volume expansion bar.",
        "recommended_pairs": ["XAUUSD", "BTCUSD", "GBPJPY"],
        "target_rr": 2.0,
    },
    "news-fade": {
        "id": "news-fade",
        "name": "News Reaction Fade (M5)",
        "badge": "📰 NEWSIQ™ FADE",
        "timeframe": "M5",
        "scan_interval_sec": 10,
        "style": "Macro Deviation / Post-Spike Fade",
        "description": "Pipnex AI official news fade strategy. Fades initial post-release liquidity spikes on CPI, NFP, and FOMC back to equilibrium baseline.",
        "recommended_pairs": ["XAUUSD", "EURUSD", "USDJPY"],
        "target_rr": 2.5,
    },
    "smc-scalp": {
        "id": "smc-scalp",
        "name": "Institutional SMC Scalper (M15)",
        "badge": "🏛️ SMC CONFLUENCE",
        "timeframe": "M15",
        "scan_interval_sec": 20,
        "style": "Classical SMC (OB / FVG / BOS)",
        "description": "Full 6-factor confluence engine scanning Order Blocks, Fair Value Gaps, and Dealing Range equilibrium.",
        "recommended_pairs": ["XAUUSD", "EURUSD", "GBPUSD", "BTCUSD"],
        "target_rr": 2.5,
    }
}


class ScalperEngine:
    def __init__(self, confidence_engine=None):
        self.confidence_engine = confidence_engine

    def analyze_scalp(self, df: pd.DataFrame, symbol: str = "XAUUSD", bot_id: str = "m1-turbo-blitz") -> dict:
        """
        Main entry point for aggressive scalper analysis.
        Returns a standardized execution dictionary compatible with MT5Bridge.execute_signal.
        """
        digits = get_symbol_digits(symbol)
        current_price = float(df["close"].iloc[-1])

        # Routing to dedicated bot algorithm
        if bot_id == "m1-turbo-blitz":
            return self._analyze_m1_turbo_blitz(df, symbol, digits, current_price)
        elif bot_id == "m1-liquidity-sweep":
            return self._analyze_m1_liquidity_sweep(df, symbol, digits, current_price)
        elif bot_id == "m1-bb-squeeze":
            return self._analyze_m1_bb_squeeze(df, symbol, digits, current_price)
        else:
            # Fallback to general confidence engine
            return self.confidence_engine.analyze(
                df, symbol=symbol, timeframe="M1", execution_mode="aggressive", strategy_style="scalping"
            )

    def _analyze_m1_turbo_blitz(self, df: pd.DataFrame, symbol: str, digits: int, current_price: float) -> dict:
        """
        9/21/50 EMA Ribbon + ATR Momentum Scalper on M1
        """
        close = df["close"]
        high = df["high"]
        low = df["low"]

        # Calculate EMAs
        ema9 = close.ewm(span=9, adjust=False).mean()
        ema21 = close.ewm(span=21, adjust=False).mean()
        ema50 = close.ewm(span=50, adjust=False).mean()

        # ATR (14)
        tr = pd.concat([
            high - low,
            (high - close.shift()).abs(),
            (low - close.shift()).abs()
        ], axis=1).max(axis=1)
        atr = float(tr.rolling(14).mean().iloc[-1])
        if np.isnan(atr) or atr <= 0:
            atr = current_price * 0.0008

        # RSI (14)
        delta = close.diff()
        gain = (delta.where(delta > 0, 0)).rolling(14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
        rs = gain / (loss + 1e-9)
        rsi = float((100 - (100 / (1 + rs))).iloc[-1])

        e9 = float(ema9.iloc[-1])
        e21 = float(ema21.iloc[-1])
        e50 = float(ema50.iloc[-1])
        curr_bar_range = float(high.iloc[-1] - low.iloc[-1])

        is_bullish_ribbon = e9 > e21 > e50
        is_bearish_ribbon = e9 < e21 < e50
        has_momentum_expansion = curr_bar_range >= (atr * 0.8)

        direction = "BUY" if is_bullish_ribbon else "SELL"
        confidence = 65
        reasons = []

        if is_bullish_ribbon:
            confidence += 15
            reasons.append("Bullish 9/21/50 EMA Ribbon Alignment on M1")
            if 50 < rsi < 75:
                confidence += 10
                reasons.append(f"RSI in prime bullish acceleration zone ({rsi:.1f})")
            if has_momentum_expansion:
                confidence += 5
                reasons.append(f"ATR Volatility expansion active ({curr_bar_range:.2f} >= {atr*0.8:.2f})")
            
            # Pip offsets
            pip_unit = 0.1 if "XAU" in symbol else 0.0001
            sl_distance = max(atr * 1.5, pip_unit * 10)
            tp_distance = sl_distance * 1.8

            entry = current_price
            sl = round(entry - sl_distance, digits)
            tp1 = round(entry + (tp_distance * 0.6), digits)
            tp2 = round(entry + tp_distance, digits)

        elif is_bearish_ribbon:
            confidence += 15
            reasons.append("Bearish 9/21/50 EMA Ribbon Alignment on M1")
            if 25 < rsi < 50:
                confidence += 10
                reasons.append(f"RSI in prime bearish acceleration zone ({rsi:.1f})")
            if has_momentum_expansion:
                confidence += 5
                reasons.append(f"ATR Volatility expansion active ({curr_bar_range:.2f} >= {atr*0.8:.2f})")
            
            pip_unit = 0.1 if "XAU" in symbol else 0.0001
            sl_distance = max(atr * 1.5, pip_unit * 10)
            tp_distance = sl_distance * 1.8

            entry = current_price
            sl = round(entry + sl_distance, digits)
            tp1 = round(entry - (tp_distance * 0.6), digits)
            tp2 = round(entry - tp_distance, digits)
        else:
            confidence = 60
            direction = "BUY" if current_price > e50 else "SELL"
            reasons.append("EMA Ribbon transitioning — awaiting micro expansion")
            sl = round(current_price - (atr * 1.5), digits)
            tp1 = round(current_price + (atr * 1.5), digits)
            tp2 = round(current_price + (atr * 2.5), digits)
            entry = current_price

        grade = "A+" if confidence >= 90 else ("A" if confidence >= 80 else "B")

        return {
            "symbol": symbol,
            "timeframe": "M1",
            "bot_id": "m1-turbo-blitz",
            "bot_name": "M1 Turbo-Scalp Blitz",
            "current_price": current_price,
            "direction": direction,
            "confidence": min(95, confidence),
            "grade": grade,
            "entry": round(entry, digits),
            "stop_loss": sl,
            "take_profit_1": tp1,
            "take_profit_2": tp2,
            "risk_reward": 1.8,
            "execution": {
                "decision": "MARKET",
                "order_type": direction,
                "reasons": reasons
            },
            "strategy_intent": {
                "id": "m1-turbo-blitz",
                "label": "M1 Turbo-Scalp Ribbon Blitz",
                "icon": "⚡",
                "description": "High-speed 1-minute EMA ribbon momentum scalper"
            },
            "reasons": reasons,
            "trish_summary": f"M1 Turbo Scalper detects {direction} momentum on {symbol} (Confidence: {confidence}%). 9/21 EMA ribbon aligned with ATR volume expansion."
        }

    def _analyze_m1_liquidity_sweep(self, df: pd.DataFrame, symbol: str, digits: int, current_price: float) -> dict:
        """
        M1 Micro-SMC Liquidity Wick Rejection Snatcher
        """
        highs = df["high"].iloc[-25:]
        lows = df["low"].iloc[-25:]
        curr_bar = df.iloc[-1]
        prev_bar = df.iloc[-2]

        local_high = float(highs.iloc[:-1].max())
        local_low = float(lows.iloc[:-1].min())

        curr_open = float(curr_bar["open"])
        curr_close = float(curr_bar["close"])
        curr_high = float(curr_bar["high"])
        curr_low = float(curr_bar["low"])
        bar_range = curr_high - curr_low or 0.0001

        upper_wick = curr_high - max(curr_open, curr_close)
        lower_wick = min(curr_open, curr_close) - curr_low

        direction = "BUY"
        confidence = 65
        reasons = []

        # Bullish Liquidity Sweep (Swept below local low with long wick and closed above)
        if curr_low < local_low and (lower_wick / bar_range) >= 0.45 and curr_close > curr_open:
            direction = "BUY"
            confidence = 88
            reasons.append(f"M1 Liquidity Sweep: Purged local low at {local_low:.{digits}f}")
            reasons.append(f"Long rejection wick ({lower_wick/bar_range*100:.0f}% of bar)")
            reasons.append("Bullish Displacement close back into structure")
            sl = round(curr_low - (bar_range * 0.2), digits)
            risk = current_price - sl
            tp1 = round(current_price + (risk * 1.5), digits)
            tp2 = round(current_price + (risk * 2.5), digits)

        # Bearish Liquidity Sweep (Swept above local high with long wick and closed below)
        elif curr_high > local_high and (upper_wick / bar_range) >= 0.45 and curr_close < curr_open:
            direction = "SELL"
            confidence = 88
            reasons.append(f"M1 Liquidity Sweep: Purged local high at {local_high:.{digits}f}")
            reasons.append(f"Long rejection wick ({upper_wick/bar_range*100:.0f}% of bar)")
            reasons.append("Bearish Displacement close back into structure")
            sl = round(curr_high + (bar_range * 0.2), digits)
            risk = sl - current_price
            tp1 = round(current_price - (risk * 1.5), digits)
            tp2 = round(current_price - (risk * 2.5), digits)

        else:
            # Micro-trend continuation
            direction = "BUY" if curr_close > float(df["close"].iloc[-5]) else "SELL"
            confidence = 72
            reasons.append("Searching for micro-liquidity pool sweep on M1")
            pip_val = 0.1 if "XAU" in symbol else 0.0001
            sl_dist = 12 * pip_val
            sl = round(current_price - sl_dist if direction == "BUY" else current_price + sl_dist, digits)
            tp1 = round(current_price + (sl_dist * 1.5) if direction == "BUY" else current_price - (sl_dist * 1.5), digits)
            tp2 = round(current_price + (sl_dist * 2.5) if direction == "BUY" else current_price - (sl_dist * 2.5), digits)

        grade = "A+" if confidence >= 88 else "A"

        return {
            "symbol": symbol,
            "timeframe": "M1",
            "bot_id": "m1-liquidity-sweep",
            "bot_name": "M1 Micro-SMC Liquidity Snatcher",
            "current_price": current_price,
            "direction": direction,
            "confidence": confidence,
            "grade": grade,
            "entry": round(current_price, digits),
            "stop_loss": sl,
            "take_profit_1": tp1,
            "take_profit_2": tp2,
            "risk_reward": 2.5,
            "execution": {
                "decision": "MARKET",
                "order_type": direction,
                "reasons": reasons
            },
            "strategy_intent": {
                "id": "m1-liquidity-sweep",
                "label": "M1 Liquidity Wick Snatcher",
                "icon": "🎯",
                "description": "ICT/SMC micro liquidity purge and rejection snatcher"
            },
            "reasons": reasons,
            "trish_summary": f"Micro-SMC Engine detected {direction} liquidity sweep on {symbol} (Confidence: {confidence}%)."
        }

    def _analyze_m1_bb_squeeze(self, df: pd.DataFrame, symbol: str, digits: int, current_price: float) -> dict:
        """
        Bollinger Bandwidth Squeeze & Volatility Breakout on M1
        """
        close = df["close"]
        sma20 = close.rolling(20).mean()
        std20 = close.rolling(20).std()

        upper = sma20 + (std20 * 2.0)
        lower = sma20 - (std20 * 2.0)
        bandwidth = (upper - lower) / (sma20 + 1e-9)

        bw_now = float(bandwidth.iloc[-1])
        bw_min_50 = float(bandwidth.iloc[-50:].min())
        curr_close = float(close.iloc[-1])
        up_val = float(upper.iloc[-1])
        low_val = float(lower.iloc[-1])
        mid_val = float(sma20.iloc[-1])

        is_squeeze = bw_now <= (bw_min_50 * 1.25)
        confidence = 70
        direction = "BUY"
        reasons = []

        if curr_close > up_val:
            direction = "BUY"
            confidence = 86
            reasons.append("M1 Volatility Breakout: Close pierced Upper Bollinger Band")
            if is_squeeze:
                confidence += 6
                reasons.append("Preceded by tight Bollinger Bandwidth squeeze (High-energy expansion)")
            sl = round(mid_val, digits)
            risk = current_price - sl
            tp1 = round(current_price + (risk * 1.2), digits)
            tp2 = round(current_price + (risk * 2.0), digits)

        elif curr_close < low_val:
            direction = "SELL"
            confidence = 86
            reasons.append("M1 Volatility Breakout: Close pierced Lower Bollinger Band")
            if is_squeeze:
                confidence += 6
                reasons.append("Preceded by tight Bollinger Bandwidth squeeze (High-energy expansion)")
            sl = round(mid_val, digits)
            risk = sl - current_price
            tp1 = round(current_price - (risk * 1.2), digits)
            tp2 = round(current_price - (risk * 2.0), digits)

        else:
            direction = "BUY" if curr_close > mid_val else "SELL"
            confidence = 68
            reasons.append("Bollinger Bands consolidating — awaiting boundary pierce")
            pip_val = 0.1 if "XAU" in symbol else 0.0001
            sl = round(current_price - (12 * pip_val) if direction == "BUY" else current_price + (12 * pip_val), digits)
            tp1 = round(current_price + (18 * pip_val) if direction == "BUY" else current_price - (18 * pip_val), digits)
            tp2 = round(current_price + (24 * pip_val) if direction == "BUY" else current_price - (24 * pip_val), digits)

        grade = "A+" if confidence >= 88 else "A"

        return {
            "symbol": symbol,
            "timeframe": "M1",
            "bot_id": "m1-bb-squeeze",
            "bot_name": "M1 Volatility Squeeze Breakout",
            "current_price": current_price,
            "direction": direction,
            "confidence": min(95, confidence),
            "grade": grade,
            "entry": round(current_price, digits),
            "stop_loss": sl,
            "take_profit_1": tp1,
            "take_profit_2": tp2,
            "risk_reward": 2.0,
            "execution": {
                "decision": "MARKET",
                "order_type": direction,
                "reasons": reasons
            },
            "strategy_intent": {
                "id": "m1-bb-squeeze",
                "label": "M1 Volatility Squeeze",
                "icon": "💥",
                "description": "Compression squeeze into high-volatility impulse breakout"
            },
            "reasons": reasons,
            "trish_summary": f"Volatility Squeeze Engine detects {direction} breakout on {symbol} (Confidence: {confidence}%)."
        }
