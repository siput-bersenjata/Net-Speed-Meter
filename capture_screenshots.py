import os
import sys
import datetime
import random
from pathlib import Path
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QCoreApplication

# Ensure project root is on sys.path
_dir = os.path.dirname(os.path.abspath(__file__))
if _dir not in sys.path:
    sys.path.insert(0, _dir)

from config_manager import ConfigManager
from traffic_history import TrafficHistory
from settings_dialog import SettingsDialog
from widget_window import SpeedMeterWidget


def generate_sample_history(history: TrafficHistory):
    """Fills the history database with realistic simulated network traffic."""
    today = datetime.date.today()

    with history._get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM hourly_traffic")

        # Generate last 35 days of data
        for day_offset in range(35):
            d = today - datetime.timedelta(days=day_offset)
            date_str = d.strftime("%Y-%m-%d")
            year_month = date_str[:7]

            for h in range(24):
                hour_key = f"{date_str}-{h:02d}"

                # Create realistic traffic curve based on hour
                if 1 <= h <= 6:
                    # Overnight idle
                    base_recv = random.randint(15 * 1024 * 1024, 80 * 1024 * 1024)
                    base_sent = random.randint(5 * 1024 * 1024, 25 * 1024 * 1024)
                elif 8 <= h <= 17:
                    # Daytime work & browsing
                    base_recv = random.randint(250 * 1024 * 1024, 1200 * 1024 * 1024)
                    base_sent = random.randint(80 * 1024 * 1024, 380 * 1024 * 1024)
                elif 18 <= h <= 23:
                    # Evening peak streaming & gaming
                    base_recv = random.randint(800 * 1024 * 1024, 2800 * 1024 * 1024)
                    base_sent = random.randint(150 * 1024 * 1024, 650 * 1024 * 1024)
                else:
                    base_recv = random.randint(100 * 1024 * 1024, 400 * 1024 * 1024)
                    base_sent = random.randint(30 * 1024 * 1024, 120 * 1024 * 1024)

                cursor.execute("""
                    INSERT INTO hourly_traffic (hour_key, date_str, year_month, hour, bytes_sent, bytes_recv)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (hour_key, date_str, year_month, h, base_sent, base_recv))

        conn.commit()


def main():
    app = QApplication.instance()
    if not app:
        app = QApplication(sys.argv)

    assets_dir = Path(_dir) / "assets"
    assets_dir.mkdir(parents=True, exist_ok=True)

    db_path = Path(_dir) / "temp_screenshot_traffic.db"
    history = TrafficHistory(db_path=str(db_path))
    generate_sample_history(history)

    config_path = Path(_dir) / "temp_screenshot_config.json"
    config = ConfigManager(filepath=str(config_path))
    config.set("shape_template", "pill")
    config.set("up_color", "#00E676")
    config.set("down_color", "#00E5FF")

    # 1. Capture Settings Dialog - Riwayat & Statistik
    dialog = SettingsDialog(config_manager=config, traffic_history=history)
    dialog.show()

    # Switch to History tab (Tab index 2)
    dialog.tabs.setCurrentIndex(2)
    # Select 7 Hari Terakhir (week) for great looking bars
    idx_week = dialog.combo_history_period.findData("week")
    if idx_week >= 0:
        dialog.combo_history_period.setCurrentIndex(idx_week)
    QCoreApplication.processEvents()

    pix_history = dialog.grab()
    history_png = assets_dir / "settings_history.png"
    pix_history.save(str(history_png), "PNG")
    print(f"[OK] Saved {history_png}")

    # 2. Capture Settings Dialog - Tampilan & Ukuran
    dialog.tabs.setCurrentIndex(1)
    QCoreApplication.processEvents()
    pix_app = dialog.grab()
    app_png = assets_dir / "settings_appearance.png"
    pix_app.save(str(app_png), "PNG")
    print(f"[OK] Saved {app_png}")

    # 3. Capture Settings Dialog - Umum
    dialog.tabs.setCurrentIndex(0)
    QCoreApplication.processEvents()
    pix_gen = dialog.grab()
    gen_png = assets_dir / "settings_general.png"
    pix_gen.save(str(gen_png), "PNG")
    print(f"[OK] Saved {gen_png}")

    dialog.close()

    # 4. Capture Floating Widget in Capsule Mode
    widget = SpeedMeterWidget(config_manager=config)
    widget.set_mode("capsule")
    widget.set_shape_template("pill")
    widget.show()
    widget.update_stats(
        12.8 * 1024 * 1024,
        48.5 * 1024 * 1024,
        1024 * 1024 * 1024 * 15,
        1024 * 1024 * 1024 * 68,
        14
    )
    widget.adjustSize()
    QCoreApplication.processEvents()
    pix_widget_capsule = widget.grab()
    widget_capsule_png = assets_dir / "widget_capsule.png"
    pix_widget_capsule.save(str(widget_capsule_png), "PNG")
    print(f"[OK] Saved {widget_capsule_png}")

    # 5. Capture Floating Widget in Card Mode
    widget.set_mode("card")
    widget.set_shape_template("rounded")
    widget.resize(230, 100)
    widget.show()
    widget.adjustSize()
    QCoreApplication.processEvents()
    pix_widget_card = widget.grab()
    widget_card_png = assets_dir / "widget_card.png"
    pix_widget_card.save(str(widget_card_png), "PNG")
    print(f"[OK] Saved {widget_card_png}")

    # 6. Capture Text Only Mode
    widget.set_mode("capsule")
    widget.set_shape_template("text_only")
    widget.show()
    widget.adjustSize()
    QCoreApplication.processEvents()
    pix_widget_text = widget.grab()
    widget_text_png = assets_dir / "widget_text_only.png"
    pix_widget_text.save(str(widget_text_png), "PNG")
    print(f"[OK] Saved {widget_text_png}")

    widget.close()

    # Clean up temp files
    try:
        if db_path.exists():
            db_path.unlink()
        if config_path.exists():
            config_path.unlink()
    except Exception:
        pass

    print("[SUCCESS] All screenshots generated successfully!")


if __name__ == "__main__":
    main()
