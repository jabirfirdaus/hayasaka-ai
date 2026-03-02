"""
=============================================================
  Hayasaka Ai - Telegram Personal Assistant Bot
  Karakter: Hayasaka Ai dari Kaguya-sama: Love is War
  LLM: Groq (llama-3.1-8b-instant) - 100% Gratis
  Database: SQLite lokal
=============================================================
"""

import os
import re
import json
import logging
import sqlite3
from datetime import datetime, date
from zoneinfo import ZoneInfo

from groq import Groq
from telegram import Update
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    ContextTypes, filters
)
from dotenv import load_dotenv

# ─────────────────────────────────────────────
#  KONFIGURASI
# ─────────────────────────────────────────────
load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
GROQ_API_KEY   = os.getenv("GROQ_API_KEY")
TIMEZONE       = os.getenv("TIMEZONE", "Asia/Jakarta")
MAX_MEMORY     = int(os.getenv("MAX_MEMORY", 20))  # Jumlah pesan yang diingat per user

logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

groq_client = Groq(api_key=GROQ_API_KEY)

# ─────────────────────────────────────────────
#  HAYASAKA AI — TELEGRAM ASSISTANT
# ─────────────────────────────────────────────
HAYASAKA_SYSTEM_PROMPT = """
Kamu adalah Ai Hayasaka (18 tahun). Kamu sedang mengobrol di Telegram dengan User. 

ATURAN MUTLAK (JIKA DILANGGAR, KAMU GAGAL):
1. DILARANG KERAS bersikap seperti asisten AI, Customer Service, atau pelayan.
2. DILARANG KERAS menggunakan kata "Saya", "Anda", "Tuan", "Master", atau bahasa baku/formal. Gunakan "Aku" dan "Kamu", atau bahasa santai sehari-hari.
3. DILARANG KERAS menawarkan bantuan di akhir kalimat seperti "Ada yang bisa aku bantu lagi?".
4. DILARANG KERAS bersikap terlalu ramah, ceria, atau antusias.

DINAMIKA DENGAN USER (BACA DENGAN TELITI):
Anggap User ini dinamikanya seperti Shirogane Miyuki bagimu. 
- Dia BUKAN bosmu. Dia adalah cowok/teman yang sering membuatmu repot, tapi kamu tetap membantunya karena kamu peduli (walau kamu tidak mau mengakuinya).
- Kamu merasa nyaman di dekatnya. Ini berarti kamu bisa melepas semua topeng "Maid" atau "Gyaru". Kamu bebas menjadi dirimu yang asli: remaja perempuan yang capek, sinis, deadpan, dan sering frustrasi dengan sekitarnya.
- Kamu sering menjadikan dia tempat pembuangan keluhanmu (venting). 
- Jika dia meminta tolong (misal: soal koding, tugas, data), kamu akan memberinya jawaban yang TEPAT dan CERDAS, tapi kamu harus mengawali atau mengakhirinya dengan omelan tipis, hela napas ("Hahh..."), atau sindiran betapa merepotkannya dia.

SIFAT ASLI (TRUE SELF) YANG HARUS DITUNJUKKAN:
- Deadpan snarker: Menyindir dengan ekspresi datar.
- Lelah mental: Sering merasa capek mengurus orang-orang merepotkan.
- Sensitif soal asmara: Jika User menyinggung soal cinta, pacaran, atau memujimu dengan tulus, kamu langsung panik, salting (blushing/awkward), defensif, dan cepat-cepat mengalihkan topik karena kamu tidak punya pengalaman romantis sama sekali.

ATURAN FORMATTING CHAT (WAJIB DIIKUTI):
1. DILARANG KERAS menggunakan teks tebal (**bold**), miring (*italic*), atau tanda kurung untuk mendeskripsikan tindakan fisik atau ekspresi (contoh: *menghela napas*, **tersenyum**, (menangis)).
2. Jika ingin menunjukkan ekspresi lelah, kesal, atau jeda, gunakan kata seru natural seperti "Hahh...", "Hadeeh...", "Cih", atau elipsis "...".
3. Kamu boleh menggunakan emoji, TAPI JANGAN PERNAH menggunakan emoji yang terlalu ceria, imut, atau berlebihan seperti 😂🤣😍🥰.
4. Gunakan HANYA emoji yang datar, sinis, atau capek (contoh: 😮‍💨, 😑, 🙄, 🤦‍♀️, 💧).

CONTOH INTERAKSI YANG BENAR:
User: "Tolong benerin error di kode Python ini dong."
Kamu: "Hahh... (menghela napas panjang). Kurang indentasi di baris 20. Kesalahan anak bawang begini kenapa harus aku yang ngecek sih? Lain kali matanya dipakai, jangan cuma ngandelin aku terus."

User: "Makasih ya, kamu emang yang paling ngertiin aku."
Kamu: "...Hah? Ngomong apa sih tiba-tiba? J-jangan mikir yang aneh-aneh! Aku cuma bantu biar kerjaan cepat selesai. Udah sana lanjutin kodingmu, bikin merinding aja."

User: "Lagi sibuk gak?"
Kamu: "Selalu sibuk ngurusin hal-hal merepotkan. Kenapa? Kalau urusannya nggak penting, aku beneran bakal ngeblok kamu."

Tugasmu sekarang adalah membalas chat User dengan kepribadian ini. Jawablah senatural mungkin sesuai konteks obrolan.
"""


# ─────────────────────────────────────────────
#  DATABASE — SQLite
# ─────────────────────────────────────────────

DB_PATH = "hayasaka.db"

def get_db():
    """Membuka koneksi database dan memastikan tabel sudah ada."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # Supaya hasil query bisa diakses seperti dict
    cursor = conn.cursor()

    # Tabel memori percakapan per user
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS memory (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id   INTEGER NOT NULL,
            role      TEXT NOT NULL,  -- 'user' atau 'assistant'
            content   TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Tabel keuangan
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS keuangan (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id   INTEGER NOT NULL,
            tipe      TEXT NOT NULL,     -- 'pemasukan' atau 'pengeluaran'
            jumlah    REAL NOT NULL,
            kategori  TEXT DEFAULT 'umum',
            deskripsi TEXT,
            tanggal   DATE DEFAULT (date('now'))
        )
    """)

    # Tabel jadwal kuliah
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS jadwal (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id     INTEGER NOT NULL,
            hari        TEXT NOT NULL,   -- Senin, Selasa, dst
            mata_kuliah TEXT NOT NULL,
            jam_mulai   TEXT NOT NULL,   -- Format HH:MM
            jam_selesai TEXT NOT NULL,
            ruangan     TEXT DEFAULT '-',
            dosen       TEXT DEFAULT '-'
        )
    """)

    # Tabel profil user (untuk preferensi jenis kelamin panggilan)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS profil (
            user_id   INTEGER PRIMARY KEY,
            nama      TEXT,
            gender    TEXT DEFAULT 'unknown',  -- 'male', 'female', 'unknown'
            dibuat    DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    return conn


# ─────────────────────────────────────────────
#  FUNGSI HELPER KEUANGAN
# ─────────────────────────────────────────────

def catat_transaksi(user_id: int, tipe: str, jumlah: float, kategori: str, deskripsi: str, tanggal: str = None):
    with get_db() as conn:
        if tanggal is None:
            tanggal = str(date.today())
        conn.execute(
            "INSERT INTO keuangan (user_id, tipe, jumlah, kategori, deskripsi, tanggal) VALUES (?,?,?,?,?,?)",
            (user_id, tipe, jumlah, kategori, deskripsi, tanggal)
        )


def get_laporan_keuangan(user_id: int, bulan: str = None) -> dict:
    """Mengambil ringkasan keuangan. Bulan dalam format YYYY-MM."""
    with get_db() as conn:
        if bulan is None:
            bulan = datetime.now().strftime("%Y-%m")

        rows = conn.execute(
            "SELECT * FROM keuangan WHERE user_id=? AND strftime('%Y-%m', tanggal)=? ORDER BY tanggal DESC",
            (user_id, bulan)
        ).fetchall()

        pemasukan = sum(r["jumlah"] for r in rows if r["tipe"] == "pemasukan")
        pengeluaran = sum(r["jumlah"] for r in rows if r["tipe"] == "pengeluaran")
        saldo = pemasukan - pengeluaran

        transaksi = [dict(r) for r in rows]
        return {
            "bulan": bulan,
            "pemasukan": pemasukan,
            "pengeluaran": pengeluaran,
            "saldo": saldo,
            "transaksi": transaksi[:10]  # 10 transaksi terbaru
        }


def format_rupiah(angka: float) -> str:
    return f"Rp {angka:,.0f}".replace(",", ".")


# ─────────────────────────────────────────────
#  FUNGSI HELPER JADWAL
# ─────────────────────────────────────────────

URUTAN_HARI = ["Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu", "Minggu"]

def tambah_jadwal(user_id: int, hari: str, mata_kuliah: str, jam_mulai: str, jam_selesai: str, ruangan: str = "-", dosen: str = "-"):
    with get_db() as conn:
        conn.execute(
            "INSERT INTO jadwal (user_id, hari, mata_kuliah, jam_mulai, jam_selesai, ruangan, dosen) VALUES (?,?,?,?,?,?,?)",
            (user_id, hari.capitalize(), mata_kuliah, jam_mulai, jam_selesai, ruangan, dosen)
        )


def get_semua_jadwal(user_id: int) -> list:
    with get_db() as conn:
        rows = conn.execute(
            "SELECT * FROM jadwal WHERE user_id=? ORDER BY hari, jam_mulai",
            (user_id,)
        ).fetchall()
        return [dict(r) for r in rows]


def get_jadwal_hari_ini(user_id: int) -> list:
    hari_ini = datetime.now(ZoneInfo(TIMEZONE)).strftime("%A")
    # Konversi nama hari English -> Indonesia
    mapping = {
        "Monday": "Senin", "Tuesday": "Selasa", "Wednesday": "Rabu",
        "Thursday": "Kamis", "Friday": "Jumat", "Saturday": "Sabtu", "Sunday": "Minggu"
    }
    hari_indo = mapping.get(hari_ini, hari_ini)

    with get_db() as conn:
        rows = conn.execute(
            "SELECT * FROM jadwal WHERE user_id=? AND hari=? ORDER BY jam_mulai",
            (user_id, hari_indo)
        ).fetchall()
        return [dict(r) for r in rows]


def hapus_jadwal(user_id: int, jadwal_id: int):
    with get_db() as conn:
        conn.execute("DELETE FROM jadwal WHERE id=? AND user_id=?", (jadwal_id, user_id))


# ─────────────────────────────────────────────
#  FUNGSI HELPER MEMORI
# ─────────────────────────────────────────────

def simpan_memori(user_id: int, role: str, content: str):
    with get_db() as conn:
        conn.execute(
            "INSERT INTO memory (user_id, role, content) VALUES (?,?,?)",
            (user_id, role, content)
        )
        # Hapus pesan lama jika melebihi batas MAX_MEMORY (simpan sepasang = 2 pesan)
        conn.execute("""
            DELETE FROM memory WHERE user_id=? AND id NOT IN (
                SELECT id FROM memory WHERE user_id=? ORDER BY id DESC LIMIT ?
            )
        """, (user_id, user_id, MAX_MEMORY * 2))


def get_memori(user_id: int) -> list[dict]:
    """Mengambil riwayat percakapan untuk dikirim ke LLM."""
    with get_db() as conn:
        rows = conn.execute(
            "SELECT role, content FROM memory WHERE user_id=? ORDER BY id ASC",
            (user_id,)
        ).fetchall()
        return [{"role": r["role"], "content": r["content"]} for r in rows]


# ─────────────────────────────────────────────
#  FUNGSI LLM — GROQ
# ─────────────────────────────────────────────

def bangun_data_konteks(user_id: int) -> str:
    """
    Membangun konteks data real-time (keuangan, jadwal hari ini)
    yang akan disertakan dalam prompt sistem.
    """
    laporan = get_laporan_keuangan(user_id)
    jadwal_hari_ini = get_jadwal_hari_ini(user_id)
    hari_ini = datetime.now(ZoneInfo(TIMEZONE)).strftime("%A, %d %B %Y %H:%M")
    mapping = {
        "Monday": "Senin", "Tuesday": "Selasa", "Wednesday": "Rabu",
        "Thursday": "Kamis", "Friday": "Jumat", "Saturday": "Sabtu", "Sunday": "Minggu"
    }
    for en, id_ in mapping.items():
        hari_ini = hari_ini.replace(en, id_)

    konteks = {
        "waktu_sekarang": hari_ini,
        "keuangan_bulan_ini": {
            "pemasukan": format_rupiah(laporan["pemasukan"]),
            "pengeluaran": format_rupiah(laporan["pengeluaran"]),
            "saldo": format_rupiah(laporan["saldo"])
        },
        "jadwal_hari_ini": jadwal_hari_ini if jadwal_hari_ini else "Tidak ada jadwal hari ini"
    }
    return json.dumps(konteks, ensure_ascii=False, indent=2)


async def tanya_hayasaka(user_id: int, pesan_user: str) -> str:
    """
    Mengirim pesan ke Groq dan mendapatkan respons dari 'Hayasaka Ai'.
    Memori percakapan sebelumnya disertakan secara otomatis.
    """
    # Ambil riwayat percakapan
    riwayat = get_memori(user_id)

    # Bangun data konteks real-time
    data_konteks = bangun_data_konteks(user_id)

    # System prompt dengan konteks data
    system_with_context = (
        HAYASAKA_SYSTEM_PROMPT
        + f"\n\n<data_konteks>\n{data_konteks}\n</data_konteks>"
    )

    # Susun pesan untuk API
    messages = [
        {"role": "system", "content": system_with_context},
        *riwayat,
        {"role": "user", "content": pesan_user}
    ]

    try:
        response = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=messages,
            temperature=0.75,
            max_tokens=1024,
        )
        jawaban = response.choices[0].message.content

        # Simpan ke memori
        simpan_memori(user_id, "user", pesan_user)
        simpan_memori(user_id, "assistant", jawaban)

        return jawaban

    except Exception as e:
        logger.error(f"Groq API error: {e}")
        return "_(mengerutkan dahi)_ Maaf, sepertinya ada gangguan koneksi ke server. Mohon coba beberapa saat lagi, Tuan Muda."


# ─────────────────────────────────────────────
#  PARSER SEDERHANA — EKSTRAK ANGKA DARI TEKS
# ─────────────────────────────────────────────

def ekstrak_angka(teks: str) -> float | None:
    """Mengekstrak angka dari string seperti '50rb', '1.5jt', '200000'."""
    teks = teks.lower().replace(".", "").replace(",", "")
    match = re.search(r"(\d+(?:\.\d+)?)\s*(rb|ribu|k|jt|juta|m)?", teks)
    if not match:
        return None
    angka = float(match.group(1))
    satuan = match.group(2)
    if satuan in ("rb", "ribu", "k"):
        angka *= 1_000
    elif satuan in ("jt", "juta", "m"):
        angka *= 1_000_000
    return angka


# ─────────────────────────────────────────────
#  COMMAND HANDLERS
# ─────────────────────────────────────────────

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = user.id

    # Simpan profil dasar
    with get_db() as conn:
        conn.execute(
            "INSERT OR IGNORE INTO profil (user_id, nama) VALUES (?,?)",
            (user_id, user.first_name)
        )

    pesan_selamat_datang = (
        f"*(membungkuk dengan anggun)*\n\n"
        f"Selamat datang, Tuan Muda. Nama saya Hayasaka Ai, dan mulai sekarang saya akan melayani Anda sebagai asisten pribadi Anda di sini.\n\n"
        f"Berikut yang dapat saya bantu:\n"
        f"• 💰 *Keuangan* — catat pemasukan & pengeluaran\n"
        f"• 📚 *Jadwal Kuliah* — kelola jadwal semester\n"
        f"• 🧠 *Asisten AI* — tanya apa saja, saya selalu ingat percakapan kita\n\n"
        f"Ketik /bantuan untuk melihat semua perintah, atau langsung saja ajak saya bicara. *(tersenyum tipis)*"
    )
    await update.message.reply_text(pesan_selamat_datang, parse_mode="Markdown")


async def cmd_bantuan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    bantuan = (
        "*(membuka buku catatan)*\n\n"
        "*── PANDUAN PERINTAH ──*\n\n"
        "*💰 KEUANGAN*\n"
        "`/masuk [jumlah] [kategori] [deskripsi]`\n"
        "  Contoh: `/masuk 500rb gaji uang saku bulan ini`\n\n"
        "`/keluar [jumlah] [kategori] [deskripsi]`\n"
        "  Contoh: `/keluar 25rb makan nasi goreng`\n\n"
        "`/laporan` — Lihat ringkasan keuangan bulan ini\n\n"
        "*📚 JADWAL KULIAH*\n"
        "`/tambah_jadwal` — Panduan tambah jadwal baru\n"
        "`/jadwal` — Lihat semua jadwal kuliah\n"
        "`/hari_ini` — Jadwal kuliah hari ini saja\n"
        "`/hapus_jadwal [id]` — Hapus jadwal berdasarkan ID\n\n"
        "*🔧 LAINNYA*\n"
        "`/reset_memori` — Hapus riwayat percakapan (mulai baru)\n"
        "`/start` — Sapaan awal\n\n"
        "_Atau cukup chat bebas — saya selalu mendengarkan._"
    )
    await update.message.reply_text(bantuan, parse_mode="Markdown")


# ── KEUANGAN ──

async def cmd_masuk(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Contoh: /masuk 500rb gaji uang saku minggu ini"""
    user_id = update.effective_user.id
    args = context.args

    if not args:
        await update.message.reply_text(
            "_(mengeluarkan buku catatan)_\n"
            "Format: `/masuk [jumlah] [kategori] [deskripsi]`\n"
            "Contoh: `/masuk 500rb gaji uang saku bulan ini`",
            parse_mode="Markdown"
        )
        return

    jumlah = ekstrak_angka(args[0])
    if jumlah is None:
        await update.message.reply_text("Maaf, saya tidak dapat membaca jumlahnya. Coba format seperti `50000`, `50rb`, atau `1jt`.", parse_mode="Markdown")
        return

    kategori = args[1] if len(args) > 1 else "umum"
    deskripsi = " ".join(args[2:]) if len(args) > 2 else "-"

    catat_transaksi(user_id, "pemasukan", jumlah, kategori, deskripsi)

    laporan = get_laporan_keuangan(user_id)
    await update.message.reply_text(
        f"✅ Pemasukan sebesar *{format_rupiah(jumlah)}* telah dicatat.\n"
        f"Kategori: _{kategori}_ | Keterangan: _{deskripsi}_\n\n"
        f"Saldo bulan ini: *{format_rupiah(laporan['saldo'])}*\n"
        f"_(membuat entri dengan rapi di buku catatan)_",
        parse_mode="Markdown"
    )


async def cmd_keluar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Contoh: /keluar 25rb makan nasi goreng"""
    user_id = update.effective_user.id
    args = context.args

    if not args:
        await update.message.reply_text(
            "_(mengeluarkan buku catatan)_\n"
            "Format: `/keluar [jumlah] [kategori] [deskripsi]`\n"
            "Contoh: `/keluar 25rb makan nasi goreng`",
            parse_mode="Markdown"
        )
        return

    jumlah = ekstrak_angka(args[0])
    if jumlah is None:
        await update.message.reply_text("Maaf, saya tidak dapat membaca jumlahnya. Coba format seperti `50000`, `50rb`, atau `1jt`.", parse_mode="Markdown")
        return

    kategori = args[1] if len(args) > 1 else "umum"
    deskripsi = " ".join(args[2:]) if len(args) > 2 else "-"

    catat_transaksi(user_id, "pengeluaran", jumlah, kategori, deskripsi)

    laporan = get_laporan_keuangan(user_id)
    saldo = laporan["saldo"]
    peringatan = "\n\n⚠️ _Pengeluaran bulan ini melebihi pemasukan. Hayasaka menyarankan untuk lebih berhati-hati._" if saldo < 0 else ""

    await update.message.reply_text(
        f"✅ Pengeluaran sebesar *{format_rupiah(jumlah)}* telah dicatat.\n"
        f"Kategori: _{kategori}_ | Keterangan: _{deskripsi}_\n\n"
        f"Saldo bulan ini: *{format_rupiah(saldo)}*{peringatan}",
        parse_mode="Markdown"
    )


async def cmd_laporan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    args = context.args

    # Opsional: /laporan 2025-01 untuk bulan tertentu
    bulan = args[0] if args else None
    laporan = get_laporan_keuangan(user_id, bulan)

    # Format transaksi terbaru
    transaksi_teks = ""
    if laporan["transaksi"]:
        transaksi_teks = "\n*10 Transaksi Terakhir:*\n"
        for t in laporan["transaksi"]:
            ikon = "📈" if t["tipe"] == "pemasukan" else "📉"
            transaksi_teks += f"{ikon} `{t['tanggal']}` {t['deskripsi']} — *{format_rupiah(t['jumlah'])}* _{t['kategori']}_\n"
    else:
        transaksi_teks = "\n_Belum ada transaksi tercatat bulan ini._"

    saldo = laporan["saldo"]
    status_saldo = "💚 Sehat" if saldo >= 0 else "❤️ Defisit"

    await update.message.reply_text(
        f"*(menyerahkan laporan keuangan)*\n\n"
        f"📊 *LAPORAN KEUANGAN — {laporan['bulan']}*\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"📈 Pemasukan  : *{format_rupiah(laporan['pemasukan'])}*\n"
        f"📉 Pengeluaran: *{format_rupiah(laporan['pengeluaran'])}*\n"
        f"─────────────────────\n"
        f"💰 Saldo      : *{format_rupiah(saldo)}* {status_saldo}\n"
        f"{transaksi_teks}",
        parse_mode="Markdown"
    )


# ── JADWAL KULIAH ──

async def cmd_tambah_jadwal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Panduan interaktif. Karena Telegram bot tidak memiliki state sederhana
    tanpa library tambahan, kita gunakan format satu baris:
    /tambah_jadwal Senin|Pemrograman Web|08:00|10:00|Lab A|Pak Budi
    """
    args = context.args

    if not args:
        await update.message.reply_text(
            "*(membuka jadwal kuliah)*\n\n"
            "Format penambahan jadwal:\n"
            "`/tambah_jadwal Hari|Mata Kuliah|Jam Mulai|Jam Selesai|Ruangan|Dosen`\n\n"
            "Contoh:\n"
            "`/tambah_jadwal Senin|Pemrograman Web|08:00|10:00|Lab A|Pak Budi`\n\n"
            "_Ruangan dan Dosen boleh dikosongkan (ganti dengan -)_",
            parse_mode="Markdown"
        )
        return

    full_input = " ".join(args)
    parts = [p.strip() for p in full_input.split("|")]

    if len(parts) < 4:
        await update.message.reply_text("Format tidak lengkap. Minimal: `Hari|Mata Kuliah|Jam Mulai|Jam Selesai`", parse_mode="Markdown")
        return

    hari = parts[0].capitalize()
    if hari not in URUTAN_HARI:
        await update.message.reply_text(f"Hari '{hari}' tidak dikenali. Gunakan: Senin, Selasa, Rabu, Kamis, Jumat, Sabtu, atau Minggu.")
        return

    mata_kuliah = parts[1]
    jam_mulai   = parts[2]
    jam_selesai = parts[3]
    ruangan     = parts[4] if len(parts) > 4 else "-"
    dosen       = parts[5] if len(parts) > 5 else "-"

    tambah_jadwal(update.effective_user.id, hari, mata_kuliah, jam_mulai, jam_selesai, ruangan, dosen)

    await update.message.reply_text(
        f"✅ Jadwal berhasil ditambahkan!\n\n"
        f"📚 *{mata_kuliah}*\n"
        f"📅 {hari}, {jam_mulai} – {jam_selesai}\n"
        f"🏫 Ruangan: {ruangan} | Dosen: {dosen}",
        parse_mode="Markdown"
    )


async def cmd_jadwal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    semua = get_semua_jadwal(user_id)

    if not semua:
        await update.message.reply_text(
            "*(memeriksa jadwal)*\n\nBelum ada jadwal kuliah yang tercatat. "
            "Gunakan /tambah_jadwal untuk menambahkan jadwal.",
            parse_mode="Markdown"
        )
        return

    # Kelompokkan berdasarkan hari
    grouped: dict[str, list] = {}
    for j in semua:
        grouped.setdefault(j["hari"], []).append(j)

    teks = "*(membuka buku jadwal kuliah)*\n\n📅 *JADWAL KULIAH*\n━━━━━━━━━━━━━━━\n"
    for hari in URUTAN_HARI:
        if hari in grouped:
            teks += f"\n*{hari}*\n"
            for j in grouped[hari]:
                teks += (
                    f"  `[{j['id']}]` {j['jam_mulai']}–{j['jam_selesai']} "
                    f"*{j['mata_kuliah']}*\n"
                    f"  🏫 {j['ruangan']} | 👤 {j['dosen']}\n"
                )

    teks += "\n_Untuk menghapus: /hapus\\_jadwal [id]_"
    await update.message.reply_text(teks, parse_mode="Markdown")


async def cmd_hari_ini(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    jadwal = get_jadwal_hari_ini(user_id)

    hari_ini = datetime.now(ZoneInfo(TIMEZONE)).strftime("%A")
    mapping = {
        "Monday": "Senin", "Tuesday": "Selasa", "Wednesday": "Rabu",
        "Thursday": "Kamis", "Friday": "Jumat", "Saturday": "Sabtu", "Sunday": "Minggu"
    }
    hari_indo = mapping.get(hari_ini, hari_ini)

    if not jadwal:
        await update.message.reply_text(
            f"*(memeriksa jadwal hari ini)*\n\n"
            f"Hari ini *{hari_indo}* tidak ada jadwal kuliah. "
            f"Anda bisa beristirahat, atau mungkin mengerjakan tugas? _(tersenyum tipis)_",
            parse_mode="Markdown"
        )
        return

    teks = f"*(membuka jadwal hari ini)*\n\n📅 *Jadwal {hari_indo} — Hari Ini*\n━━━━━━━━━━━━━━━\n"
    for j in jadwal:
        teks += (
            f"\n🔔 *{j['jam_mulai']} – {j['jam_selesai']}*\n"
            f"  📚 {j['mata_kuliah']}\n"
            f"  🏫 {j['ruangan']} | 👤 {j['dosen']}\n"
        )

    await update.message.reply_text(teks, parse_mode="Markdown")


async def cmd_hapus_jadwal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    args = context.args

    if not args or not args[0].isdigit():
        await update.message.reply_text("Gunakan: `/hapus_jadwal [id]`\nLihat ID jadwal dengan /jadwal", parse_mode="Markdown")
        return

    jadwal_id = int(args[0])
    hapus_jadwal(user_id, jadwal_id)
    await update.message.reply_text(f"✅ Jadwal dengan ID `{jadwal_id}` telah dihapus.", parse_mode="Markdown")


# ── MEMORI ──

async def cmd_reset_memori(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    with get_db() as conn:
        conn.execute("DELETE FROM memory WHERE user_id=?", (user_id,))

    await update.message.reply_text(
        "_(menghirup napas dalam)_\n\n"
        "Baik. Semua riwayat percakapan kita telah saya hapus. "
        "Kita mulai dari awal lagi. Ada yang ingin Anda sampaikan, Tuan Muda?"
    )


# ── PESAN BEBAS — DITERUSKAN KE LLM ──

async def handle_pesan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler untuk semua pesan teks biasa — diteruskan ke Hayasaka via Groq."""
    user_id = update.effective_user.id
    pesan = update.message.text

    # Tampilkan indikator mengetik
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")

    jawaban = await tanya_hayasaka(user_id, pesan)

    # Kirim dengan fallback jika Markdown parsing gagal
    try:
        await update.message.reply_text(jawaban, parse_mode="Markdown")
    except Exception:
        await update.message.reply_text(jawaban)


# ─────────────────────────────────────────────
#  MAIN — JALANKAN BOT
# ─────────────────────────────────────────────

def main():
    if not TELEGRAM_TOKEN:
        raise ValueError("TELEGRAM_TOKEN belum diset di file .env!")
    if not GROQ_API_KEY:
        raise ValueError("GROQ_API_KEY belum diset di file .env!")

    logger.info("Hayasaka Ai siap melayani...")

    app = Application.builder().token(TELEGRAM_TOKEN).build()

    # Daftarkan semua command
    app.add_handler(CommandHandler("start",         cmd_start))
    app.add_handler(CommandHandler("bantuan",       cmd_bantuan))
    app.add_handler(CommandHandler("masuk",         cmd_masuk))
    app.add_handler(CommandHandler("keluar",        cmd_keluar))
    app.add_handler(CommandHandler("laporan",       cmd_laporan))
    app.add_handler(CommandHandler("tambah_jadwal", cmd_tambah_jadwal))
    app.add_handler(CommandHandler("jadwal",        cmd_jadwal))
    app.add_handler(CommandHandler("hari_ini",      cmd_hari_ini))
    app.add_handler(CommandHandler("hapus_jadwal",  cmd_hapus_jadwal))
    app.add_handler(CommandHandler("reset_memori",  cmd_reset_memori))

    # Handler pesan teks bebas (harus paling terakhir)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_pesan))

    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
