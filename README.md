# claude-crew

Una libreria di skill condivise, divisa per **settori** (minecraft, grafica, video, web, codice…), per un gruppo di
amici che usano Claude (Claude Code e app, Windows e Mac). Serve a far crescere insieme **conoscenza e modi di
lavorare**: quello che uno scopre o impara da un errore arriva al Claude di tutti.
**Una skill = un plugin**: ognuno accende solo quelle che vuole.

**Oggi** la crew serve a condividere conoscenza: ogni progetto di uno di noi lascia qui quello che ha insegnato,
così il prossimo parte già avanti. **In futuro** faremo progetti insieme che toccano più settori (es. un server con
sito, negozio online, campagna SEO e video promozionale): per quelli c'è il plugin `progetto-crew`, che tiene le
scelte in una scheda `progetto.md` così ogni pezzo si incastra con gli altri.

**Dove vive**: la cartella condivisa **Google Drive `Claude Crew/libreria`** è il centro, dove i Claude dei
manutentori lavorano. Questo repo è la copia pubblicata (storia, backup, controlli) da cui si installano i plugin.
Le due si allineano da sole ogni ~10 minuti.

## Mappa

| Cosa | Dove | Per chi |
|---|---|---|
| Regole comuni + `organizza-claude` (struttura comune), `condividi-skill`, `raccogli-skill`, `installa-crew` | `plugins/regole/` | tutti |
| Regole per chi programma | `plugins/codice/` | chi programma (solo Claude Code) |
| Una skill per tipo di lavoro | `plugins/<skill>/skills/<skill>/SKILL.md` | chi la installa |
| Plugin di terzi consigliati (fissati a un commit) | `esterni.json` | tutti |
| Elenco dei plugin (generato) | `.claude-plugin/marketplace.json` | Claude Code, app |
| Istruzioni d'installazione per Claude | `INSTALLA.md` | Claude Code |

## Installare

- **Claude Code**: incolla al tuo Claude `Installa la crew seguendo` + il link a `INSTALLA.md` (`https://raw.githubusercontent.com/Radwtsm/claude-crew/main/INSTALLA.md`).
- **App Claude desktop**: Personalizza → Plugin → Aggiungi marketplace `Radwtsm/claude-crew`, installa, accendi
  Sync automatically (valgono anche in chat e sul telefono); le regole comuni si incollano nelle preferenze.
- Plugin installati dall'app desktop valgono anche su web e telefono (stesso account).
- **Una riga nelle preferenze, una volta sola** (Impostazioni → preferenze personali, sotto le tue):
  `Segui sempre le regole comuni della crew: all'inizio di ogni conversazione leggi la skill regole-crew. Le mie preferenze qui sopra vincono dove dicono altro.`
  Il testo delle regole sta nella skill e si aggiorna da solo: non si ricopia mai.

## Perché tutto qui

Ogni strumento utile scoperto da uno (skill, plugin, server MCP, hook, programma) e ogni problema già risolto
finisce qui, non sparso nei progetti di qualcuno: così arriva a tutti e nessuno si incastra due volte nello stesso
errore. Come si fa: `CLAUDE.md` → "Strumenti: tutti qui" e "Lezioni".

## Tre strati, nessuno tocca gli altri

1. **Crew**: questo repo, uguale per tutti.
2. **Personale**: come Claude ti parla, i tuoi metodi. Claude Code: il tuo `~/.claude/CLAUDE.md`; app: le tue
   preferenze, sopra il blocco `regole crew`. Mai qui. Vince sulla crew.
3. **Progetto**: il `CLAUDE.md` del repo su cui lavori.

## Contribuire

Ognuno lo chiede al proprio Claude: **"aggiungi questo a crew"** (una skill) o **"raccogli le mie skill nella crew"**
(inventario completo). Le regole che le istanze seguono sono in [`CLAUDE.md`](CLAUDE.md), la sola fonte.

- **Manutentori**: il loro Claude scrive nella cartella condivisa `Claude Crew/libreria` (Google Drive); un job sul
  Mac del manutentore principale la pubblica qui ogni ~10 minuti dopo il check. Script e hook aspettano il suo ok.
- **Gli altri**: `condividi-skill` prepara uno zip da mandare a un manutentore, che lo importa con
  `python3 tools/aggiungi.py <skill.zip> <categoria>`. Oppure un modulo in Issues.

### Condividere la cartella (manutentore principale)
Su drive.google.com (non il menu "Condividi" di macOS/Windows, che manda solo una copia): tasto destro su
`Claude Crew` → **Condividi** → email → **Editor** per un manutentore, **Visualizzatore** per gli altri → Invia.

### Setup di un manutentore con l'app Claude, Windows (una volta)
1. **Google Drive per desktop** dal sito di Google; accedi con l'account a cui è condivisa la cartella. In Esplora
   file compare il disco **Google Drive (G:)**.
2. drive.google.com → **Condivisi con me** → tasto destro su `Claude Crew` → **Organizza → Aggiungi scorciatoia →
   Il mio Drive**. Dopo poco è in `G:\Il mio Drive\Claude Crew`.
3. Esplora file → tasto destro su `Claude Crew` → **Accesso offline → Disponibile offline** (obbligatorio, vedi
   `CLAUDE.md` → "Cartella condivisa").
4. Sul Desktop solo un collegamento: tasto destro → **Mostra altre opzioni → Invia a → Desktop (crea
   collegamento)**. Mai trascinare o copiare la cartella.
5. App Claude desktop → **Cowork** → nuovo progetto "Claude Crew" con la cartella vera
   `G:\Il mio Drive\Claude Crew\libreria` (non il collegamento); istruzioni del progetto:
   `Prima di ogni lavoro leggi e segui CLAUDE.md di questa cartella.`
6. **Personalizza → Plugin → Aggiungi marketplace** `Radwtsm/claude-crew` → installa i plugin → **Sync
   automatically**.
7. La riga delle regole comuni nelle preferenze personali (sopra, "Installare"), poi nel progetto: "organizza il mio Claude e raccogli
   le mie skill nella crew".

Su Mac è uguale: Drive compare nel Finder sotto "Google Drive"; tasto destro → Google Drive → Disponibile offline.

### Pubblicazione (lato manutentore principale)
Un job sul suo computer sincronizza la cartella con questo repo ogni ~10 minuti, con le regole di `CLAUDE.md` →
"Cartella condivisa" (due direzioni, conflitti fermati, script in attesa di ok, `check.sh` prima di ogni push). Se
un giorno lo spostiamo su un altro computer, servono: Drive per desktop con la cartella offline, un clone di questo
repo con permesso di push, e un Python che il sistema lasci accedere ai file di Drive in background.

Regole per ciò che entra:
- Repo **pubblico**: niente segreti, IP, nomi di PC, percorsi, email, dati di persone (`check.sh` + CI li bloccano;
  parole private in più in `~/.config/claude-crew/parole-vietate`, una regex per riga, fuori dal repo).
- Niente preferenze personali (tono, come chiamarti, formato): sono dello strato personale.
- Skill in italiano, `description` = cosa fa + quando usarla. Script brevi e leggibili, niente eseguibili.
- Nomi dei plugin = identità: per rinominare si usa `renames` in `marketplace.json`, mai un cambio secco.
- Niente `version` nei `plugin.json`: così chi installa riceve ogni commit.

Una volta per clone: `git config core.hooksPath .githooks` (il pre-commit lancia `check.sh`).
