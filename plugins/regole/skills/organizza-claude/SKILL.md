---
name: organizza-claude
description: Struttura comune per organizzare il proprio Claude (regole personali, skill, progetti, plugin) e riorganizzare un setup senza perdere niente; risparmio di token. Usala per "organizza il mio Claude", "dove metto questa regola", "sistema i miei CLAUDE.md".
---

# Organizzare il proprio Claude (struttura di Pleyades)

Tutti in Pleyades usano la stessa struttura: così condividere una skill è solo spostarla, e ogni Claude sa dove
cercare e dove scrivere.

## I tre strati
| Strato | Cosa contiene | Chi lo cambia |
|---|---|---|
| **Pleyades** | regole comuni e skill di tutti (plugin di Pleyades) | i manutentori, tramite la libreria |
| **Personale** | come Claude lavora con te: lingua, tono, formato, cautele, i tuoi strumenti | solo tu |
| **Progetto** | regole di un repo o di un lavoro: comandi, struttura, cosa non toccare | chi ci lavora |

Il personale vince su Pleyades, il progetto sul personale dove è più preciso; su sicurezza e azioni irreversibili
solo per stringere (allentare = proposta allo strato sopra). Mai mischiarli: una preferenza
tua non va in Pleyades, una regola di progetto non va nel personale.

## Claude Code
```
~/.claude/CLAUDE.md               solo import, niente regole scritte qui:
                                    @~/claude-personale/regole.md
~/claude-personale/               repo GitHub privato, uguale su ogni PC (lo crea `configura-claude`)
  regole.md                       le tue regole personali (modello sotto)
  memoria/                        memoria di Claude, unica per ogni progetto
  <tema>.md                       se crescono: un file per tema, importato da ~/.claude/CLAUDE.md
~/.claude/skills/<nome>/SKILL.md  skill solo tue (procedure con nomi, account, macchine tue)
<progetto>/CLAUDE.md              regole del progetto: mappa, comandi, divieti
<progetto>/.claude/skills/<nome>/ skill che servono solo in quel progetto
plugin di Pleyades                 installati con /plugin, aggiornati da soli: mai copiati a mano
```
Cose della singola macchina (percorsi, nomi dei PC): in un file `~/claude-personale/macchina-<nome>.md` importato
solo su quella macchina, o direttamente in `~/.claude/CLAUDE.md` sotto gli import.

## App Claude (desktop, web, telefono)
| Strato | Dove |
|---|---|
| Pleyades | Personalizza → Plugin → marketplace di Pleyades, Sync automatically; nelle preferenze una riga sola: "Segui sempre le regole comuni di Pleyades: all'inizio di ogni conversazione leggi la skill regole-crew" (il testo si aggiorna da solo) |
| Personale | Impostazioni → preferenze personali (sopra la riga di Pleyades); skill solo tue in Personalizza → Skill |
| Progetto | un Progetto (o un progetto Cowork con la sua cartella) con le sue istruzioni |

## Contesto snello: cosa si carica sempre
Ogni risposta di Claude rilegge tutto ciò che è sempre caricato; in una sessione lunga lo rilegge centinaia di volte.
- **CLAUDE.md = indice corto**: regole che valgono sempre + una tabella "argomento → file → leggilo prima di…".
  Lezioni, procedure lunghe, elenchi: in file per tema (es. `docs/lezioni/<tema>.md`), letti solo quando servono.
  Le 4–5 regole che non si possono mai dimenticare restano nel CLAUDE.md, una riga ciascuna.
- **CLAUDE.md nelle sottocartelle** (es. `app/CLAUDE.md`): Claude Code lo legge solo quando lavora lì. Ci va ciò che
  vale solo per quella parte.
- **Una skill grande = un indice**: `SKILL.md` sotto 6000 byte con una tabella "tema → file → leggilo prima di…";
  il dettaglio in file accanto, che Claude apre solo quando il lavoro tocca quel tema.
- **Skill invece di regole sempre caricate**: di una skill resta in contesto solo la descrizione; il resto si legge
  quando serve. Descrizione corta ma con i casi d'uso ("Usala prima di…").
- **Hook d'avvio corti** (sotto ~8 KB): oltre ~10 KB Claude Code salva l'output in un file e ne mostra solo
  l'inizio. Prima gli avvisi, poi gli elenchi; un elenco lungo = numeri + "dettagli con <comando>".
- **Plugin accesi per progetto**: ogni descrizione di skill entra a ogni risposta, quindi in un repo restano accesi
  solo i plugin del suo lavoro (`enabledPlugins` nel `.claude/settings.json` del progetto, nel repo così arriva a
  tutti); uno spento si accende con una riga quando serve. Descrizioni ≤ 300 caratteri (il lint lo controlla).
- **Testi all'avvio solo se servono sempre**: il resto entra al primo uso (es. le regole del codice al primo file
  di codice modificato, plugin `codice`) o con una skill.
- **Un controllo, non solo una regola**: un file `limiti-contesto.txt` (byte massimi per file, glob ammessi) letto
  dal check del pre-commit blocca chi fa ricrescere CLAUDE.md, regole e lezioni; alzare un limite = scelta nel commit.
- **Una sessione per argomento**, `/clear` dopo il commit: lo stato sta nel backlog e nella memoria, non nella chat.
- Misura token ed errori ripetuti: se non calano, cambia la struttura.

## Dove va una cosa nuova
- Vale per chiunque in Pleyades? → Pleyades (`condividi-skill`).
- Vale per te ovunque? → personale.
- Vale solo in un progetto? → progetto.
- Una procedura con passi ripetibili → skill (nello strato giusto); un comportamento sempre valido → regola.
- Contiene nomi, account, macchine o percorsi tuoi → mai in Pleyades.
- Regola nuova: livello, chi la tiene, perché, come si impone (`regole-che-funzionano.md`).

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
Sei passi (inventario, proposta, ok, copia di sicurezza, sposta, verifica): [`riorganizza.md`](riorganizza.md),
quando l'utente chiede di riorganizzare.
