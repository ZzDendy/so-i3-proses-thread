"""Layanan pembaca sensor dan logger multithread, subjek observasi I-3.

Dua jenis pekerjaan dijalankan bersamaan:
  - thread pembaca  : mengambil nilai sensor tiap interval
  - thread penulis  : menulis antrean ke berkas log

Antrean berukuran terbatas dipakai supaya perilaku thread terlihat, bukan
sekadar tidur bergantian.
"""
import argparse
import json
import os
import queue
import threading
import time

ANTREAN = queue.Queue(maxsize=8)
HENTI = threading.Event()
HITUNG = {"dibaca": 0, "ditulis": 0}


def pembaca_sensor(nama, jumlah, jeda):
    for i in range(jumlah):
        if HENTI.is_set():
            break
        data = {
            "sensor": nama,
            "seq": i,
            "nilai": round(40 + (i % 20) * 0.7, 2),
            "ts": time.time(),
        }
        ANTREAN.put(data)          # memblokir bila antrean penuh
        HITUNG["dibaca"] += 1
        time.sleep(jeda)
    ANTREAN.put(None)


def penulis_log(path, berhenti_setelah):
    with open(path, "w", encoding="utf-8") as f:
        selesai = 0
        while selesai < berhenti_setelah:
            data = ANTREAN.get()
            if data is None:
                ANTREAN.task_done()
                continue
            f.write(json.dumps(data) + "\n")
            f.flush()
            HITUNG["ditulis"] += 1
            selesai += 1
            ANTREAN.task_done()


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--jumlah", type=int, default=40)
    p.add_argument("--jeda", type=float, default=0.05)
    p.add_argument("--log", default="results/logger.log")
    a = p.parse_args()

    os.makedirs(os.path.dirname(a.log), exist_ok=True)

    nama_sensor = ["tanah", "suhu", "pompa"]
    per_sensor = a.jumlah // len(nama_sensor)
    total = per_sensor * len(nama_sensor)

    # Penulis menunggu jumlah yang benar-benar dibaca, bukan jumlah yang diminta:
    # pembagian per sensor dibulatkan ke bawah.
    tulis = threading.Thread(target=penulis_log, args=(a.log, total), name="penulis")
    tulis.start()

    baca = []
    for n in nama_sensor:
        t = threading.Thread(target=pembaca_sensor,
                             args=(n, per_sensor, a.jeda),
                             name=f"pembaca-{n}")
        t.start()
        baca.append(t)

    for t in baca:
        t.join()
    tulis.join()

    print(f"thread pembaca : {len(baca)} ({', '.join(t.name for t in baca)})")
    print(f"thread penulis : 1 ({tulis.name})")
    print(f"rekaman        : dibaca {HITUNG['dibaca']}, ditulis {HITUNG['ditulis']}")
    print(f"berkas log     : {a.log}")


if __name__ == "__main__":
    main()
