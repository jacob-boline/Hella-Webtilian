#!/usr/bin/env zsh
# Export hr_about images to WebP at multiple widths (keeps aspect ratio).

set -euo pipefail
umask 022


SRC="/mnt/c/users/jacob/code/hella-webtilian/media/hr_about"
OUT="$SRC/opt_webp"
LOG="/tmp/hr_about_opt.log"

mkdir -p "$OUT"
: > "$LOG"

export MAGICK_THREAD_LIMIT=1

# Target widths (aspect ratio preserved)
widths=(640 960 1280 1600 1920)

for f in "$SRC"/*.(jpg|jpeg|png|webp|JPG|JPEG|PNG|WEBP)(N); do
  base="${f:t}"
  name="${base:r}"
  echo "Processing: $base" | tee -a "$LOG"

  for w in $widths; do
    out="$OUT/${name}-${w}w.webp"

    if ! convert -limit memory 768MiB -limit map 768MiB -limit disk 3GiB \
        "$f" \
        -auto-orient \
        -strip \
        -resize "${w}x" \
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
