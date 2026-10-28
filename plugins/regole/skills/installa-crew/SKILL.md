---
name: installa-crew
description: Scegliere, aggiungere, togliere e aggiornare i plugin della crew, anche quelli nuovi, in Claude Code o nell'app. Usala per "che skill della crew ci sono", "aggiungi/togli la skill X", "aggiorna la crew", o quando un plugin manca.
---

# Gestire i plugin della crew

Le istruzioni complete, anche per la prima installazione, sono in `INSTALLA.md` alla radice del repo
`Radwtsm/claude-crew`.

## Claude Code
- Elenco: `claude plugin marketplace update claude-crew`, poi leggi il `.claude-plugin/marketplace.json` della crew
  (copia locale: `~/.claude/plugins/marketplaces/claude-crew/`) e confrontalo con `claude plugin list`; proponi
  cosa accendere o spegnere con una domanda a scelta multipla.
- Aggiungere: `claude plugin install <nome>@claude-crew`. Togliere: `claude plugin uninstall <nome>@claude-crew`.
- **Per mestiere, di default**: sul computer solo i plugin del settore dell'utente. Uno di un altro settore si
  installa solo se un lavoro lo chiede o è già stato usato, dicendolo in una riga; mai "per sicurezza".
- **"Tutte, sempre"** (solo se l'utente lo chiede): l'aggiornamento automatico (`/plugin` → Marketplaces → claude-crew →
  Enable auto-update)
  aggiorna i plugin installati, ma **non installa quelli nuovi**. A ogni "aggiorna la crew": marketplace update,
  poi installa ogni plugin dell'elenco che manca in `claude plugin list`, poi di' quali sono arrivati.
- I plugin di terzi nell'elenco (voci di `esterni.json`) si installano allo stesso modo.
- Le modifiche valgono dalla prossima sessione (o con `/reload-plugins`).
- Mai toccare il CLAUDE.md personale o le impostazioni dell'utente oltre a quanto scritto in `INSTALLA.md`.

## Insidie
- Plugin installato con Claude già aperto → le sue regole e i suoi hook mancano anche dopo `/clear` → `/clear` non
  carica i plugin nuovi: `/reload-plugins` o chiudi e riapri `claude`, poi controlla che le regole ci siano.

## App Claude desktop
- Personalizza → Plugin: i plugin nuovi della crew compaiono nel marketplace `claude-crew` (Discover); con **Sync
  automatically** quelli installati si aggiornano da soli, quelli nuovi si installano con un clic.
- Dall'app non puoi installarli tu: di' all'utente quali sono nuovi (confronta l'elenco della crew con quelli che
  ha) e dove cliccare.
