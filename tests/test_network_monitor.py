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

    def test_get_available_nics(self):
        nics = NetworkMonitor.get_available_nics()
        self.assertIsInstance(nics, list)
        self.assertIn("auto", nics)

if __name__ == "__main__":
    unittest.main()
