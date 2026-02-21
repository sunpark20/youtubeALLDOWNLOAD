import sys
import threading
import time

sys.path.insert(0, "/Users/sunguk/0.code/new/youtubeALLDOWNLOAD/src")

from src.main import start_fastapi_server

server_thread = threading.Thread(target=start_fastapi_server, daemon=True)
server_thread.start()

try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print("Exiting")
