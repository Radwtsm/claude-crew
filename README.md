# claude-crew

Regole e skill condivise di un gruppo di amici che usano Claude (Claude Code e app Claude, Windows e Mac).
**Una skill = un plugin**: ognuno accende solo quelle che vuole.

## Mappa

| Cosa | Dove | Per chi |
|---|---|---|
| Regole comuni + `condividi-skill`, `raccogli-skill`, `installa-crew` | `plugins/regole/` | tutti |
| Regole per chi programma | `plugins/codice/` | chi programma (solo Claude Code) |
| Una skill per tipo di lavoro | `plugins/<skill>/skills/<skill>/SKILL.md` | chi la installa |
| Elenco dei plugin | `.claude-plugin/marketplace.json` | Claude Code |
| Pagina per l'app (zip + regole da copiare) | `tools/build.py` + `tools/pagina.html` → GitHub Pages | chi usa l'app |
| Istruzioni d'installazione per Claude | `INSTALLA.md` | Claude Code |

## Installare

- **Claude Code**: incolla al tuo Claude `Installa la crew seguendo` + il link a `INSTALLA.md` (lo trovi sulla pagina).
- **App Claude desktop**: Personalizza → Plugin → Aggiungi marketplace `Radwtsm/claude-crew`, installa, accendi
  Sync automatically (valgono anche in chat e sul telefono); le regole comuni si incollano nelle preferenze.
- **Solo web/telefono**: dalla pagina (link in "About" del repo) scarichi gli zip delle skill e copi le regole.

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

### Setup di un manutentore con l'app Claude (una volta)
1. Google Drive per desktop; la cartella `Claude Crew` condivisa con lui (Editor) → "Aggiungi scorciatoia a Il mio
   Drive" → tasto destro → **Disponibile offline**.
2. App Claude desktop → Cowork → nuovo progetto "Claude Crew" con la cartella `Claude Crew/libreria`; istruzioni
   del progetto: `Prima di ogni lavoro leggi e segui CLAUDE.md di questa cartella.`
3. Personalizza → Plugin → Aggiungi marketplace `Radwtsm/claude-crew` → installa i plugin → Sync automatically.
4. Regole comuni nelle preferenze personali (dalla pagina).

Regole per ciò che entra:
- Repo **pubblico**: niente segreti, IP, nomi di PC, percorsi, email, dati di persone (`check.sh` + CI li bloccano;
  parole private in più in `~/.config/claude-crew/parole-vietate`, una regex per riga, fuori dal repo).
- Niente preferenze personali (tono, come chiamarti, formato): sono dello strato personale.
- Skill in italiano, `description` = cosa fa + quando usarla. Script brevi e leggibili, niente eseguibili.
- Nomi dei plugin = identità: per rinominare si usa `renames` in `marketplace.json`, mai un cambio secco.
- Niente `version` nei `plugin.json`: così chi installa riceve ogni commit.

Una volta per clone: `git config core.hooksPath .githooks` (il pre-commit lancia `check.sh`).
