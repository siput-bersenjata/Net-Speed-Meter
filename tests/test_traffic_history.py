import os
import unittest
import tempfile
import datetime
from traffic_history import TrafficHistory

class TestTrafficHistory(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.temp_dir.name, "test_traffic.db")
        self.tracker = TrafficHistory(db_path=self.db_path)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_record_and_flush(self):
        dt = datetime.datetime(2026, 9, 17, 14, 30)
        self.tracker.record_delta(1000, 5000, dt=dt)
        self.tracker.flush()

        hourly = self.tracker.get_today_hourly(dt=dt.date())
        self.assertEqual(len(hourly), 24)
        hour_14 = hourly[14]
        self.assertEqual(hour_14["bytes_sent"], 1000)
        self.assertEqual(hour_14["bytes_recv"], 5000)
        self.assertEqual(hour_14["total_bytes"], 6000)

    def test_last_7_days(self):
        base_date = datetime.date(2026, 9, 17)
        for i in range(5):
            d = base_date - datetime.timedelta(days=i)
            dt = datetime.datetime(d.year, d.month, d.day, 10, 0)
            self.tracker.record_delta(2000, 8000, dt=dt)
        self.tracker.flush()

        days = self.tracker.get_last_7_days(end_dt=base_date)
        self.assertEqual(len(days), 7)
        summary = self.tracker.get_summary(days)
        self.assertEqual(summary["total_sent"], 10000)
        self.assertEqual(summary["total_recv"], 40000)
        self.assertEqual(summary["total_bytes"], 50000)

    def test_custom_month(self):
        dt = datetime.datetime(2026, 9, 5, 12, 0)
        self.tracker.record_delta(500, 1500, dt=dt)
        self.tracker.flush()

        month_data = self.tracker.get_custom_month(2026, 9)
        self.assertEqual(len(month_data), 30)  # September has 30 days
        day_5 = month_data[4]
        self.assertEqual(day_5["bytes_sent"], 500)
        self.assertEqual(day_5["bytes_recv"], 1500)

    def test_available_months(self):
        dt = datetime.datetime(2026, 8, 10, 10, 0)
        self.tracker.record_delta(100, 200, dt=dt)
        self.tracker.flush()

        months = self.tracker.get_available_months()
        yms = [m[0] for m in months]
        self.assertIn("2026-08", yms)

if __name__ == "__main__":
    unittest.main()
