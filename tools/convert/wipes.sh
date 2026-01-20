#!/usr/bin/env zsh
# Crop to 6:1 (no stretch) then export WebP wipes at fixed sizes.

set -euo pipefail
umask 022


SRC="/mnt/c/users/jacob/code/hella-webtilian/media/wipes"
OUT="$SRC/opt_webp"
LOG="/tmp/wipes_opt.log"

mkdir -p "$OUT"
: > "$LOG"

export MAGICK_THREAD_LIMIT=1

# Target sizes (6:1)
sizes=( "960x160" "1440x240" "1920x320" "2560x426" )

for f in "$SRC"/*.(jpg|jpeg|png|webp|JPG|JPEG|PNG|WEBP)(N); do
  base="${f:t}"
  name="${base:r}"
  echo "Processing: $base" | tee -a "$LOG"

  for size in $sizes; do
    out="$OUT/${name}-${size}.webp"

    # Center-crop to 6:1, then resize exactly to $size (no distortion).
    # Explanation of the core trick:
    #   -resize "${size}^" : scale so the image fully covers the box (may exceed in one dimension)
    #   -gravity center -extent "$size" : crop the overflow to exact dimensions from the center
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
      echo "FAILED: $base -> $size" | tee -a "$LOG"
      break
    fi
  done
done

echo "Done. Output: $OUT"
echo "Log: $LOG"
