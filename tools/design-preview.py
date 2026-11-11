#!/usr/bin/env python3
"""Preview SindhOS design directions on the real ISO, with screenshots.

  tools/design-preview.py                # all directions, newest ISO in out/
  tools/design-preview.py --only B --mem 1024

Boots the ISO in QEMU, logs in on a serial console, downloads the themes from
this PC (QEMU's network sees this PC as 10.0.2.2), applies each design
direction to the running desktop and takes screenshots. Nothing is installed
on this PC and the ISO is not changed. Screenshots go to shots/design-<time>/.

Needs: qemu-system-x86_64, xorriso, Python with Pillow and librsvg (gi Rsvg).
"""
import argparse
import glob
import http.server
import io
import math
import os
import shutil
import socket
import subprocess
import sys
import tarfile
import tempfile
import threading
import time

from PIL import Image, ImageDraw, ImageFilter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

PORT = 8765
APPEND = ("boot=live components quiet splash username=sindhi user-fullname=Sindhi "
          "hostname=sindhos keyboard-layouts=us timezone=Asia/Karachi console=tty0 console=ttyS0,115200")
APPS = "/usr/share/applications/"
PINNED = ["thunar", "firefox-esr", "xfce4-terminal", "org.xfce.mousepad", "galculator",
          "sindhi-keyboard-guide", "xfce-settings-manager"]

# ---------------------------------------------------------------- directions

DIRECTIONS = {
    "A": dict(
        name="Indus Light",
        idea="Light and calm. Thin top bar (topi menu, centred clock, status), "
             "floating dock at the bottom, ajrak red only as accent.",
        gtk="SindhOS-Light", wm="SindhOS-Light", icons="Papirus",
        wallpaper=("#F4EFE6", "#E3D7C3", 0.10),
        layout="topbar+dock",
        top=dict(rgba=(0.973, 0.969, 0.957, 0.98), dark=False, size=30),
        dock=dict(rgba=(0.992, 0.988, 0.980, 0.93), dark=False, size=54),
    ),
    "B": dict(
        name="Ajrak Night",
        idea="Same layout as A, dark: indigo-black surfaces, ajrak red accent. "
             "Easy on the eyes at night, looks premium on cheap screens.",
        gtk="SindhOS-Dark", wm="SindhOS-Dark", icons="Papirus-Dark",
        wallpaper=("#1C2550", "#0B0E1C", 0.16),
        layout="topbar+dock",
        top=dict(rgba=(0.078, 0.086, 0.129, 0.98), dark=True, size=30),
        dock=dict(rgba=(0.118, 0.129, 0.192, 0.93), dark=True, size=54),
    ),
    "C": dict(
        name="Sindh Taskbar",
        idea="One indigo taskbar at the bottom (topi menu, pinned and open apps, "
             "status, clock), light windows. Familiar for people coming from "
             "Windows; uses about the same RAM as A and B.",
        gtk="SindhOS-Light", wm="SindhOS-Light", icons="Papirus",
        wallpaper=("#26346E", "#121831", 0.12),
        layout="taskbar",
        bar=dict(rgba=(0.122, 0.165, 0.353, 1.0), dark=True, size=44),
    ),
}

# ------------------------------------------------------------- panel config


def rgba_xml(c):
    return "\n".join(f'        <value type="double" value="{v}"/>' for v in c)


def panel_xml(d):
    def panel(pid, pos, length, size, icon, style, plugins, extra=""):
        ids = "\n".join(f'        <value type="int" value="{i}"/>' for i in plugins)
        return f'''    <property name="panel-{pid}" type="empty">
      <property name="position" type="string" value="{pos}"/>
      <property name="length" type="uint" value="{length}"/>
      <property name="position-locked" type="bool" value="true"/>
      <property name="size" type="uint" value="{style['size']}"/>
      <property name="icon-size" type="uint" value="{icon}"/>
      <property name="background-style" type="uint" value="1"/>
      <property name="background-rgba" type="array">
{rgba_xml(style['rgba'])}
      </property>{extra}
      <property name="plugin-ids" type="array">
{ids}
      </property>
    </property>'''

    plugins = {
        1: '''    <property name="plugin-1" type="string" value="whiskermenu">
      <property name="button-icon" type="string" value="/tmp/preview/topi-small.svg"/>
      <property name="show-button-title" type="bool" value="false"/>
    </property>''',
        2: '''    <property name="plugin-2" type="string" value="separator">
      <property name="expand" type="bool" value="true"/>
      <property name="style" type="uint" value="0"/>
    </property>''',
        3: '''    <property name="plugin-3" type="string" value="clock">
      <property name="digital-layout" type="uint" value="3"/>
      <property name="digital-time-format" type="string" value="%a %d %b   %I:%M %p"/>
    </property>''',
        4: '''    <property name="plugin-4" type="string" value="separator">
      <property name="expand" type="bool" value="true"/>
      <property name="style" type="uint" value="0"/>
    </property>''',
        5: '''    <property name="plugin-5" type="string" value="systray">
      <property name="square-icons" type="bool" value="true"/>
    </property>''',
        6: '''    <property name="plugin-6" type="string" value="pulseaudio"/>''',
        7: '''    <property name="plugin-7" type="string" value="actions">
      <!-- one icon that opens the Log out / Restart / Shut down dialog -->
      <property name="appearance" type="uint" value="0"/>
      <property name="items" type="array">
        <value type="string" value="+logout-dialog"/>
        <value type="string" value="-lock-screen"/>
        <value type="string" value="-switch-user"/>
        <value type="string" value="-separator"/>
        <value type="string" value="-suspend"/>
        <value type="string" value="-hibernate"/>
        <value type="string" value="-hybrid-sleep"/>
        <value type="string" value="-shutdown"/>
        <value type="string" value="-restart"/>
        <value type="string" value="-logout"/>
      </property>
    </property>''',
        8: '''    <property name="plugin-8" type="string" value="docklike"/>''',
        10: '''    <property name="plugin-10" type="string" value="genmon"/>''',
        9: '''    <property name="plugin-9" type="string" value="separator">
      <property name="expand" type="bool" value="false"/>
      <property name="style" type="uint" value="0"/>
    </property>''',
    }
    if d["layout"] == "topbar+dock":
        panels = [panel(1, "p=6;x=0;y=0", 100, 30, 18, d["top"], [1, 2, 3, 4, 5, 6, 7]),
                  panel(2, "p=10;x=0;y=0", 1, 54, 40, d["dock"], [8],
                        '\n      <property name="length-adjust" type="bool" value="true"/>')]
        used = [1, 2, 3, 4, 5, 6, 7, 8]
        pids = [1, 2]
    else:
        panels = [panel(1, "p=8;x=0;y=0", 100, 44, 28, d["bar"], [1, 9, 8, 2, 10, 5, 6, 3, 7])]
        used = [1, 2, 3, 5, 6, 7, 8, 9, 10]
        pids = [1]
    ids = "\n".join(f'    <value type="int" value="{i}"/>' for i in pids)
    dark = str((d.get("bar") or d["top"])["dark"]).lower()
    return f'''<?xml version="1.0" encoding="UTF-8"?>
<channel name="xfce4-panel" version="1.0">
  <property name="configver" type="int" value="2"/>
  <property name="panels" type="array">
{ids}
    <property name="dark-mode" type="bool" value="{dark}"/>
{chr(10).join(panels)}
  </property>
  <property name="plugins" type="empty">
{chr(10).join(plugins[i] for i in used)}
  </property>
</channel>
'''


# Keyboard indicator (xfce4-genmon-plugin): سنڌي / Roman Sindhi / English
GENMON_RC = "Command=sindhos-keyboard-label\nUseLabel=0\nText=\nUpdatePeriod=2000\nFont=Inter Semi-Bold 10\n"

DOCKLIKE_RC = "[user]\npinned=" + ";".join(APPS + a + ".desktop" for a in PINNED) + ";\n" + \
    "forceIconSize=true\niconSize=30\n" \
    "indicatorOrientation=0\nindicatorStyle=0\ninactiveIndicatorStyle=0\n" \
    "indicatorColorFromTheme=false\nindicatorColor=rgb(155,27,30)\ninactiveColor=rgb(155,27,30)\n" \
    "noWindowsListIfSingle=true\nshowPreviews=false\n"

# ------------------------------------------------------- placeholder wallpapers


def medallion(size, colours):
    """Ajrak-style star medallion (original geometric drawing)."""
    s = size
    im = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    c = s / 2
    red, indigo, cream = colours
    for k, (r, col) in enumerate(((0.48, indigo), (0.40, red))):
        pts = []
        for i in range(16):
            a = math.pi * i / 8
            rr = s * r if i % 2 == 0 else s * r * 0.72
            pts.append((c + rr * math.cos(a), c + rr * math.sin(a)))
        d.polygon(pts, fill=col)
    d.ellipse([c - s * 0.2, c - s * 0.2, c + s * 0.2, c + s * 0.2], fill=cream)
    d.ellipse([c - s * 0.12, c - s * 0.12, c + s * 0.12, c + s * 0.12], fill=red)
    for i in range(8):
        a = math.pi * i / 4 + math.pi / 8
        x, y = c + s * 0.3 * math.cos(a), c + s * 0.3 * math.sin(a)
        d.ellipse([x - s * 0.025, y - s * 0.025, x + s * 0.025, y + s * 0.025], fill=cream)
    return im


def wallpaper(top, bottom, motif_alpha, w=1920, h=1080):
    t = tuple(int(top[i:i + 2], 16) for i in (1, 3, 5))
    b = tuple(int(bottom[i:i + 2], 16) for i in (1, 3, 5))
    grad = Image.new("RGB", (1, h))
    for y in range(h):
        f = y / (h - 1)
        grad.putpixel((0, y), tuple(int(t[i] + (b[i] - t[i]) * f) for i in range(3)))
    im = grad.resize((w, h)).convert("RGBA")
    m = medallion(900, ((155, 27, 30, 255), (31, 42, 90, 255), (246, 241, 231, 255)))
    m.putalpha(m.getchannel("A").point(lambda v: int(v * motif_alpha)))
    im.alpha_composite(m, (w - 640, h - 620))
    return im.convert("RGB")

# ------------------------------------------------------------------ payload

APPLY_SH = r'''#!/bin/sh
# Runs inside the live session: apply one design direction.
V=$1; P=/tmp/preview
. $P/$V.env
mkdir -p ~/.local/share/themes ~/.config/xfce4/panel ~/.config/xfce4/xfconf/xfce-perchannel-xml
cp -r $P/themes/* ~/.local/share/themes/
dpkg -s xfce4-docklike-plugin >/dev/null 2>&1 || echo live | sudo -S dpkg -i $P/xfce4-docklike-plugin.deb >/dev/null 2>&1
pkill -x plank 2>/dev/null
# panel: stop it and xfconfd, swap the config, start again
xfce4-panel --quit; sleep 1; pkill -x xfconfd; sleep 1
cp $P/panel-$V.xml ~/.config/xfce4/xfconf/xfce-perchannel-xml/xfce4-panel.xml
cp $P/docklike-8.rc ~/.config/xfce4/panel/docklike-8.rc
setsid xfce4-panel >/dev/null 2>&1 &
sleep 4
q() { xfconf-query -c "$1" -p "$2" -n -t "$3" -s "$4" 2>/dev/null || xfconf-query -c "$1" -p "$2" -s "$4"; }
q xsettings /Net/ThemeName string "$GTK"
q xsettings /Net/IconThemeName string "$ICONS"
q xsettings /Gtk/DecorationLayout string "menu:minimize,maximize,close"
q xsettings /Gtk/FontName string "Inter 10"
q xfwm4 /general/theme string "$WM"
q xfwm4 /general/button_layout string "|HMC"
q xfwm4 /general/title_alignment string "center"
q xfwm4 /general/title_font string "Inter Semi-Bold 10"
q xfce4-desktop /desktop-icons/file-icons/show-filesystem bool false
q xfce4-desktop /desktop-icons/file-icons/show-removable bool false
# wallpaper: xfdesktop keys are per monitor name and workspace
for m in $(xrandr --listmonitors | awk 'NR>1 {print $NF}') 0; do
  for w in 0 1; do
    b=/backdrop/screen0/monitor$m/workspace$w
    q xfce4-desktop $b/last-image string $P/wallpaper-$V.jpg
    q xfce4-desktop $b/image-style int 5
  done
done
echo applied $V
'''


def build_payload(directions):
    tmp = tempfile.mkdtemp(prefix="sindhos-design-")
    pay = os.path.join(tmp, "preview")
    themes = os.path.join(pay, "themes")
    os.makedirs(themes)
    with tarfile.open(os.path.join(ROOT, "third_party/adw-gtk3/adw-gtk3v6.5.tar.xz")) as t:
        t.extractall(themes, filter="data")
    for th in ("SindhOS-Light", "SindhOS-Dark"):
        shutil.copytree(os.path.join(ROOT, "branding/theme", th), os.path.join(themes, th))
    for f in ("topi.svg", "topi-small.svg"):
        shutil.copy(os.path.join(ROOT, "branding/topi", f), pay)
    deb = sorted(glob.glob(os.path.join(ROOT, "cache", "xfce4-docklike-plugin_*_amd64.deb")))
    if not deb:
        sys.exit("cache/xfce4-docklike-plugin_*_amd64.deb missing")
    shutil.copy(deb[-1], os.path.join(pay, "xfce4-docklike-plugin.deb"))
    with open(os.path.join(pay, "docklike-8.rc"), "w") as f:
        f.write(DOCKLIKE_RC)
    with open(os.path.join(pay, "apply.sh"), "w") as f:
        f.write(APPLY_SH)
    with open(os.path.join(pay, "sindhi.txt"), "w") as f:
        f.write("سنڌي ٻولي اسان جي سڃاڻپ آهي.\nSindhOS: a light Linux with Sindhi built in.\n")
    for k in directions:
        d = DIRECTIONS[k]
        with open(os.path.join(pay, f"panel-{k}.xml"), "w") as f:
            f.write(panel_xml(d))
        with open(os.path.join(pay, f"{k}.env"), "w") as f:
            f.write(f'GTK={d["gtk"]}\nWM={d["wm"]}\nICONS={d["icons"]}\n')
        wallpaper(*d["wallpaper"]).save(os.path.join(pay, f"wallpaper-{k}.jpg"), quality=90)
    with tarfile.open(os.path.join(tmp, "payload.tar"), "w") as t:
        t.add(pay, arcname=".")
    return tmp

# ------------------------------------------------------------------- QEMU


class Chan:
    def __init__(self, path):
        self.s = socket.socket(socket.AF_UNIX)
        self.s.connect(path)
        self.s.settimeout(1)
        self.buf = b""

    def read(self, secs):
        end = time.time() + secs
        while time.time() < end:
            try:
                d = self.s.recv(65536)
                if d:
                    self.buf += d
            except socket.timeout:
                pass

    def wait_for(self, pat, secs, start=0):
        end = time.time() + secs
        while time.time() < end:
            if pat in self.buf[start:]:
                return True
            self.read(1)
        return False

    def send(self, line):
        self.s.sendall(line.encode() + b"\n")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--iso")
    ap.add_argument("--mem", type=int, default=2048)
    ap.add_argument("--only", help="e.g. A or AC")
    ap.add_argument("--debug", action="store_true", help="print settings from the guest")
    a = ap.parse_args()
    dirs = list(a.only) if a.only else list(DIRECTIONS)

    iso = a.iso or max(glob.glob(os.path.join(ROOT, "out", "*.iso")), key=os.path.getmtime)
    work = build_payload(dirs)
    out = os.path.join(ROOT, "shots", "design-" + time.strftime("%Y%m%d-%H%M%S"))
    os.makedirs(out)

    handler = lambda *x, **k: http.server.SimpleHTTPRequestHandler(*x, directory=work, **k)  # noqa: E731
    httpd = http.server.ThreadingHTTPServer(("127.0.0.1", PORT), handler)
    httpd.RequestHandlerClass.log_message = lambda *x: None
    threading.Thread(target=httpd.serve_forever, daemon=True).start()

    subprocess.run(["xorriso", "-osirrox", "on", "-indev", iso, "-extract", "/live/vmlinuz", f"{work}/vmlinuz",
                    "-extract", "/live/initrd.img", f"{work}/initrd.img"],
                   check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    ser_p, mon_p = f"{work}/serial.sock", f"{work}/monitor.sock"
    q = subprocess.Popen(["qemu-system-x86_64", "-enable-kvm", "-cpu", "host", "-m", str(a.mem), "-smp", "2",
                          "-cdrom", iso, "-kernel", f"{work}/vmlinuz", "-initrd", f"{work}/initrd.img",
                          "-append", APPEND, "-vga", "std", "-display", "none",
                          "-nic", "user,model=virtio-net-pci",
                          "-serial", f"unix:{ser_p},server,nowait",
                          "-monitor", f"unix:{mon_p},server,nowait"])
    try:
        for _ in range(100):
            if os.path.exists(ser_p) and os.path.exists(mon_p):
                break
            time.sleep(0.1)
        ser, mon = Chan(ser_p), Chan(mon_p)

        def shot(name, wait=0):
            time.sleep(wait)
            mon.send(f"screendump {out}/{name}.png -f png")
            time.sleep(1.5)
            print("  shot", name, flush=True)

        def key(k, wait=0.5):
            mon.send("sendkey " + k)
            time.sleep(wait)

        def sh(cmd, wait=2):
            ser.send(cmd)
            ser.read(wait)

        print("Booting...", flush=True)
        if not ser.wait_for(b"login:", 300):
            sys.exit("no serial login prompt")
        ser.read(90)                       # let the desktop start
        for _ in range(3):
            mark = len(ser.buf)
            ser.send("sindhi")
            ser.wait_for(b"assword", 60, mark)
            time.sleep(1.5)
            ser.send("live")
            if ser.wait_for(b"$ ", 30, mark):
                break
            ser.wait_for(b"login:", 60, mark + 10)
        sh("export TERM=dumb $(tr '\\0' '\\n' < /proc/$(pgrep -x xfce4-session)/environ | "
           "grep -E '^(DISPLAY|XAUTHORITY|DBUS_SESSION_BUS_ADDRESS|XDG_RUNTIME_DIR)=' | tr '\\n' ' ')")
        sh(f"mkdir -p /tmp/preview && wget -q -O - http://10.0.2.2:{PORT}/payload.tar | tar -x -C /tmp/preview && echo payload-ok", 8)
        if b"payload-ok" not in ser.buf:
            sys.exit("guest could not download the preview payload")
        shot("00-before", 1)
        first = True
        for k in dirs:
            d = DIRECTIONS[k]
            print(f"Direction {k}: {d['name']}", flush=True)
            mark = len(ser.buf)
            sh(f"sh /tmp/preview/apply.sh {k} >/tmp/apply-{k}.log 2>&1; echo done-{k}", 2)
            ser.wait_for(f"done-{k}".encode() + b"\r", 60, mark)
            if a.debug:
                m2 = len(ser.buf)
                sh(f"cat /tmp/apply-{k}.log; xfconf-query -c xfce4-panel -lv | grep -E 'panel-[12]/(background|dark|length|position|size)'; "
                   "xrandr --listmonitors; xfconf-query -c xfce4-desktop -l | head; echo dbg-EN''D", 1)
                ser.wait_for(b"dbg-END", 60, m2)
                print(ser.buf[m2:].decode(errors="replace").replace("\r", ""))
            if first:
                sh("setsid thunar ~ >/dev/null 2>&1 &", 4)
                sh("setsid mousepad /tmp/preview/sindhi.txt >/dev/null 2>&1 &", 4)
                sh("setsid xfce4-appearance-settings >/dev/null 2>&1 &", 5)
                first = False
            shot(f"{k}-1-desktop", 6)
            sh("setsid xfce4-popup-whiskermenu >/dev/null 2>&1 &", 1)
            shot(f"{k}-2-menu", 3)
            key("esc", 1)
        mon.send("quit")
        q.wait(timeout=20)
    finally:
        if q.poll() is None:
            q.kill()
        httpd.shutdown()
        shutil.rmtree(work, ignore_errors=True)
    print("Screenshots:", out)


if __name__ == "__main__":
    main()
