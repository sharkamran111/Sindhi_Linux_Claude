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
  --bootappend-live "boot=live components quiet splash username=sindhi user-fullname=Sindhi hostname=sindhi-linux keyboard-layouts=us"

# Boot menu branding: start from live-build's own templates, then swap in
# the Sindhi Linux background and names.
mkdir -p config/bootloaders
for dir in /usr/share/live/build/bootloaders/*; do
  name=$(basename "$dir")
  [ -d "config/bootloaders/$name" ] || cp -r "$dir" "config/bootloaders/$name"
done
find config/bootloaders -name 'splash.svg*' -exec cp branding/bootmenu.svg {} \;
find config/bootloaders -name 'splash.png' -exec cp branding/bootmenu.png {} \;
grep -rlI 'Live system' config/bootloaders | xargs -r sed -i 's/Live system/Sindhi Linux/g'

lb build

ls -lh ./*.iso
