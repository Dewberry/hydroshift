import numpy as np
import requests

from tst.start_r_server import start_server


def cpm_process_stream(x: np.ndarray, cpm_type: str) -> dict:
    """Run a change point analysis with the cpm R package.""" ""
    start_server()
    payload = {"x": x, "cpm_type": cpm_type}
    url = "http://127.0.0.1:9999/process_stream"
    response = requests.get(url, params=payload)
    return response.json()


def cpm_detect_change_point_batch(x: np.ndarray, cpm_type: str) -> dict:
    """Run a change point analysis with the cpm R package.""" ""
    start_server()
    payload = {"x": x, "cpm_type": cpm_type}
    url = "http://127.0.0.1:9999/detect_change_point_batch"
    response = requests.get(url, params=payload)
    return response.json()


def get_batch_threshold(cpm_type: str, alpha: float, n: int) -> float:
    """Run a change point analysis with the cpm R package.""" ""
    start_server()
    payload = {"cpm_type": cpm_type, "alpha": alpha, "n": n}
    url = "http://127.0.0.1:9999/get_batch_threshold"
    response = requests.get(url, params=payload)
    return response.json()[0]
