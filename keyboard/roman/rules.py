"""Roman Sindhi spelling rules (DRAFT, see keyboard/ROMAN-RULES-DRAFT.md).

One table drives everything in the Roman Sindhi engine:

* LETTERS: each Sindhi letter -> (sound class, Roman spellings). The class is
  what Roman input and Sindhi words are matched on (short vowels and the
  difference between e.g. ب and ٻ are left out, the word list decides). The
  FIRST Roman spelling is the one used to write the letter when a word is not
  in the word list.
* FALLBACK: Roman -> Sindhi letter for typing words that aren't in the list.

Change a row here, then rebuild the index (keyboard/roman/translit.py).
"""

# Sindhi letter: (class, [Roman spellings, first = default])
LETTERS = {
    "ب": ("b", ["b"]),
    "ٻ": ("b", ["bb", "b"]),          # implosive b
    "ڀ": ("bh", ["bh"]),
    "پ": ("p", ["p"]),
    "ت": ("t", ["t"]),
    "ٿ": ("th", ["th"]),
    "ٽ": ("t", ["T", "tt", "t"]),     # retroflex t
    "ٺ": ("th", ["Th", "tth", "th"]),
    "ث": ("s", ["s"]),
    "ج": ("j", ["j"]),
    "ڄ": ("j", ["jj", "j"]),          # implosive j
    "ڃ": ("n", ["ny", "nj", "n"]),
    "چ": ("ch", ["ch", "c"]),
    "ڇ": ("chh", ["chh"]),
    "ح": ("h", ["h"]),
    "خ": ("kh", ["kh", "x"]),
    "د": ("d", ["d"]),
    "ڌ": ("dh", ["dh"]),
    "ڏ": ("d", ["dd", "d"]),          # implosive d
    "ڊ": ("d", ["D", "d"]),           # retroflex d
    "ڍ": ("dh", ["Dh", "dh"]),
    "ذ": ("z", ["z"]),
    "ر": ("r", ["r"]),
    "ڙ": ("r", ["R", "rr", "r"]),     # retroflex flap
    "ز": ("z", ["z"]),
    "ژ": ("zh", ["zh"]),
    "س": ("s", ["s"]),
    "ش": ("sh", ["sh"]),
    "ص": ("s", ["s"]),
    "ض": ("z", ["z"]),
    "ط": ("t", ["t"]),
    "ظ": ("z", ["z"]),
    "غ": ("gh", ["gh"]),
    "ف": ("f", ["f"]),
    "ڦ": ("ph", ["ph", "f"]),
    "ق": ("k", ["q", "k"]),
    "ڪ": ("k", ["k"]),
    "ک": ("kh", ["kh"]),
    "گ": ("g", ["g"]),
    "ڳ": ("g", ["gg", "g"]),          # implosive g
    "ڱ": ("n", ["ng"]),
    "ل": ("l", ["l"]),
    "م": ("m", ["m"]),
    "۾": ("m", ["mein", "men", "me"]),  # Sindhi "in"
    "ن": ("n", ["n"]),
    "ڻ": ("n", ["N", "nn", "n"]),     # retroflex n
    "ه": ("h", ["h"]),
    "ھ": ("h", ["h"]),
}

# Letters that are vowels or (semi)vowels in matching: left out of the class
# key, used only for the fine comparison. Value = Roman sound.
VOWEL_LETTERS = {
    "ا": "a", "آ": "aa", "أ": "a", "إ": "i", "ع": "", "ء": "", "ئ": "i", "ؤ": "o",
    "و": "o", "ي": "i", "ى": "i", "ی": "i", "ے": "e", "۽": "e",
}
# Short-vowel marks (usually not written in Sindhi)
MARKS = {"َ": "a", "ِ": "i", "ُ": "u", "ّ": "", "ْ": "",
         "ً": "an", "ٍ": "in", "ٌ": "un", "ٰ": "a", "ٔ": "", "ٕ": ""}

# After ج or گ, ه / ھ is the aspiration of جھ گھ
ASPIRATE_AFTER = {"ج": "jh", "گ": "gh"}

# Letters written differently in Urdu / Arabic text, normalised to Sindhi
NORMALISE = {"ك": "ڪ", "ی": "ي", "ى": "ي", "ہ": "ه", "ۀ": "ه", "ە": "ه", "ۃ": "ه"}

# ---- Roman side ----------------------------------------------------------

# Roman tokens, longest first: token -> sound class ("" = vowel, ignored in key)
ROMAN_TOKENS = [
    ("chh", "chh"), ("tth", "th"), ("Th", "th"), ("Dh", "dh"),
    ("ch", "ch"), ("kh", "kh"), ("gh", "gh"), ("jh", "jh"), ("bh", "bh"), ("th", "th"),
    ("dh", "dh"), ("ph", "ph"), ("sh", "sh"), ("zh", "zh"), ("ny", "n"), ("nj", "n"),
    ("b", "b"), ("p", "p"), ("t", "t"), ("T", "t"), ("s", "s"), ("j", "j"), ("c", "ch"),
    ("h", "h"), ("x", "kh"), ("d", "d"), ("D", "d"), ("z", "z"), ("r", "r"), ("R", "r"),
    ("f", "f"), ("q", "k"), ("k", "k"), ("g", "g"), ("l", "l"), ("m", "m"), ("n", "n"),
    ("N", "n"), ("w", ""), ("v", ""), ("y", ""),
    ("a", ""), ("e", ""), ("i", ""), ("o", ""), ("u", ""), ("'", ""),
]

# Fallback: Roman -> Sindhi for words not in the word list (first match wins,
# longest first). Vowels are handled separately (see translit.fallback).
FALLBACK = [
    ("chh", "ڇ"), ("tth", "ٺ"), ("Th", "ٺ"), ("Dh", "ڍ"),
    ("bb", "ٻ"), ("jj", "ڄ"), ("dd", "ڏ"), ("gg", "ڳ"), ("tt", "ٽ"), ("rr", "ڙ"), ("nn", "ڻ"),
    ("bh", "ڀ"), ("th", "ٿ"), ("dh", "ڌ"), ("jh", "جھ"), ("gh", "گھ"), ("kh", "ک"),
    ("ch", "چ"), ("ph", "ڦ"), ("sh", "ش"), ("zh", "ژ"), ("ny", "ڃ"), ("ng", "ڱ"),
    ("b", "ب"), ("p", "پ"), ("t", "ت"), ("T", "ٽ"), ("s", "س"), ("j", "ج"), ("c", "چ"),
    ("h", "ه"), ("x", "خ"), ("d", "د"), ("D", "ڊ"), ("z", "ز"), ("r", "ر"), ("R", "ڙ"),
    ("f", "ف"), ("q", "ق"), ("k", "ڪ"), ("g", "گ"), ("l", "ل"), ("m", "م"), ("n", "ن"),
    ("N", "ڻ"), ("w", "و"), ("v", "و"), ("y", "ي"),
]

# Short words that the class key can't find (mostly vowels or special letters)
SPECIAL = {
    "mein": ["۾"], "men": ["۾"], "me": ["۾"], "main": ["۾"],
    "e": ["۽"], "ain": ["۽"], "aen": ["۽"], "aaen": ["۽"],
    "a": ["آ", "اي"], "aa": ["آ"], "o": ["او"], "ee": ["اي"],
}

# Capital letters that mean something (retroflex); all others are lower-cased
MEANINGFUL_CAPITALS = "TDRN"

# Punctuation typed in Roman Sindhi mode
PUNCT = {".": "۔", ",": "،", "?": "؟", ";": "؛"}
