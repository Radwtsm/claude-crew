---
name: tema-studio
description: I temi di Claude Code con i colori dello studio (blu notte o rosso su nero) e le parole della rotella in stile Pleyades. Usala per "metti il tema dello studio", "tema rosso", "cambia i colori di Claude", "parole dell'attesa".
---

# Tema dello studio

## Scegliere il tema
1. In Claude Code (terminale): scrivi `/theme` e scegli «Pleyades Studio» o «Pleiad Fire Red», oppure una tinta
   «Pleiadi Viola / Verde / Oro / Ciano».
2. Vale per quel computer; per tornare indietro, `/theme` e un tema di base.

## Il tuo aspetto (`pleyades-cli aspetto`)
La prima intro lo chiede da sola, poi si cambia con `pleyades-cli aspetto` (anche nel menu `pley`): nome
(«ciao, …»), titolo in pixel, frase, tinta (o tre colori #rrggbb), due forme 3D piene (stella, merkaba, cubo,
ottaedro, icosaedro). Anteprima, poi la stessa tinta ovunque: Claude, Terminale/iTerm2, Windows Terminal (barra
delle schede nera compresa), prompt Starship (se installato). Su Windows chiede anche i colori di tutto Windows
(`pleyades-cli finestre`: modo scuro, tinta su barre del titolo e bordi; `--togli` rimette quelli di prima).
`pleyades-cli intro --resta`: le forme girano finché premi un tasto.
Il rosso vuole uno sfondo nero pieno: lo decide il programma del terminale, non Claude.
`pleyades-cli tema` (anche nel menu `pley` e proposto dalla guida) fa tutto: Claude in «Pleiad Fire Red» (chi ha
scelto il blu lo tiene), parole Pleyades nella rotella (solo se non ne hai di tue), terminale nero con l'intro (stato
tuo e della squadra, i comandi `claude` e `pley`; al primo avvio tre strade).
- Mac: profilo «Pleiad Fire Red» del Terminale, predefinito. Toglierlo: Terminale → Impostazioni → Profili → un
  altro → Predefinito. Opzione-clic sposta il cursore nella riga; col mouse in tutto, l'app desktop di Claude.
- Windows: schema in Windows Terminal (copia in `settings.json.prima-di-crew`) e una riga nel profilo di PowerShell.
- Altri terminali (iTerm, Linux): sfondo `#000000`, opacità piena.
- L'intro da sola: `pleyades-cli intro` (un tasto la salta).

## Parole della rotella
`pleyades-cli tema` le aggiunge a quelle di Claude (`spinnerVerbs`, `"mode": "append"`) in `~/.claude/settings.json`,
solo se non ce ne sono già; `"replace"` per avere solo quelle di Pleyades.

## Cambiare i colori
I temi sono in `themes/` di questo plugin (`name`, `base`, `overrides`: nome del colore → `#rrggbb`). I colori
blu vengono dal marchio dello studio: se cambia il marchio, cambiali qui insieme. Un colore nuovo per sé solo:
`/theme` → «New custom theme» (resta sul proprio computer).

## Insidie
- Righe sottili fra i pixel dell'intro nel Terminale del Mac → ▀/▄ del font non sono metà esatte della cella →
  normale; non cambiare interlinea (0,82–0,9 provate: peggio).
- Tema non nell'elenco di `/theme` → plugin installato con Claude aperto → `/reload-plugins`.
- Colori invariati nell'app desktop di Claude → i temi valgono solo nel terminale → lì si usano i colori dell'app.
