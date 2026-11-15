"""
Pipnex AI - Fair Value Gap (FVG) & Imbalance Engine
Detects:
- Bullish Fair Value Gaps (Buy-side Imbalance)
- Bearish Fair Value Gaps (Sell-side Imbalance)
- Consequent Encroachment (50% midpoint of the gap)
- Mitigation and fill tracking
"""

import pandas as pd
import numpy as np
from typing import List, Dict, Any

def find_fair_value_gaps(df: pd.DataFrame, min_gap_points: float = 0.05, lookback: int = 150) -> List[Dict[str, Any]]:
    """
    Identifies 3-candle institutional Fair Value Gaps.
    """
    if len(df) < 5:
        return []
        
    start_idx = max(1, len(df) - lookback)
    fvgs = []
    
    highs = df['high'].values
    lows = df['low'].values
    closes = df['close'].values
    times = df['time'].values if 'time' in df.columns else list(range(len(df)))
    current_price = float(closes[-1])
    
    for i in range(start_idx, len(df) - 1):
        # Bullish FVG: Candle i-1 High < Candle i+1 Low
        c1_high = highs[i-1]
        c3_low = lows[i+1]
        
        if c3_low > c1_high + min_gap_points:
            gap_top = float(c3_low)
            gap_bottom = float(c1_high)
            ce = round((gap_top + gap_bottom) / 2.0, 5)
            
            mitigated = False
            for k in range(i + 2, len(df)):
                if lows[k] <= gap_bottom:
                    mitigated = True
                    break
                    
            fvgs.append({
                "id": f"FVG_BULL_{i}",
                "type": "BULLISH_FVG",
                "index": int(i),
                "time": str(times[i]),
                "top": gap_top,
                "bottom": gap_bottom,
                "consequent_encroachment": ce,
                "size": round(gap_top - gap_bottom, 5),
                "mitigated": bool(mitigated),
                "active": bool(not mitigated and current_price >= gap_bottom)
            })
            
        # Bearish FVG: Candle i-1 Low > Candle i+1 High
        c1_low = lows[i-1]
        c3_high = highs[i+1]
        
        if c1_low > c3_high + min_gap_points:
            gap_top = float(c1_low)
            gap_bottom = float(c3_high)
            ce = round((gap_top + gap_bottom) / 2.0, 5)
            
            mitigated = False
            for k in range(i + 2, len(df)):
                if highs[k] >= gap_top:
                    mitigated = True
                    break
                    
            fvgs.append({
                "id": f"FVG_BEAR_{i}",
                "type": "BEARISH_FVG",
                "index": int(i),
                "time": str(times[i]),
                "top": gap_top,
                "bottom": gap_bottom,
                "consequent_encroachment": ce,
                "size": round(gap_top - gap_bottom, 5),
                "mitigated": bool(mitigated),
                "active": bool(not mitigated and current_price <= gap_top)
            })
            
    return fvgs
