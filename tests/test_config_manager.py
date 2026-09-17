import os
import tempfile
import unittest
from config_manager import ConfigManager

class TestConfigManager(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.config_file = os.path.join(self.temp_dir.name, "settings.json")

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_config_defaults(self):
        cfg = ConfigManager(filepath=self.config_file)
        self.assertEqual(cfg.get("widget_mode"), "capsule")
        self.assertTrue(cfg.get("always_on_top"))
        self.assertEqual(cfg.get("opacity"), 0.92)
        self.assertEqual(cfg.get("up_color"), "#00E676")
        self.assertEqual(cfg.get("down_color"), "#00E5FF")
        self.assertFalse(cfg.get("click_through"))
        self.assertEqual(cfg.get("shape_template"), "pill")

    def test_config_save_and_reload(self):
        cfg = ConfigManager(filepath=self.config_file)
        cfg.set("pos_x", 500)
        cfg.set("pos_y", 800)
        cfg.set("widget_mode", "taskbar")

        cfg2 = ConfigManager(filepath=self.config_file)
        self.assertEqual(cfg2.get("pos_x"), 500)
        self.assertEqual(cfg2.get("pos_y"), 800)
        self.assertEqual(cfg2.get("widget_mode"), "taskbar")

if __name__ == "__main__":
    unittest.main()
