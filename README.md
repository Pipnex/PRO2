# Pipnex AI — Full Architecture & SMC Engine

An institutional-grade AI trading platform and Market Brain reverse-engineered and built to reproduce the exact capabilities and logics of **Pipnex AI** (`pipnex-ai.com`), including its **Trade Lens** TradingView extension, **PropPass™** risk protection, and direct **MetaTrader 5 (MT5)** execution bridge.

---

## Architecture Breakdown

```
pipnex_ai/
├── core/                           # The "Market Brain" Logic Engine
│   ├── market_structure.py         # Swings, Break of Structure (BOS), Change of Character (CHOCH)
│   ├── order_blocks.py             # Bullish & Bearish Institutional Order Blocks (Supply/Demand)
│   ├── fair_value_gaps.py          # 3-Candle Imbalance (FVG) & Consequent Encroachment (50%)
│   ├── liquidity_sweeps.py         # Buy-Side (BSL) & Sell-Side (SSL) Sweep & Rejection Wicks
│   ├── confidence_engine.py        # Multi-factor confluence scoring (0-100%) & Trade Plan Generator
│   ├── prop_pass_calc.py           # Prop firm risk engine (FTMO, FundedNext, 0.5% risk lot-sizing)
│   └── chart_vision.py             # Vision AI chart image parser
├── mt5/
│   └── mt5_bridge.py               # Live Python bridge to local MetaTrader 5 terminal
├── server/
│   └── app.py                      # Async REST API & Web Dashboard Server (port 8899)
├── web/
│   └── index.html                  # Pipnex-style luxury fintech dark dashboard
├── extension/                      # "Pipnex Trade Lens" Chrome Extension
│   ├── manifest.json               # Manifest V3 configuration
│   ├── content.js                  # Injects HUD directly on TradingView charts
│   └── styles.css                  # Floating HUD styling matching TradingView dark mode
├── START_PIPNEX_AI.bat             # Desktop one-click launcher
└── test_engine.py                  # Full end-to-end diagnostic & verification script
```

---

## The Core Trading Logics Reconstructed

### 1. Market Structure & Shifts
* **BOS (Break of Structure):** Identifies trend continuation when price breaks and closes past recent swing highs/lows.
* **CHOCH (Change of Character / MSS):** Identifies institutional trend reversals when price breaks counter-trend swing points with displacement.

### 2. Institutional Order Blocks (OB)
* **Demand Zones (Bullish OB):** Last down-close candle before an aggressive expansion rally breaking structure. Tracks unmitigated zones where institutions hold resting limit orders.
* **Supply Zones (Bearish OB):** Last up-close candle before an aggressive displacement drop breaking structure.

### 3. Fair Value Gaps (FVG) & Imbalance
* Identifies 3-candle price inefficiencies where aggressive orders skipped liquidity.
* Computes the **50% Consequent Encroachment (CE)** level for optimal entry.

### 4. Liquidity Sweeps (Stop Hunts)
* Detects when price spikes above previous swing highs (BSL) or below swing lows (SSL) to harvest retail stops and immediately rejects with a long wick (>35% of candle range).

### 5. Multi-Factor AI Confidence Scoring (0–100%)
Combines:
* Market Structure Trend (25 pts)
* 50 / 200 EMA Macro Alignment (15 pts)
* Recent Liquidity Sweep (25 pts)
* Unmitigated Order Block Retest (20 pts)
* Fair Value Gap Overlap (15 pts)
* RSI Momentum Confirmation (10 pts)
* Dynamic ATR Stop Loss & Target Calculation (TP1 = 1:2 R:R, TP2 = 1:3.5 R:R, TP3 = 1:5 R:R).

---

## How to Run

### Step 1: Launch the System
Double-click `START_PIPNEX_AI.bat` on your Desktop (or run `python server/app.py`).
The server will start on:
👉 **`http://localhost:8899`**

### Step 2: Open the Web Dashboard
Open your browser to `http://localhost:8899`. You will see:
* Live market structure & bias for Gold (XAUUSD), EURUSD, GBPUSD, etc.
* The Trade Lens Interactive Chart with drawn Order Block boxes and FVG zones.
* 1-Click **"Execute on MetaTrader 5"** button.
* **PropPass™ Calculator** for FTMO/FundedNext accounts.
* **Chart Vision AI Analyzer** for uploading screenshots.

### Step 3: Install the Trade Lens Chrome Extension on TradingView
1. Open Google Chrome and go to `chrome://extensions/`.
2. Turn ON **"Developer mode"** in the top right.
3. Click **"Load unpacked"** and select the folder:
   `c:\Users\USER\Desktop\pipnex_ai\extension`
4. Open any chart on **TradingView** (`tradingview.com/chart`).
5. You will see the floating **PIPNEX LENS** widget appear on your chart!
6. Click **"⚡ Analyze Market Structure"** to get live bias, Entry, SL, and TP, and click **"Dispatch Trade to MT5"** right from your TradingView screen!
