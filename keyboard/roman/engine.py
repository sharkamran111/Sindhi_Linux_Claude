#!/usr/bin/env python3
"""SindhOS Roman Sindhi input method for IBus.

Type Sindhi in Roman letters: "sindhi boli" -> سنڌي ٻولي, with a list of
alternatives. Installed as /usr/lib/sindhos/roman/engine.py and started by
IBus through /usr/share/ibus/component/sindhos-roman.xml.
"""
import os
import sys

import gi
gi.require_version("IBus", "1.0")
from gi.repository import GLib, IBus  # noqa: E402

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import composer  # noqa: E402
import translit  # noqa: E402

ENGINE_NAME = "sindhos-roman"
BUS_NAME = "org.sindhos.Roman"
INDEX = os.environ.get("SINDHOS_ROMAN_INDEX", "/usr/share/sindhos/roman/index.sqlite")
USER_DB = os.path.join(GLib.get_user_data_dir(), "sindhos", "roman-picks.sqlite")

MODS = (IBus.ModifierType.CONTROL_MASK | IBus.ModifierType.MOD1_MASK |
        IBus.ModifierType.SUPER_MASK | IBus.ModifierType.MOD4_MASK)


class Engine(IBus.Engine):
    __gtype_name__ = "SindhosRomanEngine"

    def __init__(self, connection, object_path, index):
        super().__init__(connection=connection, object_path=object_path)
        self.comp = composer.Composer(index)
        self.table = IBus.LookupTable.new(composer.PAGE, 0, True, False)
        self.table.set_orientation(IBus.Orientation.HORIZONTAL)
        # No highlight box in the list: the chosen word is shown (underlined)
        # in the text itself, and the panel's highlight colours are unreadable
        # with some themes.
        self.table.set_cursor_visible(False)
        for i in range(composer.PAGE):
            self.table.set_label(i, IBus.Text.new_from_string(f"{i + 1}."))

    # -- keys ------------------------------------------------------------
    def do_process_key_event(self, keyval, keycode, state):
        if state & IBus.ModifierType.RELEASE_MASK:
            return False
        if state & MODS:                     # shortcuts: finish the word first
            self._commit(self.comp.flush())
            self._refresh()
            return False
        uni = IBus.keyval_to_unicode(keyval)
        key = uni if uni and uni.isprintable() and uni != " " else IBus.keyval_name(keyval)
        handled, text = self.comp.key(key)
        self._commit(text)
        self._refresh()
        return handled

    def do_candidate_clicked(self, index, button, state):
        handled, text = self.comp.key(str(index + 1))
        self._commit(text)
        self._refresh()

    def do_focus_out(self):
        self._commit(self.comp.flush())
        self._refresh()

    def do_reset(self):
        self._commit(self.comp.flush())
        self._refresh()

    def do_disable(self):
        self._commit(self.comp.flush())
        self._refresh()

    # -- display ---------------------------------------------------------
    def _commit(self, text):
        if text:
            self.commit_text(IBus.Text.new_from_string(text))

    def _refresh(self):
        c = self.comp
        if not c.active:
            self.hide_preedit_text()
            self.hide_auxiliary_text()
            self.hide_lookup_table()
            return
        pre = IBus.Text.new_from_string(c.preedit)
        pre.append_attribute(IBus.AttrType.UNDERLINE, IBus.AttrUnderline.SINGLE, 0, len(c.preedit))
        self.update_preedit_text(pre, len(c.preedit), True)
        self.update_auxiliary_text(IBus.Text.new_from_string(c.buffer), True)
        self.table.clear()
        for word in c.cands:
            self.table.append_candidate(IBus.Text.new_from_string(word))
        self.table.set_cursor_pos(c.sel)
        self.update_lookup_table(self.table, bool(c.cands))


class Factory(IBus.Factory):
    def __init__(self, bus):
        self.bus = bus
        self.index = translit.Index(INDEX, USER_DB)
        self.count = 0
        super().__init__(connection=bus.get_connection(), object_path=IBus.PATH_FACTORY)

    def do_create_engine(self, engine_name):
        if engine_name != ENGINE_NAME:
            return None
        self.count += 1
        return Engine(self.bus.get_connection(), f"/org/sindhos/Roman/Engine/{self.count}", self.index)


def main():
    IBus.init()
    bus = IBus.Bus()
    if not bus.is_connected():
        sys.exit("IBus is not running")
    loop = GLib.MainLoop()
    bus.connect("disconnected", lambda *_: loop.quit())
    factory = Factory(bus)  # noqa: F841  (kept alive by the main loop)
    if "--ibus" in sys.argv:
        bus.request_name(BUS_NAME, 0)
    else:                                   # started by hand (testing)
        comp = IBus.Component(name=BUS_NAME, description="SindhOS Roman Sindhi", version="0.1",
                              license="", author="SindhOS", homepage="", textdomain="")
        comp.add_engine(IBus.EngineDesc(name=ENGINE_NAME, longname="Roman Sindhi (test)",
                                        description="", language="sd", license="", author="",
                                        icon="", layout="us"))
        bus.register_component(comp)
        bus.set_global_engine_async(ENGINE_NAME, -1, None, None, None)
    loop.run()


if __name__ == "__main__":
    main()
