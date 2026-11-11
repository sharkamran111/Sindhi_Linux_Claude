# SindhOS Roadmap · سنڌ او ايس

SindhOS (formerly "Sindhi Linux") is a light Debian 13 live/installable system
with Sindhi built in. This file plans the next six phases.

**Target hardware:** everyday PCs: **minimum 2 GB RAM, recommended 4 GB**.
Idle desktop target: **under 600 MB**. (Changed 2026-11-11; earlier phases
aimed at 1–2 GB, their measurements below are kept as history.) Every choice below is
checked against that.

**Working rules**
- One phase at a time. Nothing is built until "start phase N".
- At the end of each phase: build the ISO, boot it in QEMU (at **2 GB and 4 GB**
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

### RAM budget (minimum 2 GB, recommended 4 GB)

| Item | Rough RAM | Note |
|---|---|---|
| XFCE session + taskbar + IBus | ~540 MB (measured, Phase 1) | target: idle desktop **under 600 MB** |
| Live overlay (tmpfs) | grows with use | live session only |
| Firefox ESR, a few tabs | 300–600 MB | |
| LibreOffice Writer | 150–250 MB | only while open |
| Roman Sindhi engine | 25–35 MB | Phase 1 |
| ibus-typing-booster | 40–80 MB | Phase 4, if used |

Expectation: **2 GB runs the desktop, typing, office and a browser; 4 GB is
comfortable.** Each phase measures idle RAM with `tools/ram-check.py` at 2 GB
and boot-tests at 2 GB and 4 GB. No more optimising for 1 GB.

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
  `9500-sindhos-icon-caches` (costs 9 MB disk); checked in a rebuilt ISO.

**Phase 0 baseline (v0.1 content, 2026-11-11 build, measured in QEMU):**

| | 1 GB | 2 GB |
|---|---|---|
| Idle desktop (`ram-check`) | 619 MB used, 347 MB available, no OOM | — |
| Desktop + Mousepad + terminal | — | 726 MB used, 1,246 MB available |
| Desktop + Firefox (keyboard guide) + Mousepad + terminal | 941 MB used, **26 MB available** | fine |
| Build time (packages cached, zstd) | 15 min | |
| ISO size | 1.7 GB | |

- Optional, not planned: the initrd is 140 MB (202 MB unpacked is firmware
  for AMD/NVIDIA GPUs and server network cards); trimming it would speed up
  boot from USB a little
- Idle desktop was 620 MB at Phase 0 and is 539 MB after Phase 1, within the
  new 600 MB target
- Mousepad's monospace font draws ڌ and ٻ so they look like ت and ب (the
  typed bytes are correct). Fix the monospace fallback in Phase 4

Build speed: dpkg runs under `eatmydata` inside the image (no fsync, big
win on a hard disk), and downloaded packages are kept between builds.

Security note on `--passwordless`: the build runs hooks from this repo as
root, so a password-free build means anything running as your user can get
root through it. Fine on a personal build PC; skip the flag on a shared one.

---

## Phase 1 · Branding: SindhOS everywhere

**Status (2026-11-11):** design direction **C "Sindh Taskbar"** chosen and
built. SindhOS rename and design C tested in QEMU: boot menu, splash, login
screen, About (SindhOS 0.2), installer branding, menu, taskbar dock all OK.
Idle RAM 539 MB (target under 600 MB).

Roman Sindhi engine: **written and tested live in the ISO** (injected into a
running session): `sindhi boli asaan jee sunyaaNap aahe.` → سنڌي ٻولي اسان جي
سڃاڻپ آهي۔ with a numbered candidate list, choices remembered, about 35 MB RAM.
Word list: 62,048 words from Sindhi Wikipedia (CC BY-SA 4.0). Spelling rules
are still the draft in `keyboard/roman/rules.py`, waiting for your
corrections (`keyboard/ROMAN-RULES-DRAFT.md`).

Fixes after your QEMU test (2026-11-11), each checked live in QEMU: dock
icons 30 px with a red bar under open apps (nothing cut off), seamless
opaque taskbar, time zone Asia/Karachi (live, installed, installer), one
keyboard indicator (the "Sindhi" label was the log-out button showing the
user name; now a single icon), keyboards named "Roman Sindhi" and "Sindhi"
(both served by the SindhOS engine; ibus-m17n removed), topi menu button on
a cream tile at 28 px, wallpaper medallion above the taskbar.

Roman Sindhi tuned for WhatsApp-style typing (plain letters, unreliable vowel
length): vowel-tolerant matching, ch = چ/ڇ, nj read both ways, written forms
kept (ڀاءُ). Your 21 examples are test cases (`keyboard/roman/test_examples.py`):
17 come out first from the rules alone, all 21 with the everyday-words list
(`keyboard/roman/data/everyday.tsv`); 35 common words also first.

Phase 1 test of the 2026-11-11 build (QEMU, 2 GB and 4 GB): all boot-test
steps pass at both sizes, no out-of-memory kills. Found and fixed (needs one
more build):
- Ctrl+Space only flipped between the last two keyboards (IBus behaviour), so
  "Sindhi" wasn't reachable by tapping. Now Ctrl+Space runs
  `sindhos-next-keyboard`: English → Roman Sindhi → Sindhi → English (checked
  live); Alt+Shift stays IBus's quick flip
- Idle RAM was 611 MB at 2 GB (680 MB at 4 GB, where the kernel itself uses
  more), over the 600 MB target. IBus's emoji helper (24 MB) is now off; live
  test: −52 MB. Expected about 560–590 MB at 2 GB, to be confirmed
- Your own test: the IBus tray menu didn't close on an outside click and its
  labels repeated ("Sindhi - Sindhi"). IBus's tray icon is now hidden; the
  taskbar shows SindhOS's own indicator (xfce4-genmon-plugin) reading
  سنڌي / Roman Sindhi / English, and a click opens a plain GTK menu that
  closes on an outside click (checked live)
- New topi (approved 2026-11-11): original 3/4-view Sindhi topi drawn by
  `branding/topi/gen_topi.py` (arched front, maroon/navy, white dots, star
  medallion, diamond/cross patterns). Used only as the menu button, on a
  cream tile, bottom-left like the Windows Start button; boot menu, splash,
  About and installer keep the ajrak emblem

**Phase 1 final test (build of 2026-11-11 17:34, QEMU 2 GB and 4 GB): all
passed.** Idle RAM 592 MB at 2 GB (target under 600 MB, 8 MB to spare;
668 MB at 4 GB, where the kernel's own tables grow with RAM). Ctrl+Space
cycles English → Roman Sindhi → Sindhi in the real build (typed سنڌي ٻولي سنڌي,
bytes checked); taskbar label سنڌي / Roman Sindhi / English; keyboard menu
closes on an outside click; IBus emoji helper off; time zone PKT; topi menu
button bottom-left. If more memory headroom is wanted: Thunar's background
daemon (7 MB), IBus XIM bridge for old X11 apps (10 MB), light-locker (6 MB,
replaced in Phase 2).

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

**Look and feel: SindhOS's own identity (replaces the Mac-style look)**

Your feedback after Phase 0: the WhiteSur look reads as a cheap macOS copy.
Goal: clean, modern, premium, recognisably SindhOS.
- Window buttons **top right**, in the order minimize, maximize, close, drawn
  as **– □ ×**. Our own xfwm4 window theme, original artwork
- GTK theme: **adw-gtk3** (LGPL, the modern GNOME look ported to GTK3, made
  for recolouring) as the base, with a small SindhOS layer on top: ajrak
  palette, Inter + Lateef fonts, rounded corners, quiet shadows. WhiteSur is
  removed
- Dock: Plank is replaced by an **xfce4-panel dock with the docklike plugin**
  (Debian package): one less program, no `bamfdaemon`, about 25 MB less RAM,
  styled by the same theme
- Ajrak colours as accents only (selection, focus, active indicators, menu
  button, thin ajrak band where it fits), never whole surfaces of pattern
- **Before applying: 2–3 design directions with real screenshots.** They are
  previewed on the running ISO in QEMU (themes copied in over the network from
  this PC), so the screenshots show the real system, not drawings. You pick
  one, then it becomes the default in the ISO
- Palette: deep red `#9B1B1E`, indigo `#1F2A5A`, black `#141414`,
  white/cream `#F6F1E7`, recorded in `branding/palette.md`, used for greeter,
  Plymouth, boot menu, panel, menu, terminal colours

**Keyboard: Roman Sindhi transliteration (Gboard-style)**

Your feedback: type `sindhi boli` in English letters, get سنڌي ٻولي, with a
choice when a Roman spelling matches more than one Sindhi word. Keep the
current key-by-key layout as a second option.

What's realistic: Gboard uses large language models trained on huge amounts
of text. We can't match that offline on an everyday PC, but a **rules + word list**
engine gets common words right and offers candidates for the rest:
1. Each Roman word is looked up in an index of Sindhi words by their possible
   Roman spellings (`sindhi` → سنڌي, سنڌي ۽ …; `boli` → ٻولي, بولي), ranked by
   how common the word is
2. Words not in the list fall back to letter rules (`dh` → ڌ, `bb` → ٻ …), so
   you can always type anything, including names
3. Your choices are remembered, so the word you pick moves to the top
4. Space or punctuation commits the first candidate; number keys or arrows
   pick another one

Engine: **our own small IBus engine in Python** (`ibus-sindhos-roman`, about
25–35 MB RAM while in use). Why not the ready-made ones:
- `ibus-typing-booster` suggests words that start with what was already
  converted. It can't search "all Sindhi words whose Roman spelling is `boli`",
  which is the core of this feature
- `ibus-table` can map a Roman key to words, but has no letter-rule fallback
  for words that aren't in its table

Quality depends on the Roman spelling rules (you offered to help with
ڌ ٻ ڄ ڃ ڳ ڱ ڪ) and on the word list. Phase 1 starts with a draft rule table
for you to correct and a starter word list; Phase 4 grows the same word list
for spell checking and suggestions.

Switching: Ctrl+Space between **English / Roman Sindhi / Sindhi (key-by-key)**.
IBus's own Ctrl+Space toggles between the last two methods on a quick tap and
steps through all of them while Ctrl is held; whether that feels right gets
tested, otherwise a small switcher cycles the three in fixed order. The
top-bar indicator shows EN / سنڌي / س.

**Test checklist (to hand over):** boot menu says SindhOS · splash · login screen
· About dialog · `cat /etc/os-release` · topi in the start button · window
buttons – □ × top right · new dock · ajrak accents in a settings dialog ·
installer shows SindhOS · `sindhi boli` → سنڌي ٻولي with candidates · Ctrl+Space
through English / Roman Sindhi / Sindhi · idle RAM under 600 MB.

---

## Phase 2 · Lock screen with Sindhi poetry

**Layout:** big clock and date on the left. On the right, a Sindhi verse in a
Naskh font (Lateef or Scheherazade, decided by on-screen test), right to left,
right-aligned, with the poet's name below. Ajrak background, dimmed for
readability. A new random verse every few minutes (default 5, configurable).

**Choosing the lock screen.** XFCE's stock options (`light-locker`
→ `lightdm-gtk-greeter`, `xfce4-screensaver`) can't show this layout. HTML greeters
(web-greeter, nody-greeter) can, but they are not in Debian and need a
WebKit/Electron engine, too heavy for a lock screen.

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
lid close / idle locks · RAM while locked at 2 GB.

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
- Roman Sindhi transliteration and the key-by-key layout come in Phase 1
  (see there). Phase 4 adds the standard Sindhi layout (XKB `pk(snd)` or
  the m17n Sindhi map, whichever Sindhi typists know, to confirm with you)
  and grows the shared word list

**Word suggestions**
- `ibus-typing-booster` (in Debian). It can run the m17n Roman Sindhi and
  Sindhi keyboards as its input method and add suggestions from a Hunspell
  dictionary, so typing and suggestions come from one engine. It also learns
  the words you use
- Cost: about 40–80 MB RAM (Python), fine within the 2 GB minimum

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
Firefox, Mousepad · autocorrect fixes `ك`→`ڪ` · idle RAM still under 600 MB.

---

## Phase 5 · Education (تعليم): four apps in the topi menu

*Plan only (2026-11-11), not started. Replaces the earlier "dictionary app"
phase; the dictionary is now app 5a.*

An **Education** section in the topi menu with four apps:

| App | Sindhi name | What it does |
|---|---|---|
| Sindhi Dictionary | سنڌي لغت | search in Sindhi, Roman Sindhi or English, show meanings |
| Learning Library | علمي ڪتبخانو | starts with Shah Jo Risalo: browse by Sur, read, search |
| Sindhi Exercise Book | سنڌي مشق ڪتاب | alphabet with sounds, letter shapes, words, quizzes, progress |
| Sindhi Grammar | سنڌي گرامر | lessons on nouns, gender, plurals, verbs, tenses, with exercises |

(The Sindhi names are my drafts; please correct them.)

### Shared rules and technology

- **Offline, light, one toolkit:** each app is a small Python + GTK3 program
  (Python, PyGObject and GTK3 are already in the image), about 30–40 MB of
  RAM while open and **nothing when closed**. Idle desktop stays under
  600 MB. No web engine, no Electron
- **Look:** the SindhOS theme, Lateef / Scheherazade for Sindhi text,
  right-to-left layout in Sindhi mode, ajrak-red accents
- **Language:** Sindhi interface by default, English as an option (one
  setting shared by all four apps)
- **Data:** read-only SQLite files in `/usr/share/sindhos/education/`; your
  progress and notes in `~/.local/share/sindhos/`
- **Audio:** small Ogg Opus files, played with PipeWire (`pw-play`), which is
  already installed. About 10–15 KB per sound
- **Menu:** apps carry `Categories=Education;` and a SindhOS sub-menu, so they
  show up together under Education. The Sindhi Keyboard Guide moves there too

### 5a · Sindhi Dictionary: what's realistic

- **Search:** works immediately for all 62,000 words of the keyboard word
  list, typed in Sindhi or Roman Sindhi (using the same engine as the
  keyboard: `pani` finds پاڻي)
- **Meanings are the hard part.** The word list has no meanings. Freely
  licensed sources:
  - Wiktionary: only **1,735 Sindhi entries** (CC BY-SA). Good start, small
  - **Public-domain dictionaries, scanned on archive.org:** George Stack,
    *Dictionary English and Sindhi* (1849) and *Sindhi and English* (1855);
    George Shirt et al., *A Sindhi-English Dictionary* (1879). Large, but
    19th-century English and some old spellings, and they're scans: turning
    them into text needs OCR plus proof-reading, a long project. Plan: do it
    letter by letter, the most common words first
  - Your own meanings: the app lets you add or correct a meaning; these can
    be collected into the next release
- **Honest expectation for version 1:** every word findable, English meanings
  for a few thousand common words, growing over time

### 5b · Learning Library: Shah Jo Risalo

- **Source I'd use:** Ernest Trumpp's edition, *The Diwan of Abd-ul-Latif
  Shah, known by the name of Shaha jo Risalo* (Leipzig, 1866). Public domain
  (published 1866, Trumpp died 1885), scanned on archive.org
  (`the-diwan-of-abd-ul-latif-shah-known-by-the-name-of-shaha-jo-risalo`)
- **Caveats:** it's the first printed edition and scholars consider it
  incomplete, with some readings later corrected. The better scholarly
  edition is Hotchand Gurbakhshani's (1923–1931; he died 1947, so it's
  public domain in Pakistan and India), but I found no scan of it on
  archive.org. If you have or can find a scan of Gurbakhshani, I'd use that
  instead. Later editions (Kalyan Advani 1958, Elsa Kazi's translations,
  Agha, Qazi) are still under copyright
- **How the text gets in:** there's no clean digital public-domain text. Plan:
  one Sur at a time, I prepare the text from the scan (OCR for Sindhi Naskh is
  weak, so expect manual work), you proof-read against the scan, then it
  goes in. Nothing typed from memory
- **App:** list of Surs, verses in large Naskh RTL, search (Sindhi or Roman
  Sindhi), bookmarks, font size. Translations only from public-domain or
  your own sources
- **First release:** one or two short Surs, fully proof-read, rather than
  everything half-checked

### 5c · Sindhi Exercise Book: what's realistic

- **Alphabet:** all 52 letters, tap to hear the sound, its name, and its
  shapes (isolated, initial, medial, final, drawn by the font itself, so no
  artwork needed), with an example word
- **Simple words** with picture-free cards (word, Roman spelling, meaning,
  sound), then **small quizzes** (hear and pick the letter, match shapes,
  build a word) and **progress** per lesson, saved locally
- **Audio:**
  - Best: **your recordings.** 52 letters + about 200 starter words. I'll add a
    small recording helper: it shows each item, you press a key, it records,
    trims silence and saves Ogg Opus. Roughly 1–2 hours of your time. Total
    size about 4 MB
  - Fallback: eSpeak NG has a Sindhi voice (offline, free) but sounds
    robotic. OK for testing, not good for learners
- **Content needed from you:** the recordings, a check of the letter names in
  Sindhi, the example word per letter, the starter word list

### 5d · Sindhi Grammar: what's realistic

- I can build the lesson app and the exercise types (fill the gap, choose
  the right form, make the plural), but **the grammar content has to come
  from you or be checked by you.** I won't write Sindhi grammar rules from
  memory as fact
- Public-domain reference: Ernest Trumpp, *Grammar of the Sindhi Language*
  (1872), scanned on archive.org. Scholarly and in English, useful for
  checking, not as lesson text
- **Content needed from you:** for each lesson (nouns, gender, plurals,
  verbs, tenses), a short explanation, 5–10 examples and the exercise
  answers. I can draft the structure and examples for you to correct

### Order and small phases

| Step | What | Needs from you |
|---|---|---|
| **5a.1** (build first) | Dictionary: search in Sindhi/Roman/English, Wiktionary meanings, add-your-own meanings | nothing to start |
| 5c.1 | Exercise Book: alphabet with sounds and shapes, progress | 52 recordings, letter names check |
| 5b.1 | Library app + first Sur (proof-read) | proof-reading; a Gurbakhshani scan if available |
| 5c.2 | Exercise Book: words and quizzes | ~200 word recordings |
| 5d.1 | Grammar: nouns and gender lessons | lesson content / corrections |
| 5a.2, 5b.2, 5d.2 … | more meanings (from Stack/Shirt), more Surs, more grammar | proof-reading |

Why the dictionary first: it can be useful on day one without new content,
reuses the word list and Roman engine already built, and its "add a meaning"
feature starts collecting the data the other apps need.

**Test checklist (per step):** works with networking off · Sindhi and English
interface · RTL text and Naskh font correct · sounds play · progress
survives a reboot (installed system) · idle RAM unchanged, app RAM under 50 MB.

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
RAM with Firefox + Writer open at 2 GB and 4 GB.

---

## Questions to settle when each phase starts

| When | Question |
|---|---|
| Phase 0 | OK to add the one sudoers line for the build wrapper (or use another build option)? |
| Phase 1 | Keep live user `sindhi`? Version number (suggest 0.2)? Pick a design direction. Correct the draft Roman spelling rules |
| Phase 2 | xsecurelock-based lock screen as recommended, or also try a custom login greeter? |
| Phase 3 | Pick the default ajrak design from the preview sheet |
| Phase 4 | Is `keyboard/layout.py` your Roman Sindhi layout, or will you send a new one? Which standard Sindhi layout do you use? |
| Phase 5 | Correct the Sindhi app names; a Gurbakhshani scan if you have one; recordings (52 letters first) |
| Phase 6 | Firefox ESR (recommended) vs. a different browser |
