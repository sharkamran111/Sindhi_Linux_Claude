#!/usr/bin/env python3
"""Roman Sindhi test cases: real typing, WhatsApp style (plain letters, no
capitals, vowel length not reliable). Each word must come out as choice 1.

  python3 keyboard/roman/test_examples.py [INDEX.sqlite]

Without an argument the index is built from data/sd-words.tsv into a
temporary file. Add new cases to EXAMPLES; they keep the engine honest.
"""
import os
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import translit  # noqa: E402

# typed -> expected first choice. From the SindhOS maintainer (2026-11-11).
EXAMPLES = {
    "kaam": "ڪم", "kamran": "ڪامران", "dhan": "ڌن", "bhaa": "ڀاءُ", "asan": "اسان",
    "tunhinji": "تنهنجي", "haal": "حال", "cha": "ڇا", "bakri": "ٻڪري", "ghar": "گهر",
    "rasto": "رستو", "kitab": "ڪتاب", "nishan": "نشان", "table": "ٽيبل", "meez": "ميز",
    "pani": "پاڻي", "roti": "روٽي", "mani": "ماني", "dost": "دوست", "sij": "سج",
    "darwazo": "دروازو",
}

# Common words checked by the developer (not the maintainer's list): they
# guard against tuning one word and breaking others.
COMMON = {
    "sindhi": "سنڌي", "boli": "ٻولي", "paani": "پاڻي", "asaan": "اسان", "aahe": "آهي", "mein": "۾",
    "e": "۽", "khe": "کي", "te": "تي", "maanhoo": "ماڻهو", "duniya": "دنيا", "pyaar": "پيار",
    "dil": "دل", "watan": "وطن", "khudaa": "خدا", "ishq": "عشق", "raat": "رات", "deenhan": "ڏينهن",
    "yaar": "يار", "qalam": "قلم", "shahar": "شهر", "sachal": "سچل", "zindagi": "زندگي",
    "karachi": "ڪراچي", "pakistan": "پاڪستان", "lateef": "لطيف", "sindh": "سنڌ", "jo": "جو",
    "ji": "جي", "hik": "هڪ", "sabh": "سڀ", "chha": "ڇا", "khaan": "کان", "zabaan": "زبان", "saal": "سال",
}

INDEX = None


def index():
    global INDEX
    if INDEX is None:
        db = sys.argv[1] if len(sys.argv) > 1 and sys.argv[1].endswith(".sqlite") else None
        if not db:
            db = os.path.join(tempfile.mkdtemp(), "index.sqlite")
            translit.build(os.path.join(HERE, "data", "sd-words.tsv"), db)
        INDEX = translit.Index(db)
    return INDEX


def check(cases):
    idx = index()
    failures = []
    for typed, want in cases.items():
        got = idx.candidates(typed)
        bare = [translit.normalise(g) for g in got]
        if not got or bare[0] != translit.normalise(want):
            rank = bare.index(translit.normalise(want)) + 1 if translit.normalise(want) in bare else None
            failures.append(f"{typed}: want {want} (rank {rank}), got {' '.join(got[:5])}")
    return failures


class Examples(unittest.TestCase):
    def test_maintainer_examples(self):
        f = check(EXAMPLES)
        self.assertEqual(f, [], "\n" + "\n".join(f))

    def test_common_words(self):
        f = check(COMMON)
        self.assertEqual(f, [], "\n" + "\n".join(f))


if __name__ == "__main__":
    argv = [a for a in sys.argv if not a.endswith(".sqlite")]
    unittest.main(argv=argv, verbosity=2)
