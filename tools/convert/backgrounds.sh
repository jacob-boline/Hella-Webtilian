#!/usr/bin/env zsh
# Backgrounds -> WebP (960w, 1920w), aspect preserved.

set -euo pipefail
umask 022

SRC="/mnt/c/users/jacob/code/hella-webtilian/media/backgrounds"
OUT="$SRC/bg_opt"
LOG="/tmp/backgrounds_opt.log"

mkdir -p "$OUT"
: > "$LOG"

export MAGICK_THREAD_LIMIT=1

# widths (aspect ratio preserved)
widths=(960 1920)

for f in "$SRC"/*.(jpg|jpeg|png|JPG|JPEG|PNG)(N); do
  base="${f:t}"     # filename
  name="${base:r}"  # stem

  echo "Processing: $base" | tee -a "$LOG"

  for w in $widths; do
    out="$OUT/${name}-${w}w.webp"

    # Skip if output exists and is newer than source
    if [[ -f "$out" && "$out" -nt "$f" ]]; then
      echo "  skip (up-to-date): ${name}-${w}w" | tee -a "$LOG"
      continue
    fi

    convert -limit memory 768MiB -limit map 768MiB -limit disk 3GiB \
      "$f" \
      -auto-orient \
      -strip \
      -resize "${w}x" \
      -quality 82 \
      -define webp:method=6 \
      "$out" >>"$LOG" 2>&1
  done
done

echo "Done. Output: $OUT"
echo "Log: $LOG"
