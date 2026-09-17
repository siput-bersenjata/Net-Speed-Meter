# Modern Windows Speed Meter Widget — Walkthrough

Widget monitoring network speed modern bergaya Windows 11 Fluent Design telah selesai dibangun dan siap digunakan di sistem Windows Anda.

---

## 🌟 Fitur Utama yang Telah Diimplementasikan

### 1. Tiga (3) Gaya Tampilan Widget yang Dapat Diganti Seketika:
* **Capsule Pill (Default)**:
  - Bentuk kapsul melengkung (*rounded 17px*), latar belakang *dark frosted glass* (`rgba(20, 22, 28, 0.92)`) dengan border tipis elegan.
  - Indikator neon `▲` (Upload hijau emerald) dan `▼` (Download biru cyan) dengan font Segoe UI Variable yang sangat tajam dan terbaca jelas.
* **Taskbar Compact Bar**:
  - Format 2 baris ultra-ramping khusus dirancang menempel rapi di Windows Taskbar tepat di sebelah kumpulan icon sistem (Wi-Fi, Volume, Jam).
* **Floating Glass Card**:
  - Tampilan kartu mengambang modern yang menampilkan kecepatan, **Grafik Mini Real-Time (Sparkline)** riwayat kecepatan, **Badge Ping / Latency (ms)**, dan **Total Kuota Data Sesi Terpakai**.

---

### 2. Bebas Pindah (Drag & Drop) & Auto-Snap ke Samping Ikon Wi-Fi:
* **Drag-and-Drop Halus**: Klik dan tahan di mana saja pada widget untuk memindahkannya ke monitor atau posisi mana pun.
* **Auto-Save Posisi**: Posisi terakhir koordinat $(X, Y)$ otomatis tersimpan ke `settings.json` saat mouse dilepas.
* **⚡ Snap ke Samping Ikon Wi-Fi**:
  - Klik kanan pada widget atau tray icon -> pilih **"⚡ Snap ke Samping Wi-Fi"**.
  - Aplikasi secara dinamis mendeteksi koordinat taskbar dan notification area Windows (`TrayNotifyWnd`), lalu langsung menempatkan widget dengan presisi di sebelah kiri icon Wi-Fi/Tray.

---

### 3. Menu Klik Kanan & System Tray Windows:
* **Menu Klik Kanan Lengkap**:
  - ⚡ **Snap ke Samping Wi-Fi**
  - 🎨 **Gaya Tampilan** (*Capsule Pill*, *Taskbar Compact Bar*, *Floating Glass Card*)
  - 🔒 **Kunci Posisi** (*Lock Position*) untuk mencegah widget tergeser tidak sengaja
  - 📌 **Always on Top** (tetap melayang di atas jendela aplikasi lain)
  - ⚙️ **Pengaturan...** (buka jendela konfigurasi)
  - ❌ **Keluar**
* **System Tray Icon**:
  - Icon modern di taskbar tray dengan tooltip kecepatan real-time (`▲ Up: ... | ▼ Down: ... | Ping: ... ms`).
  - Klik 1x untuk menyembunyikan/menampilkan widget, klik 2x untuk membuka Pengaturan.

---

### 4. Dialog Pengaturan Modern (Fluent Design):
* **Tab Umum**: Pilihan mode tampilan, Always on Top, Kunci Posisi, dan tombol Snap Wi-Fi.
* **Tab Jaringan**: Pemilihan adapter kartu jaringan (Auto / Wi-Fi / Ethernet spesifik) dan frekuensi refresh (500ms, 1s, 2s).
* **Tab Tampilan**: Pemilih warna kustom untuk panah Upload & Download, slider transparansi kaca (*opacity 50% - 100%*).
* **Tab Startup**: Opsi aktivasi otomatis saat Windows mulai dinyalakan.

---

## 📁 Struktur File Proyek

```
Speed meter/
├── main.py                # Bootstrap aplikasi & single-instance enforcement
├── widget_window.py       # Widget melayang 3-mode dengan drag & sparkline
├── network_monitor.py     # Background QThread pengukur delta bytes & ping
├── win_utils.py           # Win32 taskbar Wi-Fi geometry & autostart registry
├── settings_dialog.py     # Dialog pengaturan Fluent modern
├── tray_manager.py        # System tray icon Windows + context menu
├── styles.py              # QSS stylesheets & design tokens (Fluent Glass)
├── config_manager.py      # Pengelola settings.json & persistensi koordinat
├── run.bat                # Shortcut peluncur langsung tanpa jendela konsol hitam
└── tests/                 # Automated test suite (100% PASS)
    ├── test_config_manager.py
    ├── test_network_monitor.py
    └── test_win_utils.py
```

---

## 🚀 Cara Menjalankan

Aplikasi saat ini **sudah aktif berjalan di background desktop Anda**.

Untuk menjalankannya kapan saja di kemudian hari:
1. Cukup klik ganda file **`run.bat`**, atau
2. Jalankan perintah di terminal:
   ```powershell
   pythonw.exe main.py
   ```
*(Menggunakan `pythonw.exe` akan menjalankan widget secara bersih di background tanpa membuka jendela command prompt hitam).*
