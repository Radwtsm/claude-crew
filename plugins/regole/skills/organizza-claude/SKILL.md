---
name: organizza-claude
description: La struttura comune della crew per organizzare il proprio Claude (regole personali, skill private, regole di progetto, plugin della crew) in Claude Code e nell'app, e la procedura per riorganizzare un setup esistente senza perdere niente. Usala quando l'utente dice "organizza il mio Claude", "dove metto questa regola/skill", "sistema i miei CLAUDE.md", "configura Claude come la crew", o quando una regola o skill sta nel posto sbagliato.
---

# Organizzare il proprio Claude (struttura della crew)

Tutti nella crew usano la stessa struttura: così condividere una skill è solo spostarla, e ogni Claude sa dove
cercare e dove scrivere.

## I tre strati (vince il più preciso)
| Strato | Cosa contiene | Chi lo cambia |
|---|---|---|
| **Crew** | regole comuni e skill di tutti (plugin della crew) | i manutentori, tramite la libreria |
| **Personale** | come Claude lavora con te: lingua, tono, formato, cautele, i tuoi strumenti | solo tu |
| **Progetto** | regole di un repo o di un lavoro: comandi, struttura, cosa non toccare | chi ci lavora |

Il personale vince sulla crew, il progetto vince sul personale dove è più preciso. Mai mischiarli: una preferenza
tua non va nella crew, una regola di progetto non va nel personale.

## Claude Code
```
~/.claude/CLAUDE.md               solo import, niente regole scritte qui:
                                    @~/claude-personale/regole.md
~/claude-personale/               cartella privata (meglio un repo git privato: uguale su ogni PC)
  regole.md                       le tue regole personali (modello sotto)
  <tema>.md                       se crescono: un file per tema, importato da ~/.claude/CLAUDE.md
~/.claude/skills/<nome>/SKILL.md  skill solo tue (procedure con nomi, account, macchine tue)
<progetto>/CLAUDE.md              regole del progetto: mappa, comandi, divieti
<progetto>/.claude/skills/<nome>/ skill che servono solo in quel progetto
plugin della crew                 installati con /plugin, aggiornati da soli: mai copiati a mano
```
Cose della singola macchina (percorsi, nomi dei PC): in un file `~/claude-personale/macchina-<nome>.md` importato
solo su quella macchina, oppure direttamente in `~/.claude/CLAUDE.md` sotto gli import.

## App Claude (desktop, web, telefono)
| Strato | Dove |
|---|---|
| Crew | Personalizza → Plugin → marketplace della crew, Sync automatically; nelle preferenze una riga sola: "Segui sempre le regole comuni della crew: all'inizio di ogni conversazione leggi la skill regole-crew" (il testo si aggiorna da solo) |
| Personale | Impostazioni → preferenze personali (sopra la riga della crew); skill solo tue in Personalizza → Skill |
| Progetto | un Progetto (o un progetto Cowork con la sua cartella) con le sue istruzioni |

## Dove va una cosa nuova
- Vale per chiunque nella crew? → crew (`condividi-skill`).
- Vale per te ovunque? → personale.
- Vale solo in un progetto? → progetto.
- Una procedura con passi ripetibili → skill (nello strato giusto); un comportamento sempre valido → regola.
- Contiene nomi, account, macchine o percorsi tuoi → mai nella crew.

## Modello di `regole.md` personale
```
# Regole personali
## Chi sono e cosa faccio            (lavoro, hobby, livello tecnico)
## Come rispondermi                  (lingua, tono, lunghezza, formato dei comandi)
## Come lavoriamo                    (cosa chiedermi prima, cosa fare da solo, conferme)
## I miei strumenti                  (sistema, programmi, servizi che uso)
## Da non fare mai
```

## Riorganizzare un setup esistente
1. **Inventario**: leggi `~/.claude/CLAUDE.md`, ogni file che importa, `~/.claude/skills`, `~/.claude/commands`, i
   `CLAUDE.md` e `.claude/` dei progetti dell'utente (chiedi dove sono); nell'app chiedi di incollarti le
   preferenze e l'elenco delle skill.
2. **Proposta**: una tabella "cosa → dove va (crew / personale / progetto) → perché". Le cose generiche: proponi di
   portarle nella crew con `raccogli-skill`.
3. **Ok dell'utente**, poi **copia di sicurezza** (es. `~/.claude/CLAUDE.md.prima-di-organizzare`) prima di
   spostare.
4. **Sposta** senza riscrivere il contenuto (stesse parole, solo il posto cambia); niente doppioni.
5. **Verifica**: apri una sessione nuova e controlla che le regole ci siano ("che regole hai?"); nell'app rileggi
   le preferenze salvate.
6. **Riepilogo**: cosa è andato dove, dove si trova la copia di sicurezza.
