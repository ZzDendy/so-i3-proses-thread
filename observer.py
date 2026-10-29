"""Mengamati proses logger yang sedang berjalan lewat /proc.

Hasilnya dipakai untuk memetakan state, pohon proses, perbedaan proses dan
thread, serta context switch. Semua angka dibaca dari /proc, bukan dikarang.
"""
import json
import os
import subprocess
import sys
import time


def baca_status(pid):
    hasil = {}
    try:
        with open(f"/proc/{pid}/status", encoding="utf-8") as f:
            for baris in f:
                if ":" in baris:
                    k, v = baris.split(":", 1)
                    hasil[k.strip()] = v.strip()
    except FileNotFoundError:
        return None
    return hasil


def baca_cmdline(pid):
    try:
        with open(f"/proc/{pid}/cmdline", "rb") as f:
            return f.read().replace(b"\0", b" ").decode(errors="replace").strip()
    except FileNotFoundError:
        return ""


def task_dir(pid):
    try:
        return sorted(os.listdir(f"/proc/{pid}/task"), key=int)
    except FileNotFoundError:
        return []


def anak_dari(pid, semua):
    hasil = {}
    for p, isi in semua.items():
        ppid = isi["status"].get("PPid", "")
        hasil.setdefault(ppid, []).append(p)
    return hasil.get(str(pid), [])


def kebiasaan(cuplikan):
    """Hitung berapa kali tiap state muncul, untuk menyusun diagram state."""
    hitung = {}
    for c in cuplikan:
        kode = c.get("state", "?").split()[0] or "?"
        hitung[kode] = hitung.get(kode, 0) + 1
    return hitung


def status_thread(pid):
    """Ringkasan per thread: /proc/<pid>/task/<tid>/status memberi angka sendiri.

    /proc/<pid>/status hanya memperlihatkan thread utama, sedangkan beban kerja
    sebenarnya ada di thread pembaca dan penulis. Karena itu context switch
    dijumlahkan dari semua thread.
    """
    hasil = []
    for tid in task_dir(pid):
        st = baca_status_path(f"/proc/{pid}/task/{tid}/status")
        if st:
            hasil.append({
                "tid": tid,
                "nama": st.get("Name", "?"),
                "state": st.get("State", "?"),
                "vctx": int(st.get("voluntary_ctxt_switches", 0)),
                "nctx": int(st.get("nonvoluntary_ctxt_switches", 0)),
                "rss_kb": int(st.get("VmRSS", "0 kB").split()[0]),
            })
    return hasil


def baca_status_path(path):
    hasil = {}
    try:
        with open(path, encoding="utf-8") as f:
            for baris in f:
                if ":" in baris:
                    k, v = baris.split(":", 1)
                    hasil[k.strip()] = v.strip()
    except FileNotFoundError:
        return None
    return hasil


def main():
    jeda = float(sys.argv[1]) if len(sys.argv) > 1 else 0.4
    durasi = float(sys.argv[2]) if len(sys.argv) > 2 else 4.0
    pid_luar = os.environ.get("OBSERVASI_PID")

    if pid_luar:
        # Mengamati proses yang sudah berjalan di terminal lain.
        pid = int(pid_luar)
        proc = None
    else:
        proc = subprocess.Popen([sys.executable, "logger_thread.py", "--jumlah", "240",
                                 "--jeda", "0.05", "--log", "results/logger.log"],
                                stdout=subprocess.PIPE, text=True)
        pid = proc.pid
        time.sleep(0.3)

    cuplikan = []
    terakhir = None
    awal = time.time()
    while time.time() - awal < durasi and (proc is None or proc.poll() is None):
        st = baca_status(pid)
        if st is None:
            break
        # Pohon proses harus dibaca saat prosesnya masih hidup; setelah keluar,
        # /proc/<pid> hilang dan seluruh isinya lenyap.
        tugas = task_dir(pid)
        per_thread = status_thread(pid)
        ppid = st.get("PPid", "")
        induk = baca_status(ppid) if ppid else None
        terakhir = {
            "pid": pid,
            "ppid": ppid,
            "induk_comm": induk.get("Name", "?") if induk else "?",
            "induk_cmd": baca_cmdline(ppid) if ppid else "",
            "logger_comm": st.get("Name", "?"),
            "logger_cmd": baca_cmdline(pid),
            "thread": tugas,
            "thread_status": per_thread,
        }
        cuplikan.append({
            "t": round(time.time() - awal, 3),
            "state": st.get("State", "?"),
            "threads": int(st.get("Threads", 0)),
            "vctx": sum(t["vctx"] for t in per_thread),
            "nctx": sum(t["nctx"] for t in per_thread),
            "rss_kb": int(st.get("VmRSS", "0 kB").split()[0]),
            "task": len(tugas),
        })
        time.sleep(jeda)

    semua = subprocess.run(["ps", "-eo", "pid,ppid,stat,comm,args", "--no-headers"],
                           capture_output=True, text=True).stdout

    peta = {}
    for baris in semua.splitlines():
        bagian = baris.split(None, 4)
        if len(bagian) < 5:
            continue
        p, pp, stat, comm, args = bagian
        peta[p] = {"status": {"PPid": pp, "State": stat, "Name": comm},
                   "args": args}

    pohon = terakhir or {"pid": pid, "ppid": "", "induk_comm": "?",
                         "induk_cmd": "", "logger_comm": "?", "logger_cmd": "",
                         "thread": []}
    pohon["anak"] = anak_dari(pid, peta)

    if proc is None:
        keluar = ""
    else:
        if proc.poll() is None:
            proc.terminate()
        keluar = proc.communicate()[0]

    hasil = {
        "pid": pid,
        "cuplikan": cuplikan,
        "pohon": pohon,
        "state_histogram": kebiasaan(cuplikan),
        "ringkasan": {
            "jumlah_cuplikan": len(cuplikan),
            "thread_maks": max(c["threads"] for c in cuplikan) if cuplikan else 0,
            "vctx_awal": cuplikan[0]["vctx"] if cuplikan else 0,
            "vctx_akhir": cuplikan[-1]["vctx"] if cuplikan else 0,
            "nctx_awal": cuplikan[0]["nctx"] if cuplikan else 0,
            "nctx_akhir": cuplikan[-1]["nctx"] if cuplikan else 0,
            "rss_rata": sum(c["rss_kb"] for c in cuplikan) // max(1, len(cuplikan)),
            "pid_induk": pohon.get("ppid", "?"),
            "cmd_induk": pohon.get("induk_comm", "?"),
            "cmd_logger": pohon.get("logger_cmd", ""),
            "jumlah_thread_task": len(pohon.get("thread", [])),
            "durasi_cuplikan": cuplikan[-1]["t"] if cuplikan else 0,
        },
        "keluaran_program": keluar.strip().splitlines() if keluar else [],
    }

    os.makedirs("results", exist_ok=True)
    with open("results/observasi.json", "w", encoding="utf-8") as f:
        json.dump(hasil, f, indent=2)

    r = hasil["ringkasan"]
    print(f"PID logger        : {pid}")
    print(f"Induk (shell)     : {r['pid_induk']} ({r['cmd_induk']})")
    print(f"Cuplikan          : {r['jumlah_cuplikan']} kali")
    print(f"Thread maksimum   : {r['thread_maks']} (task di /proc: "
          f"{r['jumlah_thread_task']})")
    print(f"Context switch    : voluntary {r['vctx_awal']} -> {r['vctx_akhir']}, "
          f"nonvoluntary {r['nctx_awal']} -> {r['nctx_akhir']}")
    print(f"RSS rata-rata     : {r['rss_rata']} kB")
    print("State yang terlihat:", ", ".join(f"{k}={v}" for k, v in
                                          hasil["state_histogram"].items()))
    print("\ntersimpan: results/observasi.json")


if __name__ == "__main__":
    main()
