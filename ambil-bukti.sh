#!/usr/bin/env bash
# Bukti terminal asli untuk laporan I-3: observasi proses dan thread.
# Logger dijalankan di latar jendela yang sama, lalu observer mengamati PID-nya
# lewat OBSERVASI_PID. Dengan begitu angka di laporan berasal dari proses yang
# benar-benar terlihat pada tangkapan layar.
set -u

DIR=${1:?butuh folder kerja}
OUT=${2:?butuh folder keluaran}
FIFO=/tmp/shotest/i3.fifo
mkdir -p "$OUT"
rm -f "$FIFO"; mkfifo "$FIFO"

cd "$DIR" || exit 1

io.elementary.terminal -n -w "$DIR" -x "bash --noprofile --rcfile $HOME/.bashrc -i < $FIFO" \
  > /dev/null 2>&1 &
TERM_PID=$!
sleep 4

exec 3>"$FIFO"

tangkap() {
  sleep 0.9
  gdbus call --session --dest org.gnome.Shell.Screenshot \
    --object-path /org/gnome/Shell/Screenshot \
    --method org.gnome.Shell.Screenshot.ScreenshotWindow \
    true false false "$OUT/ss-$1.png" > /dev/null 2>&1
  echo "  -> ss-$1.png"
}

ketik() { printf '%s\n' "$1" >&3; }

ketik 'clear'
sleep 1
tangkap "01-prompt"

ketik 'head -12 logger_thread.py'
tangkap "02-program"

ketik 'python3 logger_thread.py --jumlah 1500 --jeda 0.05 --log results/logger.log &'
sleep 1.5
tangkap "03-jalankan"

ketik 'PID=$(pgrep -n -f logger_thread); echo "PID logger: $PID"'
tangkap "04-pid"

ketik 'ps -eo pid,ppid,nlwp,stat,comm --sort=pid | tail -5'
tangkap "05-ps"

ketik 'grep -E "^(Name|State|Threads|voluntary|nonvoluntary)" /proc/$PID/status'
tangkap "06-status"

ketik 'for t in /proc/$PID/task/*; do echo "$(basename $t) $(grep -m1 ^State $t/status | cut -c8-20) $(grep -m1 voluntary_ctxt $t/status | cut -f2)"; done'
tangkap "07-per-thread"

ketik 'pstree -p $PID'
tangkap "08-pstree"

ketik 'OBSERVASI_PID=$PID python3 observer.py'
sleep 8
tangkap "09-observer"

ketik 'kill $PID 2>/dev/null; wait 2>/dev/null; echo selesai'
sleep 1
tangkap "10-selesai"

exec 3>&-
sleep 1
kill "$TERM_PID" 2>/dev/null
rm -f "$FIFO"
echo "selesai: $(ls -1 "$OUT"/ss-*.png | wc -l) tangkapan layar"
