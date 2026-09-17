import time
import socket
import psutil
from typing import List, Tuple
from PySide6.QtCore import QThread, Signal

class NetworkMonitor(QThread):
    """
    Background worker thread that samples network I/O counters and connection latency.
    Emits `stats_updated(up_bps, down_bps, total_sent, total_recv, ping_ms)`.
    """
    # upload_bps, download_bps, session_sent_bytes, session_recv_bytes, ping_ms
    stats_updated = Signal(float, float, float, float, int)
    # delta_sent_bytes, delta_recv_bytes
    traffic_delta = Signal(int, int)

    def __init__(self, interval_ms: int = 1000, nic_name: str = "auto", parent=None):
        super().__init__(parent)
        self.interval_sec = max(0.2, interval_ms / 1000.0)
        self.nic_name = nic_name
        self.running = True
        self.last_sent = 0
        self.last_recv = 0
        self.last_time = time.time()
        self.session_sent_start = 0
        self.session_recv_start = 0
        self._init_counters()

    def _init_counters(self):
        sent, recv = self._get_raw_counters()
        self.last_sent = sent
        self.last_recv = recv
        self.last_time = time.time()
        self.session_sent_start = sent
        self.session_recv_start = recv

    @staticmethod
    def get_available_nics() -> List[str]:
        nics = ["auto"]
        try:
            for name in psutil.net_if_addrs().keys():
                nics.append(name)
        except Exception:
            pass
        return nics

    def set_interval(self, ms: int):
        self.interval_sec = max(0.2, ms / 1000.0)

    def set_nic(self, name: str):
        self.nic_name = name
        self._init_counters()

    def _get_raw_counters(self) -> Tuple[int, int]:
        try:
            if self.nic_name == "auto" or not self.nic_name:
                io = psutil.net_io_counters()
                return io.bytes_sent, io.bytes_recv
            else:
                per_nic = psutil.net_io_counters(pernic=True)
                if self.nic_name in per_nic:
                    io = per_nic[self.nic_name]
                    return io.bytes_sent, io.bytes_recv
                # Fallback to total if specified nic not found
                io = psutil.net_io_counters()
                return io.bytes_sent, io.bytes_recv
        except Exception:
            return 0, 0

    def _measure_ping(self) -> int:
        start = time.time()
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(0.35)
            # Cloudflare DNS 1.1.1.1 on DNS port 53
            s.connect(("1.1.1.1", 53))
            s.close()
            return int((time.time() - start) * 1000)
        except Exception:
            return -1

    def run(self):
        ping_counter = 0
        current_ping = -1
        while self.running:
            try:
                time.sleep(self.interval_sec)
                now = time.time()
                elapsed = now - self.last_time
                if elapsed <= 0:
                    elapsed = 1.0

                sent, recv = self._get_raw_counters()
                delta_sent = max(0, sent - self.last_sent)
                delta_recv = max(0, recv - self.last_recv)

                up_rate = max(0.0, delta_sent / elapsed)
                down_rate = max(0.0, delta_recv / elapsed)

                self.last_sent = sent
                self.last_recv = recv
                self.last_time = now

                session_sent = max(0.0, float(sent - self.session_sent_start))
                session_recv = max(0.0, float(recv - self.session_recv_start))

                # Sample ping every 4 cycles to keep network overhead minimal
                ping_counter += 1
                if ping_counter >= 4 or current_ping == -1:
                    ping_counter = 0
                    current_ping = self._measure_ping()

                if self.running:
                    self.stats_updated.emit(up_rate, down_rate, session_sent, session_recv, current_ping)
                    if delta_sent > 0 or delta_recv > 0:
                        self.traffic_delta.emit(int(delta_sent), int(delta_recv))
            except Exception:
                pass

    def stop(self):
        self.running = False
        self.wait(2000)

    @staticmethod
    def format_speed(bytes_per_sec: float) -> str:
        if bytes_per_sec < 1000:
            return f"{int(bytes_per_sec)} B/s"
        elif bytes_per_sec < 1000 * 1000:
            return f"{bytes_per_sec / 1024:.1f} KB/s"
        elif bytes_per_sec < 1000 * 1000 * 1000:
            return f"{bytes_per_sec / (1024 * 1024):.2f} MB/s"
        else:
            return f"{bytes_per_sec / (1024 * 1024 * 1024):.2f} GB/s"

    @staticmethod
    def format_bytes(total_bytes: float) -> str:
        if total_bytes < 1024 * 1024:
            return f"{total_bytes / 1024:.1f} KB"
        elif total_bytes < 1024 * 1024 * 1024:
            return f"{total_bytes / (1024 * 1024):.1f} MB"
        else:
            return f"{total_bytes / (1024 * 1024 * 1024):.2f} GB"
