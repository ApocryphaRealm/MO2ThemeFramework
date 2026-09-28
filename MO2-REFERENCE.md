# MO2 reference - how Mod Organizer 2 itself does what this plugin touches

Gate rule `mo2-plugin-documents-mo2s-own-implementation` requires this file in every MO2 plugin repo of ours. The source
reading below was done on 2026-09-26 at the v2.5.2 tags, before any of the plugin was written.

## How MO2 Theme Framework follows MO2

| What the plugin does | What MO2 does (source) | How ours follows it |
|---|---|---|
| Finds the theme in use | MO2 applies the selected `<exe dir>\stylesheets\<Name>.qss` app-wide as `file:///<path>` with `QApplication::setStyleSheet`, and has no theme-changed signal for plugins (https://github.com/ModOrganizer2/modorganizer/blob/v2.5.2/src/moapplication.cpp#L529-L533, #L650) | Reads `QApplication.styleSheet()` from its own unparented timer; the theme's folder and `theme.json` sit beside that path. The framework never sets the application sheet itself. |
| Conflict colours | Read from `ModOrganizer.ini [Settings]` (`overwrittenLooseFilesColor` etc.) as QColor values; no stylesheet property reaches them (https://github.com/ModOrganizer2/modorganizer/blob/v2.5.2/src/settings.cpp, section 2 below) | Written with `QSettings` on the same ini path, as QColor values (the `@Variant` encoding MO2 itself writes); the values found first are kept and put back. |
| Separator / mod colours | `meta.ini` `color=` per entry, no default for an uncoloured separator (section 2 below) | MO2 Default Colors' byte-exact writer, then `refresh(False)` so MO2 re-reads and never saves over it; originals kept and put back. |
| Other plugins' windows | A widget's own `setStyleSheet` outranks the application sheet (Qt `qcssparser.cpp`, section 5 below) | Rewrites only the colour tokens inside those widgets' own sheets, keeping each original to restore; from an unparented timer, per visible top-level window - never an application-wide event filter. |
| Icons and button faces | MO2 copies `qproperty-icon` from dummy buttons named after its toolbar actions (https://github.com/ModOrganizer2/modorganizer/blob/v2.5.2/src/mainwindow.cpp#L550-L616) | Not the framework's job: a theme sets them in its own sheet (THEME-AUTHORS.md). |
## MO2 2.5.2 source reading (verbatim from the plan folder)

Read 2026-09-26 from MO2's own source at the release tags. Every claim cites file and line.

- MO2 = `https://github.com/ModOrganizer2/modorganizer/blob/v2.5.2/src/<file>#L<n>`
- uibase = `https://github.com/ModOrganizer2/modorganizer-uibase/blob/v2.5.2/src/<file>#L<n>`
- Qt = `https://github.com/qt/qtbase/blob/v6.7.1/<path>#L<n>` (the installed MO2 ships Qt 6.7.1:
  `D:\Modlists\Njordlinger\dlls\Qt6Core.dll` ProductVersion 6.7.1.0; `ModOrganizer.exe` 2.5.2)
- `modorganizer-plugin_python` has **no `v2.5.2` tag** (GitHub API: tree not found; its tags stop at
  `release_v1.3.x`), so the mobase surface was checked against uibase `imoinfo.h` (which mobase wraps) and a
  string scan of the installed `plugins\plugin_python\libs\mobase.cp312-win_amd64.pyd`.

Logic library entries already on this topic (read first): "MO2's mod list ignores a style sheet's
view/viewport background for plain rows ..." (LOGIC-LIBRARY.md line 5119, including its correction: the
skyrim theme's `border-image` on `ModListView#modList` was the real blocker, and an `::item` background
erases conflict highlights), and "An MO2 crash 'in' a native plugin was a Python plugin's
application-wide event filter" (line 6648; no app-wide event filters in our plugins).

---

## 1. Theme loading

### Where themes are looked for
- The folder name is an app constant: `APPPARAM(std::wstring, stylesheetsPath, L"stylesheets")`
  - MO2 `shared/appconfig.inc#L7`.
- It is resolved against the **application directory** (where `ModOrganizer.exe` is), not the instance:
  - Loading: `applicationDirPath() + "/" + AppConfig::stylesheetsPath() + "/" + styleName` - MO2 `moapplication.cpp#L529-L531`.
  - Settings > Theme combo box lists `QCoreApplication::applicationDirPath()/stylesheets/*.qss`, top level only
    (no subdirectory recursion flag) - MO2 `settingsdialogtheme.cpp#L55-L63`. Entry text is the file's
    `completeBaseName()`, item data is the file name (`Njordlinger.qss`) - `#L62`.
  - The combo box also offers "None" (data `""`) and every `QStyleFactory::keys()` entry (windowsvista,
    Windows, Fusion) - `settingsdialogtheme.cpp#L48-L53`.
  - For a global (non-portable) instance this is still the install dir, so themes are shared by all
    instances run from that MO2 install. Njordlinger is portable, so it is `D:\Modlists\Njordlinger\stylesheets`.

### How the selection is stored
- `ModOrganizer.ini` `[Settings] style=<value>` - `InterfaceSettings::styleName()` / `setStyleName()`,
  MO2 `settings.cpp#L2129-L2137` (declared `settings.h#L590-L593`, comment "filename of the theme").
- The value is the qss **file name including extension** (e.g. `style=Njordlinger.qss`, observed in
  `D:\Modlists\Njordlinger\ModOrganizer.ini` line 26), or a QStyleFactory key, or empty for None.
- Fallback path (undocumented but in source): if `stylesheets/<style>` does not exist, `updateStyle(styleName)`
  is called with the raw value (`moapplication.cpp#L535-L536`); `updateStyle` loads it if it is a style
  factory key, otherwise if `QFile(styleName).exists()` - so an **absolute path** to a .qss elsewhere loads
  (`moapplication.cpp#L640-L654`). Caveats from source: that path is NOT added to the file watcher (only
  the first branch calls `m_styleWatcher.addPath`, `#L533`), and the Theme tab would not find it in its
  combo (`selectStyle` leaves the index unchanged when `findData` returns -1, `settingsdialogtheme.cpp#L66-L73`),
  so pressing OK in Settings writes whatever the combo shows (`update()`, `#L30-L40`) - probably "None".
  Not tested live.
- On startup an invalid style is cleared: `if (!setStyleFile(...)) setStyleName("")` - `moapplication.cpp#L333-L336`
  (in 2.5.2 `setStyleFile` always returns true, `#L520-L544`, so this never actually fires).

### Base style (`mo2-base-style` top comment)
- The QStyle under the sheet defaults to `windowsvista` (`moapplication.cpp#L158`). A qss can choose another
  with a single-line comment among the leading comment lines: `/* mo2-base-style: fusion */`
  (`extractTopStyleSheetComments` stops at the first non-empty line not starting with `/*`,
  `moapplication.cpp#L564-L598`; `extractBaseStyleFromStyleSheet` parses `mo2-base-style:<key>`,
  case-insensitive against `QStyleFactory::keys()`, `#L600-L636`). Every style is wrapped in MO2's
  `ProxyStyle` (drop-indicator drawing, `#L60-L105`).
- `Njordlinger.qss` currently starts with a multi-line `/*!****` banner, so it has no base-style line and runs
  on windowsvista.

### How it is applied (answers "do plugin dialogs inherit it?")
- **Application-wide**: `MOApplication` derives from `QApplication` (`moapplication.h#L39`, ctor `moapplication.cpp#L147`) and calls
  `setStyle(new ProxyStyle(...))` then `setStyleSheet(QString("file:///%1").arg(fileName))`
  - `moapplication.cpp#L646-L650`. That is `QApplication::setStyleSheet`, not the main window's.
- Consequence: every widget in the process, including dialogs created by Python plugins (even parentless
  top-level `QDialog(None)`), gets the theme, unless the widget (or an ancestor) sets its own stylesheet,
  which wins (see section 5 for why).
- The main window never calls `setStyleSheet` on itself; its `updateStyle` slot only refreshes action icons
  (`mainwindow.cpp#L687-L690`).

### How relative `url()` paths resolve
- Because MO2 passes `file:///<path>`, Qt strips the prefix and parses as a file
  (`qstylesheetstyle.cpp#L1690-L1693`: `if (ss.startsWith("file:///")) ss.remove(0, 8); parser.init(ss, qApp->styleSheet() != ss)`).
- `QCss::Parser::init(css, isFile=true)` sets `sourcePath = QFileInfo(file).absolutePath() + '/'`
  (`src/gui/text/qcssparser.cpp#L2310-L2325`), and every relative `url(...)` is prefixed with it
  (`qcssparser.cpp#L2816-L2820`).
- So `url("./Njordlinger/x.png")` or `url(Njordlinger/x.png)` resolves against the **folder containing the
  .qss** (`<MO2>\stylesheets\`), independent of the working directory. Shipped themes use this
  (`Paper Automata.qss` line 319-321: `url("./Paper/Automata/Toolbar/instances.svg")`).

### Runtime re-read / re-apply
- **Live file reload**: MO2 watches the selected qss with a `QFileSystemWatcher`
  (`moapplication.cpp#L152-L155` connect, `#L533` addPath) and re-runs `updateStyle(file)` on change. Only
  the .qss itself is watched; changed images referenced by `url()` are not (nothing adds them).
- **Theme change from Settings**: `ThemeSettingsTab::update()` writes the key and emits
  `Settings::styleChanged` (`settingsdialogtheme.cpp#L30-L40`) -> forwarded as `MainWindow::styleChanged`
  (`mainwindow.cpp#L389-L390`) -> `MOApplication::setStyleFile` via a queued connection
  (`moapplication.cpp#L348-L353`) and then `MainWindow::updateStyle` -> `resetActionIcons()`
  (`mainwindow.cpp#L1226-L1233`, `#L687-L690`). No restart needed.

### Can a plugin provide or register a theme?
- **No API for it in 2.5.2.** uibase v2.5.2's plugin interfaces are `IPlugin`, `IPluginDiagnose`,
  `IPluginFileMapper`, `IPluginGame`, `IPluginInstaller(Simple/Custom)`, `IPluginList`, `IPluginModPage`,
  `IPluginPreview`, `IPluginProxy`, `IPluginTool` (+ game features) - full header list read from the v2.5.2
  tree; none mentions style/theme. `IOrganizer` (`imoinfo.h`) has no style method or signal.
- `IPluginFileMapper::mappings()` (`ipluginfilemapper.h#L31-L41`) maps files into the **game's virtual
  data directory** for launched programs (usvfs); it does not affect MO2's own `applicationDirPath()` reads.
- MO2 only discovers themes by listing `<app>/stylesheets/*.qss` (above). Practical options for a plugin:
  1. Ship/copy the .qss (+ its asset folder) into `<app>\stylesheets\` - exactly what the Plugin Browser does
     for Nexus category "Mod Organizer 2 Themes" (`utility/plugin_installer.py:169-174`, destination
     `QCoreApplication.applicationDirPath()/stylesheets`). It appears in the combo on the next Settings open.
  2. Call `QApplication.instance().setStyleSheet(...)` itself. Works (app-wide) but bypasses MO2's setting;
     MO2 overwrites it on the next theme change or watched-file change (`moapplication.cpp#L646-L650`).

---

## 2. Mod list and plugin list colours

### ModOrganizer.ini keys (all read live on every paint; `ColorSettings` holds no cache, it calls
`get<QColor>(m_Settings, ...)` each time - `settings.cpp#L1224-L1317`)

| Key (INI section) | Getter | Default (r,g,b,a) | Settings dialog caption (`colortable.cpp`) | Source |
|---|---|---|---|---|
| `[Settings] overwrittenLooseFilesColor` | `modlistOverwrittenLoose` | 0,255,0,64 | Is overwritten (loose files) `#L199-L206` | `settings.cpp#L1224-L1233` |
| `[Settings] overwritingLooseFilesColor` | `modlistOverwritingLoose` | 255,0,0,64 | Is overwriting (loose files) `#L208-L215` | `#L1235-L1244` |
| `[Settings] overwrittenArchiveFilesColor` | `modlistOverwrittenArchive` | 0,255,255,64 | Is overwritten (archives) `#L217-L224` | `#L1246-L1255` |
| `[Settings] overwritingArchiveFilesColor` | `modlistOverwritingArchive` | 255,0,255,64 | Is overwriting (archives) `#L226-L233` | `#L1257-L1266` |
| `[Settings] containsPluginColor` | `modlistContainsPlugin` | 0,0,255,64 | Mod contains selected plugin `#L235-L242` | `#L1268-L1277` |
| `[Settings] containedColor` | `pluginListContained` | 0,0,255,64 | Plugin is contained in selected mod `#L244-...` | `#L1279-L1287` |
| `[General] previousSeparatorColor` | `previousSeparatorColor` | none (optional) | - (last colour picked in "Select color") | `#L1289-L1307` |
| `[Settings] colorSeparatorScrollbars` | `colorSeparatorScrollbar` | true | Settings > Mod List checkbox `colorSeparatorsBox` (`settingsdialogmodlist.cpp#L28`, `#L53`) | `#L1309-L1317` |
| `[Settings] collapsible_separators_conflicts_to` / `_from` | `collapsibleSeparatorsHighlightTo/From` | true | Settings > Mod List | `settings.cpp#L2153-L2171` |

- Section mapping: `settingName()` writes `General` keys without a prefix (i.e. INI `[General]`) and every
  other section as `Section/key` (`settingsutilities.cpp#L28-L41`).
- **Encoding**: `set()` stores the `QColor` as a `QVariant` via `QSettings::setValue` (`settingsutilities.h#L64-L84`),
  so IniFormat writes Qt's binary variant form:
  `@Variant(\0\0\0\x43\x1 AAAA RRRR GGGG BBBB \0\0)` - 4-byte type id 0x43 (QColor), 1-byte spec (1 = RGB),
  then five big-endian quint16: alpha, red, green, blue, pad; each 8-bit channel is stored as `c*257`
  (0x40 -> `@@` = 0x4040). Checked against the live file: `overwrittenLooseFilesColor=@Variant(\0\0\0\x43\x1@@\0\0\xff\xff\0\0\0\0)`
  = (0,255,0,64), the default (`ModOrganizer.ini` line 27). The byte layout is Qt's QColor datastream
  format, inferred from the samples rather than read from Qt source.
- Getting a readable value from Python: `QSettings(path, QSettings.Format.IniFormat).value("Settings/overwrittenLooseFilesColor")` returns a `QColor`.

### Separator colours
- Per mod/separator `meta.ini` key `color` (`[General]`), same `@Variant` QColor encoding: read
  `metaFile.value("color", QColor())` (`modinforegular.cpp#L176`), written `#L275`. Separators are
  `ModInfoSeparator : ModInfoRegular` (`modinfoseparator.cpp#L41-L43`), so they use the same field.
  Example: `mods\--- 0 BASE & ENGINE ---_separator\meta.ini` line 2 `color=@Variant(\0\0\0\x43\x1\xff\xff\0\0\0\0\0\0\0\0)` (opaque black).
- Model: `Qt::BackgroundRole`/`ScrollMarkRole` return the colour for the Notes column of any mod, and for
  every column of a **separator** (scroll mark only if `colorSeparatorScrollbars`) - `modlist.cpp#L370-L380`.
  A non-separator mod never gets a full-row colour from `meta.ini`.
- **No colour set = no default colour**: the model returns an invalid `QVariant()` (`modlist.cpp#L377-L379`),
  so the row is drawn with the style's base/alternate-base like any mod. There is no "default separator
  colour" setting.
- New separators get `previousSeparatorColor` if one is stored (`modlistviewactions.cpp#L198-L200`).
  "Select color" stores the pick there (`#L1172`); "Reset color" clears the mods' colours and removes the key
  (`#L1180-L1187`).

### How the list paints them (and what a stylesheet can do)
- `ModListStyledItemDelegate::paint` (`modlistview.cpp#L67-L118`): colour = `markerColor(index)` (conflict /
  contains-plugin markers), else the model's BackgroundRole; assigned to `opt.backgroundBrush` (`#L83-L87`).
  Text colour on separator Name/Priority cells and Notes cells is recomputed with
  `ColorSettings::idealTextColor` (black or white by luminance, `settings.cpp#L1319-L1329`) after blending the
  colour over `palette.base()`/`alternateBase()` (`modlistview.cpp#L89-L112`) - so the stylesheet's
  `background-color`/`alternate-background-color` feed that blend.
- `markerColor` mapping (`modlistview.cpp#L1136-L1194`): highlight -> containsPlugin; `overwritten` or
  `archiveLooseOverwritten` sets -> **overwriting**Loose colour; `overwrite`/`archiveLooseOverwrite` ->
  **overwritten**Loose; `archiveOverwritten` -> overwritingArchive; `archiveOverwrite` -> overwrittenArchive;
  a collapsed separator (with "conflicts to" on) averages its children's marker colours.
- Scrollbar marks: `ModListViewMarkingScrollBar::color` = marker colour, else `ScrollMarkRole` (`modlistview.cpp#L120-L135`).
- Plugin list: `PluginList::backgroundData` returns `pluginListContained` for plugins in the selected mod
  (`pluginlist.cpp#L1235-L1243`); foreground hardcoded: force-loaded `Qt::gray`, force-disabled `Qt::darkRed`
  (`#L1220-L1233`).
- Mod list foreground is hardcoded in the model: name `Qt::darkRed` (important) / `Qt::darkGray` (invalid),
  version `Qt::red` (update/downgrade) / `Qt::darkGreen` (`modlist.cpp#L352-L369`).
- **None of these colours can be set from a stylesheet in 2.5.2.** There is no `Q_PROPERTY` on
  `ModListView`, `PluginListView`, `ViewMarkingScrollBar` or any delegate: a grep of all 162 `src/*.h`
  files at v2.5.2 finds `Q_PROPERTY` only in `lootdialog.h#L19` (text) and `texteditor.h#L32-L33`,
  `#L83-L86` (`TextEditorLineNumbers` / `TextEditor`: `qproperty-textColor`, `qproperty-backgroundColor`,
  `qproperty-highlightBackgroundColor`); uibase adds only `LinkLabel` `qproperty-linkColor`
  (`linklabel.h#L26`). The conflict colours come only from `ModOrganizer.ini` (or Settings > Theme > colour table).
- What a stylesheet *does* control (logic library, measured 2026-09-15): `QTreeView#modList { background-color; alternate-background-color }`
  paints plain rows once the skyrim `border-image` is removed; an `::item { background }` rule is drawn
  instead of `opt.backgroundBrush` and therefore erases separator colours and conflict highlights.

---

## 3. Toolbar and main-window object names (`mainwindow.ui` at v2.5.2)

### Main toolbar `QToolBar#toolBar` (`mainwindow.ui#L1438-L1474`), in order
| objectName | text | .ui line |
|---|---|---|
| `actionChange_Game` | Manage Instances... | `#L1838` |
| `actionInstallMod` | Install Mod... | `#L1616` |
| `actionNexus` | Visit Nexus | `#L1718` |
| `actionModPage` | Browse Mod Page (drop-down menu) | `#L1739` |
| `actionAdd_Profile` | Profiles... | `#L1637` |
| `action_Refresh` | Refresh | `#L1950` |
| `actionModify_Executables` | Executables... | `#L1658` |
| `actionTool` | Tool Plugins (drop-down menu; IPluginTool entries live here) | `#L1679` |
| `actionSettings` | Settings... | `#L1697` |
| (separator; MO2 inserts an expanding spacer before the last separator so the rest right-align, `mainwindow.cpp#L709-L724`) | | `#L1469` |
| `actionEndorseMO` | Endorse ModOrganizer (menu) | `#L1820` |
| `actionNotifications` | Notifications... (the "problems" button; older themes also style `#actionProblems`, which does not exist in 2.5.2) | `#L1781` |
| `actionUpdate` | Update Mod Organizer | `#L1760` |
| `actionHelp` | Help (menu) | `#L1799` |

- Pinned executables are added at runtime as actions named `custom__<exe title>` before the right-aligned
  group (`mainwindow.cpp#L740-L776`).
- `actionModPage`, `actionTool`, `actionHelp`, `actionEndorseMO` get a `QMenu` and `InstantPopup` mode
  (`mainwindow.cpp#L700-L704`, `#L730-L737`).
- Menu-only actions: `actionExit`, `actionToolBarMainToggle`, `actionToolBarSmallIcons`, `actionToolBarMediumIcons`,
  `actionToolBarLargeIcons`, `actionToolBarIconsOnly`, `actionToolBarTextOnly`, `actionToolBarIconsAndText`,
  `actionMainMenuToggle`, `actionStatusBarToggle`, `actionViewLog` (`#L1856-L1949`).
- Menus: `QMenuBar#menuBar` with `QMenu#menuFile`, `#menuView` (sub `#menuToolbars`), `#menuTools`,
  `#menuRun`, `#menuHelp` (`#L1476-L1551`).

### What a stylesheet can actually do with `#actionXxx`
- The real toolbar buttons are anonymous: Qt creates `new QToolButton(tb)` with no object name
  (`src/widgets/widgets/qtoolbarlayout.cpp#L697-L710`). So `#actionInstallMod { background: ... }` does
  **not** reach the toolbar button.
- MO2's hack (`MainWindow::resetActionIcons`, `mainwindow.cpp#L550-L616`): for each QAction it polishes a
  dummy `QToolButton` named after the action and copies **only the icon** to the toolbar button and the
  action (menu bar). So `#actionXxx { qproperty-icon: url(...); }` is the one supported per-action
  property; it re-runs on every theme change (`#L687-L690`). The notifications icon is remembered for the
  problem-count badge (`#L606-L611`).
- To style the buttons themselves use `QToolBar#toolBar QToolButton { ... }` (all of them) or
  `QToolButton[popupMode="2"]` (the four menu buttons, InstantPopup) - the latter is a generic Qt property
  selector, not MO2-specific.

### Other named widgets worth theming
- Left pane: `categoriesSplitter`, `categoriesGroup` (QGroupBox), `filters` (QTreeWidget), `filtersClear`,
  `filtersEdit`, `filtersAnd`, `filtersOr` (radio), `filtersSeparators` (combo) - `#L38-L218`.
- Mod pane: `splitter`, `profileBox` (combo), `listOptionsBtn`, `openFolderMenu`, `restoreModsButton`,
  `saveModsButton`, `activeModslabel`, `activeModsCounter` (LCDNumber), **`ModListView#modList`**,
  `displayCategoriesBtn`, `currentCategoryLabel`, `clearFiltersButton`, `groupCombo`,
  `MOBase--LineEditClear#modFilterEdit` - `#L219-L592`.
- Right pane: `QFrame#startGroup`, **`executablesListBox`** (combo), **`startButton`** (Run),
  **`linkButton`** (shortcut menu), **`QTabWidget#tabWidget`** with tabs `espTab`, `bsaTab`, `dataTab`,
  `savesTab`, `downloadTab` - `#L593-L1437`.
- Plugins tab: `sortButton` (Sort/LOOT), `restoreButton`, `saveButton`, `activePluginsLabel`,
  `activePluginsCounter`, **`PluginListView#espList`**, **`espFilterEdit`** - `#L781-L1005`.
- Archives: `managedArchiveLabel` (LinkLabel), `bsaList`. Data: `dataTabRefresh`, `dataTree`,
  `dataTabShowOnlyConflicts`, `dataTabShowFromArchives`, `dataTabFilter`. Saves: `savegameList`.
  Downloads: `btnRefreshDownloads`, `DownloadListView#downloadView`, `showHiddenBox`, `downloadFilterEdit`.
- Chrome: `StatusBar#statusBar`, `QDockWidget#logDock` with `LogList#logList` - `#L1475`, `#L1552-L1600`.

---

## 4. Python plugin API (mobase 2.5.2)

- **Reading the theme name: no mobase call.** `IOrganizer` (`uibase imoinfo.h#L79-L570`) has nothing for
  style or colours, and a string scan of the installed `mobase.cp312-win_amd64.pyd` finds no
  stylesheet/colour/style-name symbols. `pluginSetting(pluginName, key)` only reads the in-memory map of
  **declared plugin settings** (`settings.cpp#L1404-L1418`), never `[Settings]`.
- **Via Qt instead (works in-process):** `QApplication.instance().styleSheet()` returns
  `"file:///<MO2>/stylesheets/<name>.qss"` when a qss is active, `""` for None or a factory style
  (`moapplication.cpp#L539-L540`, `#L642-L650`). Strip the prefix and take the file name.
- **Notification of a theme change: no MO2 callback.** `onPluginSettingChanged` fires only from
  `PluginSettings::setSetting`/plugin setting maps (`settings.cpp#L1436`, `#L1461`, `#L1468`; wired
  `organizercore.cpp#L148-L150`), not from `Settings::styleChanged`. The available callbacks are
  onAboutToRun, onFinishedRun, onUserInterfaceInitialized, onNextRefresh, onProfileCreated/Renamed/Removed/Changed,
  onPluginSettingChanged, onPluginEnabled/Disabled (`imoinfo.h#L414-L562`).
  **Qt route:** MO2 calls `QApplication::setStyle(new ProxyStyle...)` on every theme change and every
  watched-file reload (`moapplication.cpp#L644`, `#L648`, `#L539`), and `QApplication::setStyle` sends
  `QEvent::StyleChange` to every widget without `WA_SetStyle` (`qapplication.cpp#L1028-L1035`). So a
  plugin widget can override `changeEvent`/`event` (or filter **its own** widget - not an app-wide filter)
  for `QEvent.Type.StyleChange` and re-read `qApp.styleSheet()`.
- **Reading ColorSettings: not exposed**; read `ModOrganizer.ini` with `QSettings(ini, IniFormat)`
  (`Settings/overwrittenLooseFilesColor` etc. return `QColor`). The instance ini path is the one MO2 opens as
  `QSettings(path, IniFormat)` (`settings.cpp#L64-L66`); for a portable instance it is
  `<app>\ModOrganizer.ini`. mobase has no call returning that path - that is not confirmed from source; for
  Njordlinger it is `D:\Modlists\Njordlinger\ModOrganizer.ini`.
- **Setting ColorSettings:** no mobase setter. Two routes:
  1. Write the ini while MO2 is closed (safe, certain).
  2. Write it live with `QSettings` on the **same absolute path**. Qt shares one `QConfFile` per absolute
     path within a process (`src/corelib/io/qsettings.cpp#L153-L165`, cache keyed by
     `QFileInfo(fileName).absoluteFilePath()`), and MO2 reads the colours on every paint with no cache
     (`settings.cpp#L1224-L1317`), so a live write should take effect on the next repaint of the list.
     This is inferred from source, **not tested**; the path string must match MO2's exactly, and MO2
     rewrites the ini on exit (logic library line 6101) from that same shared data.
- Separator colours: edit `meta.ini` `color=` (write while MO2 is closed, or expect MO2 to rewrite
  meta.ini from its in-memory `m_Color` when it saves the mod, `modinforegular.cpp#L268-L276`). mobase's
  `IModInterface` declares only a `color()` getter (`uibase imodinterface.h#L142-L144`); no setter.

---

## 5. Mod Organizer Plugin Browser (`D:\Modlists\Njordlinger\plugins\Mod Organizer Plugin Browser\`)

### How it builds its UI
- `IPluginTool.display()` creates a single `BrowserDialog` (a `QDialog`) **with no parent**
  (`plugin_browser.py:56-72`; `ui/ui_main.py:25-37`, `super().__init__(parent)` with `parent=None`) and
  `show()`s it non-modally. Composed of plain PyQt6 widgets built in code (no .ui files): header `QLabel`,
  `ErrorBanner`, `RestartBanner`, `Sidebar(QFrame)`, `QStackedWidget` holding `PluginGridView` (tiles
  `ModTile(QFrame)`) and `DetailView` (with `FileCard`s); `APIKeyEntry(QDialog)` for the key.
- It uses no `QPalette`, `setPalette`, `QColor`, `setBackground/Foreground` or `setStyle` anywhere
  (grep of every .py). All styling is `setStyleSheet` on its own widgets.

### Why these override the app theme
- Qt gives each widget-level sheet a higher depth than the app sheet (`qstylesheetstyle.cpp#L1705-L1731`:
  app sheet `depth = 1` at #L1697; object sheets `depth = size - i + 2` at #L1728), and depth outweighs selector
  specificity (`qcssparser.cpp#L2110`: weight = specificity + (origin+depth)*0x100000). So any property set
  below beats the theme for that widget regardless of how specific the theme's selector is.
- Sheets with no selector are wrapped as `* { ... }` (`qstylesheetstyle.cpp#L1713-L1716`), so they apply to
  the widget **and all its descendants**.

### Every hardcoded style call (file:line; `ui/` unless noted)
| Location | Target | What it forces |
|---|---|---|
| `ui_main.py:47-56` | BrowserDialog | `QStackedWidget`, `QScrollArea` background transparent, no border |
| `ui_main.py:63-73` | header QLabel | bg #121212, text #F1F1F1, border #000000, 14px |
| `ui_main.py:107` | main_stack | `background-color: transparent` (bare -> all descendants) |
| `ui_api_key_entry.py:17-45` | APIKeyEntry dialog | QDialog bg #000000 border #2b2b2b; QLabel #C0C0C0; `QLabel#Header` #F1F1F1; QLineEdit bg #121212 text #F1F1F1 border #5F5F5E selection #5F5F5E; QPushButton padding |
| `ui_api_key_entry.py:103` | status label | color #95BED9 bold |
| `ui_api_key_entry.py:109` | status label | color #ff6b6b |
| `ui_detail_view.py:66` | title | 20pt bold (no colour) |
| `ui_detail_view.py:77` | "uploaded by" label | 16px bold |
| `ui_detail_view.py:84` | author name | color #3399FF |
| `ui_detail_view.py:109-112` | top section QWidget | bare `background: #121212` (-> descendants) |
| `ui_detail_view.py:119` | image label | bg #121212, text #F1F1F1 |
| `ui_detail_view.py:123`, `127,132,136,141,145` | endorse/download/update/uninstall/Nexus buttons | font-size/bold/padding only (bare -> no colours) |
| `ui_detail_view.py:164`, `170` | files section / container | transparent |
| `ui_detail_view.py:191`, `285` | placeholder / loading label | color #C0C0C0 |
| `ui_detail_view.py:222` | uploader link (inline HTML) | `style="color: #3399FF"` |
| `ui_detail_view.py:309` | error label | color #3399FF |
| `ui_error_banner.py:15-37` | `#ErrorBanner` | bg #3a0000, border #661111; QLabel #F1F1F1; QPushButton bg #661111 text #F1F1F1, hover #8a1a1a |
| `ui_restart_banner.py:15-37` | `#RestartBanner` | bg #212121, border #5F5F5E; QLabel #5F5F5E; QPushButton bg #5F5F5E text #F1F1F1, hover #656565 |
| `ui_file_card.py:41-44` | FileCard (`WA_StyledBackground`, :40) | bare bg #121212 (-> descendants) |
| `ui_file_card.py:73` | install button | bold, padding |
| `ui_file_card.py:81` | name label | 16px bold, border 0 |
| `ui_file_card.py:96-100` | changelog container | bare border-top #000000, bg #141414 |
| `ui_grid_view.py:12`, `26`, `29` | grid view, scroll area, container | transparent (bare -> descendants) |
| `ui_grid_view.py:43-53` | header QFrame | border-bottom #121212; QLabel #F1F1F1 |
| `ui_grid_view.py:59` | total label | color #C0C0C0 |
| `ui_grid_view.py:77` | sort dropdown | padding |
| `ui_grid_view.py:89-92` | prev/next buttons | padding only |
| `ui_grid_view.py:93` | page label | color #F1F1F1 |
| `ui_sidebar.py:9-20` | Sidebar | bg #121212, border-right #121212; QLabel #F1F1F1 |
| `ui_sidebar.py:26` | search QLineEdit | padding |
| `ui_sidebar.py:43-57` | category QListWidget | transparent; `::item:selected` bg #5F5F5E text #F1F1F1 |
| `ui_tiles.py:24-36` | ModTile | bg #121212, border #000000, hover border #5F5F5E |
| `ui_tiles.py:45` | tile image | bg #121212, text #F1F1F1 |
| `ui_tiles.py:54` | tile name | color #F1F1F1 |
| `ui_tiles.py:70` | author avatar | bg #121212 |
| `ui_tiles.py:74` | author label | color #F1F1F1 |
| `ui_tiles.py:88`, `90` | updated / created labels | color #C0C0C0 |
| `ui_tiles.py:114` | stat labels | color #F1F1F1 |
| `ui_tiles.py:122-128`, `133-139` | INSTALLED / UPDATE AVAILABLE badges | color #3399FF on #000000 |

- Object names it sets (targetable, but its own sheets still win on the properties they set):
  `Header` (`ui_api_key_entry.py:52`), `ErrorBanner` (`ui_error_banner.py:13`), `RestartBanner`
  (`ui_restart_banner.py:13`). Class-name selectors that work from a theme: `BrowserDialog`, `Sidebar`,
  `ModTile`, `FileCard`, `PluginGridView`, `DetailView`, `APIKeyEntry` (PyQt6 exposes the Python class name
  to the style engine; that is Qt/PyQt behaviour, not verified in this read).
- What the theme still controls there: anything those sheets do not set - QPushButton colours on the grid,
  detail and file-card buttons (only font/padding set), the sort `QComboBox`, the search `QLineEdit`
  colours (padding only), scrollbars, the dialog's own background (only `QStackedWidget`/`QScrollArea`
  forced transparent; the `BrowserDialog` background itself comes from the theme).
- `update_notification.py` has no styling calls.
- Theme install behaviour: for Nexus category "Mod Organizer 2 Themes" it installs into
  `<app>\stylesheets` (`utility/plugin_installer.py:169-174`).
