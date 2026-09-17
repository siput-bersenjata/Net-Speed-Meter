import os
import unittest
import tempfile
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt

from config_manager import ConfigManager
from widget_window import SpeedMeterWidget

# Ensure QApplication instance
app = QApplication.instance()
if not app:
    app = QApplication([])

class TestWidgetBehavior(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.config_file = os.path.join(self.temp_dir.name, "settings.json")
        self.config = ConfigManager(filepath=self.config_file)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_shape_template_switching(self):
        widget = SpeedMeterWidget(config_manager=self.config)
        self.assertEqual(widget.config.get("shape_template"), "pill")
        
        widget.set_shape_template("text_only")
        self.assertEqual(widget.config.get("shape_template"), "text_only")
        self.assertIn("background-color: transparent;", widget.styleSheet())
        self.assertIn("border: none;", widget.styleSheet())

        widget.set_shape_template("badge")
        self.assertEqual(widget.config.get("shape_template"), "badge")

    def test_click_through_toggle(self):
        widget = SpeedMeterWidget(config_manager=self.config)
        self.assertFalse(widget.testAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents))

        widget.set_click_through(True)
        self.assertTrue(widget.testAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents))
        self.assertTrue(widget.config.get("click_through"))

        widget.set_click_through(False)
        self.assertFalse(widget.testAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents))
        self.assertFalse(widget.config.get("click_through"))

    def test_zero_opacity_theme(self):
        widget = SpeedMeterWidget(config_manager=self.config)
        self.config.set("opacity", 0.0)
        widget.apply_theme()
        self.assertIn("background-color: transparent;", widget.styleSheet())
        self.assertIn("border: none;", widget.styleSheet())

    def test_session_preservation_on_mode_change(self):
        widget = SpeedMeterWidget(config_manager=self.config)
        widget.update_stats(100.0, 200.0, 1024 * 1024 * 9.8, 1024 * 326.3, 27)
        self.assertEqual(widget.current_total_sent, 1024 * 1024 * 9.8)

        # Switch to card mode
        widget.set_mode("card")
        self.assertTrue(hasattr(widget, "session_label"))
        self.assertIn("9.8 MB", widget.session_label.text())
        self.assertIn("326.3 KB", widget.session_label.text())

        # Simulate applying settings again without mode change
        widget.set_mode("card")
        self.assertIn("9.8 MB", widget.session_label.text())
        self.assertIn("326.3 KB", widget.session_label.text())

    def test_mode_switching_from_docked_taskbar(self):
        widget = SpeedMeterWidget(config_manager=self.config)
        # Dock to taskbar
        widget.dock_to_taskbar(True)
        self.assertEqual(widget.mode, "taskbar")
        self.assertTrue(self.config.get("is_taskbar_docked"))

        # User selects card mode in settings
        widget.set_mode("card")
        self.assertEqual(widget.mode, "card")
        self.assertFalse(self.config.get("is_taskbar_docked"))

        # User selects capsule mode in settings
        widget.set_mode("capsule")
        self.assertEqual(widget.mode, "capsule")
        self.assertFalse(self.config.get("is_taskbar_docked"))

if __name__ == "__main__":
    unittest.main()
