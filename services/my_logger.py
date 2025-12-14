from datetime import datetime
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# LOGS_FOLDER = os.getenv("LOGS_FOLDER")
LOGS_FOLDER = "..\RRR_LOGS\logs"

class Logger:
    def __init__(self):
        self.set_logfile(f"log_{datetime.now().strftime('%Y%m%d')}.txt")


    def set_logfile(self, filename):
        os.makedirs(LOGS_FOLDER, exist_ok=True)      
        self.logfile =  os.path.join(LOGS_FOLDER, filename)


    def __call__(self, message, severity=None):
        """Log a message with optional severity level (success, info, warning, danger)."""
        # Map severity to emoji
        emoji_map = {
            'success': '✅',
            'info': 'ℹ️',
            'warning': '⚠️',
            'danger': '❌'
        }

        emoji = emoji_map.get(severity, '')
        prefix = f"{emoji} " if emoji else ""

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        entry = f"{timestamp} - {prefix}{message}"
        print(entry)
        with open(self.logfile, "a", encoding="utf-8") as f:
            f.write(entry + "\n")

log = Logger()