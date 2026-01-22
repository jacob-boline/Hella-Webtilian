#!/usr/bin/env zsh
# About images: center-crop to 3:2 (no stretch) then export WebP at multiple widths.

set -euo pipefail
umask 022

SRC="/mnt/c/users/jacob/code/hella-webtilian/media/hr_about"
OUT="$SRC/opt_webp"
LOG="/tmp/hr_about_opt.log"

mkdir -p "$OUT"
: > "$LOG"

export MAGICK_THREAD_LIMIT=1

# Target widths (3:2)
widths=(640 960 1280 1600 1920)

for f in "$SRC"/*.(jpg|jpeg|png|webp|JPG|JPEG|PNG|WEBP)(N); do
  base="${f:t}"
  name="${base:r}"
  echo "Processing: $base" | tee -a "$LOG"

  for w in $widths; do
    h=$(( w * 2 / 3 ))     # 3:2 height
    size="${w}x${h}"
    out="$OUT/${name}-${w}w.webp"

    # Skip if output exists and is newer than source
    if [[ -f "$out" && "$out" -nt "$f" ]]; then
      echo "  skip (up-to-date): ${name}-${w}w" | tee -a "$LOG"
      continue
    fi

    if ! convert -limit memory 768MiB -limit map 768MiB -limit disk 3GiB \
        "$f" \
        -auto-orient \
        -strip \
        -resize "${size}^" \
        -gravity center \
        -extent "$size" \
        -quality 82 \
        -define webp:method=6 \
        "$out" >>"$LOG" 2>&1; then
      echo "FAILED: $base -> ${w}w" | tee -a "$LOG"
      break
    fi
  done
done

echo "Done. Output: $OUT"
echo "Log: $LOG"
