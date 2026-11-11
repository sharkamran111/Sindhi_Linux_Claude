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

def normalise_letters(word):
    """Normalise look-alike Urdu/Arabic letters and drop tatweel; keep vowel
    marks (the written form, e.g. ڀاءُ لاءِ)."""
    return "".join(rules.NORMALISE.get(ch, ch) for ch in word if ch != TATWEEL)


def normalise(word):
    """normalise_letters() and also drop vowel marks: the form used to group
    spellings of one word (ڀاءُ and ڀاء are the same word)."""
    return "".join(ch for ch in normalise_letters(word) if ch not in rules.MARKS)


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
    # ambiguous pairs, read both ways: ng = ڱ or ن+گ, nj/ny = ڃ or ن+ج/ن+ي
    for pair, one in (("ng", "\x01"), ("nj", "\x02"), ("ny", "\x02")):
        for v in list(variants):
            if pair in v:
                variants.add(v.replace(pair, one))
    keys = set()
    for v in variants:
        classes = []
        for _tok, cls in _tokens(v.replace("\x01", "N").replace("\x02", "N")):
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


# ---- vowel-tolerant matching ----------------------------------------------
# WhatsApp-style Roman Sindhi doesn't mark vowel length reliably: "kaam" can be
# ڪم, "asan" is اسان. Typed letters are aligned with the Sindhi word; vowels
# may be written or not at a small cost, consonants must agree. Word-initial
# and final vowels cost more to leave out: Sindhi always writes those.

_VOWELS = [("aa", "A", True), ("ee", "I", True), ("oo", "O", True), ("ai", "I", True), ("au", "O", True),
           ("a", "A", False), ("e", "I", True), ("i", "I", False), ("o", "O", True), ("u", "O", False),
           ("y", "I", True), ("w", "O", True)]
_WORD_VOWEL = {"ا": "A", "آ": "A", "أ": "A", "إ": "I", "ي": "I", "ى": "I", "ی": "I", "ئ": "I", "ے": "I",
               "و": "O", "ؤ": "O", "ع": "E", "ء": "E", "۽": "I"}
_MARK_VOWEL = {"\u064e": "A", "\u0650": "I", "\u064f": "O"}


def typed_seq(typed):
    """[(kind, value, long)] kind C = consonant class, V = vowel."""
    s = clean(typed).replace("'", "")
    out, i = [], 0
    while i < len(s):
        for v, kind, long_ in _VOWELS:
            if s.startswith(v, i) and s[i].lower() in "aeiouyw":
                out.append(("V", kind, long_))
                i += len(v)
                break
        else:
            for tok, cls in rules.ROMAN_TOKENS:
                if cls and s.startswith(tok, i):
                    if not (out and out[-1][:2] == ("C", cls)):        # doubled letter
                        out.append(("C", cls, tok.lower()))
                    i += len(tok)
                    break
            else:
                i += 1
    return out


def word_seq(word):
    out, prev = [], ""
    for ch in word:
        if ch in ("ه", "ھ") and prev in rules.ASPIRATE_AFTER and out:
            out[-1] = ("C", rules.ASPIRATE_AFTER[prev], prev + "ه")
        elif ch in rules.LETTERS:
            cls = rules.LETTERS[ch][0]
            if not (out and out[-1][:2] == ("C", cls)):
                out.append(("C", cls, ch))
        elif ch in _WORD_VOWEL:
            out.append(("V", _WORD_VOWEL[ch], True))
        elif ch in _MARK_VOWEL:
            out.append(("V", _MARK_VOWEL[ch], False))        # written mark: optional
        prev = ch
    return out


def match_cost(typed, word):
    """Alignment cost between typed Roman and a Sindhi word (0 = perfect)."""
    t, w = typed_seq(typed), word_seq(word)
    n, m = len(t), len(w)

    def drop_typed(i):           # typed vowel/consonant with nothing in the word
        kind, _v, long_ = t[i]
        long_ = bool(long_)
        if kind == "C":
            return 1.5
        if i == 0:
            return 1.0
        if i == n - 1:
            return 0.9
        return 0.35 if long_ else 0.0       # short a/i/u: often not written

    def drop_word(j):            # word letter that wasn't typed
        kind, v, written = w[j]
        if kind == "C":
            return 1.5
        if not written:
            return 0.05
        if v == "E":
            return 0.15
        if j == 0:
            return 1.0
        if j == m - 1:
            return 0.9
        return 0.35

    def pair(i, j):
        a, b = t[i], w[j]
        if a[0] != b[0]:
            return 9.0
        if a[0] == "C":
            if a[1] != b[1]:
                return 1.2
            spellings = [x.lower() for x in rules.LETTERS.get(b[2], ("", [a[2]]))[1]]
            return 0.0 if a[2] in spellings else 0.25     # e.g. typed k for ق: possible, q is better
        if a[1] == b[1]:
            return 0.0
        if b[1] == "E":
            return 0.3                      # ع / ء for a typed vowel: possible, not free
        return 0.5

    INF = 1e9
    d = [[INF] * (m + 1) for _ in range(n + 1)]
    d[0][0] = 0.0
    for i in range(n + 1):
        for j in range(m + 1):
            c = d[i][j]
            if c >= INF:
                continue
            if i < n and j < m:
                d[i + 1][j + 1] = min(d[i + 1][j + 1], c + pair(i, j))
            if i < n:
                d[i + 1][j] = min(d[i + 1][j], c + drop_typed(i))
            if j < m:
                d[i][j + 1] = min(d[i][j + 1], c + drop_word(j))
    return d[n][m]


# ------------------------------------------------------------------ index


SCHEMA = """
CREATE TABLE words (word TEXT PRIMARY KEY, key TEXT NOT NULL, roman TEXT NOT NULL, freq INTEGER NOT NULL);
CREATE INDEX words_key ON words(key);
CREATE TABLE aliases (roman TEXT NOT NULL, word TEXT NOT NULL);
CREATE INDEX aliases_roman ON aliases(roman);
"""


EVERYDAY_FREQ = 20000     # an everyday word ranks like a very common word


def build(tsv, db, everyday=None):
    """Index the word list. Words in the everyday list (data/everyday.tsv)
    get at least EVERYDAY_FREQ, and are added if Wikipedia doesn't have them."""
    if everyday is None:
        everyday = os.path.join(os.path.dirname(os.path.abspath(tsv)), "everyday.tsv")
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
            word = normalise_letters(word.strip())       # keep vowel marks: ڀاءُ
            if not normalise(word):
                continue
            rows[word] = rows.get(word, 0) + int(freq or 1)
    aliases = []
    if everyday and os.path.exists(everyday):
        bare = {normalise(w): w for w in rows}
        with open(everyday, encoding="utf-8") as f:
            for line in f:
                if not line.strip() or line.startswith("#"):
                    continue
                cols = line.rstrip("\n").split("\t")
                word = normalise_letters(cols[0].strip())
                word = bare.get(normalise(word), word)        # the word list's written form
                rows[word] = max(rows.get(word, 0), EVERYDAY_FREQ)
                for roman in cols[1:2]:
                    if roman.strip():
                        aliases.append((roman_norm(roman.strip()), word))
    con.executemany("INSERT INTO words VALUES (?,?,?,?)",
                    ((w, sd_key(w), sd_roman(w), fq) for w, fq in rows.items()))
    con.executemany("INSERT INTO aliases VALUES (?,?)", aliases)
    con.commit()
    con.execute("VACUUM")
    con.close()
    return len(rows)


COST_WEIGHT = 3.0      # how much a spelling mismatch counts ...
FREQ_WEIGHT = 0.5      # ... against how common the word is (per x10)
LOW = -1.0             # below this a dictionary word is a poor match


def score(typed, word, freq):
    return -COST_WEIGHT * match_cost(typed, word) + FREQ_WEIGHT * math.log10(freq + 1)


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
                for word, freq in self.con.execute(
                        "SELECT word, freq FROM words WHERE key=? ORDER BY freq DESC LIMIT 300", (key,)):
                    s = score(typed, word, freq)
                    scored[word] = max(scored.get(word, -99), s)
                if prefix and key:
                    for word, freq in self.con.execute(
                            "SELECT word, freq FROM words WHERE key>? AND key<? ORDER BY freq DESC LIMIT 30",
                            (key + ".", key + "/")):   # "/" sorts right after "."
                        s = score(typed, word, freq) - 1.0      # completions: below exact matches
                        if s > LOW:
                            scored.setdefault(word, s)
        for i, word in enumerate(rules.SPECIAL.get(clean(typed), [])):
            scored[word] = max(scored.get(word, -99), 9.0 - i)
        if self.con:                         # everyday list: exact Roman spelling
            for (word,) in self.con.execute("SELECT word FROM aliases WHERE roman=?", (roman_norm(typed),)):
                scored[word] = max(scored.get(word, -99), 10.0)
        for word, n in self._user_counts(typed).items():
            scored[word] = scored.get(word, 0) + 1.0 + 0.8 * n
        fb = fallback(typed)
        ranked = sorted(scored, key=lambda w: -scored[w])[:limit]
        if fb and fb not in ranked:
            # the letter-by-letter spelling: first if nothing matched well
            if not ranked or scored[ranked[0]] < LOW:
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
