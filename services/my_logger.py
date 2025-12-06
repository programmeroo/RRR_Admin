from datetime import datetime
import os
from pathlib import Path


LOGS_FOLDER = r"./logs"

class Logger:
    def __init__(self):
        self.set_logfile(f"log_{datetime.now().strftime('%Y%m%d')}.txt")


    def set_logfile(self, filename):
        os.makedirs(LOGS_FOLDER, exist_ok=True)      
        self.logfile =  os.path.join(LOGS_FOLDER, filename)


    def __call__(self, message):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        entry = f"{timestamp} - {message}"
        print(entry)
        with open(self.logfile, "a", encoding="utf-8") as f:
            f.write(entry + "\n")

log = Logger()