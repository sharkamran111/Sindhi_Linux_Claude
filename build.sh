#!/bin/sh
# Build the Sindhi Linux live ISO with Debian's live-build.
# Run as root on Debian 13 (trixie):  sudo ./build.sh
set -e

cd "$(dirname "$0")"

lb clean --purge >/dev/null 2>&1 || true

lb config \
  --distribution trixie \
  --archive-areas "main contrib non-free-firmware" \
  --debian-installer none \
  --binary-images iso-hybrid \
  --image-name sindhi-linux \
  --iso-application "Sindhi Linux" \
  --iso-publisher "Sindhi Linux project" \
  --iso-volume "SINDHI_LINUX" \
  --security true \
  --updates true \
  --bootappend-live "boot=live components quiet splash username=sindhi user-fullname=Sindhi hostname=sindhi-linux keyboard-layouts=us,pk keyboard-variants=,snd keyboard-options=grp:alt_shift_toggle"

lb build

ls -lh ./*.iso
