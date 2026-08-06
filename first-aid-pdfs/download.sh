#!/usr/bin/env bash
# Download the offline first aid PDF library listed in sources.txt.
# Usage: ./download.sh [output-dir]   (default: ./downloads)
set -u

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
OUT_DIR="${1:-$SCRIPT_DIR/downloads}"
SOURCES="$SCRIPT_DIR/sources.txt"
UA="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36"

mkdir -p "$OUT_DIR"

ok=0; failed=0; skipped=0
failures=()

is_pdf() {
  # A real PDF starts with "%PDF" within its first bytes.
  head -c 1024 "$1" | grep -q "%PDF"
}

fetch() { # fetch <url> <dest>
  curl -fL --retry 3 --retry-delay 2 --connect-timeout 20 --max-time 600 \
       -A "$UA" -o "$2" "$1" 2>/dev/null
}

while IFS= read -r line; do
  case "$line" in ''|'#'*) continue ;; esac

  IFS='|' read -r -a parts <<< "$line"
  name="${parts[0]}"
  dest="$OUT_DIR/$name"

  if [ -s "$dest" ] && is_pdf "$dest"; then
    echo "SKIP  $name (already downloaded)"
    skipped=$((skipped + 1))
    continue
  fi

  got=""
  for url in "${parts[@]:1}"; do
    echo "GET   $name"
    echo "      $url"
    if fetch "$url" "$dest" && [ -s "$dest" ] && is_pdf "$dest"; then
      got="yes"
      break
    fi
    rm -f "$dest"
    echo "      ...failed, trying next mirror (if any)"
  done

  if [ -n "$got" ]; then
    size=$(du -h "$dest" | cut -f1)
    echo "OK    $name ($size)"
    ok=$((ok + 1))
  else
    echo "FAIL  $name"
    failed=$((failed + 1))
    failures+=("$name")
  fi
done < "$SOURCES"

echo
echo "Done: $ok downloaded, $skipped already present, $failed failed."
if [ "$failed" -gt 0 ]; then
  echo "Failed files (try the URLs in sources.txt in a browser):"
  for f in "${failures[@]}"; do echo "  - $f"; done
  exit 1
fi
echo "PDFs are in: $OUT_DIR"
