#!/usr/bin/env python3
"""Measure SindhOS memory use as text, through a serial console.

  tools/ram-check.py                 # newest ISO in out/, 2048 MB
  tools/ram-check.py --mem 4096 --settle 120 --iso X.iso

Boots the ISO's own kernel and initrd in QEMU with an extra serial console,
waits for the desktop to start, logs in on the serial line (user sindhi,
password live) and prints free -m and the biggest processes by private
memory. The full serial log is saved next to the screenshots in shots/.
Needs qemu-system-x86_64 and xorriso.
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
# Same as the ISO's boot menu entry, plus the serial console.
APPEND = ("boot=live components quiet splash username=sindhi user-fullname=Sindhi "
          "hostname=sindhos keyboard-layouts=us timezone=Asia/Karachi console=tty0 console=ttyS0,115200")

REPORT = r"""export TERM=dumb; echo live | sudo -S true >/dev/null 2>&1; echo ==RA""M==; free -m; \
echo ==PROCESSES, private MB==; for p in $(ps -eo pid=); do \
v=$(sudo awk '/^Private_(Clean|Dirty)/ {s+=$2} END {print int(s/1024)}' /proc/$p/smaps_rollup 2>/dev/null); \
[ -n "$v" ] && [ "$v" -gt 4 ] && echo "$v $(cat /proc/$p/comm 2>/dev/null)"; done | sort -rn | head -20; \
echo ==OOM kills==; sudo dmesg | grep -ciE 'killed process|out of memory'; echo ==EN""D=="""


class Serial:
    def __init__(self, path, log):
        self.s = socket.socket(socket.AF_UNIX)
        self.s.connect(path)
        self.s.settimeout(1)
        self.buf = b""
        self.log = log

    def read(self, secs):
        end = time.time() + secs
        while time.time() < end:
            try:
                d = self.s.recv(65536)
            except socket.timeout:
                continue
            if d:
                self.buf += d
                self.log.write(d.decode(errors="replace"))
                self.log.flush()

    def wait_for(self, pattern, secs, start=0):
        end = time.time() + secs
        while time.time() < end:
            if pattern in self.buf[start:]:
                return True
            self.read(1)
        return pattern in self.buf[start:]

    def send(self, line):
        self.s.sendall(line.encode() + b"\n")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--iso")
    ap.add_argument("--mem", type=int, default=2048)
    ap.add_argument("--settle", type=int, default=150, help="seconds to let the desktop start (default 150)")
    a = ap.parse_args()

    iso = a.iso or max(glob.glob(os.path.join(ROOT, "out", "*.iso")), key=os.path.getmtime, default=None)
    if not iso:
        sys.exit("No ISO in out/, pass --iso")
    tmp = tempfile.mkdtemp(prefix="sindhos-ram-")
    out = os.path.join(ROOT, "shots")
    os.makedirs(out, exist_ok=True)
    logpath = os.path.join(out, time.strftime("%Y%m%d-%H%M%S") + f"-ram-{a.mem}M.log")
    q = None
    try:
        subprocess.run(["xorriso", "-osirrox", "on", "-indev", iso,
                        "-extract", "/live/vmlinuz", f"{tmp}/vmlinuz",
                        "-extract", "/live/initrd.img", f"{tmp}/initrd.img"],
                       check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        sock = f"{tmp}/serial.sock"
        cmd = ["qemu-system-x86_64", "-m", str(a.mem), "-smp", "2", "-cdrom", iso,
               "-kernel", f"{tmp}/vmlinuz", "-initrd", f"{tmp}/initrd.img", "-append", APPEND,
               "-vga", "std", "-display", "none", "-nic", "user,model=virtio-net-pci",
               "-serial", f"unix:{sock},server,nowait"]
        if os.access("/dev/kvm", os.R_OK | os.W_OK):
            cmd[1:1] = ["-enable-kvm", "-cpu", "host"]
        q = subprocess.Popen(cmd)
        for _ in range(100):
            if os.path.exists(sock):
                break
            time.sleep(0.1)
        with open(logpath, "w") as log:
            ser = Serial(sock, log)
            print(f"Booting {os.path.basename(iso)} with {a.mem} MB...", flush=True)
            if not ser.wait_for(b"login:", 300):
                sys.exit("No login prompt on the serial console after 5 minutes")
            print(f"Booted. Letting the desktop start for {a.settle} s...", flush=True)
            ser.read(a.settle)
            # login clears its input right after printing "Password:", so a
            # password sent too early is lost: pause, and retry a few times.
            for attempt in range(3):
                mark = len(ser.buf)
                ser.send("sindhi")
                if not ser.wait_for(b"assword", 120, mark):
                    sys.exit("No password prompt: the system is too busy (likely out of memory)")
                time.sleep(1.5)
                ser.send("live")
                ser.wait_for(b"$ ", 60, mark)
                if b"$ " in ser.buf[mark:]:
                    break
                ser.wait_for(b"login:", 90, mark + 10)
            else:
                sys.exit("Could not log in on the serial console")
            ser.read(2)
            start = len(ser.buf)
            ser.send(REPORT)
            if not ser.wait_for(b"==END==", 180, start):
                print("warning: report did not finish", file=sys.stderr)
            text = ser.buf[start:].decode(errors="replace").replace("\r", "")
            body = text.split("==RAM==\n", 1)[-1].split("==END==")[0]
            print("==RAM==\n" + body.strip())
        print("Serial log:", logpath)
    finally:
        if q and q.poll() is None:
            q.kill()
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    main()
