#!/usr/bin/env python3
"""Build the SindhOS Sindhi word list (word + frequency) from a Wikipedia dump.

  build_wordlist.py cache/sdwiki-YYYYMMDD-pages-articles.xml.bz2 keyboard/roman/data/sd-words.tsv

Reads the Sindhi Wikipedia articles (CC BY-SA 4.0), strips wiki markup,
keeps words written in the Sindhi alphabet, normalises Urdu/Arabic look-alike
letters (ك ی ہ -> ڪ ي ه) and drops words with Urdu-only letters (ٹ ڈ ڑ ے ں).
A word must appear at least MIN_FREQ times in at least MIN_PAGES articles.
Spellings that differ only in vowel marks count as one word, written in its
most common form (so ڀاءُ keeps its pesh if that is how it is usually written).
The same list feeds the Roman Sindhi keyboard now, and spell checking and
the dictionary app later.
"""
import bz2
import collections
import os
import re
import sys
import xml.etree.ElementTree as ET

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import rules  # noqa: E402
import translit  # noqa: E402

MIN_FREQ = 3
MIN_PAGES = 2
MAX_WORDS = 120000

URDU_ONLY = set("ٹڈڑےۓںۂ")
SINDHI = set(rules.LETTERS) | set(rules.VOWEL_LETTERS) | set(rules.NORMALISE) | set(rules.MARKS) | {"ـ"}
WORD_RE = re.compile(r"[؀-ۿݐ-ݿ]+")

MARKUP = [
    (re.compile(r"<ref[^>/]*/>", re.S), " "),
    (re.compile(r"<ref.*?</ref>", re.S), " "),
    (re.compile(r"<!--.*?-->", re.S), " "),
    (re.compile(r"\{\|.*?\|\}", re.S), " "),            # tables
    (re.compile(r"\[\[(?:[^|\]]*\|)?([^\]]*)\]\]"), r"\1"),  # [[link|text]] -> text
    (re.compile(r"\[https?://\S+\s*([^\]]*)\]"), r"\1"),
    (re.compile(r"https?://\S+"), " "),
    (re.compile(r"<[^>]+>"), " "),
]
TEMPLATE = re.compile(r"\{\{[^{}]*\}\}")


def clean(text):
    for _ in range(4):                       # nested templates
        text, n = TEMPLATE.subn(" ", text)
        if not n:
            break
    for rx, rep in MARKUP:
        text = rx.sub(rep, text)
    return text


def pages(path):
    with bz2.open(path, "rb") as f:
        ns = text = None
        for _event, el in ET.iterparse(f, events=("end",)):
            tag = el.tag.rsplit("}", 1)[-1]
            if tag == "ns":
                ns = el.text
            elif tag == "text":
                text = el.text or ""
            elif tag == "page":
                if ns == "0" and not text.lstrip().lower().startswith("#redirect") \
                        and not text.lstrip().startswith("#چوريو"):
                    yield text
                ns = text = None
                el.clear()


def main(src, out):
    freq = collections.Counter()
    docs = collections.Counter()
    forms = collections.defaultdict(collections.Counter)   # bare word -> written forms
    n = 0
    for text in pages(src):
        n += 1
        seen = set()
        for raw in WORD_RE.findall(clean(text)):
            if any(c in URDU_ONLY for c in raw) or any(c not in SINDHI for c in raw):
                continue
            w = translit.normalise(raw)
            if len(w) < 1 or not translit.sd_key(w) and w not in ("۽", "آ", "اي", "او"):
                continue
            freq[w] += 1
            forms[w][translit.normalise_letters(raw)] += 1
            seen.add(w)
        docs.update(seen)
        if n % 5000 == 0:
            print(f"  {n} articles, {len(freq)} distinct words", flush=True)
    words = [(w, c) for w, c in freq.most_common() if c >= MIN_FREQ and docs[w] >= MIN_PAGES][:MAX_WORDS]
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w", encoding="utf-8") as f:
        f.write("# SindhOS Sindhi word list: word<TAB>frequency\n"
                f"# Built by keyboard/roman/build_wordlist.py from {os.path.basename(src)}\n"
                "# Source text: Sindhi Wikipedia (sd.wikipedia.org), CC BY-SA 4.0\n"
                f"# {n} articles, {len(words)} words (min {MIN_FREQ} uses in {MIN_PAGES}+ articles)\n")
        for w, c in words:
            f.write(f"{forms[w].most_common(1)[0][0]}\t{c}\n")
    print(f"{n} articles -> {len(words)} words -> {out}")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    main(sys.argv[1], sys.argv[2])
