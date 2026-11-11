# sd-words.tsv

Sindhi words with how often they appear (`word<TAB>count`), built by
`keyboard/roman/build_wordlist.py` from the Sindhi Wikipedia articles dump of
2026-11-01 (23,875 articles). Used by the Roman Sindhi keyboard now and by
spell checking and the dictionary app later.

Licence: **CC BY-SA 4.0**, as it is derived from Sindhi Wikipedia text
(© Wikipedia contributors). See CREDITS.md.

Known weaknesses: encyclopedic style (place names, "زمرو" category, formal
words rank high; everyday spoken words lower), some Urdu-influenced
spellings, and words with ء written in several ways.

Rebuild:

    curl -O https://dumps.wikimedia.org/sdwiki/latest/sdwiki-latest-pages-articles.xml.bz2
    python3 keyboard/roman/build_wordlist.py sdwiki-latest-pages-articles.xml.bz2 keyboard/roman/data/sd-words.tsv
