import os
import sys
import shutil
import subprocess
from pathlib import Path
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QIcon, QFont
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QProgressBar, QPushButton, QFrame, QMessageBox
)

import win32com.client
from win_utils import set_windows_autostart


class InstallWorker(QThread):
    progress = Signal(int, str)
    finished_success = Signal(str)
    failed = Signal(str)

    def run(self):
        try:
            self.progress.emit(10, "Mempersiapkan lokasi instalasi...")
            # 1. Target Directory: %LOCALAPPDATA%\Programs\Speed Meter
            local_appdata = os.environ.get("LOCALAPPDATA") or str(Path.home() / "AppData" / "Local")
            dest_dir = os.path.join(local_appdata, "Programs", "Speed Meter")
            os.makedirs(dest_dir, exist_ok=True)

            self.progress.emit(25, "Menyalin file aplikasi...")
            base_dir = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
            payload_dir = os.path.join(base_dir, "app_payload")
            if os.path.exists(payload_dir) and os.path.isdir(payload_dir):
                dist_source = payload_dir
            else:
                dist_source = os.path.join(base_dir, "dist", "Speed Meter")
                if not os.path.exists(dist_source):
                    dist_source = os.path.join(os.path.dirname(os.path.abspath(__file__)), "dist", "Speed Meter")
                if not os.path.exists(dist_source):
                    dist_source = base_dir

            # Copy all files from dist_source to dest_dir
            if os.path.exists(dist_source) and os.path.abspath(dist_source) != os.path.abspath(dest_dir):
                for item in os.listdir(dist_source):
                    s = os.path.join(dist_source, item)
                    d = os.path.join(dest_dir, item)
                    if os.path.isdir(s):
                        if os.path.exists(d):
                            shutil.rmtree(d, ignore_errors=True)
                        shutil.copytree(s, d)
                    else:
                        shutil.copy2(s, d)

            # Copy icons if present
            for icon_name in ["app_icon.ico", "app_icon.png"]:
                icon_src = os.path.join(curr_dir, icon_name)
                if os.path.exists(icon_src):
                    shutil.copy2(icon_src, os.path.join(dest_dir, icon_name))

            target_exe = os.path.join(dest_dir, "Speed Meter.exe")
            target_ico = os.path.join(dest_dir, "app_icon.ico")

            self.progress.emit(60, "Membuat shortcut di Desktop & Start Menu...")
            shell = win32com.client.Dispatch("WScript.Shell")

            # Desktop Shortcuts
            desktop_dir = shell.SpecialFolders("Desktop")
            s1 = shell.CreateShortcut(os.path.join(desktop_dir, "Speed Meter.lnk"))
            s1.TargetPath = target_exe
            s1.WorkingDirectory = dest_dir
            if os.path.exists(target_ico):
                s1.IconLocation = target_ico
            s1.Save()

            s2 = shell.CreateShortcut(os.path.join(desktop_dir, "Pengaturan Speed Meter.lnk"))
            s2.TargetPath = target_exe
            s2.Arguments = "--settings"
            s2.WorkingDirectory = dest_dir
            if os.path.exists(target_ico):
                s2.IconLocation = target_ico
            s2.Save()

            # Start Menu Shortcut
            start_menu_dir = os.path.join(os.environ.get("APPDATA", ""), r"Microsoft\Windows\Start Menu\Programs")
            if os.path.exists(start_menu_dir):
                s3 = shell.CreateShortcut(os.path.join(start_menu_dir, "Speed Meter.lnk"))
                s3.TargetPath = target_exe
                s3.WorkingDirectory = dest_dir
                if os.path.exists(target_ico):
                    s3.IconLocation = target_ico
                s3.Save()

            self.progress.emit(85, "Mengaktifkan auto-run Windows startup...")
            # Autostart Registration
            set_windows_autostart("ModernSpeedMeter", f'"{target_exe}"', enable=True)

            self.progress.emit(95, "Menjalankan widget Speed Meter...")
            # Launch the app immediately on desktop
            try:
                subprocess.Popen([target_exe], cwd=dest_dir)
            except Exception as e:
                print(f"Popen note: {e}")

            self.progress.emit(100, "Instalasi selesai dan aplikasi aktif!")
            self.finished_success.emit(target_exe)

        except Exception as e:
            self.failed.emit(str(e))


class InstallerWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Pemasang Modern Speed Meter")
        self.setFixedSize(480, 260)
        self.setStyleSheet("""
            QWidget {
                background-color: #0F1218;
                color: #F8FAFC;
                font-family: 'Segoe UI Variable Display', 'Segoe UI', sans-serif;
            }
            QLabel#Title {
                font-size: 14pt;
                font-weight: 700;
                color: #38BDF8;
            }
            QLabel#Desc {
                font-size: 9.5pt;
                color: #94A3B8;
            }
            QProgressBar {
                border: 1px solid rgba(255, 255, 255, 0.15);
                border-radius: 8px;
                background-color: #1A1E27;
                text-align: center;
                height: 18px;
                color: #FFFFFF;
                font-weight: 600;
                font-size: 8.5pt;
            }
            QProgressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #0284C7, stop:1 #00E5FF);
                border-radius: 7px;
            }
            QPushButton {
                background-color: #0284C7;
                border: 1px solid #38BDF8;
                border-radius: 8px;
                color: #FFFFFF;
                font-weight: 700;
                font-size: 10pt;
                padding: 10px 24px;
            }
            QPushButton:hover {
                background-color: #0369A1;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(14)

        lbl_title = QLabel("Modern Speed Meter — Sekali Klik Langsung Pakai", self)
        lbl_title.setObjectName("Title")
        layout.addWidget(lbl_title)

        lbl_desc = QLabel("Otomatis memasang aplikasi, membuat ikon Desktop & Start Menu, mengaktifkan auto-start saat Windows menyala, dan langsung mengaktifkan widget.", self)
        lbl_desc.setObjectName("Desc")
        lbl_desc.setWordWrap(True)
        layout.addWidget(lbl_desc)

        self.progress_bar = QProgressBar(self)
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        layout.addWidget(self.progress_bar)

        self.lbl_status = QLabel("Klik tombol di bawah untuk memasang dan menjalankan.", self)
        self.lbl_status.setStyleSheet("color: #00E5FF; font-size: 9pt; font-weight: 600;")
        layout.addWidget(self.lbl_status)

        layout.addStretch()

        btn_row = QHBoxLayout()
        btn_row.addStretch()
        self.btn_install = QPushButton("⚡ Pasang & Buka Speed Meter", self)
        self.btn_install.clicked.connect(self.start_install)
        btn_row.addWidget(self.btn_install)
        layout.addLayout(btn_row)

    def start_install(self):
        self.btn_install.setEnabled(False)
        self.worker = InstallWorker()
        self.worker.progress.connect(self.on_progress)
        self.worker.finished_success.connect(self.on_finished)
        self.worker.failed.connect(self.on_failed)
        self.worker.start()

    def on_progress(self, val, msg):
        self.progress_bar.setValue(val)
        self.lbl_status.setText(msg)

    def on_finished(self, exe_path):
        self.lbl_status.setText("✅ Berhasil dipasang dan widget sudah aktif di layar Anda!")
        self.btn_install.setText("Tutup")
        self.btn_install.setEnabled(True)
        self.btn_install.clicked.disconnect()
        self.btn_install.clicked.connect(self.close)

    def on_failed(self, err_msg):
        self.lbl_status.setText("❌ Terjadi kesalahan saat instalasi.")
        QMessageBox.critical(self, "Gagal Instalasi", f"Error: {err_msg}")
        self.btn_install.setEnabled(True)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = InstallerWindow()
    win.show()
    sys.exit(app.exec())
