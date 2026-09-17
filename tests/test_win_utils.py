import unittest
from win_utils import get_taskbar_position, get_tray_wifi_dock_coordinate, set_click_through_native

class TestWinUtils(unittest.TestCase):
    def test_taskbar_detection(self):
        tb = get_taskbar_position()
        self.assertIsInstance(tb, dict)
        self.assertIn("rect", tb)
        self.assertIn("orientation", tb)
        self.assertIn(tb["orientation"], ["bottom", "top", "left", "right"])

    def test_dock_coordinate(self):
        x, y = get_tray_wifi_dock_coordinate(120, 36)
        self.assertIsInstance(x, int)
        self.assertIsInstance(y, int)
        self.assertGreater(x, 0)
        self.assertGreater(y, 0)

    def test_set_click_through_native_with_zero_hwnd(self):
        # 0 hwnd should safely return False without exception
        res = set_click_through_native(0, True)
        self.assertFalse(res)

if __name__ == "__main__":
    unittest.main()
