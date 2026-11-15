@echo off
title Pipnex AI - Market Brain, Trade Lens & MT5 Server
color 0B
echo =================================================================
echo                PIPNEX AI - LOCAL SYSTEM LAUNCHER
echo      Institutional SMC Engine - Trade Lens - MT5 Execution
echo =================================================================
echo.
echo [1/2] Connecting to MetaTrader 5 Terminal...
echo [2/2] Starting Pipnex Web Dashboard & Extension API on port 8899...
echo.
echo -> Open in Browser: http://localhost:8899
echo -> Chrome Extension: Load unpacked from "c:\Users\USER\Desktop\pipnex_ai\extension"
echo.
cd /d "c:\Users\USER\Desktop\pipnex_ai\server"
python app.py
pause
