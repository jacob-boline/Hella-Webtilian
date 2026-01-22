#!/usr/bin/env zsh
# Variants: center-crop to 1:1 then export WebP thumbs at widths (naming: -<w>w.webp)

set -euo pipefail
umask 022

SRC="/mnt/c/users/jacob/code/hella-webtilian/media/variants"
OUT="$SRC/opt_webp"
LOG="/tmp/variants_opt.log"

mkdir -p "$OUT"
: > "$LOG"

export MAGICK_THREAD_LIMIT=1

widths=(256 512 768)

for f in "$SRC"/*.(jpg|jpeg|png|webp|JPG|JPEG|PNG|WEBP)(N); do
  base="${f:t}"
  name="${base:r}"
  echo "Processing: $base" | tee -a "$LOG"

  for w in $widths; do
    size="${w}x${w}"
    out="$OUT/${name}-${w}w.webp"

    if [[ -f "$out" && "$out" -nt "$f" ]]; then
      echo "  skip (up-to-date): ${name}-${w}w" | tee -a "$LOG"
      continue
    fi

    if ! convert -limit memory 512MiB -limit map 512MiB -limit disk 2GiB \
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
