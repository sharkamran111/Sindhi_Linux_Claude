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

# everyday.tsv

Everyday words that must win when a typed spelling fits both them and a more
formal Wikipedia word (`haal` → حال, not هال), one per line, optionally with a
Roman spelling after a TAB: typing exactly that spelling gives the word first
(for loanwords such as `table` → ٽيبل). Edit freely; the index is rebuilt at
every ISO build. Own work for SindhOS, seeded with the maintainer's examples.

# Tests

    python3 keyboard/roman/test_examples.py

Checks that the maintainer's WhatsApp-style examples and a set of common words
come out as the first choice. On 2026-11-11: 17 of 21 examples from the
spelling rules alone, 21 of 21 with everyday.tsv; 35 of 35 common words.
