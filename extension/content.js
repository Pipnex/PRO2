/**
 * Pipnex Trade Lens - TradingView Injected Content Script
 * Scrapes current chart symbol/timeframe and queries the local Pipnex Market Brain.
 */

(function () {
  console.log("[Pipnex Trade Lens] Loaded on TradingView.");

  // Inject Floating HUD
  const hud = document.createElement("div");
  hud.id = "pipnex-hud";
  hud.innerHTML = `
    <div class="pipnex-header">
      <div class="pipnex-logo">
        <span>⚡</span> PIPNEX <span>LENS</span>
      </div>
      <div style="display: flex; gap: 6px; align-items: center;">
        <span class="pipnex-badge">ACTIVE</span>
        <button id="pipnex-minimize" style="background: none; border: none; color: #64748b; cursor: pointer; font-size: 14px;">−</button>
      </div>
    </div>

    <div style="font-size: 11px; color: #94a3b8;" id="pipnex-symbol-label">
      Symbol: Detecting...
    </div>

    <button class="pipnex-btn" id="pipnex-scan-btn">
      ⚡ Analyze Market Structure
    </button>

    <div id="pipnex-results" style="display: none; flex-direction: column; gap: 8px;">
      <div style="display: flex; justify-content: space-between; align-items: center;">
        <span style="font-size: 12px; font-weight: 700;" id="pipnex-bias">BIAS: BULLISH</span>
        <span style="font-size: 11px; font-weight: 800; color: #00d2ff;" id="pipnex-conf">94% CONF</span>
      </div>

      <div class="pipnex-levels">
        <div class="pipnex-row"><span style="color: #64748b;">Entry:</span> <strong id="pipnex-entry">2735.50</strong></div>
        <div class="pipnex-row"><span style="color: #64748b;">Stop Loss:</span> <strong id="pipnex-sl" style="color: #ef4444;">2730.00</strong></div>
        <div class="pipnex-row"><span style="color: #64748b;">Target 1 (TP1):</span> <strong id="pipnex-tp1" style="color: #10b981;">2746.50</strong></div>
        <div class="pipnex-row"><span style="color: #64748b;">Risk/Reward:</span> <strong id="pipnex-rr">1:3.2</strong></div>
      </div>

      <button class="pipnex-btn" id="pipnex-mt5-btn" style="background: #10b981; color: #042f1a; margin-top: 4px;">
        ▲ Dispatch Trade to MT5
      </button>
    </div>
  `;

  document.body.appendChild(hud);

  let currentAnalysis = null;

  // Extract symbol from TradingView page
  function getTradingViewSymbol() {
    const title = document.title;
    const parts = title.split(" ");
    let sym = "XAUUSD";
    if (parts.length > 0 && parts[0].length >= 3) {
      sym = parts[0].replace(/[^a-zA-Z0-9]/g, "");
    }
    return sym;
  }

  const sym = getTradingViewSymbol();
  document.getElementById("pipnex-symbol-label").innerText = `Target: ${sym} (TradingView)`;

  // Scan handler
  document.getElementById("pipnex-scan-btn").addEventListener("click", async () => {
    const symbol = getTradingViewSymbol();
    document.getElementById("pipnex-scan-btn").innerText = "Analyzing Market Brain...";

    try {
      const res = await fetch(`http://localhost:8899/api/analyze?symbol=${symbol}`);
      const data = await res.json();
      currentAnalysis = data;

      document.getElementById("pipnex-results").style.display = "flex";
      document.getElementById("pipnex-bias").innerText = `BIAS: ${data.bias}`;
      document.getElementById("pipnex-bias").style.color = data.bias === "BUY" ? "#10b981" : "#ef4444";
      document.getElementById("pipnex-conf").innerText = `${data.confidence_score}% CONF`;

      if (data.trade_setup) {
        document.getElementById("pipnex-entry").innerText = data.trade_setup.entry;
        document.getElementById("pipnex-sl").innerText = data.trade_setup.stop_loss;
        document.getElementById("pipnex-tp1").innerText = data.trade_setup.take_profit_1;
        document.getElementById("pipnex-rr").innerText = data.trade_setup.risk_reward;
      }

      document.getElementById("pipnex-scan-btn").innerText = "⚡ Re-Scan Market";
    } catch (err) {
      alert("Please ensure Pipnex AI server is running at http://localhost:8899");
      document.getElementById("pipnex-scan-btn").innerText = "⚡ Analyze Market Structure";
    }
  });

  // Execute to MT5
  document.getElementById("pipnex-mt5-btn").addEventListener("click", async () => {
    if (!currentAnalysis || !currentAnalysis.trade_setup) return;

    try {
      const res = await fetch("http://localhost:8899/api/execute-trade", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          symbol: getTradingViewSymbol(),
          setup: currentAnalysis.trade_setup,
          lot_size: 0.10
        })
      });
      const resp = await res.json();
      alert(resp.message || "Submitted to MT5!");
    } catch (e) {
      alert("Failed to communicate with Pipnex MT5 Bridge");
    }
  });
})();
