#!/usr/bin/env zsh
# Posts hero: crop to 16:9 (no stretch) then export WebP (and try AVIF).

set -euo pipefail
umask 022


SRC="/mnt/c/users/jacob/code/hella-webtilian/media/posts/hero"
OUT="$SRC/opt"
LOG="/tmp/posts_hero_opt.log"

mkdir -p "$OUT"
: > "$LOG"

export MAGICK_THREAD_LIMIT=1

widths=(640 960 1280 1600)

# Detect whether convert supports AVIF output
AVIF_OK=0
if convert -list format 2>/dev/null | grep -qi '^ *AVIF'; then
  AVIF_OK=1
else
  echo "Note: AVIF not supported by this ImageMagick build; will output WebP only." | tee -a "$LOG"
fi

for f in "$SRC"/*.(jpg|jpeg|png|webp|JPG|JPEG|PNG|WEBP)(N); do
  base="${f:t}"
  name="${base:r}"
  echo "Processing: $base" | tee -a "$LOG"

  for w in $widths; do
    h=$(( w * 9 / 16 ))          # 16:9 height
    size="${w}x${h}"

    webp_out="$OUT/${name}-${w}w.webp"
    avif_out="$OUT/${name}-${w}w.avif"

    # Crop to exact 16:9 at the target size:
    #   -resize "${size}^" fills the box
    #   -extent crops overflow (center)
    if ! convert -limit memory 768MiB -limit map 768MiB -limit disk 3GiB \
        "$f" \
        -auto-orient \
        -strip \
        -resize "${size}^" \
        -gravity center \
        -extent "$size" \
        -quality 82 \
        -define webp:method=6 \
        "$webp_out" >>"$LOG" 2>&1; then
      echo "FAILED: $base -> WebP ${w}w" | tee -a "$LOG"
      break
    fi

    # Optional AVIF
    if (( AVIF_OK )); then
      # AVIF knobs vary by build; this is a pragmatic baseline.
      # If AVIF output looks too soft, bump quality to ~55-65.
      convert -limit memory 768MiB -limit map 768MiB -limit disk 3GiB \
        "$f" \
        -auto-orient \
        -strip \
        -resize "${size}^" \
        -gravity center \
        -extent "$size" \
        -quality 50 \
        "$avif_out" >>"$LOG" 2>&1 || {
          echo "WARN: AVIF failed for $base at ${w}w (continuing WebP-only)" | tee -a "$LOG"
          AVIF_OK=0
        }
    fi
  done
done

echo "Done. Output: $OUT"
echo "Log: $LOG"
