# Roman Sindhi spelling rules — DRAFT for review

These rules drive the new Gboard-style engine (Phase 1). They are used two
ways:

1. **Word lookup**: every Sindhi word in the word list gets all its possible
   Roman spellings from this table, so `sindhi`, `sindi` and `sindhy` can all
   find سنڌي. Ambiguity is fine here: the word list decides.
2. **Fallback** for words not in the list: the *first* spelling in each row
   is used letter by letter, so you can always type any word, including names.

Please correct anything. Rows marked **❓** are your call (you offered to
help with ڌ ٻ ڄ ڃ ڳ ڱ ڪ).

## Consonants

| Sindhi | Name | Proposed Roman | Also accepted | Note |
|---|---|---|---|---|
| ب | be | `b` | | |
| ٻ | bbe | `bb` | `b` | ❓ implosive b: doubled letter? |
| ڀ | bhe | `bh` | | |
| پ | pe | `p` | | |
| ت | te | `t` | | |
| ٿ | the | `th` | | |
| ٽ | ṭe | `T` | `tt`, `t` | retroflex: capital letter or doubled? |
| ٺ | ṭhe | `Th` | `tth`, `th` | |
| ث | se | `s` | | Arabic loans; word list decides |
| ج | jeem | `j` | | |
| ڄ | jje | `jj` | `j` | ❓ implosive j |
| جھ | jhe | `jh` | | |
| ڃ | nye | `ny` | `nj`, `n` | ❓ |
| چ | che | `ch` | `c` | |
| ڇ | chhe | `chh` | | |
| ح | he (big) | `h` | | word list decides between ح and ه |
| خ | khe | `kh` | `x` | `kh` also = ک, word list decides |
| د | dal | `d` | | |
| ڌ | dhal | `dh` | | ❓ e.g. `sindhi` → سنڌي |
| ڏ | ddal | `dd` | `d` | ❓ implosive d |
| ڊ | ḍal | `D` | `d` | retroflex |
| ڍ | ḍhal | `Dh` | `dh` | |
| ذ | zal | `z` | | |
| ر | re | `r` | | |
| ڙ | ṛe | `R` | `rr`, `r` | retroflex flap |
| ز | ze | `z` | | |
| ژ | zhe | `zh` | | |
| س | seen | `s` | | |
| ش | sheen | `sh` | | |
| ص | suad | `s` | | |
| ض | zuad | `z` | | |
| ط | toe | `t` | | |
| ظ | zoe | `z` | | |
| ع | ain | `'` | `a` | often silent |
| غ | ghain | `gh` | | `gh` also = گھ, word list decides |
| ف | fe | `f` | | |
| ڦ | phe | `ph` | `f` | |
| ق | qaf | `q` | `k` | |
| ڪ | kaf | `k` | `q` | ❓ the normal Sindhi k (not Arabic ك) |
| ک | khe | `kh` | | |
| گ | gaf | `g` | | |
| ڳ | gge | `gg` | `g` | ❓ implosive g |
| گھ | ghe | `gh` | | |
| ڱ | nge | `ng` | | ❓ |
| ل | lam | `l` | | |
| م | meem | `m` | | |
| ن | noon | `n` | | |
| ڻ | ṇoon | `N` | `nn`, `n` | retroflex n |
| و | wao | `w` | `v`, `o`, `u` | consonant or vowel |
| ه | he | `h` | | |
| ي | ye | `y` | `i`, `e` | consonant or vowel |

## Vowels

| Roman | Sindhi | Example |
|---|---|---|
| `a` | usually not written (zabar); `aa` → ا; `a` at the start of a word → ا | `ab` → اب |
| `aa` | ا | `paaNi` → پاڻي |
| `i` | not written (zer) inside a word, ي at the end | `sindhi` → سنڌي |
| `ee` | ي | |
| `u` | not written (pesh) inside a word, و at the end | |
| `oo`, `o` | و | `boli` → ٻولي |
| `e` | ي | `te` → تي |
| `ai`, `au` | ي, و | |

## Open questions for you

1. Implosives ٻ ڄ ڏ ڳ: doubled letters (`bb jj dd gg`) as proposed, or
   another convention you and other Roman Sindhi writers already use?
2. Retroflex ٽ ڊ ڙ ڻ: capitals (`T D R N`) or doubled? Capitals are
   unambiguous but awkward on phones; plain letters work too thanks to the
   word list.
3. ڃ: `ny`, `nj` or something else? ڱ: `ng`?
4. A few common words and the Roman spelling *you* would type for them
   (e.g. `sindhi`, `boli`, `paani`, `ghar`, `jahaan`, `maanhoo`). Ten to
   twenty examples help tune the engine.
