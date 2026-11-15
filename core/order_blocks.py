"""
Pipnex AI - Institutional Order Block (OB) & Supply/Demand Engine
Detects:
- Bullish Order Blocks (Demand Zones)
- Bearish Order Blocks (Supply Zones)
- Mitigation tracking (Unmitigated vs Mitigated)
- Volume/Displacement confirmation
"""

import pandas as pd
import numpy as np
from typing import List, Dict, Any

def find_order_blocks(df: pd.DataFrame, lookback: int = 150) -> List[Dict[str, Any]]:
    """
    Scans recent candle history to detect high-probability institutional Order Blocks.
    """
    if len(df) < 10:
        return []
        
    start_idx = max(2, len(df) - lookback)
    order_blocks = []
    
    opens = df['open'].values
    highs = df['high'].values
    lows = df['low'].values
    closes = df['close'].values
    times = df['time'].values if 'time' in df.columns else list(range(len(df)))
    
    current_price = float(closes[-1])
    
    for i in range(start_idx, len(df) - 2):
        # 1. Bullish Order Block (Demand):
        if closes[i] < opens[i]:
            next_1_bullish = closes[i+1] > opens[i+1] and closes[i+1] > highs[i]
            displacement = (closes[i+1] - opens[i+1]) > (highs[i] - lows[i]) * 1.2
            
            if next_1_bullish and displacement:
                ob_high = float(highs[i])
                ob_low = float(lows[i])
                
                mitigated = False
                for k in range(i + 2, len(df)):
                    if lows[k] <= ob_high:
                        mitigated = True
                        break
                        
                order_blocks.append({
                    "id": f"OB_BULL_{i}",
                    "type": "BULLISH_OB",
                    "index": int(i),
                    "time": str(times[i]),
                    "top": ob_high,
                    "bottom": ob_low,
                    "mean_threshold": round((ob_high + ob_low) / 2.0, 5),
                    "mitigated": bool(mitigated),
                    "active": bool(not mitigated and current_price >= ob_low)
                })
                
        # 2. Bearish Order Block (Supply):
        elif closes[i] > opens[i]:
            next_1_bearish = closes[i+1] < opens[i+1] and closes[i+1] < lows[i]
            displacement = (opens[i+1] - closes[i+1]) > (highs[i] - lows[i]) * 1.2
            
            if next_1_bearish and displacement:
                ob_high = float(highs[i])
                ob_low = float(lows[i])
                
                mitigated = False
                for k in range(i + 2, len(df)):
                    if highs[k] >= ob_low:
                        mitigated = True
                        break
                        
                order_blocks.append({
                    "id": f"OB_BEAR_{i}",
                    "type": "BEARISH_OB",
                    "index": int(i),
                    "time": str(times[i]),
                    "top": ob_high,
                    "bottom": ob_low,
                    "mean_threshold": round((ob_high + ob_low) / 2.0, 5),
                    "mitigated": bool(mitigated),
                    "active": bool(not mitigated and current_price <= ob_high)
                })
                
    return order_blocks
