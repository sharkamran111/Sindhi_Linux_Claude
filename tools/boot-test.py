#!/usr/bin/env python3
"""Boot a SindhOS ISO in QEMU, drive it with key presses, save screenshots.

  tools/boot-test.py                      # newest ISO in out/, 2048 MB, BIOS
  tools/boot-test.py --mem 1024           # low-end check
  tools/boot-test.py --uefi               # boot through UEFI (OVMF)
  tools/boot-test.py --gui                # just open a QEMU window to try it by hand
  tools/boot-test.py --iso X.iso --out shots/run1

Only needs qemu-system-x86_64 (KVM if available) and Python's standard library.
Used both locally and by the GitHub Actions boot test.
"""
import argparse
import glob
import os
import shutil
import socket
import subprocess
import sys
import tempfile
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TYPED_FILE = "/tmp/sindhi-typed.txt"
GUIDE = "/usr/share/sindhos/keyboard-guide/index.html"
OVMF = ["/usr/share/OVMF/OVMF_CODE_4M.fd", "/usr/share/ovmf/OVMF.fd", "/usr/share/OVMF/OVMF_CODE.fd"]

# Key names QEMU's "sendkey" understands, for characters that aren't a-z/0-9.
KEYS = {
    " ": "spc", "/": "slash", "-": "minus", ".": "dot", ",": "comma", "=": "equal",
    ";": "semicolon", "'": "apostrophe", "\n": "ret", "\t": "tab",
    "_": "shift-minus", ":": "shift-semicolon", "|": "shift-backslash",
    "~": "shift-grave_accent", ">": "shift-dot", "<": "shift-comma",
}


class Monitor:
    def __init__(self, path):
        self.path = path

    def cmd(self, line):
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as s:
            s.settimeout(10)
            s.connect(self.path)
            s.sendall((line + "\n").encode())
            time.sleep(0.15)
            try:
                return s.recv(65536).decode(errors="replace")
            except socket.timeout:
                return ""


class Run:
    def __init__(self, mon, out):
        self.mon, self.out = mon, out

    def key(self, name, pause=0.25):
        self.mon.cmd("sendkey " + name)
        time.sleep(pause)

    def type(self, text):
        for ch in text:
            if ch.isalpha() and ch.isascii():
                self.key(("shift-" + ch.lower()) if ch.isupper() else ch, 0.12)
            elif ch.isdigit():
                self.key(ch, 0.12)
            else:
                self.key(KEYS[ch], 0.12)

    def keys(self, *names):
        for n in names:
            self.key(n, 0.12)

    def shot(self, name, wait=0):
        time.sleep(wait)
        path = os.path.join(self.out, name + ".png")
        self.mon.cmd(f"screendump {path} -f png")
        time.sleep(1)
        print("  shot", name, flush=True)


def scenario(r):
    """The standard walk-through. Extend it as phases add features."""
    r.shot("00-boot-menu", 8)
    r.key("ret")
    for i in range(1, 16):
        r.shot(f"01-boot-{i:02d}", 2)
    r.shot("02-desktop", 25)
    r.shot("03-desktop-later", 20)

    # Text editor, English
    r.key("alt-f2", 3)
    r.type("mousepad\n")
    r.shot("04-editor-english", 8)

    # Roman Sindhi (Ctrl+Space = next keyboard): "sindhi boli " -> سنڌي ٻولي
    r.key("ctrl-spc", 2)
    r.type("sindhi boli ")
    r.shot("05-typed-sindhi", 1)
    r.key("ctrl-spc", 2)
    # Save it, so the terminal step can show the exact letters as UTF-8 bytes
    r.key("ctrl-s", 3)
    r.type(TYPED_FILE + "\n")
    time.sleep(2)

    # Keyboard guide app in the browser
    r.key("alt-f2", 3)
    r.type("firefox-esr " + GUIDE + "\n")
    r.key("ret", 2)
    r.shot("06-keyboard-guide", 30)
    r.key("ctrl-q", 8)          # with 2 tabs open Firefox asks "Quit Firefox?" (slow at 1 GB),
    r.key("ret", 6)             # Enter = "Quit Firefox" (harmless if it didn't ask)

    # Spotlight-style search
    r.key("meta_l-spc", 3)
    r.type("calc")
    r.shot("07-search", 2)
    r.key("esc", 1)

    # Terminal: sindh = sudo, and memory use
    r.key("ctrl-alt-t", 6)
    r.type("sindh whoami\n")
    r.type("cat /etc/os-release | head -3\n")
    r.type("free -m\n")
    # Expected: d8 b3 d9 86 da 8c d9 8a 20 d9 bb d9 88 d9 84 d9 8a = سنڌي ٻولي
    r.type("od -An -tx1 " + TYPED_FILE + " | head -2\n")
    r.shot("08-terminal-ram", 3)


def find_iso():
    isos = sorted(glob.glob(os.path.join(ROOT, "out", "*.iso")) + glob.glob(os.path.join(ROOT, "*.iso")),
                  key=os.path.getmtime)
    if not isos:
        sys.exit("No ISO found in out/. Build one with tools/build.sh, or pass --iso.")
    return isos[-1]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--iso")
    ap.add_argument("--mem", type=int, default=2048, help="RAM in MB (default 2048)")
    ap.add_argument("--uefi", action="store_true")
    ap.add_argument("--gui", action="store_true", help="open a window, no automation")
    ap.add_argument("--out", help="screenshot folder (default shots/<time>-<mem>M)")
    a = ap.parse_args()

    iso = os.path.abspath(a.iso or find_iso())
    qemu = ["qemu-system-x86_64", "-m", str(a.mem), "-smp", "2", "-cdrom", iso, "-boot", "d",
            "-vga", "std", "-nic", "user,model=virtio-net-pci", "-name", "SindhOS test"]
    if os.access("/dev/kvm", os.R_OK | os.W_OK):
        qemu += ["-enable-kvm", "-cpu", "host"]
    else:
        print("warning: no KVM, this will be slow", file=sys.stderr)
    if a.uefi:
        fw = next((f for f in OVMF if os.path.exists(f)), None)
        if not fw:
            sys.exit("UEFI firmware (ovmf) not installed")
        qemu += ["-drive", f"if=pflash,format=raw,readonly=on,file={fw}"]

    print(f"ISO {iso}\nRAM {a.mem} MB, {'UEFI' if a.uefi else 'BIOS'}", flush=True)
    if a.gui:
        os.execvp(qemu[0], qemu + ["-display", "gtk"])

    out = os.path.abspath(a.out or os.path.join(
        ROOT, "shots", time.strftime("%Y%m%d-%H%M%S") + f"-{a.mem}M" + ("-uefi" if a.uefi else "")))
    os.makedirs(out, exist_ok=True)
    tmp = tempfile.mkdtemp(prefix="sindhos-qemu-")
    sock = os.path.join(tmp, "monitor.sock")
    proc = subprocess.Popen(qemu + ["-display", "none", "-monitor", f"unix:{sock},server,nowait"])
    try:
        for _ in range(50):
            if os.path.exists(sock):
                break
            time.sleep(0.1)
        scenario(Run(Monitor(sock), out))
        Monitor(sock).cmd("quit")
        proc.wait(timeout=20)
    finally:
        if proc.poll() is None:
            proc.kill()
        shutil.rmtree(tmp, ignore_errors=True)
    print("Screenshots:", out)


if __name__ == "__main__":
    main()
