"""
Pipnex AI - Liquidity Sweep & Stop Hunt Engine
Detects:
- Buy-Side Liquidity (BSL) Sweeps above key Swing Highs
- Sell-Side Liquidity (SSL) Sweeps below key Swing Lows
- Long Rejection Wicks confirming institutional liquidity absorption
"""

import pandas as pd
import numpy as np
from typing import List, Dict, Any

def find_liquidity_sweeps(df: pd.DataFrame, swing_highs: List[Dict[str, Any]], swing_lows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Checks recent candles for liquidity sweeps against prior swing highs/lows.
    """
    if len(df) < 5:
        return []
        
    sweeps = []
    highs = df['high'].values
    lows = df['low'].values
    opens = df['open'].values
    closes = df['close'].values
    times = df['time'].values if 'time' in df.columns else list(range(len(df)))
    
    # Check last 30 bars for sweep activity
    start_bar = max(0, len(df) - 30)
    
    for i in range(start_bar, len(df)):
        c_open = opens[i]
        c_close = closes[i]
        c_high = highs[i]
        c_low = lows[i]
        candle_range = c_high - c_low
        if candle_range <= 0:
            continue
            
        upper_wick = c_high - max(c_open, c_close)
        lower_wick = min(c_open, c_close) - c_low
        
        # 1. BSL Sweep (Sweep of Swing High)
        for sh in swing_highs:
            # Swing high must have occurred before current bar
            if sh["index"] < i - 1:
                sh_price = sh["price"]
                # Candle spiked above the swing high, but closed strictly below it!
                if c_high > sh_price and c_close < sh_price:
                    # Wick must be substantial (at least 40% of total candle range)
                    if upper_wick / candle_range >= 0.35:
                        sweeps.append({
                            "type": "BSL_SWEEP",
                            "direction": "BEARISH",
                            "index": i,
                            "time": str(times[i]),
                            "swept_level": sh_price,
                            "wick_high": float(c_high),
                            "rejection_wick_ratio": round(upper_wick / candle_range, 2)
                        })
                        break
                        
        # 2. SSL Sweep (Sweep of Swing Low)
        for sl in swing_lows:
            if sl["index"] < i - 1:
                sl_price = sl["price"]
                # Candle spiked below the swing low, but closed strictly above it!
                if c_low < sl_price and c_close > sl_price:
                    if lower_wick / candle_range >= 0.35:
                        sweeps.append({
                            "type": "SSL_SWEEP",
                            "direction": "BULLISH",
                            "index": i,
                            "time": str(times[i]),
                            "swept_level": sl_price,
                            "wick_low": float(c_low),
                            "rejection_wick_ratio": round(lower_wick / candle_range, 2)
                        })
                        break
                        
    return sweeps
