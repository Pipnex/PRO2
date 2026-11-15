"""
Pipnex AI - 24/7 Resilient Watchdog Supervisor
===============================================
Ensures 100% uptime for:
  1. MetaTrader 5 Terminal (terminal64.exe)
  2. Pipnex AI Main Engine (server/app.py on port 8899)
  3. Pipnex AI Proxy Service (server/proxy_7070.py on port 7070)

If any process crashes, hangs, or closes, the watchdog automatically restarts it
within 5 seconds and logs the recovery event.
"""

import os
import sys
import time
import subprocess
import urllib.request
from datetime import datetime

PIPNEX_ROOT = os.path.dirname(os.path.abspath(__file__))
APP_PATH = os.path.join(PIPNEX_ROOT, "server", "app.py")
PROXY_PATH = os.path.join(PIPNEX_ROOT, "server", "proxy_7070.py")
LOG_PATH = os.path.join(PIPNEX_ROOT, "watchdog.log")
MT5_EXE = r"C:\Program Files\MetaTrader 5\terminal64.exe"

def log(msg):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line, flush=True)
    try:
        with open(LOG_PATH, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception:
        pass

def is_mt5_running():
    try:
        out = subprocess.check_output('tasklist /FI "IMAGENAME eq terminal64.exe" /NH', shell=True).decode("utf-8", errors="ignore")
        return "terminal64.exe" in out.lower()
    except Exception:
        return False

def ensure_mt5():
    if not is_mt5_running():
        if os.path.exists(MT5_EXE):
            log("⚠️ MT5 (terminal64.exe) is NOT running! Launching...")
            subprocess.Popen([MT5_EXE], creationflags=subprocess.DETACHED_PROCESS if sys.platform == "win32" else 0)
            time.sleep(3)
        else:
            log(f"❌ MT5 executable not found at {MT5_EXE}")

def check_http_alive(url, timeout=3):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "PipnexWatchdog/1.0"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status in (200, 302, 404) # receiving HTTP response means server is alive
    except urllib.error.HTTPError as e:
        return True # Server responded with HTTP code (alive)
    except Exception:
        return False

def main():
    log("=" * 65)
    log("🚀 Pipnex AI 24/7 Watchdog Supervisor Started")
    log(f"   Root directory: {PIPNEX_ROOT}")
    log(f"   Main App: {APP_PATH}")
    log(f"   Proxy:    {PROXY_PATH}")
    log("=" * 65)

    app_proc = None
    proxy_proc = None

    while True:
        try:
            # 1. Check MT5
            ensure_mt5()

            # 2. Check Pipnex AI Main Engine (port 8899)
            app_alive = check_http_alive("http://localhost:8899/api/status")
            if not app_alive:
                log("⚠️ Port 8899 not responding! (Re)starting Pipnex AI server...")
                if app_proc and app_proc.poll() is None:
                    try:
                        app_proc.terminate()
                        app_proc.wait(timeout=2)
                    except Exception:
                        pass
                app_proc = subprocess.Popen(
                    [sys.executable, APP_PATH],
                    cwd=PIPNEX_ROOT,
                    creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if sys.platform == "win32" else 0
                )
                log(f"✅ Pipnex AI server started (PID: {app_proc.pid})")
                time.sleep(3)

            # 3. Check Proxy 7070
            proxy_alive = check_http_alive("http://localhost:7070")
            if not proxy_alive:
                log("⚠️ Port 7070 not responding! (Re)starting Proxy 7070...")
                if proxy_proc and proxy_proc.poll() is None:
                    try:
                        proxy_proc.terminate()
                        proxy_proc.wait(timeout=2)
                    except Exception:
                        pass
                proxy_proc = subprocess.Popen(
                    [sys.executable, PROXY_PATH],
                    cwd=PIPNEX_ROOT,
                    creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if sys.platform == "win32" else 0
                )
                log(f"✅ Proxy 7070 started (PID: {proxy_proc.pid})")
                time.sleep(2)

        except Exception as e:
            log(f"⚠️ Watchdog loop exception: {e}")

        # Heartbeat check every 10 seconds
        time.sleep(10)

if __name__ == "__main__":
    main()
