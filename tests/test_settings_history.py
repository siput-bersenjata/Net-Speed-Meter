import os
import unittest
import tempfile
from PySide6.QtWidgets import QApplication

from config_manager import ConfigManager
from traffic_history import TrafficHistory
from settings_dialog import SettingsDialog

app = QApplication.instance()
if not app:
    app = QApplication([])


class TestSettingsHistory(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.config_file = os.path.join(self.temp_dir.name, "settings.json")
        self.db_file = os.path.join(self.temp_dir.name, "traffic.db")
        self.config = ConfigManager(filepath=self.config_file)
        self.history = TrafficHistory(db_path=self.db_file)

        # Populate sample traffic
        self.history.record_delta(1024 * 1024, 5 * 1024 * 1024)
        self.history.flush()

        self.dialog = SettingsDialog(config_manager=self.config, traffic_history=self.history)

    def tearDown(self):
        self.dialog.close()
        self.temp_dir.cleanup()

    def test_tabs_and_history_components(self):
        self.assertEqual(self.dialog.tabs.count(), 5)
        self.assertIn("Riwayat && Statistik", [self.dialog.tabs.tabText(i) for i in range(5)])

        self.assertTrue(hasattr(self.dialog, "chart_widget"))
        self.assertTrue(hasattr(self.dialog, "table_history"))
        self.assertTrue(hasattr(self.dialog, "lbl_kpi_down"))
        self.assertTrue(hasattr(self.dialog, "lbl_kpi_up"))

    def test_period_switching(self):
        # Default is "today"
        self.assertEqual(self.dialog.combo_history_period.currentData(), "today")
        self.assertGreater(self.dialog.table_history.rowCount(), 0)

        # Switch to "week"
        idx_week = self.dialog.combo_history_period.findData("week")
        self.dialog.combo_history_period.setCurrentIndex(idx_week)
        self.assertEqual(self.dialog.table_history.rowCount(), 7)

        # Switch to "month"
        idx_month = self.dialog.combo_history_period.findData("month")
        self.dialog.combo_history_period.setCurrentIndex(idx_month)
        self.assertEqual(self.dialog.table_history.rowCount(), 30)

    def test_kpi_values_updated(self):
        self.dialog._load_history_data()
        self.assertIn("MB", self.dialog.lbl_kpi_down.text() + self.dialog.lbl_kpi_up.text())


if __name__ == "__main__":
    unittest.main()
