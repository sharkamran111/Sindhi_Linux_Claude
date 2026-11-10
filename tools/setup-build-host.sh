#!/bin/sh
# One-time setup of the SindhOS build environment on this PC.
#
#   sudo tools/setup-build-host.sh                  # build chroot only
#   sudo tools/setup-build-host.sh --passwordless   # + let your user run the
#                                                   #   build without a password
#
# What it does:
#   1. installs debootstrap and the Debian archive keyring on the host
#   2. creates a Debian 13 (trixie) build chroot in /srv/sindhos-build and
#      installs Debian's live-build and the ISO tools inside it
#   3. installs the build command /usr/local/sbin/sindhos-build (root-owned)
#   4. with --passwordless: adds /etc/sudoers.d/sindhos-build so your user can
#      run exactly that command with sudo and no password
#
# Safe to run again: existing pieces are reused or refreshed.
set -eu

ROOT=/srv/sindhos-build
SUITE=trixie
MIRROR=http://deb.debian.org/debian
KEYRING=/usr/share/keyrings/debian-archive-keyring.gpg
REPO=$(cd "$(dirname "$0")/.." && pwd)

PASSWORDLESS=no
[ "${1:-}" = "--passwordless" ] && PASSWORDLESS=yes

if [ "$(id -u)" != 0 ]; then
  echo "Run with sudo: sudo $0 $*" >&2
  exit 1
fi
BUILD_USER=${SUDO_USER:-}
if [ "$PASSWORDLESS" = yes ] && [ -z "$BUILD_USER" ]; then
  echo "--passwordless needs to be run through sudo from your own user." >&2
  exit 1
fi

echo "== 1/4 Host packages"
apt-get update -qq
DEBIAN_FRONTEND=noninteractive apt-get install -y -qq \
  debootstrap debian-archive-keyring rsync qemu-system-x86 qemu-utils ovmf

echo "== 2/4 Debian $SUITE build chroot in $ROOT"
if [ ! -x "$ROOT/usr/bin/apt-get" ]; then
  mkdir -p "$ROOT"
  debootstrap --keyring="$KEYRING" --variant=minbase "$SUITE" "$ROOT" "$MIRROR"
fi
cat > "$ROOT/etc/apt/sources.list" <<EOF
deb $MIRROR $SUITE main
deb $MIRROR $SUITE-updates main
deb http://security.debian.org/debian-security $SUITE-security main
EOF
cp -L /etc/resolv.conf "$ROOT/etc/resolv.conf"
mount -t proc proc "$ROOT/proc"
trap 'umount "$ROOT/proc" 2>/dev/null || true' EXIT
chroot "$ROOT" sh -c '
  set -e
  export DEBIAN_FRONTEND=noninteractive
  apt-get update -qq
  apt-get install -y -qq --no-install-recommends \
    live-build debootstrap squashfs-tools xorriso \
    grub-efi-amd64-bin grub-pc-bin mtools dosfstools \
    syslinux syslinux-common isolinux ca-certificates xz-utils \
    librsvg2-bin fonts-sil-lateef fonts-dejavu-core cpio
  apt-get clean
'
umount "$ROOT/proc"
trap - EXIT

echo "== 3/4 Build command /usr/local/sbin/sindhos-build"
# The repo path is fixed inside the installed copy, so the command takes no
# arguments and always builds this checkout.
sed "s|@REPO@|$REPO|; s|@ROOT@|$ROOT|" "$REPO/tools/sindhos-build.in" \
  > /usr/local/sbin/sindhos-build
chown root:root /usr/local/sbin/sindhos-build
chmod 0755 /usr/local/sbin/sindhos-build

echo "== 4/4 Password-free build"
SUDOERS=/etc/sudoers.d/sindhos-build
if [ "$PASSWORDLESS" = yes ]; then
  printf '%s ALL=(root) NOPASSWD: /usr/local/sbin/sindhos-build\n' "$BUILD_USER" > "$SUDOERS.tmp"
  chmod 0440 "$SUDOERS.tmp"
  visudo -c -f "$SUDOERS.tmp" >/dev/null
  mv "$SUDOERS.tmp" "$SUDOERS"
  echo "$BUILD_USER can now run: sudo -n /usr/local/sbin/sindhos-build"
else
  rm -f "$SUDOERS"
  echo "Skipped. Builds will ask for your password: sudo /usr/local/sbin/sindhos-build"
fi

echo
echo "Done. Build the ISO with:  tools/build.sh"
echo "Remove everything again:   sudo rm -rf $ROOT /usr/local/sbin/sindhos-build $SUDOERS"
