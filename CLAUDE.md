# claude-crew — come Claude gestisce questa libreria

Valgono per ogni Claude (Claude Code o Cowork) che lavora qui o nella cartella condivisa `Claude Crew/libreria`
(Google Drive). Sono la sola fonte su come si aggiungono, aggiornano e tolgono skill: seguile alla lettera, così
le istanze di tutti lavorano allo stesso modo. Il repo è **pubblico**.

## Mappa
| Cosa | Dove |
|---|---|
| Una skill = un plugin | `plugins/<nome>/` |
| Regole comuni + skill `condividi-skill`, `raccogli-skill`, `installa-crew` | `plugins/regole/` |
| Elenco dei plugin (GENERATO, non toccare) | `.claude-plugin/marketplace.json` ← `tools/elenco.py` |
| Pagina per l'app, zip | `tools/build.py` + `tools/pagina.html` → GitHub Pages (CI) |
| Installazione guidata per Claude Code | `INSTALLA.md` |
| Controllo anti-fuga | `check.sh` (pre-commit + CI + sincronizzazione) |

## Dove si scrive
- **Manutentori**: nella cartella condivisa `Claude Crew/libreria`. Un job sul Mac del manutentore principale la
  pubblica su GitHub ogni ~10 minuti (dopo `check.sh`) e riporta lì le modifiche arrivate da GitHub.
- **Clone git (`~/claude-crew`)**: va bene anche lì (commit + push dopo `sh check.sh`); il job lo riporta su Drive.
  Mai la stessa modifica in tutti e due i posti: crea un conflitto.
- **Chi non è manutentore**: niente scrittura; `condividi-skill` prepara uno zip da mandare a un manutentore.

## Prima di ogni modifica
1. **Allinea**: lavora sull'ultima versione (cartella Drive sincronizzata e "disponibile offline"; nel clone
   `git pull --ff-only`). Leggi l'elenco dei plugin per sapere cosa c'è già.
2. **Raccogli, non pescare**: se l'utente vuole condividere "le sue skill", usa `raccogli-skill`: prima l'inventario
   di TUTTE le sue skill (personali, di ogni progetto, comandi, procedure nei CLAUDE.md, app), poi il confronto con
   la crew, poi la scelta. Mai solo quelle del progetto aperto.
3. **Una skill per tema**: se esiste già una skill sullo stesso tema, migliora quella invece di crearne un'altra.

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
plugin: restano **in attesa** finché il manutentore principale non li approva. Dillo all'utente. Brevi, leggibili,
che funzionino su Windows (Git Bash o PowerShell) e Mac; niente eseguibili né file scaricati.

## Non toccare
`.claude-plugin/marketplace.json`, `dist/`, `.github/`, `tools/`, `check.sh`, `LICENSE`, `INSTALLA.md`, questo file:
si cambiano solo su richiesta del manutentore principale. Ignora i file temporanei di Drive.

## Dopo
Di' all'utente: cosa hai aggiunto o cambiato (nomi dei plugin), che si pubblica entro ~10 minuti, che arriva a tutti
con la sincronizzazione dei plugin (Claude Code: da solo se l'aggiornamento automatico è acceso; app desktop: Sync
automatically) e che per usarlo lui stesso deve avere quel plugin installato.
