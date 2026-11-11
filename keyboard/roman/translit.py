#!/usr/bin/env python3
"""Roman Sindhi -> Sindhi conversion: word-list lookup plus letter fallback.

  translit.py build WORDS.tsv INDEX.sqlite     build the lookup index
  translit.py query INDEX.sqlite sindhi boli   show candidates per word

How it works
  * Every Sindhi word gets a *class key*: its consonant sound classes, without
    vowels (Sindhi usually doesn't write short vowels) and without the
    difference between e.g. ب/ٻ or د/ڏ/ڊ. سنڌي -> s.n.dh
  * Roman input gets the same kind of key: sindhi -> s.n.dh
  * All words with that key are candidates, ranked by how close their
    Roman spelling is to what was typed and by how common they are.
  * A letter-by-letter conversion is always offered too, for names and words
    that aren't in the list.
Spelling rules live in rules.py. Only the Python standard library is used.
"""
import difflib
import math
import os
import sqlite3
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import rules  # noqa: E402

TATWEEL = "ـ"


# ------------------------------------------------------------- Sindhi side

def normalise(word):
    """Normalise look-alike Urdu/Arabic letters, drop tatweel and vowel marks."""
    out = []
    for ch in word:
        ch = rules.NORMALISE.get(ch, ch)
        if ch == TATWEEL or ch in rules.MARKS:
            continue
        out.append(ch)
    return "".join(out)


def sd_key(word):
    """Class key of a Sindhi word, e.g. سنڌي -> 's.n.dh'."""
    classes = []
    prev = ""
    for ch in word:
        if ch in ("ه", "ھ") and prev in rules.ASPIRATE_AFTER:
            classes[-1] = rules.ASPIRATE_AFTER[prev]
        elif ch in rules.LETTERS:
            cls = rules.LETTERS[ch][0]
            if not classes or classes[-1] != cls:
                classes.append(cls)
        prev = ch
    return ".".join(classes)


INITIAL_VOWEL = set("اآأإعءئ")


def sd_roman(word):
    """Comparison form of a Sindhi word: consonants as plain Roman letters,
    written vowels as A (ا) I (ي) O (و), a word-initial vowel as V.
    e.g. اسان -> VsAn, گهر -> ghr, پاڻي -> pAnI"""
    out = []
    for i, ch in enumerate(word):
        if i == 0 and ch in INITIAL_VOWEL:
            out.append("V")
        elif ch in rules.LETTERS:
            out.append(rules.LETTERS[ch][0])          # sound class: b, dh, kh ...
        elif ch in ("ا", "آ", "أ"):
            out.append("A")
        elif ch in ("ي", "ى", "ی", "ئ", "ے"):
            out.append("y" if i == 0 else "I")
        elif ch in ("و", "ؤ"):
            out.append("w" if i == 0 else "O")
        elif ch == "۽":
            out.append("V")
    return _collapse("".join(out))


def _collapse(s):
    out = []
    for c in s:
        if not out or out[-1] != c:
            out.append(c)
    return "".join(out)


# -------------------------------------------------------------- Roman side

def roman_norm(s):
    """Loose form of typed Roman, used to remember the user's choices."""
    return _collapse(clean(s).lower().replace("'", ""))


def roman_form(typed, long_a=False):
    """Comparison form of typed Roman, matching sd_roman():
    sindhi -> sndhI, asaan -> VsAn, ghar -> ghr, paani -> pAnI.
    long_a=True reads a medial single 'a' as ا (common in names: Kamran)."""
    s = clean(typed).lower().replace("'", "")
    for a, b in (("x", "kh"), ("q", "k"), ("v", "w")):
        s = s.replace(a, b)
    s = "".join(("ch" if c == "c" and s[i + 1:i + 2] != "h" else c) for i, c in enumerate(s))
    s = s.replace("aa", "A").replace("ee", "I").replace("oo", "O")
    out = []
    n = len(s)
    for i, c in enumerate(s):
        first, last = i == 0, i == n - 1
        if c in "aeiouAIO":
            if first:
                out.append("V")
            elif last:
                out.append({"a": "A", "e": "I", "i": "I", "o": "O", "u": "O"}.get(c, c))
            elif c in "eIo O".replace(" ", ""):
                out.append({"e": "I", "o": "O"}.get(c, c))
            elif c == "A" or (c == "a" and long_a):
                out.append("A")
            # medial short a / i / u: not written in Sindhi
        elif c == "y":
            out.append("y" if first else "I")
        elif c == "w":
            out.append("w" if first else "O")
        else:
            out.append(c)
    return _collapse("".join(out))


def clean(s):
    """Lower-case everything except the capitals that mean retroflex."""
    return "".join(c if c in rules.MEANINGFUL_CAPITALS else c.lower() for c in s)


def _tokens(s):
    s = clean(s)
    i, toks = 0, []
    while i < len(s):
        for tok, cls in rules.ROMAN_TOKENS:
            if s.startswith(tok, i):
                toks.append((tok, cls))
                i += len(tok)
                break
        else:
            i += 1                      # unknown character: ignore
    return toks


def roman_keys(s):
    """Class keys for Roman input. 'ng' is read both as ن+گ and as ڱ."""
    variants = {s}
    if "ng" in s:
        variants.add(s.replace("ng", "N"))
    keys = set()
    for v in variants:
        classes = []
        for _tok, cls in _tokens(v):
            if cls and (not classes or classes[-1] != cls):
                classes.append(cls)
        keys.add(".".join(classes))
    return keys


def fallback(s):
    """Letter-by-letter Roman -> Sindhi, for words not in the word list."""
    s = clean(s)
    out = []
    i = 0
    n = len(s)
    while i < n:
        rest = s[i:]
        start = i == 0
        # vowels
        for v, init, mid, end in (("aa", "آ", "ا", "ا"), ("ee", "اي", "ي", "ي"), ("oo", "او", "و", "و"),
                                  ("ai", "اي", "ي", "ي"), ("au", "او", "و", "و"),
                                  ("a", "ا", "", "ا"), ("e", "اي", "ي", "ي"), ("i", "ا", "", "ي"),
                                  ("o", "او", "و", "و"), ("u", "ا", "", "و")):
            if rest.startswith(v):
                last = i + len(v) >= n
                out.append(init if start else (end if last else mid))
                i += len(v)
                break
        else:
            for tok, sd in rules.FALLBACK:
                if rest.startswith(tok):
                    out.append(sd)
                    i += len(tok)
                    break
            else:
                i += 1
    return "".join(out)


def similarity(typed, word_roman):
    """0..1: how close the typed Roman is to a word's comparison form."""
    strict = difflib.SequenceMatcher(None, roman_form(typed), word_roman).ratio()
    loose = difflib.SequenceMatcher(None, roman_form(typed, long_a=True), word_roman).ratio()
    return max(strict, 0.97 * loose)


# ------------------------------------------------------------------ index


SCHEMA = """
CREATE TABLE words (word TEXT PRIMARY KEY, key TEXT NOT NULL, roman TEXT NOT NULL, freq INTEGER NOT NULL);
CREATE INDEX words_key ON words(key);
"""


def build(tsv, db):
    if os.path.exists(db):
        os.remove(db)
    con = sqlite3.connect(db)
    con.executescript(SCHEMA)
    rows = {}
    with open(tsv, encoding="utf-8") as f:
        for line in f:
            if not line.strip() or line.startswith("#"):
                continue
            word, _, freq = line.rstrip("\n").partition("\t")
            word = normalise(word.strip())
            if not word:
                continue
            rows[word] = rows.get(word, 0) + int(freq or 1)
    con.executemany("INSERT INTO words VALUES (?,?,?,?)",
                    ((w, sd_key(w), sd_roman(w), fq) for w, fq in rows.items()))
    con.commit()
    con.execute("VACUUM")
    con.close()
    return len(rows)


class Index:
    def __init__(self, db, user_db=None):
        self.con = sqlite3.connect(f"file:{db}?mode=ro", uri=True) if db and os.path.exists(db) else None
        self.user = None
        if user_db:
            os.makedirs(os.path.dirname(user_db), exist_ok=True)
            self.user = sqlite3.connect(user_db)
            self.user.execute("CREATE TABLE IF NOT EXISTS picks (roman TEXT, word TEXT, n INTEGER, "
                              "PRIMARY KEY (roman, word))")

    def _user_counts(self, typed):
        if not self.user:
            return {}
        rows = self.user.execute("SELECT word, n FROM picks WHERE roman=?", (roman_norm(typed),))
        return dict(rows.fetchall())

    def learn(self, typed, word, weight=1):
        """Remember a commit: weight 1 for the default word, 3 for a word the
        user picked from the list (so a deliberate choice wins next time)."""
        if self.user:
            self.user.execute("INSERT INTO picks VALUES (?,?,?) ON CONFLICT(roman, word) DO UPDATE SET n=n+?",
                              (roman_norm(typed), word, weight, weight))
            self.user.commit()

    def candidates(self, typed, limit=9, prefix=True):
        """Sindhi candidates for one Roman word, best first."""
        scored = {}
        if self.con:
            keys = roman_keys(typed)
            for key in keys:
                for word, roman, freq in self.con.execute(
                        "SELECT word, roman, freq FROM words WHERE key=? ORDER BY freq DESC LIMIT 200", (key,)):
                    s = 5.0 * similarity(typed, roman) + 0.35 * math.log10(freq + 1)
                    scored[word] = max(scored.get(word, -9), s)
                if prefix and key:
                    for word, roman, freq in self.con.execute(
                            "SELECT word, roman, freq FROM words WHERE key>? AND key<? ORDER BY freq DESC LIMIT 30",
                            (key + ".", key + "/")):   # "/" sorts right after "."
                        sim = similarity(typed, roman)
                        if sim >= 0.75:                 # only close completions
                            scored.setdefault(word, 3.0 * sim + 0.35 * math.log10(freq + 1) - 1.0)
        for i, word in enumerate(rules.SPECIAL.get(clean(typed), [])):
            scored[word] = max(scored.get(word, -9), 6.0 - i)
        for word, n in self._user_counts(typed).items():
            scored[word] = scored.get(word, 0) + 1.0 + 0.8 * n
        fb = fallback(typed)
        ranked = sorted(scored, key=lambda w: -scored[w])[:limit]
        if fb and fb not in ranked:
            # the letter-by-letter spelling: first if nothing matched well
            if not ranked or scored[ranked[0]] < 4.0:
                ranked.insert(0, fb)
            else:
                ranked.append(fb)
        return ranked[:limit]


def main():
    if len(sys.argv) >= 4 and sys.argv[1] == "build":
        n = build(sys.argv[2], sys.argv[3])
        print(f"indexed {n} words -> {sys.argv[3]}")
    elif len(sys.argv) >= 4 and sys.argv[1] == "query":
        idx = Index(sys.argv[2])
        for w in sys.argv[3:]:
            print(f"{w:12} {' '.join(idx.candidates(w))}")
    else:
        sys.exit(__doc__)


if __name__ == "__main__":
    main()
