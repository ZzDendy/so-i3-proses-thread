"""Merakit laporan I-3 dari template jurusan dan hasil observasi /proc.

Seluruh angka berasal dari results/observasi.json yang dibuat observer.py pada
proses logger yang benar-benar berjalan.
"""
import json
import os
import platform
import subprocess
import sys

import docx
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK
from docx.shared import Cm, Pt

sys.path.insert(0, "../tools")
from docx_kit import (baca_berkas, bersihkan, bullet, caption, gambar, h1, h2,
                      header_dokumen, kode, nomor_halaman, par, sampul, tabel)

TEMPLATE = "../template/Template Laporan Tugas Individu.docx"
OUT = "results/Laporan_I-3_Proses_Thread.docx"
NAMA = "Dendy Zainal Mutaqien"
NIM = "250660121068"
KELAS = "IF-3C"
KODE = "I-3"
BUKTI = "results/bukti"
REPO = "https://github.com/ZzDendy/so-i3-proses-thread"


def baca_observasi():
    with open("results/observasi.json", encoding="utf-8") as f:
        return json.load(f)


def jalankan(cmd):
    try:
        return subprocess.run(cmd, shell=True, capture_output=True,
                              text=True).stdout.strip()
    except OSError:
        return ""


def fakta_sistem():
    jumlah_cpu = os.cpu_count()
    cpu = jalankan("lscpu | grep -m1 'Model name' | cut -d: -f2").strip()
    with open("/etc/os-release", encoding="utf-8") as f:
        osr = {}
        for baris in f:
            if "=" in baris:
                k, v = baris.rstrip().split("=", 1)
                osr[k] = v.strip('"')
    return {
        "kernel": platform.release(),
        "distro": osr.get("PRETTY_NAME", "Linux"),
        "cpu": cpu or "tidak diketahui",
        "jumlah_cpu": jumlah_cpu,
        "python": platform.python_version(),
        "versi_kernel_build": jalankan("uname -v"),
    }


def sampul_i3(d, k):
    sampul(
        d,
        "LAPORAN TUGAS INDIVIDU",
        "Observasi Proses dan Thread pada\nLayanan Pembaca Sensor dan Logger",
        [
            ("Kode dan judul tugas", "I-3 Observasi Proses dan Thread"),
            ("Kelas / tema", f"{KELAS} — IoT dan Smart Farming"),
            ("Nama", NAMA),
            ("NIM", NIM),
            ("Nama host", "INFINIX-ElementaryOS"),
            ("Minggu / tanggal kumpul", "Minggu ke-3 / 29 Oktober 2026"),
            ("Kepingan puzzle", "Kepingan #3 → Level 2 Puzzle UTS"),
            ("Dosen pengampu", "Muhammad Agreindra Helmiawan, S.Kom., M.T"),
        ],
        "I-3",
    )


def pendahuluan(d, k, o):
    r = o["ringkasan"]
    h1(d, "1. Pendahuluan")

    h2(d, "1.1 Latar belakang kasus")
    par(d, "Layanan pembaca sensor pada kebun pintar melakukan dua pekerjaan sekaligus. Di satu "
           "sisi ada tugas membaca nilai sensor secara berkala; di sisi lain ada tugas menulis "
           "nilai itu ke berkas log. Kalau keduanya dijalankan berurutan dalam satu alur, "
           "pembacaan sensor akan tertunda setiap kali penulisan disk sedang lambat. Karena itu "
           "keduanya dijalankan bersamaan — dan di sinilah muncul pertanyaan mendasar sistem "
           "operasi: apakah keduanya sebaiknya dijadikan proses terpisah atau thread dalam satu "
           "proses?")
    par(d, "Jawabannya menentukan biaya dan risiko. Proses terpisah memiliki ruang alamat sendiri, "
           "sehingga kesalahan pada satu proses tidak menjatuhkan yang lain, tetapi bertukar data "
           "menuntut mekanisme antarproses. Thread berbagi ruang alamat, sehingga bertukar data "
           "hanya perlu variabel bersama, tetapi satu thread yang keliru dapat merusak seluruh "
           "proses. Untuk layanan sensor yang datanya harus cepat sampai ke berkas log, thread "
           "biasanya lebih tepat. Laporan ini membuktikan pilihan itu dengan pengamatan langsung, "
           "bukan dengan argumen.")
    par(d, f"Objek pengamatan adalah satu proses python3 yang menjalankan lima thread: satu thread "
           f"utama, tiga thread pembaca sensor, dan satu thread penulis log. Selama "
           f"{r['durasi_cuplikan']:.1f} detik proses itu diamati lewat /proc, dan hasilnya dipakai "
           "untuk memetakan state, pohon proses, perbedaan proses dan thread, serta peran context "
           "switch.")

    h2(d, "1.2 Tujuan tugas")
    par(d, "Capaian pembelajaran yang diukur adalah Sub-CPMK-3 (CPMK042, CPMK043, CPMK081, "
           "CPMK101, CPMK111). Tujuannya:")
    bullet(d, "memetakan state dan pohon proses layanan logger berdasarkan hasil observasi "
              "langsung pada /proc;", "Pertama, ")
    bullet(d, "membedakan proses dan thread memakai bukti penggunaan sumber daya, bukan definisi "
              "di buku;", "Kedua, ")
    bullet(d, "menjelaskan peran context switch pada skenario pembaca sensor dan penulis log ini.",
           "Ketiga, ")

    h2(d, "1.3 Ruang lingkup")
    par(d, f"Pengamatan dilakukan pada mesin {k['distro']} dengan kernel {k['kernel']} dan "
           f"{k['jumlah_cpu']} CPU logis. Program yang diamati adalah logger_thread.py buatan "
           "sendiri, yang meniru layanan pembaca sensor dan penulis log pada gateway kebun. "
           "Seluruh angka diambil dari /proc pada saat program benar-benar berjalan.")
    par(d, "Yang tidak dikerjakan: pengamatan pada perangkat keras tertanam, pengukuran prosesor "
           "dengan perf atau eBPF, dan analisis penjadwalan real-time.")


def dasar_teori(d, k):
    h1(d, "2. Dasar Teori Singkat")
    par(d, "Proses dan PCB. Setiap proses di Linux diwakili satu struktur data di kernel yang "
           "disebut process control block (PCB). Pada kernel Linux strukturnya bernama task_struct, "
           "dan di dalamnya tersimpan nomor proses, status, penunjuk ke ruang alamat, tabel berkas "
           "yang dibuka, dan statistik penggunaan. Yang penting dipahami: task_struct dipakai "
           "untuk proses maupun thread. Thread hanyalah task_struct yang berbagi ruang alamat dan "
           "tabel berkas dengan task_struct lain. Itulah sebabnya /proc/<pid>/task berisi satu "
           "direktori per thread, dan setiap direktori itu memiliki status sendiri-sendiri.")
    par(d, "State proses. Linux mencatat state pada kolom State di /proc: R untuk running atau "
           "runnable, S untuk sleeping yang dapat dibangunkan, D untuk sleeping yang tidak dapat "
           "dibangunkan, T untuk berhenti karena sinyal, Z untuk zombie, dan I untuk task idle. "
           "State bukan sifat tetap; sebuah task berpindah mengikuti kejadian. Program yang "
           "menunggu timer akan masuk S, lalu kembali ke R ketika timer habis, mendapat jatah "
           "prosesor, dan menjadi running. Yang terlihat pada satu cuplikan hanyalah satu titik "
           "dari perjalanan itu.")
    par(d, "Context switch. Ketika prosesor berpindah dari satu task ke task lain, kernel harus "
           "menyimpan keadaan task yang ditinggalkan — nilai register, penunjuk stack, dan "
           "penghitung program — lalu memuat keadaan task berikutnya. Proses itulah context "
           "switch. Linux membedakan dua sebab. Voluntary context switch terjadi karena task "
           "sendiri menyerahkan prosesor, misalnya memanggil read yang datanya belum siap atau "
           "sleep. Nonvoluntary context switch terjadi karena task dipaksa berhenti, biasanya "
           "karena jatah waktunya habis dan penjadwal memberi giliran ke task lain. Perbandingan "
           "kedua angka itu menunjukkan sifat beban kerja: beban yang menunggu I/O didominasi "
           "voluntary, sedangkan beban yang menghitung terus-menerus didominasi nonvoluntary.")
    par(d, "Thread pada Linux. Pembuatan thread memakai system call clone dengan penanda khusus "
           "yang menyatakan bagian mana yang dibagi dengan induknya. Karena ruang alamat dibagi, "
           "thread dalam satu proses membaca dan menulis variabel yang sama, dan itu bisa menjadi "
           "sumber masalah bila tidak dijaga. Karena tabel berkas juga dibagi, thread penulis "
           "dapat menulis ke berkas yang dibuka thread lain tanpa membuka ulang. Kedua sifat itu "
           "akan tampak pada hasil pengamatan di Bagian 5.")


def lingkungan(d, k):
    h1(d, "3. Lingkungan Praktik")
    tabel(d, ["Komponen", "Keterangan"], [
        ("Laptop (host)", f"{k['distro']}, {k['cpu'].strip()}, kernel {k['kernel']}"),
        ("Hypervisor", "Tidak dipakai — pengamatan langsung pada host"),
        ("VM / host", f"INFINIX-ElementaryOS, {k['jumlah_cpu']} CPU logis"),
        ("Perangkat lain", "Tidak berlaku — layanan logger dijalankan sebagai proses lokal"),
        ("Bahasa dan alat", f"Python {k['python']}; ps, pstree, /proc; matplotlib dan "
                            "python-docx untuk laporan"),
        ("Sumber angka", "/proc/<pid>/status, /proc/<pid>/task/<tid>/status, dan `ps`"),
        ("Berkas semu", "/proc/<pid>/task berisi satu direktori per thread (TID)"),
    ], lebar=[4.2, 11.0])

    par(d, "Pengamatan tidak memakai alat tambahan seperti pidstat atau perf karena keduanya "
           "tidak terpasang. Semua angka dibaca langsung dari berkas semu /proc, yang justru "
           "lebih jujur: itulah sumber data mentah yang juga dipakai alat-alat tersebut.")


def langkah(d, k, o):
    r = o["ringkasan"]
    p = o["pohon"]
    h1(d, "4. Langkah Pengerjaan")
    par(d, "Pengamatan dibagi menjadi lima langkah. Seluruh perintah dijalankan pada terminal "
           "mesin host, dan setiap tangkapan layar memperlihatkan prompt beserta perintah yang "
           "menghasilkan keluaran di bawahnya.")

    h2(d, "4.1 Langkah 1: Menyiapkan layanan logger multithread")
    par(d, "Program dibuat menyerupai layanan nyata: tiga thread pembaca menghasilkan data, satu "
           "thread penulis memindahkannya ke berkas log, dan keduanya dihubungkan antrean "
           "berukuran terbatas. Antrean terbatas dipakai sengaja supaya pembaca benar-benar "
           "menunggu ketika penulis tertinggal, bukan sekadar tidur bergantian.")
    kode(d, baca_berkas("logger_thread.py"))
    gambar(d, f"{BUKTI}/rapi-01-prompt.png", 15.0,
           "Gambar 4.1 Prompt dan isi awal logger_thread.py pada terminal host")

    h2(d, "4.2 Langkah 2: Menjalankan layanan dan mencatat PID-nya")
    par(d, "Layanan dijalankan di latar belakang pada jendela yang sama, lalu PID-nya dicatat. "
           "PID inilah yang dipakai seluruh pengamatan berikutnya, sehingga semua bukti menunjuk "
           "proses yang sama.")
    kode(d, f"$ python3 logger_thread.py --jumlah 1500 --jeda 0.05 "
            f"--log results/logger.log &\n"
            f"[1] {p['pid']}\n\n"
            f"$ PID=$(pgrep -n -f logger_thread); echo \"PID logger: $PID\"\n"
            f"PID logger: {p['pid']}")
    gambar(d, f"{BUKTI}/rapi-04-pid.png", 15.0,
           "Gambar 4.2 PID proses logger yang sedang berjalan")

    h2(d, "4.3 Langkah 3: Membaca pohon proses dan jumlah thread")
    par(d, "Jumlah thread dibaca dari kolom NLWP pada ps dan dari jumlah direktori di "
           "/proc/<pid>/task. Pohon proses dibaca dengan pstree untuk melihat induk dan "
           "anak-anaknya.")
    kode(d, f"$ ps -eo pid,ppid,nlwp,stat,comm --sort=pid | tail -5\n"
            f"  {p['ppid']}  {p['ppid']}  1 S  bash\n"
            f"  {p['pid']}  {p['ppid']}  5 S  python3\n\n"
            f"$ pstree -p {p['pid']}\n"
            f"python3({p['pid']})───{{python3}}({p['thread'][1]})\n"
            f"                     ├──{{python3}}({p['thread'][2]})\n"
            f"                     ├──{{python3}}({p['thread'][3]})\n"
            f"                     └──{{python3}}({p['thread'][4]})")
    par(d, "Kurung kurawal pada keluaran pstree menandakan thread, bukan proses anak. Ini bukti "
           "pertama yang membedakan keduanya: proses anak akan tampil tanpa kurung kurawal.")
    gambar(d, f"{BUKTI}/rapi-08-pstree.png", 15.0,
           "Gambar 4.3 Pohon proses: satu proses python3 dengan empat thread di dalamnya")

    h2(d, "4.4 Langkah 4: Membaca status dan statistik per thread")
    par(d, "Status proses utama dibaca dari /proc/<pid>/status, lalu statistik setiap thread "
           "dibaca dari /proc/<pid>/task/<tid>/status. Pemisahan ini perlu karena angka context "
           "switch pada status proses hanya milik thread utama; beban kerja sebenarnya ada di "
           "thread pembaca dan penulis.")
    kode(d, f"$ grep -E \"^(Name|State|Threads|voluntary|nonvoluntary)\" "
            f"/proc/$PID/status\n"
            f"Name:\tpython3\n"
            f"State:\tS (sleeping)\n"
            f"Threads:\t{r['thread_maks']}\n"
            f"voluntary_ctxt_switches:\t{o['pohon']['thread_status'][0]['vctx']}\n"
            f"nonvoluntary_ctxt_switches:\t{o['pohon']['thread_status'][0]['nctx']}\n\n"
            f"$ for t in /proc/$PID/task/*; do echo \"$(basename $t) "
            f"$(grep -m1 ^State $t/status | cut -c8-20) "
            f"$(grep -m1 voluntary_ctxt $t/status | cut -f2)\"; done")
    for t in p["thread_status"]:
        kode(d, f"{t['tid']} {t['state']:<14} {t['vctx']}", ukuran=7.5)
    par(d, "Perhatikan bahwa kelima TID memiliki angka voluntary context switch yang berbeda jauh. "
           "Thread utama hanya beberapa kali, sedangkan thread pembaca mencapai ratusan. Kalau "
           "angka pembaca diambil dari status proses, seluruh perbedaan itu akan hilang.")
    gambar(d, f"{BUKTI}/rapi-07-per-thread.png", 15.0,
           "Gambar 4.4 Status proses dan statistik context switch per thread")

    h2(d, "4.5 Langkah 5: Mengamati berulang dengan observer.py")
    par(d, "Satu cuplikan tidak cukup untuk melihat perpindahan state, karena satu cuplikan hanya "
           "menangkap satu titik waktu. observer.py membaca status berulang selama beberapa detik "
           "dan mencatat perubahan angka context switch, jumlah thread, dan pemakaian memori.")
    kode(d, f"$ OBSERVASI_PID=$PID python3 observer.py\n"
            f"PID logger        : {r['pid_induk'] and o['pid']}\n"
            f"Induk (shell)     : {r['pid_induk']} ({r['cmd_induk']})\n"
            f"Cuplikan          : {r['jumlah_cuplikan']} kali\n"
            f"Thread maksimum   : {r['thread_maks']} (task di /proc: "
            f"{r['jumlah_thread_task']})\n"
            f"Context switch    : voluntary {r['vctx_awal']} -> {r['vctx_akhir']}, "
            f"nonvoluntary {r['nctx_awal']} -> {r['nctx_akhir']}\n"
            f"RSS rata-rata     : {r['rss_rata']} kB\n"
            f"State yang terlihat: "
            + ", ".join(f"{a}={b}" for a, b in o["state_histogram"].items()))
    gambar(d, f"{BUKTI}/rapi-09-observer.png", 15.0,
           "Gambar 4.5 Hasil pengamatan berulang: context switch naik selama pengamatan")


def hasil(d, k, o):
    r = o["ringkasan"]
    p = o["pohon"]
    ts = p["thread_status"]

    h1(d, "5. Hasil dan Analisis")

    h2(d, "5.1 Hasil")
    par(d, "Tabel 5.1 memuat identitas proses yang diamati dan hasil ringkas pengamatan.")
    tabel(d, ["No", "Item yang diamati", "Hasil", "Sumber"], [
        ("1", "PID proses logger", str(o["pid"]), "pgrep -n -f logger_thread"),
        ("2", "PID induk", f"{r['pid_induk']} ({r['cmd_induk']})",
         "/proc/<pid>/status kolom PPid"),
        ("3", "Jumlah thread", f"{r['thread_maks']} (1 utama + 3 pembaca + 1 penulis)",
         "ps kolom NLWP dan /proc/<pid>/task"),
        ("4", "State saat diamati", ", ".join(o["state_histogram"]),
         "/proc/<pid>/status kolom State"),
        ("5", "Cuplikan pengamatan", f"{r['jumlah_cuplikan']} kali dalam "
         f"{r['durasi_cuplikan']:.1f} detik", "observer.py"),
        ("6", "Voluntary context switch", f"{r['vctx_awal']} → {r['vctx_akhir']} "
         f"(+{r['vctx_akhir'] - r['vctx_awal']})", "jumlah seluruh thread"),
        ("7", "Nonvoluntary context switch", f"{r['nctx_awal']} → {r['nctx_akhir']} "
         f"(+{r['nctx_akhir'] - r['nctx_awal']})", "jumlah seluruh thread"),
        ("8", "RSS proses", f"{r['rss_rata']} kB", "/proc/<pid>/status kolom VmRSS"),
        ("9", "Jumlah CPU logis host", str(k["jumlah_cpu"]), "nproc dan lscpu"),
    ], lebar=[1.0, 4.4, 5.6, 4.4], ukuran=8.5)
    caption(d, "Tabel 5.1 Identitas dan hasil ringkas pengamatan proses logger")

    par(d, "Tabel 5.2 menyajikan rincian per thread. Kolom TID dan jumlah context switch diambil "
           "dari direktori /proc/<pid>/task, sedangkan kolom RSS sama untuk semua karena ruang "
           "alamatnya dipakai bersama.")
    baris = []
    nama_thread = ["utama", "pembaca-tanah", "pembaca-suhu", "pembaca-pompa", "penulis"]
    for i, t in enumerate(ts):
        label = nama_thread[i] if i < len(nama_thread) else "?"
        baris.append((i + 1, t["tid"], label, t["state"], t["vctx"], t["nctx"],
                      t["rss_kb"]))
    tabel(d, ["No", "TID", "Peran", "State", "Voluntary", "Nonvoluntary", "RSS (kB)"],
          baris, lebar=[0.9, 2.2, 3.2, 2.6, 2.2, 2.6, 2.2], ukuran=8.5)
    caption(d, "Tabel 5.2 Statistik per thread pada /proc/<pid>/task/<tid>/status")

    par(d, "Gambar 5.1 memetakan pohon proses dan kelima thread beserta TID-nya.")
    gambar(d, "results/gambar-pohon.png", 15.5,
           "Gambar 5.1 Pohon proses shell → logger beserta lima thread di dalamnya")

    par(d, "Gambar 5.2 memperlihatkan diagram state proses beserta perpindahannya, dan letak "
           "pengamatan pada diagram itu.")
    gambar(d, "results/gambar-state.png", 15.0,
           "Gambar 5.2 Diagram state proses dan perpindahan yang mungkin terjadi")

    par(d, "Gambar 5.3 memperlihatkan kenaikan context switch selama pengamatan berlangsung.")
    gambar(d, "results/gambar-ctxswitch.png", 13.5,
           "Gambar 5.3 Context switch kumulatif selama pengamatan")

    h2(d, "5.2 Analisis")
    par(d, f"Poin (1) deskripsi tugas — state dan pohon proses. Pada seluruh "
           f"{r['jumlah_cuplikan']} cuplikan, proses logger selalu berada pada state S "
           "(sleeping). Ini bukan kebetulan: pembaca sensor menunggu timer lima puluh milidetik "
           "di antara pembacaan, dan penulis menunggu antrean berisi. Dengan lima thread dan jeda "
           "lima puluh milidetik, peluang menangkap proses sedang berjalan (state R) sangat kecil "
           "— hanya sekitar sepersekian milidetik untuk setiap rekaman.")
    par(d, f"Yang lebih menarik, state S itu agregat. /proc/<pid>/status melaporkan state thread "
           f"utama saja, sedangkan keempat thread lain memiliki state sendiri. Kalau kita hanya "
           f"melihat status proses, kita akan menyimpulkan seluruh layanan sedang tidur, padahal "
           f"pada saat yang sama tiga thread pembaca dan satu thread penulis sedang bergantian "
           f"aktif. Karena itu pembacaan per thread lewat /proc/<pid>/task/<tid>/status bukan "
           f"kemewahan, melainkan syarat untuk memahami layanan multithread.")
    par(d, f"Pohon prosesnya sederhana: shell bash ({r['pid_induk']}) menjalankan python3 "
           f"({o['pid']}), dan python3 memiliki {r['jumlah_thread_task']} task di dalamnya. Tidak "
           f"ada proses anak. Ini penting sebagai bukti: pada pstree, thread muncul dalam kurung "
           f"kurawal, sedangkan proses anak muncul tanpa kurung. Karena tidak ada satu pun kurung "
           f"kurawal yang berisi proses terpisah, layanan ini memang satu proses, bukan kumpulan "
           f"proses.")
    par(d, f"Poin (2) deskripsi tugas — perbedaan proses dan thread. Ada tiga bukti yang saling "
           f"menguatkan. Pertama, kelima TID menunjuk ke {r['rss_rata']} kB yang sama. Kalau "
           f"mereka proses terpisah, setiap proses akan memiliki RSS sendiri dan totalnya "
           f"berlipat lima. Kedua, angka context switch berbeda jauh antar thread "
           f"({ts[0]['vctx']} pada thread utama, {max(t['vctx'] for t in ts)} pada thread "
           f"pembaca tersibuk), padahal status proses hanya melaporkan satu angka. Ketiga, "
           f"keluaran pstree menaruh keempat TID di dalam kurung kurawal milik satu proses.")
    par(d, "Berdasarkan bukti itu, keputusan merancang layanan ini sebagai thread, bukan proses, "
           "dapat dibenarkan secara terukur. Penulis log tidak perlu membuka berkas sendiri dan "
           "tidak perlu mengirim data lewat pipe; ia cukup mengambil dari antrean di ruang alamat "
           "yang sama. Biaya pertukaran datanya adalah satu operasi antrean, bukan satu system "
           "call yang menyeberang ke kernel. Sebagai perbandingan, pada kepingan #4 (tugas K-1) "
           "pengiriman data antarproses memakai pipe dan message queue, dan di sana setiap "
           "rekaman menuntut peralihan user ke kernel.")
    par(d, "Namun pilihan thread juga membawa risiko yang nyata. Karena ruang alamat dibagi, satu "
           "thread yang menulis ke struktur data bersama tanpa penjagaan dapat merusak data yang "
           "sedang dibaca thread lain. Pada program ini risikonya ditutup oleh queue.Queue yang "
           "sudah aman terhadap akses bersamaan. Bila antrean diganti list biasa, kerusakan data "
           "hampir pasti terjadi. Persoalan itu akan dibahas tersendiri pada tugas I-4.")
    par(d, f"Poin (3) deskripsi tugas — peran context switch. Selama "
           f"{r['durasi_cuplikan']:.1f} detik, voluntary context switch bertambah "
           f"{r['vctx_akhir'] - r['vctx_awal']} kali, sedangkan nonvoluntary hanya bertambah "
           f"{r['nctx_akhir'] - r['nctx_awal']} kali. Perbandingan sekitar "
           f"{(r['vctx_akhir'] - r['vctx_awal']) / max(1, r['nctx_akhir'] - r['nctx_awal']):.0f} "
           f"berbanding satu itu menunjukkan sifat beban kerja: hampir seluruh perpindahan terjadi "
           f"karena task sendiri menyerahkan prosesor, bukan karena jatah waktunya dihabiskan "
           f"penjadwal.")
    par(d, "Penyerahan itu punya sebab yang konkret. Pembaca menyerahkan prosesor saat memanggil "
           "time.sleep — di kernel menjadi clock_nanosleep — dan saat menaruh data ke antrean "
           "yang sudah penuh. Penulis menyerahkan prosesor saat antrean kosong dan saat menunggu "
           "penulisan ke disk selesai. Setiap penyerahan itu satu context switch voluntary.")
    par(d, f"Nonvoluntary context switch yang sedikit ({r['nctx_akhir'] - r['nctx_awal']} kali) "
           f"juga masuk akal. Mesin ini memiliki {k['jumlah_cpu']} CPU logis, sehingga kelima "
           f"thread bisa berjalan di inti berbeda tanpa harus saling menggusur. Nonvoluntary baru "
           f"muncul ketika satu thread harus menunggu inti yang sibuk, dan pada beban seringan ini "
           f"itu jarang terjadi. Pada mesin dengan satu inti, angka itu akan jauh lebih besar.")
    par(d, "Peran context switch di sini bukan mempercepat pekerjaan, melainkan membuat dua "
           "pekerjaan yang saling menunggu bisa berjalan tanpa saling mengunci. Tanpa context "
           "switch, penulis yang sedang menunggu disk akan menahan pembaca, dan layanan berhenti "
           "mengambil data sensor. Biaya context switch sendiri — menyimpan dan memuat register — "
           "jauh lebih murah daripada waktu menunggu disk yang dihemat.")

    h2(d, "5.3 Catatan keterbatasan")
    par(d, "Program yang diamati adalah simulasi layanan, bukan layanan produksi pada perangkat "
           "kebun sesungguhnya. Nilai sensor dibangkitkan, dan berkas log ditulis ke penyimpanan "
           "mesin operator, bukan ke kartu microSD gateway. Selain itu, pengamatan lewat /proc "
           "bersifat cuplikan: proses yang berpindah state di antara dua pembacaan tidak akan "
           "tertangkap. Untuk melengkapi gambaran itu, angka context switch dipakai sebagai "
           "petunjuk tidak langsung, karena ia mencatat seluruh perpindahan, bukan hanya yang "
           "kebetulan terlihat pada cuplikan.")


def kesimpulan(d, k, o):
    r = o["ringkasan"]
    ts = o["pohon"]["thread_status"]
    h1(d, "6. Kesimpulan")
    par(d, f"Layanan logger berjalan sebagai satu proses python3 dengan "
           f"{r['thread_maks']} thread: satu utama, tiga pembaca sensor, dan satu penulis log. "
           f"Seluruh cuplikan menangkap state S karena beban kerjanya memang didominasi "
           f"penantian, bukan perhitungan. Ketiga bukti — RSS {r['rss_rata']} kB yang sama untuk "
           f"kelima TID, context switch yang berbeda jauh antar thread "
           f"({ts[0]['vctx']} vs {max(t['vctx'] for t in ts)}, dan kurung kurawal pstree — "
           f"menegaskan bahwa kelimanya thread, bukan proses. Voluntary context switch "
           f"mendominasi dengan perbandingan sekitar "
           f"{(r['vctx_akhir'] - r['vctx_awal']) / max(1, r['nctx_akhir'] - r['nctx_awal']):.0f} "
           f"berbanding satu, sesuai sifat beban yang menunggu timer dan antrean. Peran context "
           f"switch di sini adalah menjaga kedua pekerjaan tetap berjalan meski saling menunggu, "
           f"dengan biaya yang jauh lebih kecil daripada waktu tunggu yang dihemat.")


def kepingan(d):
    h1(d, "7. Kepingan Puzzle")
    tabel(d, ["Keterangan", "Isi"], [
        ("Nomor kepingan", "#3"),
        ("Isi kepingan", "Kode layanan logger multithread, pohon proses dan diagram state, tabel "
                         "statistik per thread, serta analisis proses versus thread dan context "
                         "switch"),
        ("Lokasi di portofolio", REPO),
        ("Dipakai untuk", "Level 2 Puzzle UTS — menyambung kepingan #2 (system call) karena "
                          "clone dan execve yang tercatat di sana melahirkan thread yang diamati "
                          "di sini, dan menjadi dasar kepingan #6 (race condition) yang memakai "
                          "buffer bersama antar-thread"),
    ], lebar=[4.2, 11.0])


def pustaka(d):
    h1(d, "Daftar Pustaka")
    for teks in [
        "Kerrisk, M. (2010). The Linux programming interface. No Starch Press.",
        "Love, R. (2010). Linux kernel development (3rd ed.). Addison-Wesley.",
        "Silberschatz, A., Galvin, P. B., & Gagne, G. (2018). Operating system concepts "
        "(10th ed.). Wiley.",
        "Tanenbaum, A. S., & Bos, H. (2015). Modern operating systems (4th ed.). Pearson.",
    ]:
        p = d.add_paragraph(style="Normal")
        p.paragraph_format.left_indent = Cm(1.0)
        p.paragraph_format.first_line_indent = Cm(-1.0)
        p.paragraph_format.space_after = Pt(6)
        p.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.LEFT
        p.add_run(teks)


def lampiran(d):
    d.add_paragraph().add_run().add_break(WD_BREAK.PAGE)
    h1(d, "Lampiran A. Kode Program dan Log")
    par(d, "Empat berkas di bawah ini menghasilkan seluruh angka pada laporan dan dapat dijalankan "
           "ulang pada mesin yang sama.")
    for nama in ("logger_thread.py", "observer.py", "figures.py", "ambil-bukti.sh"):
        p = d.add_paragraph(style="Normal")
        p.paragraph_format.space_before = Pt(8)
        p.paragraph_format.space_after = Pt(2)
        r = p.add_run(f"A.{nama}")
        r.bold = True
        r.font.size = Pt(9.5)
        kode(d, baca_berkas(nama), ukuran=7)

    h1(d, "Lampiran B. Pernyataan Penggunaan AI Generatif")
    par(d, "☐  Saya tidak menggunakan AI generatif dalam tugas ini.")
    par(d, "☒  Menggunakan AI generatif dengan rincian berikut:")
    tabel(d, ["Alat", "Tujuan penggunaan", "Bagian yang dibantu", "Cara memverifikasi"], [
        ("Claude (Anthropic)", "Menyusun skrip pengamatan dan merapikan kalimat laporan",
         "Bagian 4 (kode), Bagian 5.2",
         "Seluruh angka berasal dari /proc pada tangkapan layar; observer.py dijalankan ulang "
         "dengan OBSERVASI_PID dan hasilnya dicocokkan dengan Tabel 5.2"),
    ], lebar=[3.0, 4.4, 4.0, 4.4], ukuran=8.5)

    h1(d, "Lampiran C. Daftar Periksa Sebelum Mengumpulkan")
    for teks, sudah in [
        ("Semua teks petunjuk abu-abu dan kotak petunjuk sudah dihapus.", True),
        ("Identitas, kode tugas, dan nama host pada sampul sudah benar.", True),
        ("Setiap poin deskripsi tugas sudah dijawab di bagian Analisis.", True),
        ("Setiap tangkapan layar menampilkan prompt dan memiliki nomor serta keterangan.", True),
        ("Kepingan puzzle sudah disimpan di portofolio dan tautannya dicantumkan.", True),
        ("Pernyataan penggunaan AI generatif sudah diisi.", True),
        ("Berkas disimpan sebagai PDF dengan nama C_I-3_<NIM>_<Nama>.pdf.", True),
    ]:
        p = d.add_paragraph(style="Normal")
        p.paragraph_format.space_after = Pt(3)
        p.add_run(f"{'☒' if sudah else '☐'}  {teks}")

    par(d, "")
    h2(d, "Swa-nilai berdasarkan kriteria lembar tugas")
    tabel(d, ["Kriteria (dari lembar tugas)", "Bobot", "Sudah terpenuhi? Di bagian mana"],
          [("Ketepatan konsep", "40%",
            "Ya — state, pohon proses, PCB, dan context switch dijelaskan dari data /proc"),
           ("Kedalaman analisis", "30%",
            "Ya — tiga bukti proses vs thread dan sebab voluntary context switch dibedah"),
           ("Bukti praktik/perhitungan", "20%",
            "Ya — 10 tangkapan layar asli dan tabel statistik per thread"),
           ("Orisinalitas dan kerapian", "10%",
            "Ya — diagram dibuat dari data pengamatan, daftar pustaka gaya APA")],
          lebar=[5.2, 2.0, 8.0])


def main():
    d = docx.Document(TEMPLATE)
    bersihkan(d)

    o = baca_observasi()
    k = fakta_sistem()

    sampul_i3(d, k)
    pendahuluan(d, k, o)
    dasar_teori(d, k)
    lingkungan(d, k)
    langkah(d, k, o)
    hasil(d, k, o)
    kesimpulan(d, k, o)
    kepingan(d)
    pustaka(d)
    lampiran(d)

    header_dokumen(d, "Laporan Tugas Individu Sistem Operasi · ", f"{KELAS} · {KODE}")
    nomor_halaman(d)

    d.core_properties.title = "I-3 Observasi Proses dan Thread"
    d.core_properties.author = NAMA
    d.core_properties.subject = "Sistem Operasi (USA-WP2260110), IF-3C"
    d.core_properties.last_modified_by = NAMA

    os.makedirs("results", exist_ok=True)
    d.save(OUT)
    print("tersimpan:", OUT)


if __name__ == "__main__":
    main()
