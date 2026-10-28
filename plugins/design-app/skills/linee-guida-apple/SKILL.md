---
name: linee-guida-apple
description: Linee guida Apple (Human Interface Guidelines) per iPhone, iPad e Mac, in file da aprire solo per la parte che serve. Usala quando progetti o rivedi un'app Apple (SwiftUI/UIKit/AppKit), Dynamic Type, modo scuro, accessibilità.
---

# Linee guida Apple (HIG)

Prima le regole del progetto e la skill `interfacce`; queste servono per le convenzioni della piattaforma.
I file sono lunghi: **non leggerli interi**. Cerca la sezione che serve (es. `grep -n "^## " <file>`) e leggi solo
quella.

| Piattaforma | File (nel plugin) |
|---|---|
| iPhone | `riferimenti/apple-iphone.md` |
| iPad (multitasking, puntatore, tastiera, barra laterale) | `riferimenti/apple-ipad.md` |
| Mac (menu, barra degli strumenti, finestre, scorciatoie) | `riferimenti/apple-mac.md` |

Fonte e licenza (MIT): `riferimenti/FONTE.txt`. Il percorso del plugin: `${CLAUDE_PLUGIN_ROOT}` o la cartella sopra
`skills/` di questa skill.
