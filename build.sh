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
rm -f ./*.iso    # also images built under an older name

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
  --image-name sindhos \
  --iso-application "SindhOS" \
  --iso-publisher "SindhOS project" \
  --iso-volume "SINDHOS" \
  --security true \
  --updates true \
  --debootstrap-options "--include=eatmydata" \
  $SQUASHFS \
  --bootappend-live "boot=live components quiet splash username=sindhi user-fullname=Sindhi hostname=sindhos keyboard-layouts=us timezone=Asia/Karachi"

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

# ---- SindhOS look: themes, icons and artwork assembled into the image ----
# Everything below is generated from branding/ and third_party/ (and
# git-ignored), so the sources stay the single source of truth.
INC=config/includes.chroot
command -v rsvg-convert >/dev/null || { echo "rsvg-convert missing (apt install librsvg2-bin fonts-sil-lateef fonts-dejavu-core)" >&2; exit 1; }
svg() { rsvg-convert -w "$2" -h "$3" -o "$4" "$1"; }

# Themes: adw-gtk3 base (LGPL) + SindhOS layers with their window decorations
rm -rf "$INC/usr/share/themes"
mkdir -p "$INC/usr/share/themes"
tar -xJf third_party/adw-gtk3/adw-gtk3v*.tar.xz -C "$INC/usr/share/themes"
cp -r branding/theme/SindhOS-Light branding/theme/SindhOS-Dark "$INC/usr/share/themes/"

# Icons: SindhOS logo (ajrak emblem) and the topi for the menu button
ICONS="$INC/usr/share/icons/hicolor/scalable/apps"
rm -rf "$INC/usr/share/icons"
mkdir -p "$ICONS"
cp branding/logo.svg "$ICONS/sindhos.svg"
cp branding/topi/topi-small.svg "$ICONS/sindhos-menu.svg"
cp branding/topi/topi.svg "$ICONS/sindhos-topi.svg"

# SindhOS keyboards (keyboard/roman): Roman Sindhi + Sindhi key by key, one
# IBus engine process; word list and IBus component.
# The lookup index is built inside the image by hook 9000-sindhos.
ROMAN_LIB="$INC/usr/lib/sindhos/roman"
ROMAN_SHARE="$INC/usr/share/sindhos/roman"
rm -rf "$ROMAN_LIB" "$ROMAN_SHARE"
mkdir -p "$ROMAN_LIB" "$ROMAN_SHARE" "$INC/usr/share/ibus/component"
cp keyboard/roman/rules.py keyboard/roman/translit.py keyboard/roman/composer.py \
   keyboard/roman/engine.py keyboard/roman/ibus-engine-sindhos-roman keyboard/layout.py "$ROMAN_LIB/"
cp keyboard/roman/data/sd-words.tsv keyboard/roman/roman-icon.svg keyboard/roman/sindhi-icon.svg "$ROMAN_SHARE/"
cp keyboard/roman/sindhos-roman.xml "$INC/usr/share/ibus/component/"

# Artwork rendered from SVG: wallpaper (desktop + login), boot splash, installer
mkdir -p "$INC/usr/share/backgrounds/sindhos"
svg branding/wallpaper.svg 1920 1080 "$INC/usr/share/backgrounds/sindhos/wallpaper.png"
svg branding/splash.svg 1920 1080 "$INC/usr/share/plymouth/themes/sindhos/splash.png"
CAL="$INC/etc/calamares/branding/sindhos"
svg branding/logo.svg 256 256 "$CAL/logo.png"
svg branding/logo.svg 300 300 "$CAL/welcome.png"
svg branding/splash.svg 640 360 "$CAL/slide1.png"

# Boot menu: start from live-build's own templates, then swap in the
# SindhOS background and name.
rm -rf config/bootloaders
mkdir -p config/bootloaders
cp -r /usr/share/live/build/bootloaders/* config/bootloaders/
BOOTMENU=$(mktemp --suffix=.png)
svg branding/bootmenu.svg 640 480 "$BOOTMENU"
find config/bootloaders -name 'splash.svg*' -exec cp branding/bootmenu.svg {} \;
find config/bootloaders -name 'splash.png' -exec cp "$BOOTMENU" {} \;
rm -f "$BOOTMENU"
grep -rlI 'Live system' config/bootloaders | xargs -r sed -i 's/Live system/SindhOS/g'

# eatmydata for the build tools on this side too (debootstrap, apt, mksquashfs)
if command -v eatmydata >/dev/null 2>&1; then
  eatmydata lb build
else
  echo "Note: eatmydata not installed on the build host, building without it"
  lb build
fi

ls -lh ./*.iso
