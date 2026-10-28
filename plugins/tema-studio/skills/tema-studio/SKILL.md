---
name: tema-studio
description: I temi di Claude Code con i colori dello studio (blu notte o rosso su nero) e le parole della rotella in stile Pleyades. Usala per "metti il tema dello studio", "tema rosso", "cambia i colori di Claude", "parole dell'attesa".
---

# Tema dello studio

## Scegliere il tema
1. In Claude Code (terminale): scrivi `/theme` e scegli «Pleyades Studio» o «Pleiad Fire Red».
2. Vale per quel computer; per tornare indietro, `/theme` e un tema di base.
Il rosso vuole uno sfondo nero pieno: lo decide il programma del terminale, non Claude.
- Mac: `pleyades-cli tema` installa il profilo «Pleiad Fire Red» del Terminale (nero, colori intonati, intro con le
  Pleiadi a ogni finestra) e lo rende predefinito. Per toglierlo: Terminale → Impostazioni → Profili → un altro →
  Predefinito.
- Windows Terminal / iTerm: Impostazioni → Profilo → Colori → sfondo `#000000`, opacità piena.
- L'intro da sola: `pleyades-cli intro` (un tasto la salta).

## Parole della rotella (facoltativo)
Sono un'impostazione personale, non del plugin: aggiungile in `~/.claude/settings.json` (con l'ok dell'utente):
```
"spinnerVerbs": { "mode": "replace", "verbs": ["Allineo le stelle", "Consulto le Pleiadi",
  "Accendo la nebulosa", "Traccio la rotta", "Lucido le costellazioni"] }
```
`"append"` invece di `"replace"` le aggiunge a quelle di Claude.

## Cambiare i colori
I temi sono in `themes/` di questo plugin (`name`, `base`, `overrides`: nome del colore → `#rrggbb`). I colori
blu vengono dal marchio dello studio: se cambia il marchio, cambiali qui insieme. Un colore nuovo per sé solo:
`/theme` → «New custom theme» (resta sul proprio computer).

## Insidie
- Righe sottili fra i pixel dell'intro nel Terminale del Mac → ▀/▄ del font non sono metà esatte della cella →
  normale; non cambiare interlinea (0,82–0,9 provate: peggio).
- Tema non nell'elenco di `/theme` → plugin installato con Claude aperto → `/reload-plugins`.
- Colori invariati nell'app desktop di Claude → i temi valgono solo nel terminale → lì si usano i colori dell'app.
