import os
import sqlite3
import datetime
from pathlib import Path
from contextlib import contextmanager
from typing import List, Dict, Any, Tuple, Optional


class TrafficHistory:
    """
    Manages persistent logging and aggregation of network data usage
    (daily, weekly, monthly, and custom month periods) using a lightweight SQLite database.
    """

    MONTH_NAMES_ID = [
        "", "Januari", "Februari", "Maret", "April", "Mei", "Juni",
        "Juli", "Agustus", "September", "Oktober", "November", "Desember"
    ]

    def __init__(self, db_path: Optional[str] = None):
        if db_path is None:
            base_dir = Path.home() / ".speed_meter"
            base_dir.mkdir(parents=True, exist_ok=True)
            self.db_path = str(base_dir / "traffic_history.db")
        else:
            self.db_path = db_path
            Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)

        self._buffer_sent = 0
        self._buffer_recv = 0
        self._buffer_hour_key: Optional[str] = None
        self._init_db()

    @contextmanager
    def _get_db(self):
        conn = sqlite3.connect(self.db_path, timeout=10.0)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()

    def _init_db(self):
        with self._get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS hourly_traffic (
                    hour_key TEXT PRIMARY KEY,
                    date_str TEXT NOT NULL,
                    year_month TEXT NOT NULL,
                    hour INTEGER NOT NULL,
                    bytes_sent INTEGER NOT NULL DEFAULT 0,
                    bytes_recv INTEGER NOT NULL DEFAULT 0
                )
            """)
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_traffic_date ON hourly_traffic(date_str)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_traffic_month ON hourly_traffic(year_month)")
            conn.commit()

    def record_delta(self, sent_bytes: int, recv_bytes: int, dt: Optional[datetime.datetime] = None):
        """
        Accumulates delta bytes into memory buffer and flushes to database periodically.
        """
        if sent_bytes <= 0 and recv_bytes <= 0:
            return

        if dt is None:
            dt = datetime.datetime.now()

        hour_key = dt.strftime("%Y-%m-%d-%H")

        if self._buffer_hour_key != hour_key and self._buffer_hour_key is not None:
            self.flush()

        self._buffer_hour_key = hour_key
        self._buffer_sent += int(sent_bytes)
        self._buffer_recv += int(recv_bytes)

        # Auto-flush if buffered bytes exceed 5 MB or periodically called
        if (self._buffer_sent + self._buffer_recv) > 5 * 1024 * 1024:
            self.flush()

    def flush(self):
        """Writes buffered traffic into the SQLite database."""
        if not self._buffer_hour_key or (self._buffer_sent <= 0 and self._buffer_recv <= 0):
            return

        try:
            parts = self._buffer_hour_key.split("-")
            date_str = f"{parts[0]}-{parts[1]}-{parts[2]}"
            year_month = f"{parts[0]}-{parts[1]}"
            hour = int(parts[3])

            with self._get_db() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO hourly_traffic (hour_key, date_str, year_month, hour, bytes_sent, bytes_recv)
                    VALUES (?, ?, ?, ?, ?, ?)
                    ON CONFLICT(hour_key) DO UPDATE SET
                        bytes_sent = bytes_sent + excluded.bytes_sent,
                        bytes_recv = bytes_recv + excluded.bytes_recv
                """, (
                    self._buffer_hour_key, date_str, year_month, hour,
                    self._buffer_sent, self._buffer_recv
                ))
                conn.commit()

            self._buffer_sent = 0
            self._buffer_recv = 0
            self._buffer_hour_key = None
        except Exception as e:
            print(f"[TrafficHistory] Flush error: {e}")

    def get_today_hourly(self, dt: Optional[datetime.date] = None) -> List[Dict[str, Any]]:
        """Returns 24 hours breakdown for today (00:00 to 23:00)."""
        self.flush()
        if dt is None:
            dt = datetime.date.today()
        date_str = dt.strftime("%Y-%m-%d")

        data_map = {}
        with self._get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT hour, bytes_sent, bytes_recv
                FROM hourly_traffic
                WHERE date_str = ?
                ORDER BY hour ASC
            """, (date_str,))
            for row in cursor.fetchall():
                data_map[row["hour"]] = (row["bytes_sent"], row["bytes_recv"])

        result = []
        for h in range(24):
            sent, recv = data_map.get(h, (0, 0))
            result.append({
                "label": f"{h:02d}:00",
                "short_label": f"{h:02d}",
                "key": f"{date_str}-{h:02d}",
                "bytes_sent": sent,
                "bytes_recv": recv,
                "total_bytes": sent + recv
            })
        return result

    def get_last_7_days(self, end_dt: Optional[datetime.date] = None) -> List[Dict[str, Any]]:
        """Returns daily usage for the last 7 days (including today)."""
        self.flush()
        if end_dt is None:
            end_dt = datetime.date.today()

        date_list = [end_dt - datetime.timedelta(days=i) for i in reversed(range(7))]
        min_date = date_list[0].strftime("%Y-%m-%d")
        max_date = date_list[-1].strftime("%Y-%m-%d")

        data_map = {}
        with self._get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT date_str, SUM(bytes_sent) as sent, SUM(bytes_recv) as recv
                FROM hourly_traffic
                WHERE date_str BETWEEN ? AND ?
                GROUP BY date_str
            """, (min_date, max_date))
            for row in cursor.fetchall():
                data_map[row["date_str"]] = (row["sent"], row["recv"])

        result = []
        for d in date_list:
            d_str = d.strftime("%Y-%m-%d")
            sent, recv = data_map.get(d_str, (0, 0))
            # Format: '17 Sep'
            month_abbr = ["", "Jan", "Feb", "Mar", "Apr", "Mei", "Jun", "Jul", "Agt", "Sep", "Okt", "Nov", "Des"][d.month]
            result.append({
                "label": f"{d.day} {month_abbr}",
                "short_label": f"{d.day}/{d.month}",
                "key": d_str,
                "bytes_sent": sent,
                "bytes_recv": recv,
                "total_bytes": sent + recv
            })
        return result

    def get_last_30_days(self, end_dt: Optional[datetime.date] = None) -> List[Dict[str, Any]]:
        """Returns daily usage for the last 30 days (including today)."""
        self.flush()
        if end_dt is None:
            end_dt = datetime.date.today()

        date_list = [end_dt - datetime.timedelta(days=i) for i in reversed(range(30))]
        min_date = date_list[0].strftime("%Y-%m-%d")
        max_date = date_list[-1].strftime("%Y-%m-%d")

        data_map = {}
        with self._get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT date_str, SUM(bytes_sent) as sent, SUM(bytes_recv) as recv
                FROM hourly_traffic
                WHERE date_str BETWEEN ? AND ?
                GROUP BY date_str
            """, (min_date, max_date))
            for row in cursor.fetchall():
                data_map[row["date_str"]] = (row["sent"], row["recv"])

        result = []
        for d in date_list:
            d_str = d.strftime("%Y-%m-%d")
            sent, recv = data_map.get(d_str, (0, 0))
            month_abbr = ["", "Jan", "Feb", "Mar", "Apr", "Mei", "Jun", "Jul", "Agt", "Sep", "Okt", "Nov", "Des"][d.month]
            result.append({
                "label": f"{d.day} {month_abbr}",
                "short_label": f"{d.day}",
                "key": d_str,
                "bytes_sent": sent,
                "bytes_recv": recv,
                "total_bytes": sent + recv
            })
        return result

    def get_custom_month(self, year: int, month: int) -> List[Dict[str, Any]]:
        """Returns daily usage for every day in a specified year and month."""
        self.flush()
        year_month = f"{year:04d}-{month:02d}"

        # Determine days in month
        if month == 12:
            next_month = datetime.date(year + 1, 1, 1)
        else:
            next_month = datetime.date(year, month + 1, 1)
        last_day = (next_month - datetime.timedelta(days=1)).day

        data_map = {}
        with self._get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT date_str, SUM(bytes_sent) as sent, SUM(bytes_recv) as recv
                FROM hourly_traffic
                WHERE year_month = ?
                GROUP BY date_str
            """, (year_month,))
            for row in cursor.fetchall():
                data_map[row["date_str"]] = (row["sent"], row["recv"])

        month_abbr = ["", "Jan", "Feb", "Mar", "Apr", "Mei", "Jun", "Jul", "Agt", "Sep", "Okt", "Nov", "Des"][month]
        result = []
        for day in range(1, last_day + 1):
            d_str = f"{year_month}-{day:02d}"
            sent, recv = data_map.get(d_str, (0, 0))
            result.append({
                "label": f"{day} {month_abbr}",
                "short_label": f"{day}",
                "key": d_str,
                "bytes_sent": sent,
                "bytes_recv": recv,
                "total_bytes": sent + recv
            })
        return result

    def get_available_months(self) -> List[Tuple[str, str]]:
        """
        Returns list of (year_month, display_label) available in history.
        Always includes the current month.
        """
        self.flush()
        months_set = set()
        now = datetime.date.today()
        current_ym = now.strftime("%Y-%m-%d")[:7]
        months_set.add(current_ym)

        with self._get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT DISTINCT year_month FROM hourly_traffic ORDER BY year_month DESC")
            for row in cursor.fetchall():
                months_set.add(row["year_month"])

        sorted_months = sorted(list(months_set), reverse=True)
        result = []
        for ym in sorted_months:
            try:
                y, m = ym.split("-")
                month_idx = int(m)
                m_name = self.MONTH_NAMES_ID[month_idx]
                result.append((ym, f"{m_name} {y}"))
            except Exception:
                result.append((ym, ym))
        return result

    @staticmethod
    def get_summary(items: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculates total sent, total recv, combined total, and average per active bucket."""
        total_sent = sum(item["bytes_sent"] for item in items)
        total_recv = sum(item["bytes_recv"] for item in items)
        total_bytes = total_sent + total_recv
        active_count = max(1, len(items))
        avg_bytes = total_bytes / active_count
        peak_bytes = max((item["total_bytes"] for item in items), default=0)

        return {
            "total_sent": total_sent,
            "total_recv": total_recv,
            "total_bytes": total_bytes,
            "avg_bytes": avg_bytes,
            "peak_bytes": peak_bytes
        }

    @staticmethod
    def format_bytes(total_bytes: float) -> str:
        if total_bytes < 1024:
            return f"{int(total_bytes)} B"
        elif total_bytes < 1024 * 1024:
            return f"{total_bytes / 1024:.1f} KB"
        elif total_bytes < 1024 * 1024 * 1024:
            return f"{total_bytes / (1024 * 1024):.2f} MB"
        else:
            return f"{total_bytes / (1024 * 1024 * 1024):.2f} GB"

    def clear_history(self):
        """Clears all historical traffic data."""
        self._buffer_sent = 0
        self._buffer_recv = 0
        self._buffer_hour_key = None
        with self._get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM hourly_traffic")
            conn.commit()
