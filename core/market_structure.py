"""
Pipnex AI - Market Structure & Trend Engine
Identifies:
- Swing Highs & Swing Lows (Fractals)
- Break of Structure (BOS)
- Change of Character (CHOCH) / Market Structure Shift (MSS)
- Current Trend State (BULLISH, BEARISH, CONSOLIDATION)
"""

import pandas as pd
import numpy as np
from typing import List, Dict, Any, Optional

def find_swings(df: pd.DataFrame, window: int = 5) -> Dict[str, List[Dict[str, Any]]]:
    """
    Finds swing highs and swing lows using a rolling fractal window.
    """
    high = df['high'].values
    low = df['low'].values
    times = df['time'].values if 'time' in df.columns else list(range(len(df)))
    
    swing_highs = []
    swing_lows = []
    n = len(df)
    
    for i in range(window, n - window):
        # Swing High
        if high[i] == max(high[i - window : i + window + 1]):
            # Confirm it's strictly greater than immediate neighbors
            if high[i] > high[i-1] and high[i] > high[i+1]:
                swing_highs.append({
                    "index": i,
                    "time": str(times[i]),
                    "price": float(high[i]),
                    "type": "SWING_HIGH"
                })
                
        # Swing Low
        if low[i] == min(low[i - window : i + window + 1]):
            if low[i] < low[i-1] and low[i] < low[i+1]:
                swing_lows.append({
                    "index": i,
                    "time": str(times[i]),
                    "price": float(low[i]),
                    "type": "SWING_LOW"
                })
                
    return {"highs": swing_highs, "lows": swing_lows}

def analyze_market_structure(df: pd.DataFrame, window: int = 5) -> Dict[str, Any]:
    """
    Evaluates historical price action to identify BOS, CHOCH, and prevailing trend.
    """
    if len(df) < window * 2 + 10:
        return {
            "trend": "NEUTRAL",
            "bos": [],
            "choch": [],
            "recent_swing_high": None,
            "recent_swing_low": None
        }
        
    swings = find_swings(df, window=window)
    swing_highs = swings["highs"]
    swing_lows = swings["lows"]
    
    bos_events = []
    choch_events = []
    
    current_trend = "NEUTRAL"
    last_sh = None
    last_sl = None
    
    # Merge swings chronologically
    all_swings = sorted(swing_highs + swing_lows, key=lambda s: s["index"])
    
    for swing in all_swings:
        if swing["type"] == "SWING_HIGH":
            if last_sh is not None:
                if swing["price"] > last_sh["price"]:
                    if current_trend == "BEARISH":
                        choch_events.append({
                            "type": "BULLISH_CHOCH",
                            "index": swing["index"],
                            "time": swing["time"],
                            "level": last_sh["price"],
                            "break_price": swing["price"]
                        })
                        current_trend = "BULLISH"
                    else:
                        bos_events.append({
                            "type": "BULLISH_BOS",
                            "index": swing["index"],
                            "time": swing["time"],
                            "level": last_sh["price"],
                            "break_price": swing["price"]
                        })
                        current_trend = "BULLISH"
            last_sh = swing
            
        elif swing["type"] == "SWING_LOW":
            if last_sl is not None:
                if swing["price"] < last_sl["price"]:
                    if current_trend == "BULLISH":
                        choch_events.append({
                            "type": "BEARISH_CHOCH",
                            "index": swing["index"],
                            "time": swing["time"],
                            "level": last_sl["price"],
                            "break_price": swing["price"]
                        })
                        current_trend = "BEARISH"
                    else:
                        bos_events.append({
                            "type": "BEARISH_BOS",
                            "index": swing["index"],
                            "time": swing["time"],
                            "level": last_sl["price"],
                            "break_price": swing["price"]
                        })
                        current_trend = "BEARISH"
            last_sl = swing
            
    recent_sh = swing_highs[-1] if swing_highs else None
    recent_sl = swing_lows[-1] if swing_lows else None
    
    return {
        "trend": current_trend,
        "bos": bos_events[-5:],
        "choch": choch_events[-5:],
        "recent_swing_high": recent_sh,
        "recent_swing_low": recent_sl,
        "swing_highs": swing_highs[-10:],
        "swing_lows": swing_lows[-10:]
    }
