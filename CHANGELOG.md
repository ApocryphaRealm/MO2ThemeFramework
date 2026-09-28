# Changelog - MO2 Theme Framework

Versions are issued by the project's version gate. Written as the change happens (rule 61).

## 1.0.0 - 2026-09-26

First version. The owner: *"could we make a plugin seperatley as a requirement for themes that does the things the
.qss file cant do alone like the separator color and the ini file edit? that way others can build their theme off of
it"*, and earlier the same day, *"exports that apply to other plugins ... just like how imgui draws in game and we
change the theme for amf and all mod menus change with it"*.

* Notices the theme MO2 is using and **reads its colours from the theme itself** - sample widgets styled by the sheet,
  plus the sheet's hover / selection / focus rules - so any theme works with no work from its author (the owner:
  *"couldnt we just make the plugin automatically read the current theme colors and apply them to added plugins as
  needed? no need for authors to do anything"*). Tested on Njordlinger, Dark Bronze and MO2's default look.
* An optional `theme.json` (format 1, THEME-AUTHORS.md) sets what no stylesheet can: separator / mod colours and the
  conflict colours.
* Writes the theme's six conflict colours to `ModOrganizer.ini`; colours separators (and mods, when the theme sets a
  colour) in `meta.ini`, including separators added later.
* Publishes the palette to every plugin: `mo2theme.palette` / `mo2theme.name` / `mo2theme.revision` on the application
  object, and the application `QPalette`.
* Re-colours the colours other plugins hard-code in their own widget stylesheets (the Plugin Browser sets about 40)
  onto the palette, per window from a timer - no application-wide event filter.
* Keeps every colour it replaces and puts them all back when a theme without `theme.json` is chosen, or on request.
* Its own window from the toolbar / Tools menu: which theme is active, four switches, apply again, put my colours back,
  open the theme's folder, and the guide for theme authors. Eleven languages.