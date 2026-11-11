#!/usr/bin/env python3
"""Generate the SindhOS boot menu, boot splash and wallpaper SVGs.

  python3 branding/gen_artwork.py

Writes branding/bootmenu.svg, branding/splash.svg and branding/wallpaper.svg.
build.sh renders them to PNG with rsvg-convert (needs the Lateef font for the
Sindhi text). Original artwork: indigo gradient (design direction C), the
SindhOS ajrak emblem (branding/logo.svg) and an ajrak-style star medallion.
"""
import math
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
NAME_SD = "سنڌ او ايس"          # SindhOS in Sindhi script
WELCOME_SD = "ڀلي ڪري آيا"       # welcome
NAME = "SindhOS"
TOP, BOTTOM = "#26346E", "#121831"
CREAM, SAND, RED, INDIGO = "#F6F1E7", "#C9B98F", "#9B1B1E", "#1F2A5A"


def emblem(x, y, size, uid):
    """The SindhOS emblem from logo.svg, nested at x,y. Clip ids made unique."""
    svg = open(os.path.join(HERE, "logo.svg")).read()
    inner = re.sub(r"^<svg[^>]*>", "", svg.strip())
    inner = re.sub(r"</svg>\s*$", "", inner)
    inner = inner.replace('id="c"', f'id="c{uid}"').replace("url(#c)", f"url(#c{uid})")
    return f'<svg x="{x}" y="{y}" width="{size}" height="{size}" viewBox="0 0 512 512">{inner}</svg>'


def medallion(cx, cy, r, opacity):
    """Ajrak-style 8-point star medallion with mirrors."""
    def star(rad, inner_ratio):
        pts = []
        for i in range(16):
            a = math.pi * i / 8 - math.pi / 2
            rr = rad if i % 2 == 0 else rad * inner_ratio
            pts.append(f"{cx + rr * math.cos(a):.1f},{cy + rr * math.sin(a):.1f}")
        return " ".join(pts)
    dots = "".join(
        f'<circle cx="{cx + r * 0.62 * math.cos(math.pi * i / 4 + math.pi / 8):.1f}" '
        f'cy="{cy + r * 0.62 * math.sin(math.pi * i / 4 + math.pi / 8):.1f}" r="{r * 0.05:.1f}" fill="{CREAM}"/>'
        for i in range(8))
    return (f'<g opacity="{opacity}">'
            f'<polygon points="{star(r, 0.72)}" fill="{INDIGO}"/>'
            f'<polygon points="{star(r * 0.82, 0.70)}" fill="{RED}"/>'
            f'<circle cx="{cx}" cy="{cy}" r="{r * 0.40}" fill="{CREAM}"/>'
            f'<circle cx="{cx}" cy="{cy}" r="{r * 0.25}" fill="{RED}"/>'
            f'<circle cx="{cx}" cy="{cy}" r="{r * 0.08}" fill="{INDIGO}"/>'
            f'{dots}</g>')


def background(w, h):
    return (f'<defs><linearGradient id="bg" x1="0" y1="0" x2="0.35" y2="1">'
            f'<stop offset="0" stop-color="{TOP}"/><stop offset="1" stop-color="{BOTTOM}"/>'
            f'</linearGradient></defs><rect width="{w}" height="{h}" fill="url(#bg)"/>')


def wallpaper():
    w, h = 1920, 1080
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">'
            + background(w, h) + medallion(1560, 760, 470, 0.06) + medallion(250, 170, 150, 0.035) + "</svg>")


def splash():
    w, h = 1920, 1080
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">'
            + background(w, h) + medallion(1560, 760, 470, 0.05)
            + emblem(960 - 110, 300, 220, "s")
            + f'<text x="960" y="660" font-family="Lateef" font-weight="bold" font-size="104" fill="{CREAM}" '
              f'text-anchor="middle" direction="rtl">{WELCOME_SD}</text>'
            + f'<text x="960" y="740" font-family="DejaVu Sans" font-size="38" fill="{SAND}" '
              f'text-anchor="middle" letter-spacing="3">{NAME}</text></svg>')


def bootmenu():
    w, h = 640, 480
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">'
            + background(w, h) + medallion(560, 420, 150, 0.10)
            + emblem(40, 36, 96, "b")
            + f'<text x="600" y="92" font-family="Lateef" font-weight="bold" font-size="56" fill="{CREAM}" '
              f'text-anchor="start" direction="rtl">{NAME_SD}</text>'
            + f'<text x="600" y="128" font-family="DejaVu Sans" font-size="22" fill="{SAND}" '
              f'text-anchor="end" letter-spacing="2">{NAME}</text></svg>')


if __name__ == "__main__":
    for name, fn in (("wallpaper", wallpaper), ("splash", splash), ("bootmenu", bootmenu)):
        path = os.path.join(HERE, name + ".svg")
        with open(path, "w") as f:
            f.write(fn() + "\n")
        print("wrote", path)
