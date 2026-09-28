r"""MO2 Theme Framework - does for a Mod Organizer 2 theme what a .qss file cannot do on its own, so any theme can be
installed the usual way (paste the .qss and its folder into <MO2>\stylesheets) and still reach everything.

The owner, 2026-09-26: "could we make a plugin seperatley as a requirement for themes that does the things the .qss
file cant do alone like the separator color and the ini file edit? that way others can build their theme off of it" -
and, of the theme itself, "they just tell you to past the files into the stylesheets folder so we should do that".
Earlier the same day: "exports that apply to other plugins ... just like how imgui draws in game and we change the
theme for amf and all mod menus change with it".

For whatever theme MO2 is using, the framework reads the theme's colours from the theme itself (the owner, later the
same day: "no need for authors to do anything") and, with an optional stylesheets\<Theme>\theme.json for the parts a
stylesheet cannot express (THEME-AUTHORS.md has the format):
  * (theme.json) writes MO2's six conflict colours to ModOrganizer.ini [Settings] (MO2 reads them there only),
  * (theme.json) colours separators (and, if the theme says so, mods) in meta.ini color=,
  * publishes the theme's palette to every other plugin: QApplication property "mo2theme.palette" (JSON, role ->
    css colour), "mo2theme.name" and "mo2theme.revision", and the application QPalette,
  * re-colours the colours other plugins hard-code in their own widget stylesheets (which beat any theme) onto the
    palette - per window, from a timer, never an application-wide event filter (gate rule
    mo2-plugin-no-application-event-filter).
Switch to a theme without a theme.json and it puts back the colours that were there before the first theme touched
them. How MO2 itself does each part is in MO2-REFERENCE.md.

Copyright (C) 2026 ApocryphaRealm. GPL-3.0-or-later - see LICENSE and NOTICE.md.
"""
__version__ = "1.0.0"

import json
import os
import re
import time

import mobase

try:
    from PyQt6 import sip as _sip
except ImportError:  # pragma: no cover
    _sip = None

from PyQt6.QtCore import QByteArray, QCoreApplication, QRectF, QSettings, Qt, QTimer, QUrl
from PyQt6.QtGui import QColor, QDesktopServices, QIcon, QPainter, QPalette, QPixmap
from PyQt6.QtWidgets import (QApplication, QCheckBox, QDialog, QGridLayout, QGroupBox, QHBoxLayout, QLabel,
                             QLineEdit, QPushButton, QTreeView, QVBoxLayout, QWidget)

try:
    from PyQt6.QtSvg import QSvgRenderer
except ImportError:  # pragma: no cover
    QSvgRenderer = None

PLUGIN_NAME = "MO2 Theme Framework"
FORMAT = 1
HERE = os.path.dirname(os.path.abspath(__file__))

# ---------------------------------------------------------------------------------------------------------------------
# Languages (rule 66): TR("KEY", "English") reads translations\<language>.txt ($KEY<TAB>text, UTF-16LE with a BOM)
# ---------------------------------------------------------------------------------------------------------------------
_LANG_FILES = {"en": "english", "ja": "japanese", "ko": "korean", "zh": "chinese", "ru": "russian", "de": "german",
               "fr": "french", "es": "spanish", "it": "italian", "pl": "polish", "cs": "czech"}
_STRINGS = {}


def _load_strings(language_code):
    name = _LANG_FILES.get((language_code or "en").split("_")[0].split("-")[0].lower(), "english")
    for candidate in (name, "english"):
        try:
            raw = open(os.path.join(HERE, "translations", candidate + ".txt"), "rb").read()
        except OSError:
            continue
        text = raw[2:].decode("utf-16-le", "replace") if raw[:2] == b"\xff\xfe" else raw.decode("utf-8-sig", "replace")
        for line in text.replace("\r\n", "\n").split("\n"):
            if line.startswith("$") and "\t" in line:
                k, _, v = line.partition("\t")
                _STRINGS.setdefault(k[1:].strip(), v.strip().replace("\\n", "\n"))


def TR(key, english):
    return _STRINGS.get(key, english)


# ---------------------------------------------------------------------------------------------------------------------
# Colours
# ---------------------------------------------------------------------------------------------------------------------
# ModOrganizer.ini [Settings] keys MO2 2.5.2 reads its conflict colours from (src/settings.cpp)
CONFLICT_KEYS = ["overwrittenLooseFilesColor", "overwritingLooseFilesColor", "overwrittenArchiveFilesColor",
                 "overwritingArchiveFilesColor", "containsPluginColor", "containedColor"]

# When a theme gives no otherPlugins.remap, these colours - the ones the Mod Organizer Plugin Browser hard-codes in
# about 40 setStyleSheet calls (MO2-REFERENCE.md, part 5) - are mapped onto these palette roles.
DEFAULT_REMAP = {
    "#000000": "bg", "#121212": "hover", "#141414": "input", "#212121": "input_focus", "#5f5f5e": "selected",
    "#c0c0c0": "text", "#f1f1f1": "text_bright", "#ffffff": "text_hover", "#656565": "text_disabled",
    "#999999": "frame", "#3399ff": "link", "#661111": "invalid", "#2b2b2b": "mod_row",
}


def _qcolor(text):
    """#RRGGBB, #AARRGGBB, a colour name, or css rgb()/rgba() with alpha 0-1."""
    text = (text or "").strip()
    m = re.match(r"rgba?\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*(?:,\s*([\d.]+)\s*)?\)$", text)
    if m:
        a = m.group(4)
        alpha = 255 if a is None else (int(round(float(a) * 255)) if float(a) <= 1 else int(float(a)))
        return QColor(int(m.group(1)), int(m.group(2)), int(m.group(3)), alpha)
    return QColor(text)


def _css(c):
    if c.alpha() == 255:
        return c.name()
    return "rgba(%d, %d, %d, %s)" % (c.red(), c.green(), c.blue(), ("%.2f" % (c.alpha() / 255)).rstrip("0").rstrip("."))


def _argb(c):
    return c.name(QColor.NameFormat.HexArgb)


# meta.ini color= - MO2 stores a QColor in QSettings' @Variant encoding (same writer as MO2 Default Colors 1.0.0)
def _escape(data):
    return "".join("\\0" if b == 0 else "\\x%x" % b for b in data)


def color_line(c):
    def u16(v):
        v = v * 257
        return bytes(((v >> 8) & 0xFF, v & 0xFF))
    payload = b"\x00\x00\x00\x43" + b"\x01" + u16(c.alpha()) + u16(c.red()) + u16(c.green()) + u16(c.blue()) + b"\x00\x00"
    return "color=@Variant(" + _escape(payload) + ")"


def read_color_line(meta_path):
    try:
        for line in open(meta_path, encoding="utf-8", errors="ignore"):
            if line.startswith("color="):
                return line.rstrip("\r\n")
    except OSError:
        pass
    return None


def write_color_line(meta_path, line):
    """Set (line) or remove (None) the color= line, keeping everything else in meta.ini as it was."""
    try:
        text = open(meta_path, "rb").read().decode("utf-8-sig") if os.path.isfile(meta_path) else "[General]\n"
    except OSError:
        return False
    nl = "\r\n" if "\r\n" in text else "\n"
    lines = text.split(nl)
    idx = next((i for i, l in enumerate(lines) if l.startswith("color=")), None)
    if line is None:
        if idx is None:
            return True
        del lines[idx]
    elif idx is not None:
        lines[idx] = line
    elif "[General]" in lines:
        lines.insert(lines.index("[General]") + 1, line)
    else:
        lines[0:0] = ["[General]", line]
    try:
        open(meta_path, "wb").write(nl.join(lines).encode("utf-8"))
        return True
    except OSError:
        return False


def _is_deleted(obj):
    try:
        return bool(_sip is not None and _sip.isdeleted(obj))
    except Exception:  # noqa: BLE001
        return True


# ---------------------------------------------------------------------------------------------------------------------
# Reading a theme's colours from the theme itself
# ---------------------------------------------------------------------------------------------------------------------
_RULE = re.compile(r"([^{}]+)\{([^{}]*)\}")
_DECL_COLOUR = re.compile(r"#[0-9a-fA-F]{8}\b|#[0-9a-fA-F]{6}\b|#[0-9a-fA-F]{3}\b|rgba?\([^)]*\)")


def _sheet_rules(sheet_path):
    """(selector, {property: first colour in its value}) for every rule of a .qss file; [] when unreadable."""
    try:
        text = open(sheet_path, encoding="utf-8", errors="replace").read()
    except OSError:
        return []
    text = re.sub(r"/\*.*?\*/", "", text, flags=re.S)
    rules = []
    for m in _RULE.finditer(text):
        props = {}
        for decl in m.group(2).split(";"):
            if ":" not in decl:
                continue
            k, _, v = decl.partition(":")
            c = _DECL_COLOUR.search(v)
            if c and "gradient" not in v:
                props.setdefault(k.strip().lower(), c.group(0))
        if props:
            rules.append((" ".join(m.group(1).split()), props))
    return rules


def _from_rules(rules, want, props=("background-color", "background")):
    """The first colour of `props` in a rule whose selector contains every string in `want`."""
    for sel, p in rules:
        s = sel.lower()
        if all(w in s for w in want) and ":disabled" not in s:
            for k in props:
                if k in p:
                    c = _qcolor(p[k])
                    if c.isValid():
                        return c
    return None


def derive_palette(sheet_path):
    """role -> QColor for the stylesheet the application is using right now."""
    R, G = QPalette.ColorRole, QPalette.ColorGroup
    host = QWidget()
    host.setAttribute(Qt.WidgetAttribute.WA_DontShowOnScreen, True)
    view, edit, button, label = QTreeView(host), QLineEdit(host), QPushButton("x", host), QLabel("x", host)
    try:
        for w in (host, view, edit, button, label):
            w.ensurePolished()
        out = {
            "bg": host.palette().color(R.Window), "text": view.palette().color(R.Text),
            "text_bright": host.palette().color(R.WindowText), "text_hover": view.palette().color(R.HighlightedText),
            "text_disabled": host.palette().color(G.Disabled, R.WindowText), "input": edit.palette().color(R.Base),
            "mod_row": view.palette().color(R.AlternateBase), "view_bg": view.palette().color(R.Base),
            "button": button.palette().color(R.Button), "button_text": button.palette().color(R.ButtonText),
        }
    finally:
        host.deleteLater()
    rules = _sheet_rules(sheet_path) if sheet_path else []
    pick = lambda *alts: next((c for c in (_from_rules(rules, a) for a in alts) if c is not None), None)  # noqa: E731
    out["selected"] = pick(("::item:selected",), (":selected",)) or view.palette().color(R.Highlight)
    out["hover"] = pick(("::item:hover",), (":hover",)) or QColor(out["bg"]).lighter(160)
    out["input_focus"] = pick(("qlineedit", ":focus"), ("spinbox", ":focus"), (":focus",)) or out["input"]
    out["invalid"] = pick(("valid-filter=false",)) or QColor("#661111")
    out["frame"] = (_from_rules(rules, ("qabstractitemview",), ("border-color", "border"))
                    or _from_rules(rules, ("qgroupbox",), ("border-color", "border")) or out["text_disabled"])
    link = next((_qcolor(p["qproperty-linkcolor"]) for _s, p in rules if "qproperty-linkcolor" in p), None)
    out["link"] = link if link is not None and link.isValid() else label.palette().color(R.Link)
    out["icon"] = out["text"]
    out["icon_accent"] = out["frame"]
    return {k: QColor(v) for k, v in out.items() if v is not None and QColor(v).isValid()}


# ---------------------------------------------------------------------------------------------------------------------
# The active theme
# ---------------------------------------------------------------------------------------------------------------------
class Theme:
    """The theme MO2 is using, read from the application stylesheet MO2 set (file:///<dir>/<Name>.qss)."""

    def __init__(self, sheet_url):
        self.sheet_url = sheet_url or ""
        path = self.sheet_url
        if path.startswith("file:///"):
            path = path[len("file:///"):]
        self.sheet = os.path.normpath(path) if path.lower().endswith(".qss") else ""
        self.name = os.path.splitext(os.path.basename(self.sheet))[0] if self.sheet else ""
        self.folder = os.path.join(os.path.dirname(self.sheet), self.name) if self.sheet else ""
        self.spec_path = ""
        self.spec = None
        self.error = ""
        candidates = (os.path.join(self.folder, "theme.json"),
                      os.path.join(os.path.dirname(self.sheet), self.name + ".theme.json")) if self.sheet else ()
        for candidate in candidates:
            if os.path.isfile(candidate):
                self.spec_path = candidate
                try:
                    spec = json.load(open(candidate, encoding="utf-8-sig"))
                    if int(spec.get("mo2ThemeFramework", 0)) > FORMAT:
                        self.error = "theme.json is format %s; this framework reads %d" % (spec.get("mo2ThemeFramework"), FORMAT)
                    else:
                        self.spec = spec
                except (OSError, ValueError) as exc:
                    self.error = "theme.json unreadable: %s" % exc
                break

        self.derived = {}

    def derive(self):
        """Read the theme's colours from the theme itself - no theme.json needed (the owner, 2026-09-26: "couldnt we
        just make the plugin automatically read the current theme colors and apply them to added plugins as needed?
        no need for authors to do anything"). Qt's stylesheet style sets a styled widget's palette from its
        background / color rules when it polishes it, so hidden sample widgets carry the active theme's colours;
        what lives only in pseudo-state rules (hover, selection, focus, the filter warning, link colour) is read from
        the sheet's text."""
        self.derived = derive_palette(self.sheet)

    def palette(self):
        out = dict(self.derived)
        for k, v in ((self.spec or {}).get("palette") or {}).items():
            c = _qcolor(str(v))
            if c.isValid():
                out[k] = c
        return out

    def mod_list(self):
        return (self.spec or {}).get("modList") or {}

    def remap(self):
        """literal colour (lower-case, as written in a sheet) -> the css colour that replaces it."""
        pal = self.palette()
        table = ((self.spec or {}).get("otherPlugins") or {}).get("remap")
        if table is None:
            table = DEFAULT_REMAP
        out = {}
        for literal, target in table.items():
            src = _qcolor(literal)
            dst = pal.get(target) if target in pal else _qcolor(str(target))
            if not src.isValid() or dst is None or not dst.isValid() or src == dst:
                continue
            h = src.name().lower()
            forms = {h, "rgb(%d,%d,%d)" % (src.red(), src.green(), src.blue())}
            if h[1] == h[2] and h[3] == h[4] and h[5] == h[6]:
                forms.add("#" + h[1] + h[3] + h[5])
            if h == "#000000":
                forms.add("black")
            if h == "#ffffff":
                forms.add("white")
            for f in forms:
                out.setdefault(f, _css(dst))
        return out


# ---------------------------------------------------------------------------------------------------------------------
# Other plugins' windows - one unparented timer rescans visible top-level windows; never an application-wide filter
# ---------------------------------------------------------------------------------------------------------------------
_COLOUR_TOKEN = re.compile(r"#[0-9a-fA-F]{6}\b|#[0-9a-fA-F]{3}\b|rgba?\([^)]*\)|\bblack\b|\bwhite\b", re.I)


class OtherPlugins:
    ORIG = "mo2theme_original_sheet"
    DONE = "mo2theme_applied_sheet"

    def __init__(self, log):
        self._log = log
        self._table = {}
        self._timer = QTimer()                 # unparented (gate rule mo2-plugin-timers-not-parented-to-mo2-widgets)
        self._timer.setInterval(1200)
        self._timer.timeout.connect(self._scan)

    def set_table(self, table):
        self._table = dict(table)
        if self._timer.isActive():
            self._scan()

    def start(self):
        if not self._timer.isActive():
            self._timer.start()
        self._scan()

    def stop(self):
        if self._timer.isActive():
            self._timer.stop()
            self._walk(restore=True)

    def _map(self, sheet):
        if not self._table:
            return sheet
        return _COLOUR_TOKEN.sub(lambda m: self._table.get(m.group(0).lower().replace(" ", ""), m.group(0)), sheet)

    def _scan(self):
        try:
            self._walk()
        except Exception as exc:  # noqa: BLE001 - a foreign window must never take MO2 down
            self._log(f"other plugins: {exc!r}")

    def _walk(self, restore=False):
        changed = 0
        for top in QApplication.topLevelWidgets():
            if _is_deleted(top) or not top.isVisible() or top.property("mo2theme_skip"):
                continue
            for w in [top] + top.findChildren(QWidget):
                if _is_deleted(w):
                    continue
                cur = w.styleSheet()
                if not cur:
                    continue
                if cur != w.property(self.DONE):         # a new widget, or its plugin set its sheet again
                    w.setProperty(self.ORIG, cur)
                orig = w.property(self.ORIG) or cur
                want = orig if restore else self._map(orig)
                if want != cur:
                    w.setStyleSheet(want)
                    changed += 1
                w.setProperty(self.DONE, want)
        if changed:
            self._log(f"restored {changed} widget sheet(s)" if restore
                      else f"re-coloured {changed} widget sheet(s) in other plugins' windows")


# ---------------------------------------------------------------------------------------------------------------------
# The popup
# ---------------------------------------------------------------------------------------------------------------------
class FrameworkDialog(QDialog):
    def __init__(self, plugin):
        super().__init__(None)
        self._p = plugin
        self.setWindowTitle(PLUGIN_NAME)
        self.setProperty("mo2theme_skip", True)
        self.setWindowIcon(plugin.icon())
        self.resize(760, 460)
        v = QVBoxLayout(self)

        intro = QLabel(TR("MTF_Intro", "Whatever theme MO2 is using, its colours are read from the theme itself and "
                                       "given to other plugins' windows, so they match it. A theme that also ships a "
                                       "theme.json can set what a stylesheet cannot: separator and mod colours and "
                                       "the mod list's conflict colours."))
        intro.setWordWrap(True)
        v.addWidget(intro)

        self._status = QLabel()
        self._status.setWordWrap(True)
        self._status.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        v.addWidget(self._status)

        box = QGroupBox(TR("MTF_GroupApply", "Apply from the theme"))
        g = QGridLayout(box)
        for i, (key, tr_key, text) in enumerate([
            ("apply_conflicts", "MTF_ApplyConflicts", "Mod list conflict colours"),
            ("apply_separators", "MTF_ApplySeparators", "Separator colour"),
            ("apply_mods", "MTF_ApplyMods", "Mod colour (when the theme sets one)"),
            ("theme_other_plugins", "MTF_ThemeOthers", "Other plugins' windows"),
        ]):
            cb = QCheckBox(TR(tr_key, text))
            cb.setChecked(bool(plugin._get(key)))
            cb.toggled.connect(lambda on, k=key: self._switch(k, on))
            g.addWidget(cb, i // 2, i % 2)
        v.addWidget(box)
        v.addStretch(1)

        row = QHBoxLayout()
        b1 = QPushButton(TR("MTF_Reapply", "Apply again now"))
        b1.clicked.connect(self._reapply)
        b2 = QPushButton(TR("MTF_Restore", "Put my original colours back"))
        b2.clicked.connect(self._restore)
        b3 = QPushButton(TR("MTF_OpenFolder", "Open the theme's folder"))
        b3.clicked.connect(lambda: QDesktopServices.openUrl(QUrl.fromLocalFile(plugin._theme.folder or plugin._styles_dir())))
        b4 = QPushButton(TR("MTF_Authors", "Guide for theme authors"))
        b4.clicked.connect(lambda: QDesktopServices.openUrl(QUrl.fromLocalFile(os.path.join(HERE, "THEME-AUTHORS.md"))))
        close = QPushButton(TR("MTF_Close", "Close"))
        close.clicked.connect(self.accept)
        for b in (b1, b2, b3, b4):
            row.addWidget(b)
        row.addStretch(1)
        row.addWidget(close)
        v.addLayout(row)
        self._refresh()

    def _switch(self, key, on):
        self._p._set_switch(key, on)
        self._refresh()

    def _reapply(self):
        self._p._apply(force=True)
        self._refresh()

    def _restore(self):
        self._p._restore()
        self._refresh()

    def _refresh(self):
        t = self._p._theme
        if not t.name:
            text = TR("MTF_NoTheme", "MO2 is using its default look; its colours are given to other plugins.")
        elif t.spec is not None:
            text = TR("MTF_Active", "Theme: %1 - colours read from the theme and given to other plugins; its theme.json also sets the mod list colours.").replace("%1", t.name)
        elif t.error:
            text = TR("MTF_Error", "Theme: %1 - theme.json could not be used: %2").replace("%1", t.name).replace("%2", t.error)
        else:
            text = TR("MTF_Plain", "Theme: %1 - colours read from the theme and given to other plugins. It has no theme.json, so the mod list keeps your own colours.").replace("%1", t.name)
        self._status.setText(text)


# ---------------------------------------------------------------------------------------------------------------------
# The plugin
# ---------------------------------------------------------------------------------------------------------------------
ICON_SVG = ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="{i}" stroke-width="1.8" '
            'stroke-linecap="round" stroke-linejoin="round"><path d="M12 3a9 9 0 1 0 0 18c1.2 0 1.6-.9 1.3-1.8-.4-1.1.3-2.2 '
            '1.5-2.2H17a4 4 0 0 0 4-4c0-5.5-4-10-9-10z"/><circle cx="7.5" cy="11" r="1.2" stroke="{a}"/><circle cx="10" '
            'cy="7" r="1.2" stroke="{a}"/><circle cx="14.5" cy="7" r="1.2" stroke="{a}"/></svg>')


class ThemeFramework(mobase.IPluginTool):
    SETTINGS = {"apply_conflicts": True, "apply_separators": True, "apply_mods": True, "theme_other_plugins": True}

    def __init__(self):
        super().__init__()
        self._organizer = None
        self._theme = Theme("")
        self._applied_key = None
        self._saved_palette = None
        self._others = OtherPlugins(self._log)
        self._watch = QTimer()                 # unparented; notices a theme change (MO2 has no signal for it)
        self._watch.setInterval(1500)
        self._watch.timeout.connect(self._poll)
        self._new_entries = QTimer()           # unparented; colours separators added while a theme is active
        self._new_entries.setInterval(15000)
        self._new_entries.timeout.connect(self._colour_new_entries)

    # mobase ---------------------------------------------------------------------------------------------------------
    def init(self, organizer):
        self._organizer = organizer
        try:
            lang = self._ini().value("Settings/language", "en")
        except Exception:  # noqa: BLE001
            lang = "en"
        _load_strings(str(lang or "en"))
        organizer.onUserInterfaceInitialized(self._ui_ready)
        self._log(f"loaded {__version__}")
        return True

    def name(self):
        return PLUGIN_NAME

    def localizedName(self):
        return TR("MTF_Name", PLUGIN_NAME)

    def author(self):
        return "ApocryphaRealm"

    def description(self):
        return TR("MTF_Description", "Gives MO2 themes what a stylesheet cannot do: separator and mod colours, the "
                                     "mod list's conflict colours, a palette other plugins can read, and other "
                                     "plugins' windows in the theme's colours.")

    def version(self):
        return mobase.VersionInfo(*(int(x) for x in __version__.split(".")), mobase.ReleaseType.FINAL)

    def settings(self):
        return [mobase.PluginSetting(k, k.replace("_", " "), v) for k, v in self.SETTINGS.items()]

    def displayName(self):
        return TR("MTF_Name", PLUGIN_NAME)

    def tooltip(self):
        return TR("MTF_Tooltip", "Separator, mod-list and plugin colours from the active theme")

    def icon(self):
        pal = self._theme.palette()
        ic = pal.get("icon", QColor("#c0c0c0")).name()
        ac = pal.get("icon_accent", QColor("#999999")).name()
        if QSvgRenderer is None:
            return QIcon()
        pm = QPixmap(64, 64)
        pm.fill(Qt.GlobalColor.transparent)
        p = QPainter(pm)
        QSvgRenderer(QByteArray(ICON_SVG.replace("{i}", ic).replace("{a}", ac).encode())).render(p, QRectF(0, 0, 64, 64))
        p.end()
        return QIcon(pm)

    def setParentWidget(self, widget):
        pass

    def display(self):
        FrameworkDialog(self).exec()

    # settings -------------------------------------------------------------------------------------------------------
    def _get(self, key):
        try:
            v = self._organizer.pluginSetting(PLUGIN_NAME, key)
        except Exception:  # noqa: BLE001
            v = None
        return self.SETTINGS[key] if v is None else v

    def _set_switch(self, key, on):
        try:
            self._organizer.setPluginSetting(PLUGIN_NAME, key, bool(on))
        except Exception as exc:  # noqa: BLE001
            self._log(f"setting {key}: {exc!r}")
        self._log(f"{key} = {bool(on)}")
        self._apply(force=True)

    # paths ----------------------------------------------------------------------------------------------------------
    def _ini(self):
        return QSettings(os.path.join(self._organizer.basePath(), "ModOrganizer.ini"), QSettings.Format.IniFormat)

    @staticmethod
    def _styles_dir():
        return os.path.join(QCoreApplication.applicationDirPath(), "stylesheets")

    def _data_dir(self):
        base = self._organizer.basePath() if self._organizer else os.path.dirname(os.path.dirname(HERE))
        d = os.path.join(base, "plugins", "data", "MO2ThemeFramework")
        os.makedirs(d, exist_ok=True)
        return d

    # the theme --------------------------------------------------------------------------------------------------------
    def _ui_ready(self, _window):
        QTimer.singleShot(0, self._startup)

    def _startup(self):
        self._poll()
        self._watch.start()
        self._new_entries.start()

    def _poll(self):
        try:
            url = QApplication.instance().styleSheet() or ""
            spec_mtime = self._spec_mtime()
            if url != self._theme.sheet_url or spec_mtime != (self._applied_key or ("", "", 0))[2]:
                self._theme = Theme(url)
                self._log(f"theme: {self._theme.name or '(none)'}; theme.json: "
                          f"{'yes' if self._theme.spec is not None else (self._theme.error or 'no')}")
                self._apply()
        except Exception as exc:  # noqa: BLE001
            self._log(f"poll: {exc!r}")

    def _spec_mtime(self):
        p = self._theme.spec_path
        try:
            return os.path.getmtime(p) if p else 0
        except OSError:
            return 0

    def _apply(self, force=False):
        t = self._theme
        key = (t.sheet_url, t.spec_path, self._spec_mtime())
        if key == self._applied_key and not force:
            return
        self._applied_key = key
        try:
            # every theme: its colours are read from the theme itself, published, and given to other plugins.
            # Read against MO2's own palette, never the one published for the previous theme.
            if self._saved_palette is not None:
                QApplication.instance().setPalette(self._saved_palette)
            t.derive()
            self._publish(t)
            # the mod list's colours are a theme's own choice - only a theme.json can make it
            if t.spec is None:
                self._restore()
            else:
                if self._get("apply_conflicts"):
                    self._write_conflicts(t)
                self._colour_entries(only_missing=False)
            if self._get("theme_other_plugins"):
                self._others.set_table(t.remap())
                self._others.start()
            else:
                self._others.stop()
        except Exception as exc:  # noqa: BLE001
            self._log(f"apply: {exc!r}")

    # the export for other plugins -------------------------------------------------------------------------------------
    def _publish(self, t):
        app = QApplication.instance()
        app.setProperty("mo2theme.revision", int(time.time() * 1000) & 0x7FFFFFFF)
        if t is None:
            app.setProperty("mo2theme.palette", "")
            app.setProperty("mo2theme.name", "")
            if self._saved_palette is not None:
                app.setPalette(self._saved_palette)
                self._saved_palette = None
            self._others.stop()
            return
        pal = t.palette()
        app.setProperty("mo2theme.palette", json.dumps({"name": t.name, "fromThemeJson": t.spec is not None,
                                                        "roles": {k: _css(c) for k, c in pal.items()}}))
        app.setProperty("mo2theme.name", t.name)
        if self._saved_palette is None:
            self._saved_palette = QPalette(app.palette())
        qp = QPalette(self._saved_palette)
        G, R = QPalette.ColorGroup, QPalette.ColorRole
        roles = [(R.Window, "bg"), (R.WindowText, "text"), (R.Base, "bg"), (R.AlternateBase, "mod_row"), (R.Text, "text"),
                 (R.Button, "input"), (R.ButtonText, "text"), (R.Highlight, "selected"), (R.HighlightedText, "text_hover"),
                 (R.Link, "link"), (R.ToolTipBase, "hover"), (R.ToolTipText, "text"), (R.PlaceholderText, "text_disabled"),
                 (R.BrightText, "text_bright")]
        for group in (G.Active, G.Inactive):
            for role, name in roles:
                if name in pal:
                    qp.setColor(group, role, pal[name])
        if "text_disabled" in pal:
            for role in (R.WindowText, R.Text, R.ButtonText):
                qp.setColor(G.Disabled, role, pal["text_disabled"])
        app.setPalette(qp)

    # originals - what was there before the first theme.json touched anything -------------------------------------
    def _originals_path(self):
        return os.path.join(self._data_dir(), "originals.json")

    def _originals(self):
        try:
            o = json.load(open(self._originals_path(), encoding="utf-8"))
            o.setdefault("conflicts", {})
            o.setdefault("entries", {})
            return o
        except (OSError, ValueError):
            return {"conflicts": {}, "entries": {}}

    def _save_originals(self, o):
        tmp = self._originals_path() + ".tmp"
        json.dump(o, open(tmp, "w", encoding="utf-8"), indent=1)
        os.replace(tmp, self._originals_path())

    def _write_conflicts(self, t):
        colours = t.mod_list().get("conflictColors") or {}
        s = self._ini()
        o = self._originals()
        n = 0
        for key in CONFLICT_KEYS:
            if key not in colours:
                continue
            c = _qcolor(str(colours[key]))
            if not c.isValid():
                continue
            cur = s.value("Settings/" + key)
            if key not in o["conflicts"]:
                o["conflicts"][key] = _argb(cur) if isinstance(cur, QColor) else None
            if isinstance(cur, QColor) and cur == c:
                continue
            s.setValue("Settings/" + key, c)
            n += 1
        s.sync()
        self._save_originals(o)
        if n:
            self._log(f"wrote {n} conflict colour(s) to ModOrganizer.ini")

    def _colour_new_entries(self):
        try:
            self._colour_entries(only_missing=True)
        except Exception as exc:  # noqa: BLE001
            self._log(f"new entries: {exc!r}")

    def _colour_entries(self, only_missing):
        t = self._theme
        if t.spec is None:
            return
        ml = t.mod_list()
        jobs = []
        if self._get("apply_separators") and ml.get("separatorColor"):
            jobs.append((True, _qcolor(str(ml["separatorColor"]))))
        if self._get("apply_mods") and ml.get("modColor"):
            jobs.append((False, _qcolor(str(ml["modColor"]))))
        if not jobs:
            return
        try:
            names = list(self._organizer.modList().allMods())
            mods_dir = self._organizer.modsPath()
        except Exception as exc:  # noqa: BLE001
            self._log(f"mod list: {exc!r}")
            return
        o = self._originals()
        written = 0
        for seps, c in jobs:
            if not c.isValid():
                continue
            line = color_line(c)
            for n in names:
                if n.endswith("_separator") != seps:
                    continue
                meta = os.path.join(mods_dir, n, "meta.ini")
                cur = read_color_line(meta)
                if (only_missing and cur) or cur == line:
                    continue
                o["entries"].setdefault(n, cur)
                if write_color_line(meta, line):
                    written += 1
        if written:
            self._save_originals(o)
            self._log(f"coloured {written} entr{'y' if written == 1 else 'ies'} from the theme")
            QTimer.singleShot(800, self._reread)

    def _reread(self):
        self._organizer.refresh(False)       # re-read what was written; never save MO2's copy over it

    def _restore(self):
        o = self._originals()
        if not o["conflicts"] and not o["entries"]:
            return
        s = self._ini()
        for key, value in o["conflicts"].items():
            if value is None:
                s.remove("Settings/" + key)
            else:
                s.setValue("Settings/" + key, _qcolor(value))
        s.sync()
        restored = 0
        try:
            mods_dir = self._organizer.modsPath()
            for n, line in o["entries"].items():
                if write_color_line(os.path.join(mods_dir, n, "meta.ini"), line):
                    restored += 1
        except Exception as exc:  # noqa: BLE001
            self._log(f"restore entries: {exc!r}")
        self._log(f"put back {len(o['conflicts'])} conflict colour(s) and {restored} entry colour(s)")
        try:
            os.remove(self._originals_path())
        except OSError:
            pass
        if restored:
            QTimer.singleShot(800, self._reread)

    # log ------------------------------------------------------------------------------------------------------------
    def _log(self, msg):
        try:
            with open(os.path.join(self._data_dir(), "log.txt"), "a", encoding="utf-8") as fh:
                fh.write(time.strftime("%Y-%m-%d %H:%M:%S ") + msg + "\n")
        except Exception:  # noqa: BLE001
            pass


def createPlugin():
    return ThemeFramework()


# --- fault handling (standing rule, 2026-09-23: every MO2 plugin of ours logs and arms faulthandler) ---------------
def _arm_faulthandler():
    """Arm Python's faulthandler once per process, into plugins\\data\\faults.log. When MO2 dies inside C++ with a
    Python slot on the stack, the minidump names only modules; faulthandler writes the Python frames of every
    thread first, so the log names the plugin and the line. Whichever of our plugins loads first arms it."""
    try:
        import faulthandler
        if faulthandler.is_enabled():
            return
        here = os.path.abspath(__file__)
        while os.path.basename(here).lower() != "plugins":
            parent = os.path.dirname(here)
            if parent == here:
                return
            here = parent
        path = os.path.join(here, "data", "faults.log")
        os.makedirs(os.path.dirname(path), exist_ok=True)
        fh = open(path, "a", encoding="utf-8")
        fh.write(time.strftime("%Y-%m-%d %H:%M:%S") + " faulthandler armed by MO2ThemeFramework" + chr(10))
        fh.flush()
        globals()["_FAULT_LOG_HANDLE"] = fh          # kept open for the life of the process
        faulthandler.enable(file=fh, all_threads=True)
    except Exception:  # noqa: BLE001
        pass


_arm_faulthandler()
