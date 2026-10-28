# Installare Pleyades (istruzioni per Claude Code)

**Il modo più veloce**: una riga che scarica e lancia la guida `pleyades-cli` (`crew.py`, uguale su Mac, Linux e Windows):
Claude Code, GitHub con o senza account, plugin, progetti con la loro stanza Talk e cartelle Nextcloud, link.
Mac/Linux (Terminale): `curl -fsSL https://raw.githubusercontent.com/Radwtsm/claude-crew/main/installa.sh | bash`
(con un progetto: `| bash -s -- PROPRIETARIO/REPO`).
Windows (PowerShell, provato ancora su nessun PC): `irm https://raw.githubusercontent.com/Radwtsm/claude-crew/main/installa.ps1 | iex`
(con un progetto: prima `$env:PROGETTO='PROPRIETARIO/REPO';` sulla stessa riga). Dopo: `pleyades-cli` (menu, aggiorna,
controlla, entra in un progetto). Un progetto dice cosa gli serve in `.claude/progetto.json` (vedi `crew.py`).

Queste istruzioni sono per Claude: l'utente ha incollato una frase come "installa Pleyades seguendo INSTALLA.md".
Fai tu i passi, spiegando in breve cosa fai; chiedi solo le scelte. Funziona su Windows, Mac e Linux.

1. **Controlla** che `git --version` risponda. Se manca: su Windows di' all'utente di installare Git for Windows
   dal sito ufficiale (git-scm) e di riaprire Claude Code; poi riparti.
2. **HTTPS per GitHub**: nel file delle impostazioni utente (`~/.claude/settings.json`; su Windows
   `%USERPROFILE%\.claude\settings.json`) aggiungi, senza togliere niente di quello che c'è:
   `"env": { "CLAUDE_CODE_PLUGIN_PREFER_HTTPS": "1" }` (unisci alla chiave `env` se esiste già).
   Serve a chi non ha una chiave SSH di GitHub; non chiede account.
3. **Aggiungi la libreria**: `claude plugin marketplace add Radwtsm/claude-crew`
4. **Fai scegliere per mestiere**: leggi l'elenco dei plugin (`.claude-plugin/marketplace.json` di Pleyades), chiedi
   all'utente che lavoro fa e proponi solo i plugin del suo settore, con una domanda a scelta multipla. Sempre
   `regole`; `codice` solo a chi programma. **Mai di default strumenti di un altro settore**: arrivano quando un
   lavoro li chiede (skill `installa-crew`). "Tutte" solo se lo chiede lui.
5. **Installa** ognuno: `claude plugin install <nome>@claude-crew`
6. **Aggiornamenti automatici**: di' all'utente di scrivere `/plugin`, aprire **Marketplaces**, scegliere
   `claude-crew` e premere **Enable auto-update** (è l'unico passo che deve fare lui). Aggiorna i plugin installati,
   non installa quelli nuovi: se ha scelto "Tutte, anche quelle future", di' che basta chiedere "aggiorna Pleyades"
   ogni tanto (skill `installa-crew` installa quelli arrivati).
7. **Personale**: se l'utente ha già preferenze sue (come vuole essere chiamato, tono, formato), restano nel suo
   `~/.claude/CLAUDE.md`, che non va toccato. Le regole personali vincono su quelle di Pleyades.
8. **Verifica**: `claude plugin list` deve mostrare i plugin scelti come abilitati. Di' all'utente che le regole
   e le skill valgono dalla prossima sessione, e che per condividere una sua skill basta dire
   "condividi questa skill con Pleyades".
