---
name: installa-crew
description: Scegliere, aggiungere o togliere skill della crew in Claude Code, aggiornarle o controllare che siano installate bene. Usala quando l'utente chiede "che skill della crew ci sono", "aggiungi/togli la skill X", "aggiorna la crew".
---

# Gestire le skill della crew (Claude Code)

Le istruzioni complete, che valgono anche per la prima installazione, sono in `INSTALLA.md` alla radice del repo
`Radwtsm/claude-crew`. In breve:

- Elenco: leggi il `.claude-plugin/marketplace.json` della crew (`claude plugin list` per quelle installate) e
  proponi all'utente cosa accendere o spegnere, con una domanda a scelta multipla.
- Aggiungere: `claude plugin install <nome>@claude-crew`. Togliere: `claude plugin uninstall <nome>@claude-crew`.
- Aggiornare subito: `claude plugin marketplace update claude-crew`.
- Le modifiche valgono dalla prossima sessione (o con `/reload-plugins`).
- Mai toccare il CLAUDE.md personale o le impostazioni dell'utente oltre a quanto scritto in `INSTALLA.md`.
