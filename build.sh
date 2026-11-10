#!/bin/sh
# Build the SindhOS live ISO with Debian's live-build.
# Run as root on Debian 13 (trixie):
#
#   sudo ./build.sh            # test build: fast zstd compression
#   sudo ./build.sh --release  # release build: smaller xz compression
#
# Local files in cache/ (git-ignored) are used instead of downloads:
#   broadcom-wl-6.30.163.46.tar.bz2   firmware for firmware-b43-installer
#   wl_apsta-3.130.20.0.o             firmware for firmware-b43legacy-installer
set -e

cd "$(dirname "$0")"

RELEASE=no
case "${1:-}" in
  --release) RELEASE=yes ;;
  "") ;;
  *) echo "usage: $0 [--release]" >&2; exit 2 ;;
esac

# Keep the downloaded package cache between local builds (much faster).
lb clean >/dev/null 2>&1 || true

# The cached base system must contain eatmydata (see below); an older cache
# without it is thrown away and rebuilt from the cached .deb files.
if [ -d cache/bootstrap ] && [ ! -e cache/bootstrap/usr/bin/eatmydata ]; then
  echo "Old bootstrap cache without eatmydata, rebuilding it"
  rm -rf cache/bootstrap
fi

# Squashfs: zstd level 3 packs fast for test builds; xz is ~10% smaller
# but much slower, so only for releases.
if [ "$RELEASE" = yes ]; then
  SQUASHFS="--chroot-squashfs-compression-type xz"
else
  SQUASHFS="--chroot-squashfs-compression-type zstd --chroot-squashfs-compression-level 3"
fi

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
  --debootstrap-options "--include=eatmydata" \
  $SQUASHFS \
  --bootappend-live "boot=live components quiet splash username=sindhi user-fullname=Sindhi hostname=sindhi-linux keyboard-layouts=us"

# eatmydata inside the image chroot: dpkg/apt skip fsync, which is the slow
# part on a hard disk. Only affects the build, not the installed system.
echo "LD_PRELOAD=libeatmydata.so.1" > config/environment.chroot

# Broadcom firmware from local files instead of the internet (see the wget
# helper in config/includes.chroot_before_packages/usr/local/bin/).
FW=config/includes.chroot_before_packages/usr/local/share/sindhos/firmware
rm -rf "$FW"
mkdir -p "$FW"
for f in broadcom-wl-6.30.163.46.tar.bz2 wl_apsta-3.130.20.0.o; do
  if [ -f "cache/$f" ]; then
    cp "cache/$f" "$FW/"
  else
    echo "Note: cache/$f not found, the firmware installer will download it"
  fi
done

# Mac-style theme (WhiteSur, MIT) unpacked into the image
mkdir -p config/includes.chroot/usr/share/themes
for t in third_party/whitesur/WhiteSur-*.tar.xz; do
  tar -xJf "$t" -C config/includes.chroot/usr/share/themes
done

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

# eatmydata for the build tools on this side too (debootstrap, apt, mksquashfs)
if command -v eatmydata >/dev/null 2>&1; then
  eatmydata lb build
else
  echo "Note: eatmydata not installed on the build host, building without it"
  lb build
fi

ls -lh ./*.iso
