#!/usr/bin/env zsh
set -euo pipefail
umask 022


SRC="/mnt/c/users/jacob/code/hella-webtilian/media/variants"
OUT="$SRC/opt_webp"
LOG="/tmp/variants_opt.log"

mkdir -p "$OUT"
: > "$LOG"

export MAGICK_THREAD_LIMIT=1

sizes=(256x256 512x512 786x768)

for f in "$SRC"/*.(jpg|jpeg|png|JPG|JPEG|PNG)(N); do
  base="${f:t}"
  name="${base:r}"
  echo "Processing: $base" | tee -a "$LOG"

  for size in $sizes; do
    out="$OUT/${name}-${size}.webp"
    if ! convert -limit memory 512MiB -limit map 512MiB -limit disk 2GiB \
        "$f" -strip -resize "$size" -quality 82 -define webp:method=6 "$out" >>"$LOG" 2>&1; then
      echo "FAILED: $base -> $size" | tee -a "$LOG"
      break
    fi
  done
done

echo "Done. Output: $OUT"
echo "Log: $LOG"
