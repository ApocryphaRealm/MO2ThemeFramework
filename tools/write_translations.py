"""Writes plugins\\MO2ThemeFramework\\translations\\<language>.txt ($KEY<TAB>text, UTF-16LE with a BOM - the shape of our
SKSE translation files, which .MD\\scripts\\translation-coverage.py reads). English comes from the plugin's own TR()
defaults; the other ten are below, one row per key in LANGS order. Run from the repo root after changing a string.
"""
import codecs
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PLUGIN = os.path.join(ROOT, "plugins", "MO2ThemeFramework", "__init__.py")
OUT = os.path.join(ROOT, "plugins", "MO2ThemeFramework", "translations")
LANGS = ["japanese", "korean", "chinese", "russian", "german", "french", "spanish", "italian", "polish", "czech"]

T = {
 "MTF_Name": ["MO2 Theme Framework"] * 10,
 "MTF_Tooltip": [
  "有効なテーマのセパレーター、MOD リスト、プラグインの色", "활성 테마의 구분자, 모드 목록, 플러그인 색상", "来自当前主题的分隔符、模组列表和插件颜色",
  "Цвета разделителей, списка модов и плагинов из активной темы", "Trenner-, Mod-Listen- und Plugin-Farben aus dem aktiven Theme",
  "Couleurs des séparateurs, de la liste des mods et des plugins issues du thème actif",
  "Colores de separadores, lista de mods y plugins del tema activo", "Colori di separatori, elenco mod e plugin dal tema attivo",
  "Kolory separatorów, listy modów i wtyczek z aktywnego motywu", "Barvy oddělovačů, seznamu modů a pluginů z aktivního motivu"],
 "MTF_Description": [
  "スタイルシートだけではできないことを MO2 のテーマに与えます:セパレーターと MOD の色、MOD リストの競合色、他のプラグインが読めるパレット、テーマ色の他プラグインのウィンドウ。",
  "스타일시트만으로 할 수 없는 것을 MO2 테마에 제공합니다: 구분자와 모드 색상, 모드 목록 충돌 색상, 다른 플러그인이 읽을 수 있는 팔레트, 테마 색상의 다른 플러그인 창.",
  "为 MO2 主题提供样式表无法实现的功能:分隔符和模组颜色、模组列表冲突颜色、其他插件可读取的调色板,以及采用主题颜色的其他插件窗口。",
  "Даёт темам MO2 то, чего не может таблица стилей: цвета разделителей и модов, цвета конфликтов в списке модов, палитру для других плагинов и окна других плагинов в цветах темы.",
  "Gibt MO2-Themes, was ein Stylesheet nicht kann: Trenner- und Mod-Farben, Konfliktfarben der Mod-Liste, eine Palette für andere Plugins und deren Fenster in den Theme-Farben.",
  "Donne aux thèmes MO2 ce qu'une feuille de style ne peut pas faire : couleurs des séparateurs et des mods, couleurs de conflit de la liste, une palette lisible par les autres plugins et leurs fenêtres aux couleurs du thème.",
  "Da a los temas de MO2 lo que una hoja de estilos no puede: colores de separadores y mods, colores de conflicto de la lista, una paleta legible por otros plugins y sus ventanas con los colores del tema.",
  "Dà ai temi di MO2 ciò che un foglio di stile non può fare: colori di separatori e mod, colori dei conflitti nell'elenco, una tavolozza leggibile dagli altri plugin e le loro finestre nei colori del tema.",
  "Daje motywom MO2 to, czego nie potrafi arkusz stylów: kolory separatorów i modów, kolory konfliktów na liście, paletę czytelną dla innych wtyczek i ich okna w kolorach motywu.",
  "Dává motivům MO2 to, co šablona stylů nezvládne: barvy oddělovačů a modů, barvy konfliktů v seznamu, paletu čitelnou pro jiné pluginy a jejich okna v barvách motivu."],
 "MTF_Intro": [
  "テーマは .qss ファイルとフォルダーを MO2 の stylesheets フォルダーに貼り付けてインストールします。theme.json を同梱したテーマには、スタイルシートでは届かない部分(セパレーターと MOD の色、MOD リストの競合色、他のプラグインのウィンドウ)も適用されます。",
  "테마는 .qss 파일과 폴더를 MO2의 stylesheets 폴더에 붙여 넣어 설치합니다. theme.json을 포함한 테마는 스타일시트가 닿지 못하는 부분(구분자와 모드 색상, 모드 목록 충돌 색상, 다른 플러그인 창)까지 적용됩니다.",
  "将主题的 .qss 文件和文件夹粘贴到 MO2 的 stylesheets 文件夹即可安装。附带 theme.json 的主题还能覆盖样式表无法触及的部分:分隔符和模组颜色、模组列表冲突颜色以及其他插件的窗口。",
  "Темы устанавливаются вставкой их файла .qss и папки в папку stylesheets MO2. Тема с файлом theme.json получает и то, до чего таблица стилей не дотягивается: цвета разделителей и модов, цвета конфликтов в списке модов и окна других плагинов.",
  "Themes werden installiert, indem man ihre .qss-Datei und ihren Ordner in MO2s stylesheets-Ordner einfügt. Ein Theme mit theme.json bekommt auch, was ein Stylesheet nicht erreicht: Trenner- und Mod-Farben, Konfliktfarben der Mod-Liste und die Fenster anderer Plugins.",
  "Les thèmes s'installent en collant leur fichier .qss et leur dossier dans le dossier stylesheets de MO2. Un thème qui fournit un theme.json reçoit aussi ce qu'une feuille de style n'atteint pas : couleurs des séparateurs et des mods, couleurs de conflit de la liste et fenêtres des autres plugins.",
  "Los temas se instalan pegando su archivo .qss y su carpeta en la carpeta stylesheets de MO2. Un tema que incluye theme.json recibe también lo que una hoja de estilos no alcanza: colores de separadores y mods, colores de conflicto de la lista y ventanas de otros plugins.",
  "I temi si installano incollando il loro file .qss e la cartella nella cartella stylesheets di MO2. Un tema con theme.json riceve anche ciò che un foglio di stile non raggiunge: colori di separatori e mod, colori dei conflitti nell'elenco e finestre degli altri plugin.",
  "Motywy instaluje się, wklejając ich plik .qss i folder do folderu stylesheets MO2. Motyw z plikiem theme.json dostaje też to, czego arkusz stylów nie sięga: kolory separatorów i modów, kolory konfliktów na liście i okna innych wtyczek.",
  "Motivy se instalují vložením jejich souboru .qss a složky do složky stylesheets v MO2. Motiv se souborem theme.json dostane i to, kam šablona stylů nedosáhne: barvy oddělovačů a modů, barvy konfliktů v seznamu a okna jiných pluginů."],
 "MTF_GroupApply": ["テーマから適用", "테마에서 적용", "从主题应用", "Применять из темы", "Aus dem Theme anwenden", "Appliquer depuis le thème",
                    "Aplicar desde el tema", "Applica dal tema", "Zastosuj z motywu", "Použít z motivu"],
 "MTF_ApplyConflicts": ["MOD リストの競合色", "모드 목록 충돌 색상", "模组列表冲突颜色", "Цвета конфликтов в списке модов", "Konfliktfarben der Mod-Liste",
                        "Couleurs de conflit de la liste des mods", "Colores de conflicto de la lista de mods", "Colori dei conflitti nell'elenco mod",
                        "Kolory konfliktów na liście modów", "Barvy konfliktů v seznamu modů"],
 "MTF_ApplySeparators": ["セパレーターの色", "구분자 색상", "分隔符颜色", "Цвет разделителей", "Trennerfarbe", "Couleur des séparateurs",
                         "Color de los separadores", "Colore dei separatori", "Kolor separatorów", "Barva oddělovačů"],
 "MTF_ApplyMods": ["MOD の色(テーマが指定した場合)", "모드 색상(테마가 지정한 경우)", "模组颜色(主题设置时)", "Цвет модов (если тема его задаёт)",
                   "Mod-Farbe (wenn das Theme eine setzt)", "Couleur des mods (si le thème en définit une)", "Color de los mods (si el tema lo define)",
                   "Colore delle mod (se il tema lo imposta)", "Kolor modów (jeśli motyw go ustawia)", "Barva modů (pokud ji motiv nastaví)"],
 "MTF_ThemeOthers": ["他のプラグインのウィンドウ", "다른 플러그인의 창", "其他插件的窗口", "Окна других плагинов", "Fenster anderer Plugins",
                     "Fenêtres des autres plugins", "Ventanas de otros plugins", "Finestre degli altri plugin", "Okna innych wtyczek", "Okna jiných pluginů"],
 "MTF_Reapply": ["今すぐ再適用", "지금 다시 적용", "立即重新应用", "Применить снова", "Jetzt erneut anwenden", "Réappliquer maintenant",
                 "Aplicar de nuevo ahora", "Applica di nuovo ora", "Zastosuj ponownie teraz", "Znovu použít nyní"],
 "MTF_Restore": ["元の色に戻す", "원래 색상으로 되돌리기", "恢复我原来的颜色", "Вернуть мои исходные цвета", "Meine ursprünglichen Farben zurücksetzen",
                 "Remettre mes couleurs d'origine", "Restaurar mis colores originales", "Ripristina i miei colori originali",
                 "Przywróć moje oryginalne kolory", "Vrátit mé původní barvy"],
 "MTF_OpenFolder": ["テーマのフォルダーを開く", "테마 폴더 열기", "打开主题文件夹", "Открыть папку темы", "Ordner des Themes öffnen",
                    "Ouvrir le dossier du thème", "Abrir la carpeta del tema", "Apri la cartella del tema", "Otwórz folder motywu", "Otevřít složku motivu"],
 "MTF_Authors": ["テーマ作者向けガイド", "테마 제작자 가이드", "主题作者指南", "Руководство для авторов тем", "Anleitung für Theme-Autoren",
                 "Guide pour les auteurs de thèmes", "Guía para autores de temas", "Guida per gli autori di temi", "Poradnik dla autorów motywów",
                 "Průvodce pro autory motivů"],
 "MTF_Close": ["閉じる", "닫기", "关闭", "Закрыть", "Schließen", "Fermer", "Cerrar", "Chiudi", "Zamknij", "Zavřít"],
 "MTF_NoTheme": ["MO2 は既定の外観を使用しています(テーマ未選択)。", "MO2가 기본 모양을 사용 중입니다(테마 없음).", "MO2 正在使用默认外观(未选择主题)。",
                 "MO2 использует стандартный вид (тема не выбрана).", "MO2 verwendet das Standardaussehen (kein Theme gewählt).",
                 "MO2 utilise son apparence par défaut (aucun thème choisi).", "MO2 usa su aspecto predeterminado (ningún tema elegido).",
                 "MO2 usa l'aspetto predefinito (nessun tema scelto).", "MO2 używa domyślnego wyglądu (nie wybrano motywu).",
                 "MO2 používá výchozí vzhled (není vybrán motiv)."],
 "MTF_Active": ["テーマ: %1 - theme.json があり、フレームワークが適用中です。", "테마: %1 - theme.json이 있어 프레임워크가 적용 중입니다.",
                "主题:%1 - 已找到 theme.json,框架正在应用它。", "Тема: %1 - найден theme.json, фреймворк применяет его.",
                "Theme: %1 - theme.json gefunden, das Framework wendet es an.", "Thème : %1 - theme.json trouvé, le framework l'applique.",
                "Tema: %1 - se encontró theme.json; el framework lo está aplicando.", "Tema: %1 - trovato theme.json, il framework lo sta applicando.",
                "Motyw: %1 - znaleziono theme.json, framework go stosuje.", "Motiv: %1 - nalezen theme.json, framework jej používá."],
 "MTF_Error": ["テーマ: %1 - theme.json を使用できません: %2", "테마: %1 - theme.json을 사용할 수 없음: %2", "主题:%1 - 无法使用 theme.json:%2",
               "Тема: %1 - theme.json не удалось использовать: %2", "Theme: %1 - theme.json nicht verwendbar: %2",
               "Thème : %1 - theme.json inutilisable : %2", "Tema: %1 - no se pudo usar theme.json: %2", "Tema: %1 - impossibile usare theme.json: %2",
               "Motyw: %1 - nie można użyć theme.json: %2", "Motiv: %1 - theme.json nelze použít: %2"],
 "MTF_Plain": ["テーマ: %1 - 通常のスタイルシート(theme.json なし)。元の色を使用しています。", "테마: %1 - 일반 스타일시트(theme.json 없음). 원래 색상을 사용 중입니다.",
               "主题:%1 - 普通样式表(无 theme.json),正在使用你原来的颜色。", "Тема: %1 - обычная таблица стилей (без theme.json); используются ваши исходные цвета.",
               "Theme: %1 - ein einfaches Stylesheet (ohne theme.json); deine ursprünglichen Farben sind aktiv.",
               "Thème : %1 - une simple feuille de style (sans theme.json) ; vos couleurs d'origine sont utilisées.",
               "Tema: %1 - una hoja de estilos simple (sin theme.json); se usan tus colores originales.",
               "Tema: %1 - un semplice foglio di stile (senza theme.json); sono in uso i tuoi colori originali.",
               "Motyw: %1 - zwykły arkusz stylów (bez theme.json); używane są twoje oryginalne kolory.",
               "Motiv: %1 - obyčejná šablona stylů (bez theme.json); používají se vaše původní barvy."],
}


def english():
    s = open(PLUGIN, encoding="utf-8").read()
    keys = {"MTF_Name": "MO2 Theme Framework"}
    for m in re.finditer(r'TR\(\s*"(MTF_\w+)",\s*((?:"[^"]*"\s*)+)\)', s):
        keys[m.group(1)] = "".join(re.findall(r'"([^"]*)"', m.group(2)))
    for m in re.finditer(r'\(\s*"\w+",\s*"(MTF_\w+)",\s*"([^"]*)"\)', s):
        keys.setdefault(m.group(1), m.group(2))
    return keys

# 2026-09-26: colours are read from any theme itself; theme.json is only for the mod list (reworded strings)
T.update({
 "MTF_Intro": [
  "MO2 が使っているテーマの色をテーマ自体から読み取り、他のプラグインのウィンドウに適用して揃えます。theme.json も同梱したテーマは、スタイルシートではできないこと(セパレーターと MOD の色、MOD リストの競合色)も設定できます。",
  "MO2가 사용하는 테마의 색상을 테마 자체에서 읽어 다른 플러그인 창에 적용해 맞춥니다. theme.json도 포함한 테마는 스타일시트로 할 수 없는 것(구분자와 모드 색상, 모드 목록 충돌 색상)도 설정할 수 있습니다.",
  "无论 MO2 使用哪个主题,都会从主题本身读取其颜色并应用到其他插件的窗口,使其保持一致。同时附带 theme.json 的主题还能设置样式表无法设置的内容:分隔符和模组颜色以及模组列表冲突颜色。",
  "Какую бы тему ни использовал MO2, её цвета считываются из самой темы и передаются окнам других плагинов, чтобы они совпадали. Тема с файлом theme.json может задать и то, что недоступно таблице стилей: цвета разделителей и модов и цвета конфликтов в списке модов.",
  "Welches Theme MO2 auch verwendet: Seine Farben werden aus dem Theme selbst gelesen und an die Fenster anderer Plugins gegeben, damit sie passen. Ein Theme mit theme.json kann zusätzlich festlegen, was ein Stylesheet nicht kann: Trenner- und Mod-Farben und die Konfliktfarben der Mod-Liste.",
  "Quel que soit le thème utilisé par MO2, ses couleurs sont lues dans le thème lui-même et données aux fenêtres des autres plugins pour qu'elles s'accordent. Un thème qui fournit aussi un theme.json peut régler ce qu'une feuille de style ne peut pas : couleurs des séparateurs et des mods et couleurs de conflit de la liste.",
  "Sea cual sea el tema que usa MO2, sus colores se leen del propio tema y se aplican a las ventanas de otros plugins para que coincidan. Un tema que además incluye theme.json puede fijar lo que una hoja de estilos no puede: colores de separadores y mods y colores de conflicto de la lista.",
  "Qualunque tema usi MO2, i suoi colori vengono letti dal tema stesso e dati alle finestre degli altri plugin, così si abbinano. Un tema che include anche theme.json può impostare ciò che un foglio di stile non può: colori di separatori e mod e colori dei conflitti nell'elenco.",
  "Niezależnie od motywu używanego przez MO2 jego kolory są odczytywane z samego motywu i przekazywane oknom innych wtyczek, by do niego pasowały. Motyw, który dołącza też theme.json, może ustawić to, czego nie potrafi arkusz stylów: kolory separatorów i modów oraz kolory konfliktów na liście.",
  "Ať MO2 používá jakýkoli motiv, jeho barvy se načtou přímo z motivu a předají oknům jiných pluginů, aby ladily. Motiv, který přidá i theme.json, může nastavit to, co šablona stylů neumí: barvy oddělovačů a modů a barvy konfliktů v seznamu."],
 "MTF_NoTheme": [
  "MO2 は既定の外観を使用しています。その色を他のプラグインに適用します。", "MO2가 기본 모양을 사용 중이며, 그 색상을 다른 플러그인에 적용합니다.",
  "MO2 正在使用默认外观,其颜色会应用到其他插件。", "MO2 использует стандартный вид; его цвета передаются другим плагинам.",
  "MO2 verwendet das Standardaussehen; seine Farben gehen an andere Plugins.", "MO2 utilise son apparence par défaut ; ses couleurs sont données aux autres plugins.",
  "MO2 usa su aspecto predeterminado; sus colores se aplican a otros plugins.", "MO2 usa l'aspetto predefinito; i suoi colori vanno agli altri plugin.",
  "MO2 używa domyślnego wyglądu; jego kolory trafiają do innych wtyczek.", "MO2 používá výchozí vzhled; jeho barvy dostávají i jiné pluginy."],
 "MTF_Active": [
  "テーマ: %1 - テーマから色を読み取り他のプラグインに適用中。theme.json で MOD リストの色も設定しています。",
  "테마: %1 - 테마에서 색상을 읽어 다른 플러그인에 적용 중이며, theme.json으로 모드 목록 색상도 설정합니다.",
  "主题:%1 - 已从主题读取颜色并应用到其他插件;其 theme.json 还设置了模组列表颜色。",
  "Тема: %1 - цвета считаны из темы и переданы другим плагинам; её theme.json задаёт и цвета списка модов.",
  "Theme: %1 - Farben aus dem Theme gelesen und an andere Plugins gegeben; seine theme.json setzt auch die Farben der Mod-Liste.",
  "Thème : %1 - couleurs lues dans le thème et données aux autres plugins ; son theme.json règle aussi les couleurs de la liste des mods.",
  "Tema: %1 - colores leídos del tema y aplicados a otros plugins; su theme.json también fija los colores de la lista de mods.",
  "Tema: %1 - colori letti dal tema e dati agli altri plugin; il suo theme.json imposta anche i colori dell'elenco mod.",
  "Motyw: %1 - kolory odczytane z motywu i przekazane innym wtyczkom; jego theme.json ustawia też kolory listy modów.",
  "Motiv: %1 - barvy načteny z motivu a předány jiným pluginům; jeho theme.json nastavuje i barvy seznamu modů."],
 "MTF_Plain": [
  "テーマ: %1 - テーマから色を読み取り他のプラグインに適用中。theme.json がないため、MOD リストは元の色のままです。",
  "테마: %1 - 테마에서 색상을 읽어 다른 플러그인에 적용 중. theme.json이 없어 모드 목록은 원래 색상을 유지합니다.",
  "主题:%1 - 已从主题读取颜色并应用到其他插件。没有 theme.json,因此模组列表保留你自己的颜色。",
  "Тема: %1 - цвета считаны из темы и переданы другим плагинам. theme.json нет, поэтому список модов сохраняет ваши цвета.",
  "Theme: %1 - Farben aus dem Theme gelesen und an andere Plugins gegeben. Keine theme.json, daher behält die Mod-Liste deine eigenen Farben.",
  "Thème : %1 - couleurs lues dans le thème et données aux autres plugins. Pas de theme.json, la liste des mods garde donc vos couleurs.",
  "Tema: %1 - colores leídos del tema y aplicados a otros plugins. No tiene theme.json, así que la lista de mods conserva tus colores.",
  "Tema: %1 - colori letti dal tema e dati agli altri plugin. Nessun theme.json, quindi l'elenco mod mantiene i tuoi colori.",
  "Motyw: %1 - kolory odczytane z motywu i przekazane innym wtyczkom. Brak theme.json, więc lista modów zachowuje twoje kolory.",
  "Motiv: %1 - barvy načteny z motivu a předány jiným pluginům. Chybí theme.json, takže seznam modů si ponechá vaše barvy."],
})


def write(lang, table, order):
    body = "".join("$%s\t%s\r\n" % (k, table[k]) for k in order)
    with open(os.path.join(OUT, lang + ".txt"), "wb") as fh:
        fh.write(codecs.BOM_UTF16_LE + body.encode("utf-16-le"))


def main():
    en = english()
    order = list(T)
    gap = sorted(set(en) ^ set(order))
    if gap:
        raise SystemExit("keys out of step with the plugin: %s" % gap)
    if os.path.isdir(OUT):
        for f in os.listdir(OUT):
            os.remove(os.path.join(OUT, f))
    os.makedirs(OUT, exist_ok=True)
    write("english", en, order)
    for i, lang in enumerate(LANGS):
        write(lang, {k: T[k][i] for k in order}, order)
    print("wrote", 1 + len(LANGS), "files,", len(order), "keys each")


if __name__ == "__main__":
    main()
