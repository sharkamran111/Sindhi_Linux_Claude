#!/usr/bin/env python3
"""Generate the Sindhi Keyboard Guide (HTML) from layout.py.

Run from the repo root:  python3 keyboard/gen.py
"""
import html
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from layout import LOWER, UPPER, MARKS, PUNCT  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parent.parent
INC = ROOT / "config" / "includes.chroot"


def guide() -> str:
    data = {
        "rows": [list("qwertyuiop"), list("asdfghjkl"), list("zxcvbnm")],
        "lower": LOWER,
        "upper": UPPER,
    }
    marks = "\n".join(
        f'<tr><td><kbd>{html.escape(k)}</kbd></td><td class="sd big">'
        f'{"ـ" + v if v in chr(0x64E) + chr(0x650) + chr(0x64F) + chr(0x651) + chr(0x652) else v}'
        f'</td><td>{html.escape(en)}</td><td class="sd">{sd}</td></tr>'
        for k, v, en, sd in MARKS
    )
    punct = "\n".join(
        f'<tr><td><kbd>{html.escape(k)}</kbd></td><td class="sd big">{v}</td>'
        f'<td>{html.escape(en)}</td><td class="sd">{sd}</td></tr>'
        for k, v, en, sd in PUNCT
    )
    tpl = (ROOT / "keyboard" / "guide.html.in").read_text(encoding="utf-8")
    return (
        tpl.replace("@DATA@", json.dumps(data, ensure_ascii=False))
        .replace("@MARKS@", marks)
        .replace("@PUNCT@", punct)
    )


def main() -> None:
    # The "Sindhi" keyboard itself is served by keyboard/roman/engine.py,
    # which reads layout.py directly; only the guide is generated here.
    out_guide = INC / "usr/share/sindhos/keyboard-guide/index.html"
    out_guide.parent.mkdir(parents=True, exist_ok=True)
    out_guide.write_text(guide(), encoding="utf-8")
    print("wrote", out_guide.relative_to(ROOT))


if __name__ == "__main__":
    main()
