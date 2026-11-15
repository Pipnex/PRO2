import asyncio
import time
from datetime import datetime
from .prop_pass_calc import calculate_prop_pass_risk
from .scalper_engine import ScalperEngine, SCALPER_BOT_PROFILES


class AutoTraderDaemon:
    """
    Pipnex AI Cloud Bots & 24/7 Autonomous Auto-Trading Engine (CloudBots-qUBVfKqI.js parity).
    Features:
      - Aggressive M1 / Fast Scalper Bot Suite (M1 Turbo-Blitz, M1 Liquidity Sweep, M1 BB Squeeze)
      - Classical M15 Institutional SMC & M5 News Reaction Fade
      - Multi-Pair, Multi-Strategy scanning across live MT5 feed
      - Enforces max_open_positions against actual live MT5 open positions
      - Auto-Breakeven management (moves SL to Entry once position reaches 45% of TP)
      - Categorized real-time logs ('trades', 'signals', 'market', 'errors')
      - 1-Click Test Trade (0.01 lot) verification
    """

    def __init__(self, bridge, confidence_engine, newsiq_engine=None):
        self.bridge = bridge
        self.confidence_engine = confidence_engine
        self.newsiq_engine = newsiq_engine
        self.scalper_engine = ScalperEngine(confidence_engine=confidence_engine)
        self.bot_profiles = SCALPER_BOT_PROFILES

        self.enabled = False
        self.bot_strategy = "m1-turbo-blitz"  # Default to 1-minute aggressive scalper!
        self.symbols = ["XAUUSD", "EURUSD", "GBPUSD", "BTCUSD"]
        self.timeframe = "M1"
        self.execution_mode = "aggressive"
        self.strategy_style = "scalping"
        self.min_confidence = 75
        self.risk_pct = 1.0
        self.fixed_lot = 0.01
        self.use_dynamic_risk = True
        self.max_open_positions = 3
        self.auto_breakeven = True
        self.skip_news_events = True
        self.scan_interval_sec = 5  # Ultra-fast 5-second scan for M1 scalping!

        self.executed_trades = []
        self.activity_log = []
        self.last_scan_time = None
        self.last_trade_bar_by_symbol = {}
        self._task = None

        self.log("Pipnex Cloud Bot Engine initialized with M1 Aggressive Scalper Suite.", category="market")

    def log(self, msg: str, category: str = "market"):
        ts = datetime.now().strftime("%H:%M:%S")
        entry = {"time": ts, "category": category, "text": f"[{ts}] {msg}"}
        self.activity_log.insert(0, entry)
        self.activity_log = self.activity_log[:80]

    def get_status(self) -> dict:
        open_positions = self.bridge.get_open_positions()
        history = self.bridge.get_trade_history(days=30)
        bot_data = self.bridge.get_bot_executions_and_metrics(days=30)
        return {
            "enabled": self.enabled,
            "bot_strategy": self.bot_strategy,
            "bot_profiles": self.bot_profiles,
            "symbols": self.symbols,
            "timeframe": self.timeframe,
            "execution_mode": self.execution_mode,
            "strategy_style": self.strategy_style,
            "min_confidence": self.min_confidence,
            "risk_pct": self.risk_pct,
            "fixed_lot": self.fixed_lot,
            "use_dynamic_risk": self.use_dynamic_risk,
            "max_open_positions": self.max_open_positions,
            "auto_breakeven": self.auto_breakeven,
            "skip_news_events": self.skip_news_events,
            "scan_interval_sec": self.scan_interval_sec,
            "last_scan_time": self.last_scan_time,
            "open_positions_count": len(open_positions),
            "open_positions": open_positions,
            "history_summary": history,
            "metrics": bot_data.get("metrics", {}),
            "executed_trades": bot_data.get("trades", []),
            "activity_log": self.activity_log[:40],
        }

    def clear_history(self) -> dict:
        self.executed_trades = []
        ts = datetime.now().strftime("%H:%M:%S")
        self.activity_log = [
            {"time": ts, "category": "market", "text": f"[{ts}] Bot session history reset to zero. Ready for new testing session."}
        ]
        self.bridge.clear_bot_history()
        return self.get_status()

    def update_config(self, cfg: dict) -> dict:
        if "bot_strategy" in cfg and cfg["bot_strategy"] in self.bot_profiles:
            self.bot_strategy = cfg["bot_strategy"]
            prof = self.bot_profiles[self.bot_strategy]
            if "timeframe" not in cfg:
                self.timeframe = prof.get("timeframe", self.timeframe)
            if "scan_interval_sec" not in cfg:
                self.scan_interval_sec = prof.get("scan_interval_sec", self.scan_interval_sec)

        if "symbols" in cfg and isinstance(cfg["symbols"], list) and len(cfg["symbols"]) > 0:
            self.symbols = [s.strip().upper() for s in cfg["symbols"] if s.strip()]
        if "timeframe" in cfg:
            self.timeframe = str(cfg["timeframe"]).upper()
        if "execution_mode" in cfg:
            self.execution_mode = str(cfg["execution_mode"]).lower()
        if "strategy_style" in cfg:
            self.strategy_style = str(cfg["strategy_style"]).lower()
        if "min_confidence" in cfg:
            self.min_confidence = int(cfg["min_confidence"])
        if "risk_pct" in cfg:
            self.risk_pct = float(cfg["risk_pct"])
        if "fixed_lot" in cfg:
            self.fixed_lot = float(cfg["fixed_lot"])
        if "use_dynamic_risk" in cfg:
            self.use_dynamic_risk = bool(cfg["use_dynamic_risk"])
        if "max_open_positions" in cfg:
            self.max_open_positions = int(cfg["max_open_positions"])
        if "auto_breakeven" in cfg:
            self.auto_breakeven = bool(cfg["auto_breakeven"])
        if "skip_news_events" in cfg:
            self.skip_news_events = bool(cfg["skip_news_events"])
        if "scan_interval_sec" in cfg:
            self.scan_interval_sec = max(3, int(cfg["scan_interval_sec"]))

        if "enabled" in cfg:
            new_state = bool(cfg["enabled"])
            if new_state and not self.enabled:
                self.start()
            elif not new_state and self.enabled:
                self.stop()

        return self.get_status()

    def start(self):
        self.enabled = True
        prof = self.bot_profiles.get(self.bot_strategy, {})
        bot_label = prof.get("name", self.bot_strategy)
        self.log(
            f"CLOUD BOT STARTED — [{bot_label}] Scanning {', '.join(self.symbols)} ({self.timeframe}) every {self.scan_interval_sec}s | "
            f"Mode: {self.execution_mode.upper()} | Min Confidence: {self.min_confidence}%",
            category="signals",
        )
        if self._task is None or self._task.done():
            loop = asyncio.get_event_loop()
            self._task = loop.create_task(self._run_loop())

    def stop(self):
        self.enabled = False
        self.log("CLOUD BOT PAUSED by user.", category="market")

    def execute_test_trade(self, symbol: str = "XAUUSD") -> dict:
        """
        1-Click 0.01 Lot Test Trade with the active bot strategy.
        """
        tf = "M1" if self.bot_strategy.startswith("m1-") else self.timeframe
        df = self.bridge.get_candles(symbol=symbol, timeframe=tf, count=150)
        
        if self.bot_strategy.startswith("m1-"):
            setup = self.scalper_engine.analyze_scalp(df, symbol=symbol, bot_id=self.bot_strategy)
        else:
            setup = self.confidence_engine.analyze(
                df, symbol=symbol, timeframe=tf, execution_mode="aggressive"
            )
            
        res = self.bridge.execute_signal(setup, lot_size=0.01, execution_override=setup["direction"])
        if res.get("status") in ("EXECUTED_LIVE", "SIMULATED_EXECUTION"):
            self.log(f"TEST TRADE FIRED [{self.bot_strategy}]: {res.get('message')}", category="trades")
            self.executed_trades.insert(0, {
                "time": datetime.now().strftime("%H:%M:%S"),
                "symbol": symbol,
                "direction": setup["direction"],
                "lots": 0.01,
                "entry": res.get("entry"),
                "sl": res.get("sl"),
                "tp": res.get("tp"),
                "confidence": setup["confidence"],
                "status": res.get("status"),
                "ticket": res.get("ticket", 0),
            })
        else:
            self.log(f"TEST TRADE ERROR on {symbol}: {res.get('message')}", category="errors")
        return res

    def _manage_breakeven(self, open_positions: list):
        if not self.auto_breakeven or not open_positions:
            return
        for pos in open_positions:
            entry = float(pos["price_open"])
            curr = float(pos["price_current"])
            sl = float(pos["sl"])
            tp = float(pos["tp"])
            if tp <= 0 or sl <= 0:
                continue
            if pos["type"] == "BUY":
                target_dist = tp - entry
                current_gain = curr - entry
                if target_dist > 0 and current_gain >= (target_dist * 0.45) and sl < entry:
                    if self.bridge.modify_position_sl(pos["ticket"], entry, tp, pos["symbol"]):
                        self.log(f"Auto-Breakeven: Moved SL to Entry ({entry}) on #{pos['ticket']} ({pos['symbol']})", category="trades")
            else:
                target_dist = entry - tp
                current_gain = entry - curr
                if target_dist > 0 and current_gain >= (target_dist * 0.45) and sl > entry:
                    if self.bridge.modify_position_sl(pos["ticket"], entry, tp, pos["symbol"]):
                        self.log(f"Auto-Breakeven: Moved SL to Entry ({entry}) on #{pos['ticket']} ({pos['symbol']})", category="trades")

    async def _run_loop(self):
        while self.enabled:
            try:
                self.last_scan_time = datetime.now().strftime("%H:%M:%S")
                mt5_status = self.bridge.initialize()
                balance = 10000.0
                if mt5_status.get("account") and mt5_status["account"].get("balance"):
                    balance = float(mt5_status["account"]["balance"])

                open_positions = self.bridge.get_open_positions()
                self._manage_breakeven(open_positions)

                if len(open_positions) >= self.max_open_positions:
                    self.log(
                        f"Max open positions reached ({len(open_positions)}/{self.max_open_positions}). Monitoring active trades.",
                        category="market",
                    )
                    await asyncio.sleep(self.scan_interval_sec)
                    continue

                if self.skip_news_events and self.newsiq_engine:
                    guard = self.newsiq_engine.get_guard_status(blackout_minutes_before=30, blackout_minutes_after=15)
                    if not guard.get("safe_to_trade", True):
                        self.log(
                            f"NewsIQ Guard: {guard.get('badge', 'PAUSED')} — {guard.get('reason', 'Upcoming high impact release')}",
                            category="market"
                        )
                        await asyncio.sleep(self.scan_interval_sec)
                        continue

                for sym in self.symbols:
                    if not self.enabled:
                        break

                    # Check if symbol already has an open position
                    if any( sym in p["symbol"].upper() for p in open_positions ):
                        continue

                    tf = "M1" if self.bot_strategy.startswith("m1-") else self.timeframe
                    df = self.bridge.get_candles(symbol=sym, timeframe=tf, count=220)
                    last_bar_time = int(df["time"].iloc[-1])

                    # Prevent rapid re-firing on the exact same M1 candle
                    if self.last_trade_bar_by_symbol.get(sym) == last_bar_time:
                        continue

                    if self.bot_strategy.startswith("m1-"):
                        setup = self.scalper_engine.analyze_scalp(df, symbol=sym, bot_id=self.bot_strategy)
                    elif self.bot_strategy == "news-fade" and self.newsiq_engine:
                        setup = self.confidence_engine.analyze(
                            df, symbol=sym, timeframe="M5", execution_mode=self.execution_mode, strategy_style="scalping"
                        )
                    else:
                        setup = self.confidence_engine.analyze(
                            df,
                            symbol=sym,
                            timeframe=self.timeframe,
                            execution_mode=self.execution_mode,
                            strategy_style=self.strategy_style,
                        )

                    conf = setup["confidence"]
                    direction = setup["direction"]
                    order_type = setup["execution"]["order_type"]

                    if conf >= self.min_confidence:
                        if self.use_dynamic_risk:
                            risk_info = calculate_prop_pass_risk(
                                account_balance=balance,
                                risk_pct=self.risk_pct,
                                entry_price=setup["entry"],
                                stop_loss=setup["stop_loss"],
                                symbol=sym,
                            )
                            lots = max(0.01, float(risk_info["recommended_lot_size"]))
                        else:
                            lots = self.fixed_lot

                        self.log(
                            f"SIGNAL DETECTED: {sym} {order_type} ({conf}% Grade {setup['grade']}) — Firing {lots} lots...",
                            category="signals",
                        )
                        res = self.bridge.execute_signal(setup, lot_size=lots)
                        self.last_trade_bar_by_symbol[sym] = last_bar_time

                        trade_record = {
                            "time": datetime.now().strftime("%H:%M:%S"),
                            "symbol": sym,
                            "direction": order_type,
                            "lots": lots,
                            "entry": res.get("entry", setup["entry"]),
                            "sl": res.get("sl", setup["stop_loss"]),
                            "tp": res.get("tp", setup["take_profit_2"]),
                            "confidence": conf,
                            "status": res.get("status", "UNKNOWN"),
                            "ticket": res.get("ticket", 0),
                            "message": res.get("message", ""),
                        }
                        self.executed_trades.insert(0, trade_record)
                        cat = "trades" if "EXECUTED" in str(res.get("status")) or "SIMULATED" in str(res.get("status")) else "errors"
                        self.log(f"{res.get('message')}", category=cat)
                    else:
                        self.log(
                            f"Scanned {sym} ({self.timeframe}): {direction} {conf}% (Need >= {self.min_confidence}%)",
                            category="market",
                        )

            except Exception as e:
                self.log(f"Auto-Trade scan error: {str(e)}", category="errors")

            await asyncio.sleep(self.scan_interval_sec)
