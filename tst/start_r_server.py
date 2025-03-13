import atexit
import subprocess
import time

import psutil
import requests


def server_running(port: str) -> bool:
    """Check if server is running."""
    try:
        resp = requests.get(f"http://127.0.0.1:{port}/ping")
    except:
        return False
    if resp.status_code == 200:
        return True
    else:
        return False


def stop_server(pid: int):
    print("Stopping server")
    psutil.Process(pid).terminate()


def start_server():
    r_server_path = __file__.replace("start_r_server.py", "server.r")
    starter_path = __file__.replace("start_r_server.py", "start_server.r")
    port = "9999"

    if server_running(port):
        return

    process = subprocess.Popen(["Rscript", starter_path, r_server_path, port])
    pid = process.pid
    atexit.register(lambda: stop_server(pid))

    max_iter = 600
    _iter = 0
    while _iter < max_iter:
        if server_running(port):
            break
        time.sleep(0.1)
        if _iter % 10 == 0:
            print("waiting for server to start")
            _iter += 1
    else:
        raise RuntimeError("Server failed to start after 60 seconds")
    print("Server started")
