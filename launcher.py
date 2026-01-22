import sys
import os
import socket
import webbrowser
import time

if getattr(sys, 'frozen', False):
    base_path = sys._MEIPASS
else:
    base_path = os.path.dirname(os.path.abspath(__file__))

os.chdir(base_path)
sys.path.insert(0, base_path)

LOCK_FILE = os.path.expanduser("~/.youtube_downloader.lock")
PORT = 8501

def is_port_in_use(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) == 0

def read_lock_file():
    if os.path.exists(LOCK_FILE):
        try:
            with open(LOCK_FILE, 'r') as f:
                return int(f.read().strip())
        except:
            return None
    return None

def write_lock_file(port):
    with open(LOCK_FILE, 'w') as f:
        f.write(str(port))

def remove_lock_file():
    if os.path.exists(LOCK_FILE):
        os.remove(LOCK_FILE)

if __name__ == '__main__':
    existing_port = read_lock_file()

    if existing_port and is_port_in_use(existing_port):
        webbrowser.open(f'http://localhost:{existing_port}')
        sys.exit(0)

    remove_lock_file()

    if is_port_in_use(PORT):
        remove_lock_file()
        sys.exit(1)

    write_lock_file(PORT)

    from streamlit.web import cli as stcli
    sys.argv = ['streamlit', 'run', os.path.join(base_path, 'app.py'),
                '--server.headless', 'false',
                '--server.port', str(PORT),
                '--browser.gatherUsageStats', 'false',
                '--global.developmentMode', 'false']

    try:
        stcli.main()
    finally:
        remove_lock_file()
