"""
Watchdog — monitors and auto-restarts the MT5 Bridge process.
Max 3 restarts per hour. Sends Telegram alert on restart.
"""

import os
import subprocess
import sys
import time
from collections import deque
from datetime import datetime

import httpx
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")
MAX_RESTARTS_PER_HOUR = 3

restart_times: deque = deque(maxlen=MAX_RESTARTS_PER_HOUR)


def send_telegram(message: str):
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        return
    try:
        httpx.post(
            f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
            json={"chat_id": TELEGRAM_CHAT_ID, "text": message},
            timeout=10,
        )
    except Exception:
        pass


def run():
    print(f"[Watchdog] Starting MT5 Bridge monitor...")

    while True:
        # Check restart rate limit
        now = time.time()
        recent = [t for t in restart_times if now - t < 3600]
        if len(recent) >= MAX_RESTARTS_PER_HOUR:
            msg = f"[Watchdog] Max restarts ({MAX_RESTARTS_PER_HOUR}/hour) reached. Stopping."
            print(msg)
            send_telegram(f"⛔ MT5 Bridge Watchdog: {msg}")
            sys.exit(1)

        print(f"[Watchdog] Starting MT5 Bridge at {datetime.now()}")
        process = subprocess.Popen(
            [sys.executable, "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001"],
            cwd=os.path.dirname(os.path.abspath(__file__)),
        )

        process.wait()
        exit_code = process.returncode

        restart_times.append(time.time())
        msg = f"🔄 MT5 Bridge crashed (exit code: {exit_code}). Restarting..."
        print(f"[Watchdog] {msg}")
        send_telegram(msg)

        time.sleep(5)  # Brief pause before restart


if __name__ == "__main__":
    run()
