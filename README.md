# MO2 Theme Framework

A Mod Organizer 2 plugin that gives themes what a `.qss` stylesheet cannot do on its own:

* **Mod list colours** - the six conflict highlight colours (stored in `ModOrganizer.ini`) and separator / mod colours
  (stored in each `meta.ini`).
* **Other plugins' windows** - many plugins hard-code colours in their own widgets, which beats any theme; the framework
  maps those colours onto the theme's palette.
* **A palette other plugins can read** - `QApplication.instance().property("mo2theme.palette")`.

Themes stay ordinary MO2 themes: paste the `.qss` and its folder into `<MO2>\stylesheets`. The framework reads the
colours of whatever theme is in use from the theme itself, so other plugins follow **any** theme with nothing added to
it. Only the mod list's colours need the theme to ask, with a small `theme.json` in its folder - see
`plugins\MO2ThemeFramework\THEME-AUTHORS.md`. Switch to a theme without one and your original mod-list colours come back.

## Install

Copy `plugins\MO2ThemeFramework\` into `<MO2>\plugins\` and restart Mod Organizer 2. Requires MO2 2.5.x.

Licence: GPL-3.0-or-later (`LICENSE`, `NOTICE.md`).