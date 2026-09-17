# ⚡ Net Speed Meter

A sleek, lightweight, and modern real-time internet speed monitor widget for Windows 10 & Windows 11. Built with Python & PySide6 (Qt6), featuring Windows 11 Fluent Design, translucent glassmorphism, and customizable neon accents.

---

## 🌟 Fitur Utama (Features)

- **🚀 Real-Time Speed Telemetry**: Memantau kecepatan unduh (*download*) dan unggah (*upload*) secara akurat dan responsif.
- **🎨 3 Mode Tampilan**:
  - **Capsule Pill**: Kapsul melayang modern di atas layar.
  - **Taskbar Docked**: Menyatu rapi di dalam taskbar Windows, tepat di sebelah ikon Wi-Fi & Baterai.
  - **Floating Glass Card**: Kartu detail lengkap dengan grafik sparkline mini, latensi ping, dan total pemakaian sesi.
- **📐 4 Template Bentuk (Anti-Mengkotak)**:
  - 💊 **Kapsul Bulat Penuh (*Pill*)**: Ujung membulat sempurna setengah lingkaran (`border-radius: 9999px`).
  - 🔘 **Badge Melengkung (*Badge*)**: Oval melengkung halus dan proporsional.
  - 🫧 **Melengkung Modern (*Rounded*)**: Sudut membulat 12px bergaya Fluent Design.
  - ✨ **Hanya Tulisan (*Text-Only*)**: Bersih tanpa kotak latar belakang dan tanpa border.
- **🖱️ Mode Tembus Klik (*Click-Through*)**:
  - Semua klik mouse langsung menembus widget menuju tombol, ikon tray, atau jendela di belakangnya tanpa terhalang.
  - Tetap dapat dikontrol dengan mudah kapan saja melalui klik kanan pada **Ikon System Tray**.
- **🎚️ Transparansi Penuh (0% - 100% Opacity)**:
  - Slider opasitas fleksibel hingga 0% (transparan murni hanya tulisan).
- **📌 Always on Top & Lock Position**: Opsi untuk mengunci posisi widget agar tidak sengaja tergeser.
- **⚙️ Dialog Pengaturan Lengkap**:
  - Pilihan adaptor jaringan (NIC selector).
  - Penyesuaian frekuensi refresh (500ms, 1s, 2s).
  - Skala ukuran widget (65% hingga 150%) atau dengan `Ctrl + Scroll`.
  - Pemilih warna indikator Upload & Download.
  - Integrasi startup otomatis Windows.

---

## 🛠️ Instalasi & Menjalankan dari Source

### Persyaratan:
- Windows 10 atau Windows 11
- Python 3.10+

### Langkah-langkah:
1. **Clone repository ini**:
   ```bash
   git clone https://github.com/siput-bersenjata/Net-Speed-Meter.git
   cd Net-Speed-Meter
   ```

2. **Install dependensi**:
   ```bash
   pip install -r requirements.txt
   ```
   *(atau `pip install PySide6 psutil pywin32`)*

3. **Jalankan aplikasi**:
   ```bash
   python main.py
   ```

---

## 🖱️ Pintasan & Kontrol
- **Klik Kanan Widget**: Membuka context menu (Mode, Template Bentuk, Tembus Klik, Kunci Posisi, Pengaturan).
- **Ikon System Tray (Dekat Jam)**:
  - **Klik Kiri**: Tampilkan / Sembunyikan widget.
  - **Klik Ganda**: Buka menu Pengaturan.
  - **Klik Kanan**: Menu lengkap (selalu dapat diakses meskipun Mode Tembus Klik aktif).
- **Ctrl + Scroll Mouse**: Mengubah ukuran/skala widget secara instan.

---

## 📄 Lisensi
Didistribusikan di bawah lisensi MIT.
