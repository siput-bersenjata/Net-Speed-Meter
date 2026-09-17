import json
import os
from pathlib import Path
from typing import Any, Dict

DEFAULT_CONFIG: Dict[str, Any] = {
    "pos_x": 100,
    "pos_y": 100,
    "widget_mode": "capsule",  # "capsule", "taskbar", "card"
    "always_on_top": True,
    "locked_position": False,
    "nic_name": "auto",
    "refresh_interval_ms": 1000,
    "opacity": 0.92,
    "theme": "dark_glass",
    "up_color": "#00E676",      # Vivid Emerald Neon
    "down_color": "#00E5FF",    # Vivid Cyan Neon
    "font_family": "Segoe UI Variable Display, Segoe UI, sans-serif",
    "font_size": 9,
    "autostart": True,
    "show_sparkline": True,
    "unit_mode": "auto",        # "auto", "KB/s", "MB/s"
    "widget_scale": 1.0,        # 0.65 to 1.50
    "hold_to_drag": True,       # Require holding mouse for 2 seconds before drag
    "hold_duration_ms": 2000,   # 2000 ms hold delay
    "is_taskbar_docked": False, # Whether the widget is docked inside the Windows taskbar
    "click_through": False,     # Pass mouse events through to windows/buttons behind
    "shape_template": "pill"    # "pill", "badge", "rounded", "text_only"
}

class ConfigManager:
    """Manages application configuration, reading/writing to settings.json."""

    def __init__(self, filepath: str = None):
        if filepath is None:
            base_dir = Path.home() / ".speed_meter"
            base_dir.mkdir(parents=True, exist_ok=True)
            self.filepath = str(base_dir / "settings.json")
        else:
            self.filepath = filepath
            Path(self.filepath).parent.mkdir(parents=True, exist_ok=True)

        self.is_first_run = not os.path.exists(self.filepath)
        self.config: Dict[str, Any] = self._load()
        if self.is_first_run:
            self.save()

    def _load(self) -> Dict[str, Any]:
        if os.path.exists(self.filepath):
            try:
                with open(self.filepath, "r", encoding="utf-8") as f:
                    saved = json.load(f)
                    data = DEFAULT_CONFIG.copy()
                    data.update(saved)
                    return data
            except Exception as e:
                print(f"[ConfigManager] Warning: failed to parse config file: {e}")
                return DEFAULT_CONFIG.copy()
        return DEFAULT_CONFIG.copy()

    def save(self) -> None:
        try:
            with open(self.filepath, "w", encoding="utf-8") as f:
                json.dump(self.config, f, indent=4)
        except Exception as e:
            print(f"[ConfigManager] Error saving config: {e}")

    def get(self, key: str, default: Any = None) -> Any:
        return self.config.get(key, default)

    def set(self, key: str, value: Any, auto_save: bool = True) -> None:
        self.config[key] = value
        if auto_save:
            self.save()

    def get_all(self) -> Dict[str, Any]:
        return self.config.copy()
