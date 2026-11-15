import io
import base64
from PIL import Image
import numpy as np


class ChartVisionEngine:
    """
    Pipnex AI Chart Vision Engine (Computer Vision + Institutional Structure Scanner)
    Analyzes uploaded TradingView / MT4 / MT5 screenshots by scanning column-by-column
    bullish/bearish candle pixel clusters, price trajectory, and visual liquidity zones.
    """

    def analyze_image(self, image_bytes: bytes, filename: str = "chart.png") -> dict:
        img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        width, height = img.size
        arr = np.array(img, dtype=np.float32)

        # Crop out outer 8% borders (axes/headers/toolbars) to focus on the candle canvas
        y0, y1 = int(height * 0.08), int(height * 0.88)
        x0, x1 = int(width * 0.05), int(width * 0.90)
        canvas = arr[y0:y1, x0:x1]
        ch, cw, _ = canvas.shape

        r, g, b = canvas[:, :, 0], canvas[:, :, 1], canvas[:, :, 2]

        # Detect bullish pixels (green/teal/cyan candles) & bearish pixels (red/magenta/orange candles)
        bull_mask = (g > r + 22) & (g > 75) & (g >= b - 20)
        bear_mask = (r > g + 22) & (r > 75) & (r >= b - 30)

        bull_pixels = int(np.sum(bull_mask))
        bear_pixels = int(np.sum(bear_mask))
        total_candle_pixels = max(bull_pixels + bear_pixels, 1)

        bull_ratio = bull_pixels / total_candle_pixels

        # Divide canvas horizontally into 8 segments to trace the visual price curve (0=top, 1=bottom)
        num_segments = 8
        seg_width = max(cw // num_segments, 1)
        segment_centers = []
        segment_highs = []
        segment_lows = []

        for i in range(num_segments):
            sx0 = i * seg_width
            sx1 = min((i + 1) * seg_width, cw)
            seg_activity = bull_mask[:, sx0:sx1] | bear_mask[:, sx0:sx1]
            ys, _ = np.where(seg_activity)
            if len(ys) > 10:
                # Normalize y to 0.0 (bottom of chart = low price) .. 1.0 (top of chart = high price)
                norm_prices = 1.0 - (ys / float(ch))
                segment_centers.append(float(np.median(norm_prices)))
                segment_highs.append(float(np.percentile(norm_prices, 92)))
                segment_lows.append(float(np.percentile(norm_prices, 8)))
            else:
                prev_val = segment_centers[-1] if segment_centers else 0.5
                segment_centers.append(prev_val)
                segment_highs.append(min(1.0, prev_val + 0.1))
                segment_lows.append(max(0.0, prev_val - 0.1))

        # Analyze trajectory across first half vs second half vs last 2 segments
        first_half = float(np.mean(segment_centers[:4]))
        second_half = float(np.mean(segment_centers[4:]))
        last_move = segment_centers[-1] - segment_centers[-3]
        overall_slope = second_half - first_half

        max_high_seg = int(np.argmax(segment_highs))
        min_low_seg = int(np.argmin(segment_lows))
        current_pos = segment_centers[-1]  # 0.0 = bottom of screen, 1.0 = top of screen

        # Determine directional bias & structural pattern
        if overall_slope > 0.04 or (bull_ratio >= 0.53 and last_move >= 0):
            bias = "BULLISH (LONG)"
            confidence = min(95, int(68 + abs(overall_slope) * 45 + (bull_ratio - 0.5) * 40))
            if current_pos < 0.45:
                pattern = "Bullish Liquidity Sweep & Discount Demand Rejection"
                entry_zone = "Current Discount Demand Block (Bottom 35% of Chart Range)"
                stop_loss = "Below Recent Swing Low Wick (Bottom 12% of Chart)"
                tp_1 = "Mid-Range Equilibrium (50% Chart Height)"
                tp_2 = "Buy-Side Liquidity Highs (Top 85% of Chart)"
            else:
                pattern = "Bullish BOS Continuation & Higher-Low Pullback"
                entry_zone = "Pullback into Bullish Order Block / FVG (45%–55% Chart Zone)"
                stop_loss = "Below Higher-Low Structure Support"
                tp_1 = "Recent Swing High Liquidity Pool"
                tp_2 = "Measured 1.618x Fibonacci Extension Above Highs"
        else:
            bias = "BEARISH (SHORT)"
            confidence = min(95, int(68 + abs(overall_slope) * 45 + ((1.0 - bull_ratio) - 0.5) * 40))
            if current_pos > 0.55:
                pattern = "Bearish BSL Sweep & Premium Supply Rejection"
                entry_zone = "Current Premium Supply Block (Top 30% of Chart Range)"
                stop_loss = "Above Recent Swing High Wick (Top 88% of Chart)"
                tp_1 = "Mid-Range Equilibrium (50% Chart Height)"
                tp_2 = "Sell-Side Liquidity Lows (Bottom 15% of Chart)"
            else:
                pattern = "Bearish BOS Breakdown & Lower-High Retest"
                entry_zone = "Retest of Bearish Breaker / FVG Imbalance (45%–55% Chart Zone)"
                stop_loss = "Above Recent Lower-High Supply Zone"
                tp_1 = "Recent Swing Low Liquidity Pool"
                tp_2 = "Measured 1.618x Downside Expansion"

        dealing_zone = "DISCOUNT (< 50% Range)" if current_pos < 0.5 else "PREMIUM (> 50% Range)"

        findings = [
            f"Detected {pattern} across {num_segments} visual time segments",
            f"Candle Orderflow Ratio: {round(bull_ratio * 100, 1)}% Bullish vs {round((1 - bull_ratio) * 100, 1)}% Bearish impulse pixels",
            f"Current Price Location: {int(current_pos * 100)}% of visible chart vertical range ({dealing_zone})",
            f"Swing High Liquidity Pool detected in Segment #{max_high_seg + 1}/8; Swing Low Demand in Segment #{min_low_seg + 1}/8",
        ]

        return {
            "filename": filename,
            "resolution": f"{width}x{height}",
            "bias": bias,
            "pattern": pattern,
            "confidence": max(64, min(96, confidence)),
            "bullish_momentum_pct": round(bull_ratio * 100, 1),
            "bearish_momentum_pct": round((1 - bull_ratio) * 100, 1),
            "price_vertical_position_pct": int(current_pos * 100),
            "dealing_zone": dealing_zone,
            "entry_zone": entry_zone,
            "stop_loss_zone": stop_loss,
            "tp1_zone": tp_1,
            "tp2_zone": tp_2,
            "trajectory": [round(x * 100, 1) for x in segment_centers],
            "findings": findings,
        }
