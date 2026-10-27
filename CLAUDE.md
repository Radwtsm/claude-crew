# claude-crew — come Claude gestisce questa libreria

Valgono per ogni Claude (Claude Code o app) che lavora in questo repo. Sono la sola fonte su come si aggiungono, aggiornano e tolgono skill: seguile alla lettera, così
le istanze di tutti lavorano allo stesso modo. Il repo è **pubblico**.

**Scopo**: una libreria di skill condivise per settori diversi, per far crescere insieme conoscenza e flussi di
lavoro. Quello che un utente scopre (uno strumento, un modo di lavorare, la soluzione a un errore) deve finire qui e
arrivare al Claude di tutti, invece di restare in un progetto o in una chat.

**Oggi**: condividere conoscenza e flussi di lavoro. **In futuro**: progetti fatti insieme che usano le skill di
più settori (es. un server con sito, negozio, campagna SEO e video promozionale) con la stessa identità in ogni
pezzo. Per quelli: plugin `progetto-crew` (scheda `progetto.md`, sola fonte delle scelte del progetto). Le regole
comuni non lo richiamano: entra in gioco solo in un progetto della crew.

## Il centro è questo repo (solo git, dal 2026-10-27)
Il repo GitHub `Radwtsm/claude-crew` è la sola fonte: chi scrive ci lavora in un clone (`~/claude-crew`), tutti
installano i plugin da qui. Nessun'altra copia (la vecchia cartella Drive `Claude Crew/libreria` è un archivio fermo).
- Prima di ogni lavoro: `git pull --ff-only`. Dopo: `sh check.sh` verde, commit breve, push.
- Push rifiutato (qualcuno ha pubblicato prima): `git pull --rebase`, di nuovo `sh check.sh`, push.

## Settori
- Il **settore** di un plugin è la sua categoria (`keywords[0]` del `plugin.json`): `regole`, `codice`,
  `minecraft`, `grafica`, `video`, `web`… Uno nuovo si crea quando serve, breve e minuscolo; prima controlla che
  non ce ne sia già uno simile.
- In ogni settore due tipi di skill: **conoscenza** (come funziona, scelte, insidie) e **flusso di lavoro** (i passi
  per fare una cosa dall'inizio alla fine, con le verifiche). Una skill di flusso cita quelle di conoscenza invece
  di ripeterle.
- Le skill di un settore si richiamano per nome (es. "per le misure di export vedi il plugin `grafica`").

## Mappa
| Cosa | Dove |
|---|---|
| Una skill = un plugin | `plugins/<nome>/` |
| Regole comuni + skill `condividi-skill`, `raccogli-skill`, `organizza-claude`, `installa-crew` | `plugins/regole/` |
| Come ognuno organizza il proprio Claude (strati, cartelle, app) | `plugins/regole/skills/organizza-claude/SKILL.md` |
| Plugin di terzi consigliati, fissati a un commit | `esterni.json` |
| Elenco dei plugin (GENERATO, non toccare) | `.claude-plugin/marketplace.json` ← `tools/elenco.py` (plugins/ + esterni.json) |
| Installazione guidata per Claude Code | `INSTALLA.md` |
| Controllo anti-fuga + formato | `check.sh` (pre-commit + CI) con `tools/lint_regole.py` |

## Dove si scrive
- **Collaboratori del repo** (invitati su GitHub): il loro Claude li guida la prima volta: account GitHub,
  `gh auth login`, `git clone`, `git config core.hooksPath .githooks` (il pre-commit lancia `check.sh`). Skill e
  testi (`plugins/**/*.md`, `plugin.json`): commit e push su `main`. Script, hook, json o file fuori da `plugins/`:
  un branch e una pull request, che legge il manutentore principale.
- **Chi non è collaboratore**: `condividi-skill` prepara uno zip da mandare a un collaboratore.
- **Cancellare** un file lo toglie dai plugin di tutti: solo se l'utente lo vuole.
- **Tempi**: dopo il push Claude Code la riceve all'avvio successivo (aggiornamento automatico acceso), l'app con
  Sync automatically.

## Prima di ogni modifica
1. **Allinea**: lavora sull'ultima versione (`git pull --ff-only` nel clone). Leggi l'elenco dei plugin per sapere cosa c'è già.
2. **Raccogli, non pescare**: se l'utente vuole condividere "le sue skill", usa `raccogli-skill`: prima l'inventario
   di TUTTE le sue skill (personali, di ogni progetto, comandi, procedure nei CLAUDE.md, app), poi il confronto con
   la crew, poi la scelta. Mai solo quelle del progetto aperto.
3. **Strato giusto**: la struttura comune (crew / personale / progetto) è nella skill `organizza-claude`; nella
   crew entra solo ciò che vale per chiunque.
4. **Una skill per tema**: se esiste già una skill sullo stesso tema, migliora quella invece di crearne un'altra.

## Struttura di un plugin
```
plugins/<nome>/.claude-plugin/plugin.json
plugins/<nome>/skills/<nome>/SKILL.md
```
`plugin.json`:
```
{
  "name": "<nome>",
  "description": "<cosa contiene, concreto: la gente sceglie da qui>",
  "author": { "name": "crew" },
  "keywords": ["<categoria>"]
}
```
`SKILL.md`: frontmatter `name: <nome>` e `description: <cosa fa>. Usala quando <frasi tipiche dell'utente>`, poi
sezioni `##` brevi (prima "Prima di tutto chiedi", poi le regole, poi comandi in blocchi).
- `<nome>`: minuscole e trattini, uguale in cartella, `plugin.json` e frontmatter; descrive il lavoro, non la persona
  (`server-minecraft`, non `skill-di-marco`).
- Mai `version` (chi installa smetterebbe di ricevere gli aggiornamenti).
- Categoria: una già usata (`regole`, `minecraft`, `grafica`, `video`) o una nuova breve, minuscola.
- Italiano, frasi brevi, stile delle skill che ci sono.
- File in più (esempi, modelli) dentro `skills/<nome>/`, citati dal `SKILL.md`.

## Strumenti: tutti qui, niente sparso
Ogni strumento utile a più di una persona sta nella crew, non in un solo progetto o computer:
| Strumento | Come entra nella crew |
|---|---|
| Skill / procedura | plugin `plugins/<nome>/` (sopra) |
| Hook (comando che parte da solo) | `plugins/<nome>/hooks/hooks.json` + script in `plugins/<nome>/scripts/` — aspetta l'ok |
| Server MCP | `plugins/<nome>/.mcp.json` (niente chiavi: le mette ognuno nelle sue impostazioni) — aspetta l'ok |
| Plugin di terzi | una voce in `esterni.json`: `name`, `description`, `category`, `source` git (`github` o `git-subdir`) con `sha` del commit (40 caratteri) — aspetta l'ok |
| Programma da installare | nella skill del tema: nome, fonte ufficiale, comando di verifica |

Per un plugin di terzi: solo fonti note, letto per intero (hook e script compresi), fissato a un commit; per
aggiornarlo si cambia lo `sha` dopo aver riletto cosa è cambiato. Chi ha installato tutta la crew lo riceve da
solo: per questo serve l'ok del manutentore principale.

## Lezioni: un errore si fa una volta sola
Un problema non ovvio risolto (da te o da un collaboratore) diventa una riga dove lo troverà il prossimo:
- nella skill del tema, sezione insidie/trappole (es. `blender-riga-di-comando` → "Insidie");
- nel plugin `codice` → skill `trappole-tecniche` se riguarda programmazione, sistemi, strumenti;
- nelle regole comuni se vale per qualunque lavoro.
Una riga: sintomo → causa → cosa fare. Prima di aggiungerla cerca se c'è già (migliora quella, niente doppioni).
Se l'errore si può riconoscere con uno script, la lezione diventa anche un **controllo** che lo blocca (come
`check.sh` fa con IP e segreti): nella skill uno script di verifica, oppure una regola in `check.sh` se riguarda la
crew stessa (chiedi al manutentore principale). Le lezioni stanno nelle sezioni delle skill con "Insidie" o "Trappole"
nel titolo: per cercarle, cerca queste parole nei `SKILL.md` della crew; usale anche tu nei titoli.

## Pulizia (obbligatoria, ogni volta)
Togli e chiedi conferma all'utente: password, token, chiavi; IP, nomi di PC/server, percorsi del suo computer, URL
privati; nomi, email, account, dati di persone; preferenze solo sue (tono, come vuole essere chiamato, formato):
quelle restano nelle sue regole personali.

## Aggiornare, togliere, rinominare
- **Aggiornare**: modifica i file del plugin; nella risposta di' cosa è cambiato. Il plugin di un altro: piccole
  correzioni sì, cambi grandi chiedi prima al tuo utente.
- **Togliere**: cancella la cartella del plugin; avvisa che sparirà a chi lo usa.
- **Rinominare**: solo il manutentore principale (serve una voce `renames` in `marketplace.json`, altrimenti si
  rompe l'installazione di chi lo usa).

## Script e hook
Permessi (`plugins/<nome>/scripts/`, `plugins/<nome>/hooks/hooks.json`), ma partono da soli sui PC di chi usa il
plugin: vanno in una pull request, che il manutentore principale legge e approva. Dillo all'utente. Brevi, leggibili,
che funzionino su Windows (Git Bash o PowerShell) e Mac; niente eseguibili né file scaricati.

## Non toccare
`.claude-plugin/marketplace.json`, `.github/`, `tools/`, `check.sh`, `LICENSE`, `INSTALLA.md`, questo file:
si cambiano solo su richiesta del manutentore principale.

## Dopo
Di' all'utente: cosa hai aggiunto o cambiato (nomi dei plugin), che si pubblica entro ~10 minuti, che arriva a tutti
con la sincronizzazione dei plugin (Claude Code: da solo se l'aggiornamento automatico è acceso; app desktop: Sync
automatically) e che per usarlo lui stesso deve avere quel plugin installato.
