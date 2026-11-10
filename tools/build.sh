#!/bin/sh
# Build the SindhOS ISO on this PC (after tools/setup-build-host.sh).
# The ISO and build log land in out/.
#
#   tools/build.sh            test build (fast zstd compression)
#   tools/build.sh --release  release build (xz, smaller ISO, slower)
#   tools/build.sh --clean    remove earlier build leftovers, keep downloads
set -e
CMD=/usr/local/sbin/sindhos-build
[ -x "$CMD" ] || { echo "Run once first: sudo tools/setup-build-host.sh" >&2; exit 1; }
if sudo -n -l "$CMD" >/dev/null 2>&1; then
  exec sudo -n "$CMD" "$@"      # password-free rule installed
fi
exec sudo "$CMD" "$@"           # asks for your password
