# SindhOS Roadmap · سنڌ او ايس

SindhOS (formerly "Sindhi Linux") is a light Debian 13 live/installable system
with Sindhi built in. This file plans the next six phases.

**Target hardware:** low-end PCs with **1–2 GB RAM**. Every choice below is
checked against that.

**Working rules**
- One phase at a time. Nothing is built until "start phase N".
- At the end of each phase: build the ISO, boot it in QEMU (at **1 GB and 2 GB**
  RAM), take screenshots, hand over a short test checklist.
- Commit locally after each phase. **No push** until asked (pushing also
  triggers the GitHub Actions build).
- Only original artwork, or freely licensed material listed in `CREDITS.md`.

---

## Where we start (current state, v0.1)

| Area | Today |
|---|---|
| Base | Debian 13 (trixie), `live-build`, iso-hybrid, Calamares installer |
| Desktop | XFCE + Plank dock + Whisker menu, WhiteSur (Mac-style) theme, Papirus icons, Inter font |
| Login | `lightdm-gtk-greeter`, Greybird-dark, ajrak background |
| Boot | Plymouth theme `sindhi`, branded isolinux/GRUB menu |
| Sindhi | Lateef + Scheherazade fonts, `sd_IN`/`ur_PK` locales, IBus + m17n Roman Sindhi layout (`keyboard/layout.py`), Ctrl+Space switch, keyboard guide app |
| Extras | `sindh` = `sudo`, CI build and boot test with screenshots |
| Name | "Sindhi Linux" in ~20 files (os-release, boot menu, splash, ISO label, installer, paths like `/usr/share/sindhi-linux`) |

### RAM budget (the 1–2 GB rule)

| Item | Rough RAM | Note |
|---|---|---|
| XFCE session + Plank + IBus | 350–450 MB | target: idle desktop **under 450 MB** |
| Live overlay (tmpfs) | grows with use | the reason 1 GB live sessions feel tight |
| Firefox ESR, 1–2 tabs | 300–500 MB | tuned prefs (fewer content processes) help |
| LibreOffice Writer | 150–250 MB | only while open |
| ibus-typing-booster | 40–80 MB | Phase 4 |

Honest expectation: **2 GB is comfortable, 1 GB works for the desktop, typing
and office, but the browser will swap.** Each phase measures `free -m` at idle in
QEMU with 1 GB, and a change that adds more than ~30 MB at idle needs a reason.
The compositor (rounded corners, shadows) gets switched off automatically when
there is less than 1.5 GB of RAM.

---

## Phase 0 · Build setup (once, before Phase 1)

The ISO must be built with Debian's `live-build`. Ubuntu's package is an old
fork, so builds run in a Debian 13 chroot.

| File | What it does |
|---|---|
| `tools/setup-build-host.sh` | Run once with sudo: installs debootstrap, creates `/srv/sindhos-build` (Debian trixie + live-build), installs `/usr/local/sbin/sindhos-build`. `--passwordless` adds a sudoers rule for that one command |
| `tools/sindhos-build.in` | The build command: copies the checkout into the chroot, runs `./build.sh`, puts the ISO and log in `out/`. Keeps the package cache between builds |
| `tools/build.sh` | What you (or I) run to build. `--release` = xz squashfs (smaller, slower); default = zstd level 3 (fast test builds). `--clean` = remove old build leftovers, keep downloaded packages |
| `cache/` (git-ignored) | Local copies of files the build would otherwise download: the Broadcom b43/b43legacy firmware, served to Debian's installer packages by a build-time `wget` helper (checksums still verified) |
| `tools/ram-check.py` | Boots the ISO with a serial console, logs in after the desktop starts and prints `free -m` and the biggest processes as text |
| `tools/boot-test.py` | Boots the ISO in QEMU (KVM, any RAM size, BIOS or UEFI), sends keys, saves PNG screenshots to `shots/`. Also used by CI. `--gui` for testing by hand |

**Found in the Phase 0 test (v0.1 ISO):**
- The desktop did not start at 1 GB. live-build's default hook
  `9000-remove-gnome-icon-cache` deletes all GTK icon caches, so each GTK
  program indexed Papirus's 43,000 icons itself (80–120 MB each). Fixed by hook
  `9500-sindhos-icon-caches` (costs 9 MB disk). Checked on the v0.1 ISO by
  rebuilding the caches at runtime: 1 GB desktop then runs with 606 MB used,
  360 MB available
- Still open for Phase 1: the initrd is 140 MB (202 MB of it is firmware for
  AMD/NVIDIA GPUs and server network cards). It boots fine at 1 GB but slows
  boot from USB; worth trimming
- Idle desktop at 1 GB uses about 600 MB, above the 450 MB target. Biggest
  remaining items: xfwm4 (compositor), ibus UI, Xorg

Build speed: dpkg runs under `eatmydata` inside the image (no fsync, big
win on a hard disk), and downloaded packages are kept between builds.

Security note on `--passwordless`: the build runs hooks from this repo as
root, so a password-free build means anything running as your user can get
root through it. Fine on a personal build PC; skip the flag on a shared one.

---

## Phase 1 · Branding: SindhOS everywhere

**Name**
- `/etc/os-release` and `/usr/lib/os-release`: `NAME="SindhOS"`,
  `PRETTY_NAME="SindhOS 0.2"`, `ID=sindhos`, `ID_LIKE=debian`, keep
  `VERSION_CODENAME=trixie` so Debian tools and Calamares still work.
  Also `/etc/issue`, `/etc/lsb-release`, `HOME_URL` and `LOGO=sindhos`
- Boot menu (isolinux + GRUB EFI), Plymouth splash, ISO name/label
  (`sindhos-amd64.hybrid.iso`, `SINDHOS`), hostname `sindhos`
- Installed system: `GRUB_DISTRIBUTOR=SindhOS`, Calamares branding
  (name, logo, welcome text, slideshow title)
- Login screen: name and logo on the greeter
- About screen: `xfce4-about` reads os-release, plus the SindhOS logo as an
  icon-theme icon named `sindhos`
- Rename internal paths and IDs: `/usr/share/sindhi-linux` → `/usr/share/sindhos`,
  config file names, README, CI artifact names
- The live user stays `sindhi` (password `live`) unless you want it changed

**Start button icon: Sindhi topi**
- Original SVG: the dome-shaped Sindhi topi with the cut-out front arch, mirror
  work and embroidery shown as simple geometric shapes. Readable at 16–24 px,
  so a simplified small version plus a detailed large one
- Used for the Whisker menu button, the `sindhos` icon (About screen, installer)
  and the Plymouth/boot logo where it fits

**Ajrak theme accents**
- Palette: deep red `#9B1B1E`, indigo `#1F2A5A`, black `#141414`,
  white/cream `#F6F1E7` (final values set in Phase 1 and recorded in
  `branding/palette.md`)
- WhiteSur ships as prebuilt tarballs. At build time, swap its blue accent
  for ajrak red (selection, buttons, switches, focus ring) and indigo
  (top bar, headers). No sass toolchain needed
- Same palette in: greeter, Plymouth, boot menu, Plank theme, Whisker menu,
  terminal colour scheme, Papirus folder colour (closest to red)

**Test checklist (to hand over):** boot menu says SindhOS · splash · login screen
· About dialog · `cat /etc/os-release` · topi in the start button · red/indigo
accents in a settings dialog · installer shows SindhOS.

---

## Phase 2 · Lock screen with Sindhi poetry

**Layout:** big clock and date on the left. On the right, a Sindhi verse in a
Naskh font (Lateef or Scheherazade, decided by on-screen test), right to left,
right-aligned, with the poet's name below. Ajrak background, dimmed for
readability. A new random verse every few minutes (default 5, configurable).

**Choosing the lock screen.** XFCE's stock options (`light-locker`
→ `lightdm-gtk-greeter`, `xfce4-screensaver`) can't show this layout. HTML greeters
(web-greeter, nody-greeter) can, but they are not in Debian and need a
WebKit/Electron engine, too heavy for 1 GB.

Recommended: **`xsecurelock` + a small custom "saver"**
- `xsecurelock` (Debian package, tiny, written in C) handles locking and
  the password check through PAM. It runs any program as its full-screen
  "saver", and that program never handles the password
- `sindhos-verse`: a small Python + GTK3 (PyGObject) program that draws the
  clock/date and verse layout. About 30–40 MB while locked, nothing when
  unlocked
- Wired into XFCE as the lock command (`xflock4`, Super+L, lid close,
  idle timeout)
- Login screen stays `lightdm-gtk-greeter` (robust, light), restyled to match:
  same background, clock in its panel, a fixed verse drawn into the
  background image
- Possible extra if you want it: the same verse layout on the login screen
  as a custom LightDM greeter. Riskier, since a greeter crash means no login,
  so it would need an automatic fallback

**poetry.txt** (`/usr/share/sindhos/poetry.txt`, plain UTF-8, editable)
```
# verse lines (one or more), then a line starting with "— " for the poet
<verse line 1>
<verse line 2>
— شاهه عبداللطيف ڀٽائي
%
```
- Poets: Shah Abdul Latif Bhittai, Sachal Sarmast, Sami, and other classical
  poets who died long ago (e.g. Rohal Faqir, Bedil, Shah Inayat Rizvi).
  No modern copyrighted poetry
- Verses come from public-domain editions or freely licensed transcriptions,
  with each source noted in `CREDITS.md`. I won't write classical verses from
  memory, because the exact wording matters and I could misquote. Please
  proof-read the starter set (around 30–50 verses)
- Users can add their own verses. A file in `~/.local/share/sindhos/poetry.txt` is
  read too

**Test checklist:** Super+L locks · layout and RTL shaping look right ·
verse changes after N minutes · wrong password refused, right one unlocks ·
lid close / idle locks · RAM while locked at 1 GB.

---

## Phase 3 · Default wallpapers

- `/usr/share/backgrounds/sindhos/`, all listed in the XFCE wallpaper picker
- **Ajrak designs (original, made here):** 4–6 SVG designs generated from
  scratch with a script in `branding/ajrak/`: block-print style repeats in
  red, indigo, black and white. Exported to PNG at 1920×1080 and 1366×768,
  the screen size common on low-end laptops
- **Default wallpaper:** one of the ajrak designs (you choose from a preview
  sheet)
- **Photos:** Indus landscapes, Sindhi culture (e.g. Indus river, Keenjhar Lake,
  Kirthar range, Makli, Mohenjo-daro, Ranikot, Sufi shrines, ajrak printing).
  Only Wikimedia Commons or similar with **CC0, CC-BY or CC-BY-SA** licences;
  no NC/ND licences, no unclear sources
- `CREDITS.md`: file name, title, author, source URL, licence, changes made
  (crop/resize). CC-BY-SA photos stay under CC-BY-SA
- Size limit: photos as optimised JPEG at about 300–500 KB each, around 10–12
  photos, so the ISO grows by less than 10 MB

**Test checklist:** default is ajrak on desktop and login · all wallpapers appear
in Desktop Settings · nothing stretched at 1366×768 and 1920×1080 ·
CREDITS.md entries match the files.

---

## Phase 4 · Sindhi typing

**Keyboards**
- Standard Sindhi layout (XKB `pk(snd)` or the m17n Sindhi map; whichever one
  matches what Sindhi typists know, to confirm with you) plus the **Roman
  Sindhi** layout
- Roman Sindhi: `keyboard/layout.py` already holds a full layout from v0.1.
  If you send a newer one, it replaces that file and the generator rebuilds
  the input method and the keyboard guide
- Quick switch: keep Ctrl+Space (cycles English → Sindhi → Roman Sindhi)
  and the top-bar indicator

**Word suggestions**
- `ibus-typing-booster` (in Debian). It can run the m17n Roman Sindhi and
  Sindhi keyboards as its input method and add suggestions from a Hunspell
  dictionary, so typing and suggestions come from one engine. It also learns
  the words you use
- Cost: about 40–80 MB RAM (Python). If that is too much at 1 GB, it becomes
  opt-in and the plain m17n keyboards stay the default

**Spell check (red underline)**
- Step 1, research: Debian has no Sindhi Hunspell package. Check LibreOffice
  dictionaries, Mozilla add-ons, the Sindhi Language Authority, GitHub and
  academic word lists, and check each licence
- Step 2, if nothing usable and freely licensed exists: build `sd_PK.dic/.aff`
  from a freely licensed word list (e.g. Wikipedia/Wikisource Sindhi text
  frequency lists, Wiktionary, CC-licensed corpora). Add affix rules for
  common plural and case endings. Produce a report on weak spots: rare
  words, inflections not covered, spelling variants, names, Arabic/Persian
  loanwords, and words written with Urdu/Arabic letters (`ك ي ہ`
  instead of `ڪ ي ه`)
- Where it works:
  - LibreOffice: yes, red underline as you type (installed as a dictionary
    extension or system dictionary, language set to Sindhi)
  - Firefox: yes, through system Hunspell
  - GTK apps using gspell (Mousepad and others): yes
  - **Not truly system-wide.** Linux has no global spell check. Terminals
    and many apps won't underline. Suggestions from typing-booster do work
    everywhere you can type

**Grammar: what's realistic**
- There is no Sindhi grammar checker (LanguageTool has no Sindhi, and it's
  Java, too heavy anyway). A real one is a research project
- Possible and useful: a small set of **rule-based checks** in LibreOffice
  (autocorrect + a light checker extension): wrong look-alike letters
  (Arabic `ك`/`ى`, Urdu `ہ`/`ی`) → Sindhi `ڪ`/`ي`/`ه`, Latin
  punctuation in Sindhi text → `،` `۔` `؟`, doubled words, spaces
  before punctuation, common misspellings
- I'll say clearly in the phase report what got done and what's missing

**Test checklist:** each layout types correctly · Ctrl+Space cycles · suggestions
appear in Mousepad and Firefox · misspelled word underlined in LibreOffice,
Firefox, Mousepad · autocorrect fixes `ك`→`ڪ` · RAM with typing-booster at 1 GB.

---

## Phase 5 · Sindhi dictionary app (لغت)

- Small offline app, Python + GTK3, about 30 MB RAM, starts in under 1 second
- Search in Sindhi or English, as-you-type results, shows meaning(s), part of
  speech when known, and related forms
- **UI in Sindhi, right to left** (GTK RTL direction), English labels as an
  option; ajrak-accented, Naskh font
- Data: SQLite (`/usr/share/sindhos/dictionary.db`) built from the **same word
  list as the spell checker**, plus meanings from freely licensed sources
  (Wiktionary is CC-BY-SA; other sources only if the licence allows)
- Honest limit: the spell-check list will have far more words than there are
  free meanings for. Words without a meaning still show as "known word,
  no meaning yet", and the app can take user-added meanings (stored
  locally)
- Right-click "Look up" from selected text (via `xdg` / a keyboard shortcut)
  if it stays simple

**Test checklist:** search Sindhi and English · RTL layout · words with/without
meanings · startup time and RAM · user-added meaning survives reboot (installed).

---

## Phase 6 · Apps with a Sindhi touch

**Web browser**
- Recommended: **keep Firefox ESR**, tuned for low RAM (fewer content
  processes, no telemetry/Pocket, smaller cache). The "lighter" browsers in
  Debian (Falkon/QtWebEngine, Epiphany/WebKitGTK) use about the same RAM on
  real sites, have weaker Sindhi spell-check support, and don't match the
  GTK theme as well
- Sindhi fonts preferred for Arabic script (fontconfig + Firefox prefs)
- Sindhi spell check from Phase 4 on by default
- **Sindhi start page**: local HTML file, ajrak style, clock and date in
  Sindhi, the verse of the day, a search box, shortcuts (Sindhi Wikipedia,
  news, dictionary app). No tracking, works offline

**Office, calculator, PDF**
- LibreOffice Writer, Calc, Impress with the GTK3 back end (no Base/Draw/Java),
  Sindhi set as a CTL language, Sindhi spell check, Lateef as default
  complex-text font. Adds about 250–300 MB to the ISO (disk only; RAM only
  while open)
- Calculator: `galculator` (already in)
- PDF viewer: **Atril** (GTK3, light, matches the theme, can search Arabic-script
  text)

**Same look everywhere**
- Ajrak accents, Sindhi fonts and the topi icon in every app above
- Sindhi UI labels where translations exist: check coverage for LibreOffice,
  XFCE and Firefox (`sd` translations are partial or missing in many
  projects) and report it. Turn on whatever exists in a Sindhi session

**Test checklist:** start page · Sindhi typing + underline in Firefox and Writer ·
open a Sindhi PDF and search it · theme consistency screenshots · idle RAM and
RAM with Firefox + Writer open at 1 GB and 2 GB.

---

## Questions to settle when each phase starts

| When | Question |
|---|---|
| Phase 0 | OK to add the one sudoers line for the build wrapper (or use another build option)? |
| Phase 1 | Keep live user `sindhi`? Version number for this release (suggest 0.2)? |
| Phase 2 | xsecurelock-based lock screen as recommended, or also try a custom login greeter? |
| Phase 3 | Pick the default ajrak design from the preview sheet |
| Phase 4 | Is `keyboard/layout.py` your Roman Sindhi layout, or will you send a new one? Which standard Sindhi layout do you use? |
| Phase 6 | Firefox ESR (recommended) vs. a different browser |
