# 🎀 Hayasaka Ai — Telegram Personal Assistant Bot

Bot asisten pribadi berbasis AI dengan karakter **Hayasaka Ai** dari anime *Kaguya-sama: Love is War*.
Ditenagai **Groq API** (llama-3.1-8b-instant) dan berjalan 100% gratis.

---

## ✨ Fitur

| Fitur | Deskripsi |
|---|---|
| 💰 Pencatatan Keuangan | Catat pemasukan & pengeluaran, lihat laporan bulanan |
| 📚 Jadwal Kuliah | Tambah, lihat, dan hapus jadwal per hari |
| 🧠 Memori Percakapan | Bot mengingat konteks percakapan sebelumnya |
| 🎭 Karakter Hayasaka Ai | Persona pelayan profesional, efisien, dan sedikit sarkastis |

---

## 🛠️ Persiapan Sebelum Instalasi

Kamu membutuhkan dua hal utama (keduanya **gratis**):

### 1. Token Bot Telegram
1. Buka Telegram, cari **@BotFather**
2. Ketik `/newbot` dan ikuti instruksinya
3. Setelah selesai, kamu akan mendapat **token** seperti `123456:ABC-DEF1234...`
4. Simpan token ini!

### 2. API Key Groq
1. Buka https://console.groq.com
2. Daftar akun gratis (bisa pakai Google)
3. Pergi ke **API Keys** → **Create API Key**
4. Salin API Key yang diberikan

---

## 🚀 Cara Instalasi

### Opsi A — Menjalankan di PC/Laptop (Windows/Mac/Linux)

```bash
# 1. Clone atau download project ini ke foldermu

# 2. Masuk ke folder project
cd hayasaka-bot

# 3. Buat virtual environment (sangat disarankan)
python -m venv venv

# Di Windows:
venv\Scripts\activate
# Di Mac/Linux:
source venv/bin/activate

# 4. Install semua dependensi
pip install -r requirements.txt

# 5. Buat file .env dari template
cp .env.example .env

# 6. Edit file .env dan isi TELEGRAM_TOKEN serta GROQ_API_KEY
# Gunakan Notepad (Windows) atau nano (Linux/Mac):
nano .env

# 7. Jalankan bot!
python bot.py
```

Bot akan berjalan selama terminal terbuka. Untuk menghentikan: tekan `Ctrl+C`.

---

### Opsi B — Menjalankan di Android via Termux (100% Gratis, Tanpa PC)

**Termux** adalah emulator terminal untuk Android yang memungkinkan kamu menjalankan Python langsung di HP.

```bash
# 1. Install Termux dari F-Droid (BUKAN dari Play Store — versi Play Store sudah tidak diupdate)
#    Link: https://f-droid.org/en/packages/com.termux/

# 2. Buka Termux, update package
pkg update && pkg upgrade -y

# 3. Install Python dan Git
pkg install python git -y

# 4. Clone project (atau upload manual ke /sdcard lalu salin)
git clone <URL_REPO_KAMU>
cd hayasaka-bot

# 5. Install dependensi
pip install -r requirements.txt

# 6. Buat dan edit file .env
cp .env.example .env
nano .env
# Isi TELEGRAM_TOKEN dan GROQ_API_KEY, lalu simpan (Ctrl+X, Y, Enter)

# 7. Jalankan bot
python bot.py
```

> **Tip Termux:** Gunakan `nohup python bot.py &` agar bot tetap berjalan meski Termux ditutup.
> Untuk menghentikannya: `kill $(pgrep -f bot.py)`

---

### Opsi C — Deploy ke Render (Hosting Gratis, Berjalan 24 Jam)

1. Push project ini ke GitHub (pastikan `.env` ada di `.gitignore`!)
2. Daftar di https://render.com (gratis)
3. Buat **New Web Service** → hubungkan ke repo GitHub kamu
4. Atur:
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `python bot.py`
5. Di bagian **Environment Variables**, tambahkan `TELEGRAM_TOKEN` dan `GROQ_API_KEY`
6. Deploy!

---

## 📖 Cara Menggunakan Bot

### Perintah Keuangan

```
/masuk 500rb gaji uang saku bulan April
/masuk 1.5jt freelance proyek website
/keluar 25rb makan nasi goreng ayam
/keluar 150rb transportasi ongkos ojek seminggu
/laporan              ← laporan bulan ini
/laporan 2025-03      ← laporan bulan tertentu
```

### Perintah Jadwal Kuliah

```
/tambah_jadwal Senin|Pemrograman Web|08:00|10:00|Lab A|Pak Budi
/tambah_jadwal Rabu|Basis Data|13:00|15:00|Ruang 301|Bu Sari
/jadwal         ← tampilkan semua jadwal
/hari_ini       ← jadwal hari ini saja
/hapus_jadwal 3 ← hapus jadwal dengan ID 3
```

### Chat Bebas

Cukup kirim pesan biasa! Hayasaka akan merespons sesuai konteks percakapan sebelumnya.

```
"Hari ini ada kuliah apa ya?"
"Rekap pengeluaranku bulan ini gimana?"
"Tolong buatkan jadwal belajar yang efektif untukku"
"Apa tips mengelola keuangan mahasiswa?"
```

### Lainnya

```
/reset_memori   ← hapus semua riwayat percakapan
/bantuan        ← tampilkan semua perintah
```

---

## 🗂️ Struktur Project

```
hayasaka-bot/
├── bot.py            ← File utama bot
├── requirements.txt  ← Daftar dependensi Python
├── .env.example      ← Template konfigurasi
├── .env              ← Konfigurasi aktual (jangan di-commit!)
├── .gitignore        ← Daftar file yang diabaikan Git
└── hayasaka.db       ← Database SQLite (dibuat otomatis saat pertama jalan)
```

---

## 🔒 Keamanan

- File `.env` berisi data sensitif. **Jangan pernah** membagikannya atau meng-commit-nya ke Git.
- Database `hayasaka.db` berisi semua catatan keuangan dan jadwal kamu. Backup secara berkala!
- Bot ini hanya merespons perintah dari Telegram — datamu aman di device/server kamu sendiri.

---

## 🧩 Teknologi yang Digunakan

| Komponen | Tool | Biaya |
|---|---|---|
| Telegram Bot | python-telegram-bot v21 | Gratis |
| LLM API | Groq (llama-3.1-8b-instant) | Gratis |
| Database | SQLite (bawaan Python) | Gratis |
| Konfigurasi | python-dotenv | Gratis |

---

## ❓ FAQ

**Q: Apakah bot ini bisa digunakan oleh banyak orang sekaligus?**
A: Ya! Data keuangan, jadwal, dan memori percakapan disimpan terpisah per `user_id` Telegram.

**Q: Kenapa bot tidak merespons?**
A: Pastikan bot sedang berjalan (`python bot.py` aktif di terminal). Cek juga apakah `TELEGRAM_TOKEN` sudah benar.

**Q: Apakah data saya aman di Groq?**
A: Groq memproses pesanmu untuk menghasilkan respons. Baca kebijakan privasi Groq di https://groq.com/privacy-policy.

**Q: Bisa ganti model LLM-nya?**
A: Bisa! Di `bot.py`, cari `model="llama-3.1-8b-instant"` dan ganti dengan model Groq lain seperti `llama-3.3-70b-versatile` (lebih pintar tapi lebih lambat).
