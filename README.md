# claude-crew

Regole e skill condivise di un gruppo di amici che usano Claude (Claude Code e app Claude, Windows e Mac).
**Una skill = un plugin**: ognuno accende solo quelle che vuole.

## Mappa

| Cosa | Dove | Per chi |
|---|---|---|
| Regole comuni + `condividi-skill` + `installa-crew` | `plugins/regole/` | tutti |
| Regole per chi programma | `plugins/codice/` | chi programma (solo Claude Code) |
| Una skill per tipo di lavoro | `plugins/<skill>/skills/<skill>/SKILL.md` | chi la installa |
| Elenco dei plugin | `.claude-plugin/marketplace.json` | Claude Code |
| Pagina per l'app (zip + regole da copiare) | `tools/build.py` + `tools/pagina.html` → GitHub Pages | chi usa l'app |
| Istruzioni d'installazione per Claude | `INSTALLA.md` | Claude Code |

## Installare

- **Claude Code**: incolla al tuo Claude `Installa la crew seguendo` + il link a `INSTALLA.md` (lo trovi sulla pagina).
- **App Claude**: dalla pagina (link in "About" del repo) scarichi gli zip delle skill e copi le regole.

## Tre strati, nessuno tocca gli altri

1. **Crew**: questo repo, uguale per tutti.
2. **Personale**: come Claude ti parla, i tuoi metodi. Claude Code: il tuo `~/.claude/CLAUDE.md`; app: le tue
   preferenze, sopra il blocco `regole crew`. Mai qui. Vince sulla crew.
3. **Progetto**: il `CLAUDE.md` del repo su cui lavori.

## Contribuire

- **Facile**: di' al tuo Claude "condividi questa skill con la crew": prepara uno zip ripulito da mandare in chat a
  un manutentore. Oppure un modulo in Issues.
- **Manutentori**: `python3 tools/aggiungi.py <skill.zip> <categoria>`, rileggi per intero i file aggiunti,
  `sh check.sh`, PR. Il merge su `main` lo fa un manutentore dopo averla letta tutta (CODEOWNERS).

Regole per ciò che entra:
- Repo **pubblico**: niente segreti, IP, nomi di PC, percorsi, email, dati di persone (`check.sh` + CI li bloccano;
  parole private in più in `~/.config/claude-crew/parole-vietate`, una regex per riga, fuori dal repo).
- Niente preferenze personali (tono, come chiamarti, formato): sono dello strato personale.
- Skill in italiano, `description` = cosa fa + quando usarla. Script brevi e leggibili, niente eseguibili.
- Nomi dei plugin = identità: per rinominare si usa `renames` in `marketplace.json`, mai un cambio secco.
- Niente `version` nei `plugin.json`: così chi installa riceve ogni commit.

Una volta per clone: `git config core.hooksPath .githooks` (il pre-commit lancia `check.sh`).
