"""
Design Tokens and QSS Stylesheets for Modern Windows Speed Meter.
Features Windows 11 Fluent Design, dark frosted glassmorphism, and clean neon accents.
"""

def hex_to_rgba(hex_code: str, alpha: float) -> str:
    hex_code = hex_code.lstrip("#")
    if len(hex_code) == 6:
        r = int(hex_code[0:2], 16)
        g = int(hex_code[2:4], 16)
        b = int(hex_code[4:6], 16)
        return f"rgba({r}, {g}, {b}, {alpha:.2f})"
    return f"rgba(255, 255, 255, {alpha:.2f})"

def _resolve_template_styles(shape_template: str, opacity: float, scale: float,
                            mode: str, is_drag_mode: bool, down_color: str,
                            default_bg_rgb: str = "20, 22, 28"):
    """Returns (radius_css, box_css, hover_css) based on shape template, scale, and opacity."""
    if shape_template == "pill":
        radius_css = "border-radius: 9999px;"
    elif shape_template == "badge":
        if mode == "taskbar":
            radius_css = f"border-radius: {max(8, int(round(12 * scale)))}px;"
        elif mode == "card":
            radius_css = f"border-radius: {max(14, int(round(22 * scale)))}px;"
        else:
            radius_css = f"border-radius: {max(12, int(round(20 * scale)))}px;"
    elif shape_template == "rounded":
        if mode == "taskbar":
            radius_css = f"border-radius: {max(4, int(round(7 * scale)))}px;"
        elif mode == "card":
            radius_css = f"border-radius: {max(8, int(round(14 * scale)))}px;"
        else:
            radius_css = f"border-radius: {max(8, int(round(12 * scale)))}px;"
    elif shape_template == "text_only":
        radius_css = "border-radius: 0px;"
    else:  # fallback to pill
        radius_css = "border-radius: 9999px;"

    if is_drag_mode:
        box_css = "border: 2px solid #00E5FF; background-color: rgba(14, 165, 233, 0.30);"
        hover_css = box_css
    elif shape_template == "text_only" or opacity < 0.05:
        box_css = "border: none; background-color: transparent;"
        hover_css = "border: none; background-color: transparent;"
    else:
        bg_rgba = f"rgba({default_bg_rgb}, {opacity:.2f})"
        border_alpha = min(0.25, max(0.06, opacity * 0.16))
        box_css = f"border: 1px solid rgba(255, 255, 255, {border_alpha:.2f}); background-color: {bg_rgba};"
        hover_alpha = min(1.0, opacity + 0.06)
        hover_border = hex_to_rgba(down_color, min(0.50, opacity * 0.45))
        hover_css = f"border: 1px solid {hover_border}; background-color: rgba(26, 29, 36, {hover_alpha:.2f});"

    return radius_css, box_css, hover_css

def get_capsule_style(opacity: float = 0.92, up_color: str = "#00E676", down_color: str = "#00E5FF",
                      font_family: str = "Segoe UI Variable Display, Segoe UI, sans-serif", font_size: int = 9,
                      scale: float = 1.0, is_drag_mode: bool = False, shape_template: str = "pill") -> str:
    scaled_font = max(6, int(round(font_size * scale)))
    radius_css, box_css, hover_css = _resolve_template_styles(
        shape_template, opacity, scale, "capsule", is_drag_mode, down_color, "20, 22, 28"
    )

    return f"""
    QWidget#CentralCapsule {{
        {box_css}
        {radius_css}
    }}
    QWidget#CentralCapsule:hover {{
        {hover_css}
    }}
    QLabel {{
        color: #E2E8F0;
        font-family: {font_family};
        font-size: {scaled_font}pt;
        font-weight: 600;
        background: transparent;
    }}
    QLabel#UpIcon {{
        color: {up_color};
        font-size: {max(5, scaled_font - 1)}pt;
        font-weight: 800;
    }}
    QLabel#DownIcon {{
        color: {down_color};
        font-size: {max(5, scaled_font - 1)}pt;
        font-weight: 800;
    }}
    QLabel#SpeedText {{
        color: #F8FAFC;
        font-size: {scaled_font}pt;
        font-weight: 600;
        letter-spacing: 0.3px;
    }}
    """

def get_taskbar_style(opacity: float = 0.92, up_color: str = "#00E676", down_color: str = "#00E5FF",
                      font_family: str = "Segoe UI Variable Text, Segoe UI, sans-serif", font_size: int = 8,
                      scale: float = 1.0, is_drag_mode: bool = False, shape_template: str = "pill") -> str:
    scaled_font = max(5, int(round(font_size * scale)))
    radius_css, box_css, hover_css = _resolve_template_styles(
        shape_template, opacity, scale, "taskbar", is_drag_mode, down_color, "18, 22, 30"
    )

    return f"""
    QWidget#CentralTaskbar {{
        {box_css}
        {radius_css}
    }}
    QWidget#CentralTaskbar:hover {{
        {hover_css}
    }}
    QLabel {{
        color: #E2E8F0;
        font-family: {font_family};
        font-size: {scaled_font}pt;
        font-weight: 600;
        background: transparent;
        padding: 0px;
        margin: 0px;
    }}
    QLabel#UpIcon {{
        color: {up_color};
        font-size: {max(5, scaled_font - 1)}pt;
        font-weight: 800;
    }}
    QLabel#DownIcon {{
        color: {down_color};
        font-size: {max(5, scaled_font - 1)}pt;
        font-weight: 800;
    }}
    QLabel#SpeedText {{
        color: #F8FAFC;
        font-size: {scaled_font}pt;
        font-weight: 600;
        letter-spacing: 0.2px;
    }}
    """

def get_card_style(opacity: float = 0.92, up_color: str = "#00E676", down_color: str = "#00E5FF",
                   font_family: str = "Segoe UI Variable Display, Segoe UI, sans-serif", font_size: int = 9,
                   scale: float = 1.0, is_drag_mode: bool = False, shape_template: str = "pill") -> str:
    scaled_font = max(6, int(round(font_size * scale)))
    radius_css, box_css, hover_css = _resolve_template_styles(
        shape_template, opacity, scale, "card", is_drag_mode, down_color, "18, 20, 26"
    )

    return f"""
    QWidget#CentralCard {{
        {box_css}
        {radius_css}
    }}
    QWidget#CentralCard:hover {{
        {hover_css}
    }}
    QLabel {{
        color: #CBD5E1;
        font-family: {font_family};
        font-size: {scaled_font}pt;
        background: transparent;
    }}
    QLabel#HeaderTitle {{
        color: #94A3B8;
        font-size: {max(5, scaled_font - 1)}pt;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.8px;
    }}
    QLabel#UpIcon {{
        color: {up_color};
        font-size: {scaled_font + 1}pt;
        font-weight: 800;
    }}
    QLabel#DownIcon {{
        color: {down_color};
        font-size: {scaled_font + 1}pt;
        font-weight: 800;
    }}
    QLabel#CardSpeedUp {{
        color: #F8FAFC;
        font-size: {scaled_font + 1}pt;
        font-weight: 700;
    }}
    QLabel#CardSpeedDown {{
        color: #F8FAFC;
        font-size: {scaled_font + 1}pt;
        font-weight: 700;
    }}
    QLabel#BadgePing {{
        background-color: rgba(59, 130, 246, 0.18);
        color: #60A5FA;
        border: 1px solid rgba(59, 130, 246, 0.35);
        border-radius: {max(4, int(round(8 * scale)))}px;
        padding: 2px 6px;
        font-size: {max(5, scaled_font - 1)}pt;
        font-weight: 600;
    }}
    QLabel#SessionTotal {{
        color: #94A3B8;
        font-size: {max(5, scaled_font - 1)}pt;
    }}
    """

def get_context_menu_style() -> str:
    return """
    QMenu {
        background-color: #1A1D24;
        border: 1px solid rgba(255, 255, 255, 0.14);
        border-radius: 10px;
        padding: 6px;
        font-family: 'Segoe UI Variable Text', 'Segoe UI', sans-serif;
        font-size: 9.5pt;
        color: #F1F5F9;
    }
    QMenu::item {
        padding: 7px 24px 7px 12px;
        border-radius: 6px;
        background-color: transparent;
    }
    QMenu::item:selected {
        background-color: rgba(255, 255, 255, 0.09);
        color: #38BDF8;
    }
    QMenu::item:disabled {
        color: #64748B;
    }
    QMenu::separator {
        height: 1px;
        background-color: rgba(255, 255, 255, 0.08);
        margin: 4px 6px;
    }
    """

def get_settings_dialog_style() -> str:
    return """
    QDialog {
        background-color: #0F1218;
        color: #F8FAFC;
        font-family: 'Segoe UI Variable Text', 'Segoe UI', sans-serif;
    }
    QTabWidget::pane {
        border: 1px solid rgba(255, 255, 255, 0.08);
        background-color: #161922;
        border-radius: 12px;
        padding: 16px;
    }
    QTabBar::tab {
        background: transparent;
        color: #94A3B8;
        font-size: 10pt;
        font-weight: 600;
        padding: 10px 20px;
        border-radius: 8px;
        margin-right: 4px;
        margin-bottom: 6px;
    }
    QTabBar::tab:selected {
        background-color: rgba(56, 189, 248, 0.15);
        color: #38BDF8;
        border: 1px solid rgba(56, 189, 248, 0.35);
    }
    QTabBar::tab:hover:!selected {
        background-color: rgba(255, 255, 255, 0.05);
        color: #E2E8F0;
    }
    QGroupBox {
        font-size: 10pt;
        font-weight: 700;
        color: #38BDF8;
        border: 1px solid rgba(255, 255, 255, 0.09);
        border-radius: 10px;
        margin-top: 14px;
        padding-top: 18px;
        background-color: rgba(25, 29, 38, 0.5);
    }
    QGroupBox::title {
        subcontrol-origin: margin;
        subcontrol-position: top left;
        padding: 0 8px;
        left: 12px;
    }
    QLabel {
        color: #E2E8F0;
        font-size: 9.5pt;
    }
    QComboBox {
        background-color: #212632;
        border: 1px solid rgba(255, 255, 255, 0.12);
        border-radius: 8px;
        padding: 6px 12px;
        color: #F8FAFC;
        font-size: 9.5pt;
        min-height: 24px;
    }
    QComboBox:hover {
        border: 1px solid #38BDF8;
    }
    QComboBox QAbstractItemView {
        background-color: #1A1E27;
        border: 1px solid rgba(255, 255, 255, 0.15);
        selection-background-color: #38BDF8;
        selection-color: #0F1218;
        color: #F8FAFC;
        padding: 4px;
        border-radius: 6px;
    }
    QCheckBox {
        color: #F1F5F9;
        font-size: 9.5pt;
        spacing: 8px;
    }
    QCheckBox::indicator {
        width: 18px;
        height: 18px;
        border-radius: 5px;
        border: 1px solid rgba(255, 255, 255, 0.25);
        background-color: #212632;
    }
    QCheckBox::indicator:checked {
        background-color: #00E5FF;
        border: 1px solid #00E5FF;
        image: none;
    }
    QSlider::groove:horizontal {
        height: 6px;
        background: #272C38;
        border-radius: 3px;
    }
    QSlider::sub-page:horizontal {
        background: #38BDF8;
        border-radius: 3px;
    }
    QSlider::handle:horizontal {
        background: #F8FAFC;
        width: 16px;
        margin-top: -5px;
        margin-bottom: -5px;
        border-radius: 8px;
        border: 1px solid #38BDF8;
    }
    QPushButton {
        background-color: #262B37;
        border: 1px solid rgba(255, 255, 255, 0.12);
        border-radius: 8px;
        color: #F8FAFC;
        font-weight: 600;
        font-size: 9.5pt;
        padding: 8px 18px;
    }
    QPushButton:hover {
        background-color: #333A4A;
        border: 1px solid rgba(255, 255, 255, 0.25);
    }
    QPushButton#PrimaryButton {
        background-color: #0284C7;
        color: #FFFFFF;
        border: 1px solid #38BDF8;
        font-weight: 700;
    }
    QPushButton#PrimaryButton:hover {
        background-color: #0369A1;
    }
    QPushButton#DevButton {
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #1E3A8A, stop:0.5 #0284C7, stop:1 #06B6D4);
        border: 1px solid #38BDF8;
        border-radius: 8px;
        color: #FFFFFF;
        font-weight: 700;
        font-size: 9.5pt;
        padding: 9px 18px;
    }
    QPushButton#DevButton:hover {
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #2563EB, stop:0.5 #0EA5E9, stop:1 #22D3EE);
        border: 1px solid #7DD3FC;
    }
    QTableWidget {
        background-color: #141822;
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 8px;
        gridline-color: rgba(255, 255, 255, 0.04);
        color: #F8FAFC;
        font-size: 8.5pt;
        selection-background-color: rgba(56, 189, 248, 0.22);
    }
    QHeaderView::section {
        background-color: #1D222E;
        color: #94A3B8;
        font-weight: 700;
        font-size: 8.5pt;
        border: none;
        border-bottom: 1px solid rgba(255, 255, 255, 0.10);
        padding: 5px 8px;
    }
    QTableWidget::item {
        padding: 4px 8px;
        border-bottom: 1px solid rgba(255, 255, 255, 0.03);
    }
    """
