"""Python interface to initialize R server."""

import atexit
import subprocess
import time

import psutil
import requests

from hydroshift.consts import R_SERVER_PORT


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
    """Kill server subprocess."""
    print("Stopping server")
    psutil.Process(pid).terminate()


def start_server():
    """Start an R server."""
    r_server_path = __file__.replace("start_r_server.py", "server.r")
    starter_path = __file__.replace("start_r_server.py", "start_server.r")

    if server_running(R_SERVER_PORT):
        return

    process = subprocess.Popen(["Rscript", starter_path, r_server_path, str(R_SERVER_PORT)])
    pid = process.pid
    atexit.register(lambda: stop_server(pid))

    max_iter = 600
    _iter = 0
    while _iter < max_iter:
        if server_running(R_SERVER_PORT):
            break
        time.sleep(0.1)
        if _iter % 10 == 0:
            print("waiting for server to start")
            _iter += 1
    else:
        raise RuntimeError("Server failed to start after 60 seconds")
    print("Server started")
