# claude-crew

Una libreria di skill condivise, divisa per **settori** (minecraft, grafica, video, web, codice…), per un gruppo di
amici che usano Claude (Claude Code e app, Windows e Mac). Serve a far crescere insieme **conoscenza e modi di
lavorare**: quello che uno scopre o impara da un errore arriva al Claude di tutti.
**Una skill = un plugin**: ognuno accende solo quelle che vuole.

**Oggi** Pleyades serve a condividere conoscenza: ogni progetto di uno di noi lascia qui quello che ha insegnato,
così il prossimo parte già avanti. **In futuro** faremo progetti insieme che toccano più settori (es. un server con
sito, negozio online, campagna SEO e video promozionale): per quelli c'è il plugin `progetto-crew`, che tiene le
scelte in una scheda `progetto.md` così ogni pezzo si incastra con gli altri.

**Dove vive**: solo in questo repo. Chi contribuisce lavora con git (il suo Claude lo guida), tutti installano da qui.

## Mappa

| Cosa | Dove | Per chi |
|---|---|---|
| Regole comuni + `organizza-claude` (struttura comune), `configura-claude` (il tuo Claude come il nostro), `condividi-skill`, `raccogli-skill`, `installa-crew` | `plugins/regole/` | tutti |
| Regole per chi programma | `plugins/codice/` | chi programma (solo Claude Code) |
| Una skill per tipo di lavoro | `plugins/<skill>/skills/<skill>/SKILL.md` | chi la installa |
| Plugin di terzi consigliati (fissati a un commit) | `esterni.json` | tutti |
| Elenco dei plugin (generato) | `.claude-plugin/marketplace.json` | Claude Code, app |
| Istruzioni d'installazione per Claude | `INSTALLA.md` | Claude Code |

## Installare

- **Claude Code**: incolla al tuo Claude `Installa Pleyades seguendo` + il link a `INSTALLA.md` (`https://raw.githubusercontent.com/Radwtsm/claude-crew/main/INSTALLA.md`).
- **App Claude desktop**: Personalizza → Plugin → Aggiungi marketplace `Radwtsm/claude-crew`, installa, accendi
  Sync automatically (valgono anche in chat e sul telefono); le regole comuni si incollano nelle preferenze.
- Plugin installati dall'app desktop valgono anche su web e telefono (stesso account).
- **Una riga nelle preferenze, una volta sola** (Impostazioni → preferenze personali, sotto le tue):
  `Segui sempre le regole comuni di Pleyades: all'inizio di ogni conversazione leggi la skill regole-crew. Le mie preferenze qui sopra vincono dove dicono altro.`
  Il testo delle regole sta nella skill e si aggiorna da solo: non si ricopia mai.

## Perché tutto qui

Ogni strumento utile scoperto da uno (skill, plugin, server MCP, hook, programma) e ogni problema già risolto
finisce qui, non sparso nei progetti di qualcuno: così arriva a tutti e nessuno si incastra due volte nello stesso
errore. Come si fa: `CLAUDE.md` → "Strumenti: tutti qui" e "Lezioni".

## Tre strati, nessuno tocca gli altri

1. **Pleyades**: questo repo, uguale per tutti.
2. **Personale**: come Claude ti parla, i tuoi metodi. Claude Code: il tuo `~/.claude/CLAUDE.md`; app: le tue
   preferenze, sopra il blocco `regole Pleyades`. Mai qui. Vince su Pleyades.
3. **Progetto**: il `CLAUDE.md` del repo su cui lavori.

## Formato
Le stesse regole per Pleyades, i tuoi repo e quelli di progetto, controllate da `plugins/regole/scripts/lint_regole.py`: il plugin
`regole` lo lancia **mentre Claude scrive** (hook su ogni regola o skill modificata), `check.sh` prima di ogni commit;
nei tuoi repo, nel pre-commit: `python3 ~/.claude/plugins/marketplaces/claude-crew/plugins/regole/scripts/lint_regole.py .`
- **Skill**: frontmatter con `name` uguale alla cartella e `description` di 80–300 caratteri che dice cosa fa e
  "Usala quando/prima di…"; un titolo `# …`; corpo corto, i dettagli in file per tema letti quando servono.
- **Insidie e trappole**: una voce per errore, `sintomo → causa → cosa fare`, sotto un titolo "Insidie" o "Trappole".
- **Righe** di massimo 120 caratteri (tabelle e link esclusi), niente spazi in fondo, a capo finale.
- **Lunghezza**: ogni `SKILL.md` sotto 6000 byte (una skill grande = indice + file per tema), gli altri file letti a
  ogni sessione in `limiti-contesto.txt`.
I problemi già presenti stanno in `lint-regole-baseline.txt`: bloccano solo quelli nuovi, e l'elenco può solo calare
(rigeneralo con `--baseline` dopo averne sistemati).

## Contribuire

Ognuno lo chiede al proprio Claude: **"aggiungi questo a Pleyades"** (una skill) o **"raccogli le mie skill in Pleyades"**
(inventario completo). Le regole che le istanze seguono sono in [`CLAUDE.md`](CLAUDE.md), la sola fonte.

- **Collaboratori** (invitati al repo su GitHub: Settings → Collaborators): il loro Claude li guida a clonare il
  repo e pubblica con git dopo `check.sh`. Skill e testi vanno diretti; script e hook in una pull request.
- **Gli altri**: `condividi-skill` prepara uno zip da mandare a un collaboratore, che lo importa con
  `python3 tools/aggiungi.py <skill.zip> <categoria>`. Oppure un modulo in Issues.

Regole per ciò che entra:
- Repo **pubblico**: niente segreti, IP, nomi di PC, percorsi, email, dati di persone (`check.sh` + CI li bloccano;
  parole private in più in `~/.config/claude-crew/parole-vietate`, una regex per riga, fuori dal repo).
- Niente preferenze personali (tono, come chiamarti, formato): sono dello strato personale.
- Skill in italiano, `description` = cosa fa + quando usarla. Script brevi e leggibili, niente eseguibili.
- Nomi dei plugin = identità: per rinominare si usa `renames` in `marketplace.json`, mai un cambio secco.
- Niente `version` nei `plugin.json`: così chi installa riceve ogni commit.

Una volta per clone: `git config core.hooksPath .githooks` (il pre-commit lancia `check.sh`).
