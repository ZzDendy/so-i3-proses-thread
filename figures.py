"""Diagram untuk laporan I-3: pohon proses, diagram state, dan context switch."""
import json
import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

FONT = "DejaVu Sans"
OUT = "results"


def kotak(ax, x, y, w, h, judul, isi="", warna="#E8EEF7", tepi="#3B5B8C",
          ukuran=8.0, tebal_judul=8.6):
    ax.add_patch(FancyBboxPatch((x, y), w, h,
                                boxstyle="round,pad=0.02,rounding_size=0.06",
                                facecolor=warna, edgecolor=tepi, linewidth=1.2))
    ax.text(x + w / 2, y + h - 0.14, judul, ha="center", va="top",
            fontsize=tebal_judul, fontfamily=FONT, fontweight="bold", color=tepi)
    if isi:
        ax.text(x + w / 2, y + h - 0.40, isi, ha="center", va="top", fontsize=ukuran,
                fontfamily=FONT, linespacing=1.5, color="#222222")


def panah(ax, x1, y1, x2, y2, warna="#555555", putus=False, gaya="-|>"):
    ax.add_patch(FancyArrowPatch((x1, y1), (x2, y2), arrowstyle=gaya,
                                 mutation_scale=11, color=warna, linewidth=1.1,
                                 linestyle="--" if putus else "-"))


def pohon(d, path):
    p = d["pohon"]
    r = d["ringkasan"]
    fig, ax = plt.subplots(figsize=(8.6, 3.9))
    ax.set_xlim(0, 8.6)
    ax.set_ylim(0, 3.9)
    ax.axis("off")

    kotak(ax, 0.35, 2.55, 2.5, 0.95, "Shell / terminal",
          "bash (induk dari pengamat)", "#F4F4F4", "#6B6B6B")

    kotak(ax, 0.35, 1.15, 2.5, 0.95, f"observer.py (PID {p['ppid']})",
          "proses pengamat\nmembaca /proc", "#EDE7F6", "#5B3B8C")

    kotak(ax, 3.3, 1.15, 2.55, 1.35, f"logger (PID {p['pid']})",
          f"python3 logger_thread.py\nThreads: {r['thread_maks']}\n"
          f"RSS: {r['rss_rata']} kB",
          "#E8EEF7", "#3B5B8C", 7.6, 8.4)

    nama_thread = ["TID utama", "pembaca-tanah", "pembaca-suhu", "pembaca-pompa",
                   "penulis"]
    warna_thread = ["#DDE6F4", "#DCEFE2", "#DCEFE2", "#DCEFE2", "#FDF2E0"]
    tepi_thread = ["#3B5B8C", "#2F6B3C", "#2F6B3C", "#2F6B3C", "#B7791F"]
    ts = p.get("thread_status", [])
    for i, (label, w, t) in enumerate(zip(nama_thread, warna_thread, tepi_thread)):
        y = 3.30 - i * 0.55
        tid = ts[i]["tid"] if i < len(ts) else "?"
        ax.add_patch(FancyBboxPatch((6.15, y), 2.2, 0.46,
                                    boxstyle="round,pad=0.02,rounding_size=0.06",
                                    facecolor=w, edgecolor=t, linewidth=1.2))
        ax.text(6.35, y + 0.23, label, ha="left", va="center", fontsize=7.6,
                fontfamily=FONT, fontweight="bold", color=t)
        ax.text(8.15, y + 0.23, f"TID {tid}", ha="right", va="center", fontsize=6.8,
                fontfamily=FONT, color="#555555")

    panah(ax, 1.6, 2.55, 1.6, 2.10)
    panah(ax, 2.85, 1.62, 3.30, 1.62)
    ax.text(3.07, 1.72, "parent", ha="center", fontsize=6.6, fontfamily=FONT,
            color="#555555", style="italic")

    ax.text(6.15, 1.02, "Lima TID berbagi satu ruang alamat, satu VmRSS,\n"
                        "dan satu berkas log — bukti bahwa ini thread, bukan proses.",
            ha="left", va="top", fontsize=7.2, fontfamily=FONT, color="#555555",
            style="italic", linespacing=1.5)

    ax.set_title("Pohon proses dan thread pada layanan logger sensor",
                 fontsize=10.5, fontfamily=FONT, fontweight="bold", pad=4)
    fig.tight_layout()
    fig.savefig(path, dpi=220, facecolor="white", bbox_inches="tight")
    plt.close(fig)


def state(d, path):
    r = d["ringkasan"]
    fig, ax = plt.subplots(figsize=(8.2, 3.5))
    ax.set_xlim(0, 8.2)
    ax.set_ylim(0, 3.5)
    ax.axis("off")

    kotak(ax, 0.4, 1.65, 1.75, 0.95, "NEW", "dibuat fork()", "#F4F4F4", "#6B6B6B")
    kotak(ax, 2.65, 1.65, 1.75, 0.95, "READY", "menunggu giliran CPU",
          "#E8EEF7", "#3B5B8C")
    kotak(ax, 4.9, 1.65, 1.75, 0.95, "RUNNING", "memakai CPU",
          "#DCEFE2", "#2F6B3C")
    kotak(ax, 4.9, 0.25, 1.75, 0.95, "WAITING", "menunggu I/O atau sleep",
          "#FDF2E0", "#B7791F")
    kotak(ax, 2.65, 0.25, 1.75, 0.95, "TERMINATED", "selesai exit()",
          "#F4F4F4", "#6B6B6B")

    panah(ax, 2.15, 2.12, 2.65, 2.12)
    panah(ax, 4.40, 2.12, 4.90, 2.12)
    ax.text(4.65, 2.22, "dispatch", ha="center", fontsize=6.6, fontfamily=FONT,
            color="#555555")
    panah(ax, 4.90, 1.98, 4.40, 1.98, putus=True)
    ax.text(4.65, 1.62, "jatah habis", ha="center", fontsize=6.6, fontfamily=FONT,
            color="#A03B2C")
    panah(ax, 5.75, 1.65, 5.75, 1.20)
    ax.text(5.85, 1.42, "sleep / I/O", ha="left", fontsize=6.6, fontfamily=FONT,
            color="#B7791F")
    panah(ax, 4.90, 0.72, 4.40, 1.65, putus=True)
    ax.text(4.05, 1.05, "data siap", ha="center", fontsize=6.6, fontfamily=FONT,
            color="#2F6B3C")
    panah(ax, 3.52, 1.65, 3.52, 1.20)
    ax.text(3.62, 1.42, "exit", ha="left", fontsize=6.6, fontfamily=FONT,
            color="#555555")

    ax.text(0.4, 2.95, f"Pada pengamatan: {r['jumlah_cuplikan']} cuplikan, seluruhnya "
                       "berada di state S (sleeping) — menunggu di antrean, "
                       "timer, atau I/O.",
            fontsize=7.4, fontfamily=FONT, color="#555555", style="italic")

    ax.set_title("Diagram state proses dan perpindahannya",
                 fontsize=10.5, fontfamily=FONT, fontweight="bold", pad=4)
    fig.tight_layout()
    fig.savefig(path, dpi=220, facecolor="white", bbox_inches="tight")
    plt.close(fig)


def context_switch(d, path):
    c = d["cuplikan"]
    fig, ax = plt.subplots(figsize=(7.2, 3.0))
    t = [x["t"] for x in c]
    v = [x["vctx"] for x in c]
    n = [x["nctx"] for x in c]
    ax.plot(t, v, marker="o", markersize=3.6, linewidth=1.6, color="#3B5B8C",
            label="voluntary")
    ax.plot(t, n, marker="s", markersize=3.4, linewidth=1.4, color="#B7791F",
            label="nonvoluntary")
    ax.set_xlabel("Waktu pengamatan (detik)", fontfamily=FONT, fontsize=8.5)
    ax.set_ylabel("Context switch kumulatif", fontfamily=FONT, fontsize=8.5)
    ax.tick_params(labelsize=7.5)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.grid(color="#DDDDDD", linewidth=0.6)
    ax.set_axisbelow(True)
    ax.legend(frameon=False, fontsize=8)
    ax.set_title("Context switch kumulatif selama pengamatan",
                 fontsize=10, fontfamily=FONT, fontweight="bold")
    fig.tight_layout()
    fig.savefig(path, dpi=220, facecolor="white")
    plt.close(fig)


def main():
    os.makedirs(OUT, exist_ok=True)
    with open("results/observasi.json", encoding="utf-8") as f:
        d = json.load(f)
    pohon(d, f"{OUT}/gambar-pohon.png")
    state(d, f"{OUT}/gambar-state.png")
    context_switch(d, f"{OUT}/gambar-ctxswitch.png")
    print("gambar:", [f for f in sorted(os.listdir(OUT)) if f.endswith(".png")])


if __name__ == "__main__":
    main()
