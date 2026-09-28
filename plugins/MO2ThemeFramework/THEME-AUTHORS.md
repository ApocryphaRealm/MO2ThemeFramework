# Themes and MO2 Theme Framework

A Mod Organizer 2 theme is a `.qss` file (and usually a folder of images beside it) that the player pastes into
`<MO2>\stylesheets\`. MO2 applies it to every window. What a stylesheet **cannot** do in MO2 2.5.2:

* reach a plugin window whose widgets set their own stylesheet - a widget's own sheet always beats the theme;
* tell other plugins what its colours are;
* colour the mod list's conflict highlights - MO2 reads those from `ModOrganizer.ini`, not from the sheet;
* colour separators or mods - those live in each entry's `meta.ini`.

## You do not have to do anything for the first two

MO2 Theme Framework reads the colours of **whatever theme MO2 is using** straight from the theme: Qt gives every styled
widget the sheet's background and text colours, so the framework reads them off hidden sample widgets, and reads what
lives only in pseudo-state rules (`::item:hover`, `::item:selected`, `:focus`, `QLineEdit[valid-filter=false]`,
`LinkLabel { qproperty-linkColor }`) from the `.qss` text. With those it:

* **re-colours other plugins' windows** - the colours plugins hard-code in their own widget stylesheets (for example
  the Mod Organizer Plugin Browser's) are swapped for the matching colours of your theme;
* **publishes the palette** for plugins that want to follow the theme themselves (below), and sets the application
  `QPalette` from it.

It works for themes written before the framework existed. It notices a theme change within about a second and a half.

## theme.json - only for the mod list (optional)

Separator colours and the conflict highlights are a design choice, not something a stylesheet can express, so the
framework only changes them when your theme asks. Put a `theme.json` in your theme's folder:

```
stylesheets\
  MyTheme.qss
  MyTheme\
    theme.json
```

(`stylesheets\MyTheme.theme.json` beside the sheet also works.)

```json
{
  "mo2ThemeFramework": 1,
  "name": "MyTheme",
  "modList": {
    "separatorColor": "#000000",
    "modColor": null,
    "conflictColors": {
      "overwrittenLooseFilesColor": "#4000ff00",
      "overwritingLooseFilesColor": "#40ff0000",
      "overwrittenArchiveFilesColor": "#4000ffff",
      "overwritingArchiveFilesColor": "#40ff00ff",
      "containsPluginColor": "#400000ff",
      "containedColor": "#400000ff"
    }
  }
}
```

Colours: `#RRGGBB`, `#AARRGGBB` (alpha first, as Qt writes it) or `rgba(r, g, b, a)` with `a` from 0 to 1.

| Key | What the framework does with it |
|---|---|
| `modList.separatorColor` | Written to every separator's `meta.ini` (`color=`), and to separators created later. `null` = leave separators alone. |
| `modList.modColor` | The same for mods. `null` = leave mods alone (recommended - players colour mods themselves). |
| `modList.conflictColors` | Written to `ModOrganizer.ini [Settings]` under these exact keys. Leave a key out to leave that colour alone. |
| `palette` *(optional)* | `{ "role": "colour" }` - overrides a colour the framework read from the sheet (roles: `bg`, `text`, `text_bright`, `text_hover`, `text_disabled`, `hover`, `selected`, `frame`, `input`, `input_focus`, `mod_row`, `link`, `invalid`, `icon`, `icon_accent`). |
| `otherPlugins.remap` *(optional)* | `{ "#literal": "role or colour" }` - replaces the built-in table of colours other plugins hard-code. |

**Nothing is lost.** The first time a theme changes a mod-list colour, the framework records what was there. When the
player switches to a theme without a `theme.json` (or presses *Put my original colours back*), every conflict colour
and separator / mod colour goes back to what it was. Each part can be switched off in the framework's window.

## Reading the theme from your own plugin

```python
import json
from PyQt6.QtWidgets import QApplication

app = QApplication.instance()
raw = app.property("mo2theme.palette")
theme = json.loads(raw) if raw else None       # {"name": "MyTheme", "fromThemeJson": false, "roles": {"bg": "#000000", ...}}
revision = app.property("mo2theme.revision")  # changes every time the theme is (re)applied
```

Re-read it when `revision` changes (a `QTimer` you own is enough), or paint from `widget.palette()` - the framework
sets the application `QPalette` from the theme. Plugins that set no colours of their own need nothing at all: MO2's
stylesheet already reaches them.

## Toolbar and button icons

Pure stylesheet work. MO2 copies `qproperty-icon` from dummy buttons named after its toolbar actions onto the actions:
`#actionChange_Game`, `#actionInstallMod`, `#actionNexus`, `#actionModPage`, `#actionAdd_Profile`, `#action_Refresh`,
`#actionModify_Executables`, `#actionTool`, `#actionSettings`, `#actionEndorseMO`, `#actionNotifications`,
`#actionUpdate`, `#actionHelp`. MO2's own buttons take the icon directly: `#listOptionsBtn`, `#openFolderMenu`,
`#restoreModsButton`, `#saveModsButton`, `#clearFiltersButton`, `#bossButton`, `#refreshButton`, `#startButton`,
`#linkButton`, `#activateESP`, `#deactivateESP`, and others. Paths in `url()` are relative to the `.qss` file.
