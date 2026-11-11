"""Typing logic of the Roman Sindhi engine, independent of IBus (testable).

The user types Roman letters; the composer keeps them in a buffer, shows the
best Sindhi candidate as preedit and the alternatives in a list.
  space / enter      commit the selected candidate (space adds a space)
  1-9                commit that candidate
  up/down, tab       move the selection
  backspace          delete the last Roman letter
  escape             drop the word
  . , ? ;            commit, then the Sindhi punctuation ۔ ، ؟ ؛
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import rules  # noqa: E402
import translit  # noqa: E402

PAGE = 9
ROMAN_CHARS = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ'")
MODIFIERS = {"Shift_L", "Shift_R", "Control_L", "Control_R", "Alt_L", "Alt_R", "Super_L", "Super_R",
             "Meta_L", "Meta_R", "Caps_Lock", "Num_Lock", "ISO_Level3_Shift", "ISO_Level5_Shift",
             "Hyper_L", "Hyper_R", "VoidSymbol"}


class Composer:
    def __init__(self, index):
        self.index = index
        self.buffer = ""
        self.cands = []
        self.sel = 0

    # --- state -----------------------------------------------------------
    @property
    def active(self):
        return bool(self.buffer)

    @property
    def preedit(self):
        return self.cands[self.sel] if self.cands else ""

    def _update(self):
        self.cands = self.index.candidates(self.buffer, limit=PAGE) if self.buffer else []
        self.sel = 0

    def _take(self, i=None):
        """Commit candidate i (default: selected) and reset. Returns text."""
        if not self.buffer:
            return ""
        i = self.sel if i is None else i
        word = self.cands[i] if 0 <= i < len(self.cands) else translit.fallback(self.buffer)
        self.index.learn(self.buffer, word, weight=1 if i == 0 else 3)
        self.buffer, self.cands, self.sel = "", [], 0
        return word

    # --- input -----------------------------------------------------------
    def key(self, name):
        """Handle one key. Returns (handled, text_to_commit)."""
        if name in MODIFIERS:                # Shift for T D R N etc.: keep the word
            return False, ""
        if len(name) == 1 and name in ROMAN_CHARS:
            self.buffer += name
            self._update()
            return True, ""
        if not self.buffer:
            if name in rules.PUNCT:
                return True, rules.PUNCT[name]
            return False, ""
        if name == "BackSpace":
            self.buffer = self.buffer[:-1]
            self._update()
            return True, ""
        if name == "Escape":
            self.buffer, self.cands, self.sel = "", [], 0
            return True, ""
        if name == "space":
            return True, self._take() + " "
        if name in ("Return", "KP_Enter"):
            return True, self._take()
        if len(name) == 1 and name.isdigit() and name != "0":
            i = int(name) - 1
            if i < len(self.cands):
                return True, self._take(i)
            return True, ""
        if name in ("Down", "Tab", "Right"):
            if self.cands:
                self.sel = (self.sel + 1) % len(self.cands)
            return True, ""
        if name in ("Up", "ISO_Left_Tab", "Left"):
            if self.cands:
                self.sel = (self.sel - 1) % len(self.cands)
            return True, ""
        if name in rules.PUNCT:
            return True, self._take() + rules.PUNCT[name]
        # any other key: commit the word, let the key through
        return False, self._take()

    def flush(self):
        """Focus lost / engine switched: commit what is there."""
        return self._take()
