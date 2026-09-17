import unittest
from network_monitor import NetworkMonitor

class TestNetworkMonitor(unittest.TestCase):
    def test_format_speed(self):
        self.assertEqual(NetworkMonitor.format_speed(500), "500 B/s")
        self.assertEqual(NetworkMonitor.format_speed(1024), "1.0 KB/s")
        self.assertEqual(NetworkMonitor.format_speed(1024 * 1024 * 2.5), "2.50 MB/s")
        self.assertEqual(NetworkMonitor.format_speed(1024 * 1024 * 1024 * 1.2), "1.20 GB/s")

    def test_format_bytes(self):
        self.assertEqual(NetworkMonitor.format_bytes(1024 * 500), "500.0 KB")
        self.assertEqual(NetworkMonitor.format_bytes(1024 * 1024 * 50), "50.0 MB")
        self.assertEqual(NetworkMonitor.format_bytes(1024 * 1024 * 1024 * 3.5), "3.50 GB")

    def test_session_preservation_on_set_nic_and_interval(self):
        monitor = NetworkMonitor()
        monitor.session_sent_bytes = 1048576.0  # 1 MB
        monitor.session_recv_bytes = 2097152.0  # 2 MB

        # Simulate user applying settings with same or different NIC
        monitor.set_nic("auto")
        self.assertEqual(monitor.session_sent_bytes, 1048576.0)
        self.assertEqual(monitor.session_recv_bytes, 2097152.0)

        # Interval change
        monitor.set_interval(500)
        self.assertEqual(monitor.session_sent_bytes, 1048576.0)
        self.assertEqual(monitor.session_recv_bytes, 2097152.0)

        # Explicit reset
        monitor.reset_session()
        self.assertEqual(monitor.session_sent_bytes, 0.0)
        self.assertEqual(monitor.session_recv_bytes, 0.0)

if __name__ == "__main__":
    unittest.main()
