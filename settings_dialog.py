import sys
import datetime
import webbrowser
from PySide6.QtCore import Qt, Signal, QUrl
from PySide6.QtGui import QDesktopServices, QColor
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTabWidget, QWidget, QLabel,
    QComboBox, QCheckBox, QSlider, QPushButton, QGroupBox, QColorDialog,
    QMessageBox, QTableWidget, QTableWidgetItem, QHeaderView, QFrame
)

import styles
from config_manager import ConfigManager
from network_monitor import NetworkMonitor
from traffic_history import TrafficHistory
from traffic_chart import TrafficChartWidget
from win_utils import (
    get_tray_wifi_dock_coordinate,
    set_windows_autostart,
    is_windows_autostart_enabled
)


class SettingsDialog(QDialog):
    """
    Modern Windows 11 Fluent Settings Dialog.
    Allows user to customize widget mode, scale, colors, hold-to-drag, network adapter, refresh rate, and autostart.
    Also provides comprehensive Internet Traffic History & Analytics visualizations.
    """
    settings_changed = Signal()
    snap_requested = Signal()
    dock_taskbar_requested = Signal(bool)
    mode_preview_requested = Signal(str)
    shape_preview_requested = Signal(str)

    def __init__(self, config_manager: ConfigManager = None, traffic_history: TrafficHistory = None, parent=None):
        super().__init__(parent)
        self.config = config_manager or ConfigManager()
        self.traffic_history = traffic_history or TrafficHistory()

        self.setWindowTitle("Pengaturan & Riwayat — Modern Speed Meter")
        self.resize(720, 730)
        self.setMinimumSize(680, 680)
        self.setStyleSheet(styles.get_settings_dialog_style())

        self._setup_ui()
        self._load_values()

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(12)

        # Tab Widget
        self.tabs = QTabWidget(self)
        self.tabs.addTab(self._build_general_tab(), "Umum")
        self.tabs.addTab(self._build_appearance_tab(), "Tampilan && Ukuran")
        self.tabs.addTab(self._build_history_tab(), "Riwayat && Statistik")
        self.tabs.addTab(self._build_network_tab(), "Jaringan")
        self.tabs.addTab(self._build_startup_tab(), "Startup && Dev")
        self.tabs.currentChanged.connect(self._on_tab_changed)
        main_layout.addWidget(self.tabs)

        # Footer Action Buttons
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)

        self.btn_reset = QPushButton("Reset Default", self)
        self.btn_reset.clicked.connect(self._reset_defaults)
        btn_layout.addWidget(self.btn_reset)

        btn_layout.addStretch()

        self.btn_cancel = QPushButton("Batal", self)
        self.btn_cancel.clicked.connect(self.reject)
        btn_layout.addWidget(self.btn_cancel)

        self.btn_apply = QPushButton("Terapkan && Simpan", self)
        self.btn_apply.setObjectName("PrimaryButton")
        self.btn_apply.clicked.connect(self._save_and_apply)
        btn_layout.addWidget(self.btn_apply)

        main_layout.addLayout(btn_layout)

    def _build_general_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(12)

        # Mode Selection
        grp_mode = QGroupBox("Gaya Tampilan Widget (Layout Mode)", tab)
        v_mode = QVBoxLayout(grp_mode)
        self.combo_mode = QComboBox(grp_mode)
        self.combo_mode.addItem("Capsule Pill (Kapsul Modern Melayang)", "capsule")
        self.combo_mode.addItem("Taskbar Docked (Menyatu di Taskbar Samping Wi-Fi)", "taskbar")
        self.combo_mode.addItem("Floating Glass Card (Kartu Detail + Grafik)", "card")
        self.combo_mode.currentIndexChanged.connect(self._on_mode_combo_changed)
        v_mode.addWidget(self.combo_mode)

        lbl_mode_hint = QLabel("Pilih 'Taskbar Docked' untuk memasukkan widget langsung ke dalam bilah taskbar Windows di samping ikon Wi-Fi & Baterai.", grp_mode)
        lbl_mode_hint.setWordWrap(True)
        lbl_mode_hint.setStyleSheet("color: #94A3B8; font-size: 8.5pt; margin-top: 4px;")
        v_mode.addWidget(lbl_mode_hint)
        layout.addWidget(grp_mode)

        # Behavior Group
        grp_behav = QGroupBox("Perilaku Jendela && Posisi Taskbar", tab)
        v_behav = QVBoxLayout(grp_behav)
        self.chk_ontop = QCheckBox("Selalu di Atas (Always on Top)", grp_behav)
        self.chk_locked = QCheckBox("Kunci Posisi Sepenuhnya (Disable Drag)", grp_behav)
        self.chk_hold_to_drag = QCheckBox("Wajib Tekan Tahan 2 Detik untuk Menggeser", grp_behav)
        
        lbl_drag_hint = QLabel("Mencegah geser tak sengaja: klik biasa tidak akan memindahkan widget agar tidak menutupi tombol/file di baliknya.", grp_behav)
        lbl_drag_hint.setWordWrap(True)
        lbl_drag_hint.setStyleSheet("color: #94A3B8; font-size: 8.5pt; margin-left: 24px; margin-bottom: 6px;")

        self.chk_click_through = QCheckBox("Mode Tembus Klik Mouse (Click-Through / Bisa Klik Tombol di Belakang)", grp_behav)
        lbl_click_hint = QLabel(
            "Ketika aktif, klik mouse langsung menembus ke tombol di baliknya (ikon tray, bilah taskbar, Wi-Fi, Audio). "
            "Untuk membuka menu atau mematikan, klik kanan pada ikon di System Tray (dekat jam).",
            grp_behav
        )
        lbl_click_hint.setWordWrap(True)
        lbl_click_hint.setStyleSheet("color: #38BDF8; font-size: 8.5pt; margin-left: 24px; margin-bottom: 6px;")

        # Quick Actions Row
        row_quick = QHBoxLayout()
        row_quick.setSpacing(8)

        self.btn_dock_taskbar = QPushButton("Masuk ke Dalam Taskbar", grp_behav)
        self.btn_dock_taskbar.setObjectName("PrimaryButton")
        self.btn_dock_taskbar.setMinimumHeight(32)
        self.btn_dock_taskbar.clicked.connect(self._dock_now)

        self.btn_snap_now = QPushButton("Snap Samping Wi-Fi", grp_behav)
        self.btn_snap_now.setMinimumHeight(32)
        self.btn_snap_now.clicked.connect(lambda: self.snap_requested.emit())

        row_quick.addWidget(self.btn_dock_taskbar)
        row_quick.addWidget(self.btn_snap_now)

        v_behav.addWidget(self.chk_ontop)
        v_behav.addWidget(self.chk_locked)
        v_behav.addWidget(self.chk_hold_to_drag)
        v_behav.addWidget(lbl_drag_hint)
        v_behav.addWidget(self.chk_click_through)
        v_behav.addWidget(lbl_click_hint)
        v_behav.addLayout(row_quick)
        layout.addWidget(grp_behav)

        # Quick Data Usage Summary Group directly on Umum tab
        grp_hist = QGroupBox("Riwayat Penggunaan Data Jaringan (Data Usage)", tab)
        v_hist = QVBoxLayout(grp_hist)
        v_hist.setSpacing(8)

        row_stats = QHBoxLayout()
        row_stats.setSpacing(8)

        # Hari Ini Card
        box_today = QFrame(grp_hist)
        box_today.setStyleSheet("background-color: #171B24; border: 1px solid rgba(255, 255, 255, 0.08); border-radius: 8px;")
        v_today = QVBoxLayout(box_today)
        v_today.setContentsMargins(10, 8, 10, 8)
        v_today.setSpacing(2)
        lbl_t_title = QLabel("HARI INI (TODAY)", box_today)
        lbl_t_title.setStyleSheet("color: #94A3B8; font-size: 7.5pt; font-weight: 600; text-transform: uppercase; background: transparent;")
        self.lbl_general_today_val = QLabel("0.00 B", box_today)
        self.lbl_general_today_val.setStyleSheet("color: #00E5FF; font-size: 11.5pt; font-weight: 700; background: transparent;")
        self.lbl_general_today_sub = QLabel("▼ 0 B  •  ▲ 0 B", box_today)
        self.lbl_general_today_sub.setStyleSheet("color: #94A3B8; font-size: 8pt; background: transparent;")
        v_today.addWidget(lbl_t_title)
        v_today.addWidget(self.lbl_general_today_val)
        v_today.addWidget(self.lbl_general_today_sub)
        row_stats.addWidget(box_today)

        # Bulan Ini Card
        box_month = QFrame(grp_hist)
        box_month.setStyleSheet("background-color: #171B24; border: 1px solid rgba(255, 255, 255, 0.08); border-radius: 8px;")
        v_month = QVBoxLayout(box_month)
        v_month.setContentsMargins(10, 8, 10, 8)
        v_month.setSpacing(2)
        lbl_m_title = QLabel("BULAN INI (THIS MONTH)", box_month)
        lbl_m_title.setStyleSheet("color: #94A3B8; font-size: 7.5pt; font-weight: 600; text-transform: uppercase; background: transparent;")
        self.lbl_general_month_val = QLabel("0.00 B", box_month)
        self.lbl_general_month_val.setStyleSheet("color: #00E676; font-size: 11.5pt; font-weight: 700; background: transparent;")
        self.lbl_general_month_sub = QLabel("▼ 0 B  •  ▲ 0 B", box_month)
        self.lbl_general_month_sub.setStyleSheet("color: #94A3B8; font-size: 8pt; background: transparent;")
        v_month.addWidget(lbl_m_title)
        v_month.addWidget(self.lbl_general_month_val)
        v_month.addWidget(self.lbl_general_month_sub)
        row_stats.addWidget(box_month)

        v_hist.addLayout(row_stats)

        self.btn_goto_history = QPushButton("Lihat Grafik Lengkap && Rincian Riwayat ↗", grp_hist)
        self.btn_goto_history.setObjectName("PrimaryButton")
        self.btn_goto_history.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_goto_history.clicked.connect(self._goto_history_tab)
        v_hist.addWidget(self.btn_goto_history)

        layout.addWidget(grp_hist)

        layout.addStretch()
        return tab

    def _build_network_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(14)

        grp_nic = QGroupBox("Kartu Jaringan (Network Adapter)", tab)
        v_nic = QVBoxLayout(grp_nic)
        self.combo_nic = QComboBox(grp_nic)
        for nic in NetworkMonitor.get_available_nics():
            label = "Otomatis Deteksi Semua Jaringan" if nic == "auto" else nic
            self.combo_nic.addItem(label, nic)
        v_nic.addWidget(self.combo_nic)
        layout.addWidget(grp_nic)

        grp_rate = QGroupBox("Frekuensi Pembaruan (Refresh Rate)", tab)
        v_rate = QVBoxLayout(grp_rate)
        self.combo_interval = QComboBox(grp_rate)
        self.combo_interval.addItem("500 ms (Sangat Cepat)", 500)
        self.combo_interval.addItem("1000 ms / 1 detik (Standar Direkomendasikan)", 1000)
        self.combo_interval.addItem("2000 ms / 2 detik (Hemat Daya)", 2000)
        v_rate.addWidget(self.combo_interval)
        layout.addWidget(grp_rate)

        layout.addStretch()
        return tab

    def _build_appearance_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(14)

        # Shape Template Group
        grp_shape = QGroupBox("Template Bentuk & Sudut (Shape Template)", tab)
        v_shape = QVBoxLayout(grp_shape)
        self.combo_shape = QComboBox(grp_shape)
        self.combo_shape.addItem("💊 Kapsul Bulat Penuh (Pill — Bulat Sempurna, Tidak Mengkotak)", "pill")
        self.combo_shape.addItem("🔘 Badge Melengkung (Curved Oval Badge)", "badge")
        self.combo_shape.addItem("🫧 Melengkung Modern (Soft Rounded 12px)", "rounded")
        self.combo_shape.addItem("✨ Hanya Tulisan (Clean Text Only — Tanpa Kotak Background)", "text_only")
        self.combo_shape.currentIndexChanged.connect(self._on_shape_combo_changed)
        v_shape.addWidget(self.combo_shape)

        lbl_shape_hint = QLabel(
            "Pilih 'Kapsul Bulat Penuh' untuk tampilan bulat halus anti-mengkotak, "
            "atau 'Hanya Tulisan' agar hanya angka kecepatan internet yang muncul tanpa background kotak.",
            grp_shape
        )
        lbl_shape_hint.setWordWrap(True)
        lbl_shape_hint.setStyleSheet("color: #94A3B8; font-size: 8.5pt; margin-top: 4px;")
        v_shape.addWidget(lbl_shape_hint)
        layout.addWidget(grp_shape)

        # Colors Group
        grp_colors = QGroupBox("Warna Aksen Indikator (Colors)", tab)
        v_colors = QVBoxLayout(grp_colors)

        row_up = QHBoxLayout()
        row_up.addWidget(QLabel("Warna Upload (▲):", grp_colors))
        self.btn_up_color = QPushButton("■ Pilih Warna", grp_colors)
        self.btn_up_color.clicked.connect(self._pick_up_color)
        row_up.addWidget(self.btn_up_color)
        v_colors.addLayout(row_up)

        row_down = QHBoxLayout()
        row_down.addWidget(QLabel("Warna Download (▼):", grp_colors))
        self.btn_down_color = QPushButton("■ Pilih Warna", grp_colors)
        self.btn_down_color.clicked.connect(self._pick_down_color)
        row_down.addWidget(self.btn_down_color)
        v_colors.addLayout(row_down)

        layout.addWidget(grp_colors)

        # Scale / Size Group
        grp_scale = QGroupBox("Ukuran Tampilan Widget (Widget Scale & Size)", tab)
        v_scale = QVBoxLayout(grp_scale)
        self.slider_scale = QSlider(Qt.Orientation.Horizontal, grp_scale)
        self.slider_scale.setRange(65, 150)
        self.slider_scale.setSingleStep(5)
        self.slider_scale.setValue(100)
        self.lbl_scale_val = QLabel("100% (Standar)", grp_scale)

        def _update_scale_label(val):
            status = "Kecil" if val < 85 else ("Standar" if val <= 110 else "Besar")
            self.lbl_scale_val.setText(f"{val}% ({status})")

        self.slider_scale.valueChanged.connect(_update_scale_label)

        row_scale = QHBoxLayout()
        row_scale.addWidget(self.slider_scale)
        row_scale.addWidget(self.lbl_scale_val)
        v_scale.addLayout(row_scale)

        lbl_scale_hint = QLabel("💡 Tips: Anda juga bisa menahan tombol Ctrl sambil memutar Scroll Mouse pada widget untuk mengubah ukuran langsung di layar.", grp_scale)
        lbl_scale_hint.setWordWrap(True)
        lbl_scale_hint.setStyleSheet("color: #94A3B8; font-size: 8.5pt;")
        v_scale.addWidget(lbl_scale_hint)

        layout.addWidget(grp_scale)

        # Opacity & Font Group
        grp_opacity = QGroupBox("Transparansi Latar Kaca (Opacity — Bisa sampai 0%)", tab)
        v_opacity = QVBoxLayout(grp_opacity)
        self.slider_opacity = QSlider(Qt.Orientation.Horizontal, grp_opacity)
        self.slider_opacity.setRange(0, 100)
        self.slider_opacity.setValue(92)
        self.lbl_opacity_val = QLabel("92%", grp_opacity)

        def _update_opacity_label(v):
            if v == 0:
                self.lbl_opacity_val.setText("0% (Transparan Penuh / Hanya Tulisan)")
            elif v < 30:
                self.lbl_opacity_val.setText(f"{v}% (Sangat Bening)")
            elif v < 80:
                self.lbl_opacity_val.setText(f"{v}% (Kaca Transparan)")
            else:
                self.lbl_opacity_val.setText(f"{v}% (Pekat)")

        self._update_opacity_label = _update_opacity_label
        self.slider_opacity.valueChanged.connect(_update_opacity_label)

        row_slider = QHBoxLayout()
        row_slider.addWidget(self.slider_opacity)
        row_slider.addWidget(self.lbl_opacity_val)
        v_opacity.addLayout(row_slider)

        lbl_opacity_hint = QLabel("💡 Geser ke 0% jika ingin latar belakang dan garis kotak hilang sepenuhnya (hanya menyisakan tulisan kecepatan).", grp_opacity)
        lbl_opacity_hint.setWordWrap(True)
        lbl_opacity_hint.setStyleSheet("color: #94A3B8; font-size: 8.5pt;")
        v_opacity.addWidget(lbl_opacity_hint)

        layout.addWidget(grp_opacity)

        layout.addStretch()
        return tab

    def _build_history_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(6, 8, 6, 6)
        layout.setSpacing(10)

        # 1. Period Selector & Action Buttons Bar
        row_filter = QHBoxLayout()
        row_filter.setSpacing(8)

        lbl_period = QLabel("Periode:", tab)
        lbl_period.setStyleSheet("color: #94A3B8; font-weight: 600; font-size: 9pt;")
        row_filter.addWidget(lbl_period)

        self.combo_history_period = QComboBox(tab)
        self.combo_history_period.addItem("Hari Ini (24 Jam)", "today")
        self.combo_history_period.addItem("7 Hari Terakhir (Seminggu)", "week")
        self.combo_history_period.addItem("30 Hari Terakhir (Sebulan)", "month")
        self.combo_history_period.addItem("Pilih Bulan Tertentu...", "custom")
        self.combo_history_period.currentIndexChanged.connect(self._on_history_period_changed)
        row_filter.addWidget(self.combo_history_period)

        self.combo_custom_month = QComboBox(tab)
        self.combo_custom_month.setVisible(False)
        self.combo_custom_month.currentIndexChanged.connect(self._load_history_data)
        row_filter.addWidget(self.combo_custom_month)

        row_filter.addStretch()

        self.btn_refresh_history = QPushButton("Segarkan", tab)
        self.btn_refresh_history.setToolTip("Perbarui data riwayat penggunaan jaringan")
        self.btn_refresh_history.clicked.connect(self._load_history_data)
        row_filter.addWidget(self.btn_refresh_history)

        self.btn_clear_history = QPushButton("Bersihkan", tab)
        self.btn_clear_history.setToolTip("Hapus seluruh catatan riwayat traffic")
        self.btn_clear_history.setStyleSheet("color: #F87171; border-color: rgba(239, 68, 68, 0.3);")
        self.btn_clear_history.clicked.connect(self._clear_history_data)
        row_filter.addWidget(self.btn_clear_history)

        layout.addLayout(row_filter)

        # 2. KPI Metric Cards Row
        row_kpis = QHBoxLayout()
        row_kpis.setSpacing(8)

        def make_kpi_card(title: str, default_val: str, accent_color: str):
            card = QFrame(tab)
            card.setStyleSheet("""
                QFrame {
                    background-color: #171B24;
                    border: 1px solid rgba(255, 255, 255, 0.08);
                    border-radius: 8px;
                }
            """)
            c_layout = QVBoxLayout(card)
            c_layout.setContentsMargins(10, 8, 10, 8)
            c_layout.setSpacing(3)

            lbl_t = QLabel(title, card)
            lbl_t.setStyleSheet("color: #94A3B8; font-size: 7.5pt; font-weight: 600; text-transform: uppercase; background: transparent;")
            c_layout.addWidget(lbl_t)

            lbl_v = QLabel(default_val, card)
            lbl_v.setStyleSheet(f"color: {accent_color}; font-size: 11.5pt; font-weight: 700; background: transparent;")
            c_layout.addWidget(lbl_v)

            return card, lbl_v

        self.card_down, self.lbl_kpi_down = make_kpi_card("TOTAL DOWNLOAD", "0.00 B", self.down_color if hasattr(self, "down_color") else "#00E5FF")
        self.card_up, self.lbl_kpi_up = make_kpi_card("TOTAL UPLOAD", "0.00 B", self.up_color if hasattr(self, "up_color") else "#00E676")
        self.card_total, self.lbl_kpi_total = make_kpi_card("TOTAL KUOTA", "0.00 B", "#F8FAFC")
        self.card_peak, self.lbl_kpi_peak = make_kpi_card("PUNCAK TRAFFIC", "0.00 B", "#38BDF8")

        row_kpis.addWidget(self.card_down)
        row_kpis.addWidget(self.card_up)
        row_kpis.addWidget(self.card_total)
        row_kpis.addWidget(self.card_peak)
        layout.addLayout(row_kpis)

        # 3. Interactive Chart
        self.chart_widget = TrafficChartWidget(tab)
        self.chart_widget.setMinimumHeight(180)
        down_col = getattr(self, "down_color", "#00E5FF")
        up_col = getattr(self, "up_color", "#00E676")
        self.chart_widget.set_colors(down_col, up_col)
        layout.addWidget(self.chart_widget)

        # 4. Detailed Data Table
        self.table_history = QTableWidget(tab)
        self.table_history.setColumnCount(4)
        self.table_history.setHorizontalHeaderLabels(["Waktu / Periode", "Download (▼)", "Upload (▲)", "Total"])
        self.table_history.verticalHeader().setVisible(False)
        self.table_history.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table_history.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table_history.setAlternatingRowColors(True)
        self.table_history.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.table_history.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.table_history.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.table_history.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.table_history.setMinimumHeight(130)
        layout.addWidget(self.table_history)

        return tab

    def _on_tab_changed(self, index: int):
        if "Riwayat" in self.tabs.tabText(index):
            self._load_history_data()

    def _on_history_period_changed(self):
        period = self.combo_history_period.currentData()
        self.combo_custom_month.setVisible(period == "custom")
        self._load_history_data()

    def _populate_available_months(self):
        self.combo_custom_month.blockSignals(True)
        self.combo_custom_month.clear()
        months = self.traffic_history.get_available_months()
        for ym, label in months:
            self.combo_custom_month.addItem(label, ym)
        self.combo_custom_month.blockSignals(False)

    def _load_history_data(self):
        if not hasattr(self, "chart_widget") or not hasattr(self, "table_history"):
            return

        period = self.combo_history_period.currentData()
        records = []
        if period == "today":
            records = self.traffic_history.get_today_hourly()
        elif period == "week":
            records = self.traffic_history.get_last_7_days()
        elif period == "month":
            records = self.traffic_history.get_last_30_days()
        elif period == "custom":
            ym = self.combo_custom_month.currentData()
            if ym and "-" in ym:
                try:
                    y, m = map(int, ym.split("-"))
                    records = self.traffic_history.get_custom_month(y, m)
                except Exception:
                    records = []
            else:
                records = []

        summary = self.traffic_history.get_summary(records)

        # Update KPI cards
        self.lbl_kpi_down.setText(TrafficHistory.format_bytes(summary["total_recv"]))
        self.lbl_kpi_up.setText(TrafficHistory.format_bytes(summary["total_sent"]))
        self.lbl_kpi_total.setText(TrafficHistory.format_bytes(summary["total_bytes"]))
        self.lbl_kpi_peak.setText(TrafficHistory.format_bytes(summary["peak_bytes"]))

        # Update Chart
        down_col = getattr(self, "down_color", "#00E5FF")
        up_col = getattr(self, "up_color", "#00E676")
        self.chart_widget.set_colors(down_col, up_col)
        self.chart_widget.set_data(records)

        # Update Table
        self.table_history.setRowCount(len(records))
        for row, item in enumerate(records):
            time_item = QTableWidgetItem(str(item.get("label", "")))
            time_item.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)

            down_item = QTableWidgetItem(TrafficHistory.format_bytes(item.get("bytes_recv", 0)))
            down_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            down_item.setForeground(QColor(down_col))

            up_item = QTableWidgetItem(TrafficHistory.format_bytes(item.get("bytes_sent", 0)))
            up_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            up_item.setForeground(QColor(up_col))

            total_item = QTableWidgetItem(TrafficHistory.format_bytes(item.get("total_bytes", 0)))
            total_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            total_item.setForeground(QColor("#F8FAFC"))

            self.table_history.setItem(row, 0, time_item)
            self.table_history.setItem(row, 1, down_item)
            self.table_history.setItem(row, 2, up_item)
            self.table_history.setItem(row, 3, total_item)

        # Update General Tab quick usage summary cards if present
        if hasattr(self, "lbl_general_today_val"):
            today_recs = self.traffic_history.get_today_hourly()
            today_s = self.traffic_history.get_summary(today_recs)
            self.lbl_general_today_val.setText(TrafficHistory.format_bytes(today_s["total_bytes"]))
            self.lbl_general_today_sub.setText(
                f"▼ {TrafficHistory.format_bytes(today_s['total_recv'])}  •  ▲ {TrafficHistory.format_bytes(today_s['total_sent'])}"
            )

        if hasattr(self, "lbl_general_month_val"):
            now = datetime.date.today()
            month_recs = self.traffic_history.get_custom_month(now.year, now.month)
            month_s = self.traffic_history.get_summary(month_recs)
            self.lbl_general_month_val.setText(TrafficHistory.format_bytes(month_s["total_bytes"]))
            self.lbl_general_month_sub.setText(
                f"▼ {TrafficHistory.format_bytes(month_s['total_recv'])}  •  ▲ {TrafficHistory.format_bytes(month_s['total_sent'])}"
            )

    def _goto_history_tab(self):
        for i in range(self.tabs.count()):
            if "Riwayat" in self.tabs.tabText(i):
                self.tabs.setCurrentIndex(i)
                break

    def _clear_history_data(self):
        reply = QMessageBox.question(
            self,
            "Konfirmasi Hapus Riwayat",
            "Apakah Anda yakin ingin menghapus seluruh catatan riwayat traffic internet?\nSemua statistik akan di-reset.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.traffic_history.clear_history()
            self._populate_available_months()
            self._load_history_data()

    def _build_startup_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(14)

        # Autostart Group
        grp_boot = QGroupBox("Integrasi Windows Startup (Auto-Run)", tab)
        v_boot = QVBoxLayout(grp_boot)
        self.chk_startup = QCheckBox("Jalankan otomatis saat Windows dinyalakan (Auto Start)", grp_boot)
        lbl_hint = QLabel("Widget akan otomatis aktif di system tray dan menempati posisi terakhir Anda setiap kali PC/laptop menyala.", grp_boot)
        lbl_hint.setWordWrap(True)
        lbl_hint.setStyleSheet("color: #94A3B8; font-size: 8.5pt;")

        v_boot.addWidget(self.chk_startup)
        v_boot.addWidget(lbl_hint)
        layout.addWidget(grp_boot)

        # Dev / Support Group
        grp_dev = QGroupBox("Pengembang & Layanan Resmi (Salshya Club)", tab)
        v_dev = QVBoxLayout(grp_dev)
        
        lbl_dev_desc = QLabel("Salshya_Club | Pusat Software Premium, Produk Digital & Layanan Sosmed", grp_dev)
        lbl_dev_desc.setWordWrap(True)
        lbl_dev_desc.setStyleSheet("color: #E2E8F0; font-weight: 600; font-size: 9.5pt;")
        
        lbl_dev_sub = QLabel("Punya masukan, saran fitur, atau butuh software custom lainnya? Kunjungi situs resmi kami.", grp_dev)
        lbl_dev_sub.setWordWrap(True)
        lbl_dev_sub.setStyleSheet("color: #94A3B8; font-size: 8.5pt;")

        self.btn_dev = QPushButton("🌐 Hubungi Dev (Salshya Club) ↗", grp_dev)
        self.btn_dev.setObjectName("DevButton")
        self.btn_dev.setCursor(Qt.CursorShape.PointingHandCursor)
        
        def _open_dev_link():
            url = "https://salshya-club.vercel.app/"
            try:
                QDesktopServices.openUrl(QUrl(url))
            except Exception:
                webbrowser.open(url)

        self.btn_dev.clicked.connect(_open_dev_link)

        v_dev.addWidget(lbl_dev_desc)
        v_dev.addWidget(lbl_dev_sub)
        v_dev.addSpacing(6)
        v_dev.addWidget(self.btn_dev)
        layout.addWidget(grp_dev)

        layout.addStretch()
        return tab

    def _load_values(self):
        # Mode
        mode = self.config.get("widget_mode", "capsule")
        self.combo_mode.blockSignals(True)
        idx = self.combo_mode.findData(mode)
        if idx >= 0:
            self.combo_mode.setCurrentIndex(idx)
        self.combo_mode.blockSignals(False)

        # Shape template
        cur_shape = self.config.get("shape_template", "pill")
        self.combo_shape.blockSignals(True)
        s_idx = self.combo_shape.findData(cur_shape)
        if s_idx >= 0:
            self.combo_shape.setCurrentIndex(s_idx)
        self.combo_shape.blockSignals(False)

        # Always on top, Lock, Hold to drag, Click-through
        self.chk_ontop.setChecked(self.config.get("always_on_top", True))
        self.chk_locked.setChecked(self.config.get("locked_position", False))
        self.chk_hold_to_drag.setChecked(self.config.get("hold_to_drag", True))
        self.chk_click_through.setChecked(self.config.get("click_through", False))

        # Scale
        cur_scale = int(round(float(self.config.get("widget_scale", 1.0)) * 100))
        self.slider_scale.setValue(cur_scale)
        status = "Kecil" if cur_scale < 85 else ("Standar" if cur_scale <= 110 else "Besar")
        self.lbl_scale_val.setText(f"{cur_scale}% ({status})")

        # NIC
        nic = self.config.get("nic_name", "auto")
        nic_idx = self.combo_nic.findData(nic)
        if nic_idx >= 0:
            self.combo_nic.setCurrentIndex(nic_idx)

        # Interval
        interval = self.config.get("refresh_interval_ms", 1000)
        int_idx = self.combo_interval.findData(interval)
        if int_idx >= 0:
            self.combo_interval.setCurrentIndex(int_idx)

        # Colors
        self.up_color = self.config.get("up_color", "#00E676")
        self.down_color = self.config.get("down_color", "#00E5FF")
        self._update_color_button_styles()

        # Opacity
        op = int(round(float(self.config.get("opacity", 0.92)) * 100))
        self.slider_opacity.setValue(op)
        if hasattr(self, "_update_opacity_label"):
            self._update_opacity_label(op)
        else:
            self.lbl_opacity_val.setText(f"{op}%")

        # Startup
        is_startup = is_windows_autostart_enabled("ModernSpeedMeter")
        self.chk_startup.setChecked(is_startup)

        # History
        self._populate_available_months()
        self._load_history_data()

    def _update_color_button_styles(self):
        self.btn_up_color.setStyleSheet(f"background-color: {self.up_color}; color: #000; font-weight: bold; border-radius: 6px; padding: 6px;")
        self.btn_down_color.setStyleSheet(f"background-color: {self.down_color}; color: #000; font-weight: bold; border-radius: 6px; padding: 6px;")

    def _pick_up_color(self):
        col = QColorDialog.getColor(self.up_color, self, "Pilih Warna Indikator Upload")
        if col.isValid():
            self.up_color = col.name()
            self._update_color_button_styles()
            if hasattr(self, "lbl_kpi_up"):
                self.lbl_kpi_up.setStyleSheet(f"color: {self.up_color}; font-size: 11.5pt; font-weight: 700; background: transparent;")
            if hasattr(self, "chart_widget"):
                self.chart_widget.set_colors(self.down_color, self.up_color)

    def _pick_down_color(self):
        col = QColorDialog.getColor(self.down_color, self, "Pilih Warna Indikator Download")
        if col.isValid():
            self.down_color = col.name()
            self._update_color_button_styles()
            if hasattr(self, "lbl_kpi_down"):
                self.lbl_kpi_down.setStyleSheet(f"color: {self.down_color}; font-size: 11.5pt; font-weight: 700; background: transparent;")
            if hasattr(self, "chart_widget"):
                self.chart_widget.set_colors(self.down_color, self.up_color)

    def _reset_defaults(self):
        reply = QMessageBox.question(
            self, "Konfirmasi Reset",
            "Apakah Anda yakin ingin mengembalikan semua pengaturan ke default?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.combo_mode.setCurrentIndex(self.combo_mode.findData("capsule"))
            self.combo_shape.setCurrentIndex(self.combo_shape.findData("pill"))
            self.chk_ontop.setChecked(True)
            self.chk_locked.setChecked(False)
            self.chk_hold_to_drag.setChecked(True)
            self.chk_click_through.setChecked(False)
            self.slider_scale.setValue(100)
            self.lbl_scale_val.setText("100% (Standar)")
            self.combo_nic.setCurrentIndex(0)
            self.combo_interval.setCurrentIndex(1)
            self.up_color = "#00E676"
            self.down_color = "#00E5FF"
            self._update_color_button_styles()
            if hasattr(self, "lbl_kpi_down"):
                self.lbl_kpi_down.setStyleSheet("color: #00E5FF; font-size: 11.5pt; font-weight: 700; background: transparent;")
            if hasattr(self, "lbl_kpi_up"):
                self.lbl_kpi_up.setStyleSheet("color: #00E676; font-size: 11.5pt; font-weight: 700; background: transparent;")
            if hasattr(self, "chart_widget"):
                self.chart_widget.set_colors("#00E5FF", "#00E676")
            self.slider_opacity.setValue(92)
            if hasattr(self, "_update_opacity_label"):
                self._update_opacity_label(92)
            else:
                self.lbl_opacity_val.setText("92%")
            self.chk_startup.setChecked(True)

    def _dock_now(self):
        """Immediately switches to taskbar mode, docks into Windows taskbar, and closes dialog."""
        idx = self.combo_mode.findData("taskbar")
        if idx >= 0:
            self.combo_mode.setCurrentIndex(idx)
        self.config.set("widget_mode", "taskbar", auto_save=False)
        self.config.set("is_taskbar_docked", True, auto_save=False)
        self.config.set("always_on_top", True, auto_save=False)
        self.config.save()
        self.dock_taskbar_requested.emit(True)
        self.settings_changed.emit()
        self.accept()

    def _on_mode_combo_changed(self, idx: int):
        mode = self.combo_mode.itemData(idx)
        if mode:
            self.mode_preview_requested.emit(mode)

    def _on_shape_combo_changed(self, idx: int):
        shape = self.combo_shape.itemData(idx)
        if shape:
            self.shape_preview_requested.emit(shape)

    def reject(self):
        # Revert any unapplied live previews back to saved config
        orig_mode = self.config.get("widget_mode", "capsule")
        orig_shape = self.config.get("shape_template", "pill")
        self.mode_preview_requested.emit(orig_mode)
        self.shape_preview_requested.emit(orig_shape)
        super().reject()

    def _save_and_apply(self):
        mode = self.combo_mode.currentData()
        self.config.set("widget_mode", mode, auto_save=False)
        self.config.set("shape_template", self.combo_shape.currentData(), auto_save=False)
        if mode == "taskbar":
            self.config.set("is_taskbar_docked", True, auto_save=False)
        else:
            self.config.set("is_taskbar_docked", False, auto_save=False)
        self.config.set("always_on_top", self.chk_ontop.isChecked(), auto_save=False)
        self.config.set("locked_position", self.chk_locked.isChecked(), auto_save=False)
        self.config.set("hold_to_drag", self.chk_hold_to_drag.isChecked(), auto_save=False)
        self.config.set("click_through", self.chk_click_through.isChecked(), auto_save=False)
        self.config.set("widget_scale", round(self.slider_scale.value() / 100.0, 2), auto_save=False)
        self.config.set("nic_name", self.combo_nic.currentData(), auto_save=False)
        self.config.set("refresh_interval_ms", self.combo_interval.currentData(), auto_save=False)
        self.config.set("up_color", self.up_color, auto_save=False)
        self.config.set("down_color", self.down_color, auto_save=False)
        self.config.set("opacity", round(self.slider_opacity.value() / 100.0, 2), auto_save=False)
        self.config.set("autostart", self.chk_startup.isChecked(), auto_save=False)

        # Autostart
        set_windows_autostart("ModernSpeedMeter", enable=self.chk_startup.isChecked())

        self.config.save()
        if mode == "taskbar":
            self.dock_taskbar_requested.emit(True)
        self.settings_changed.emit()
        self.accept()
