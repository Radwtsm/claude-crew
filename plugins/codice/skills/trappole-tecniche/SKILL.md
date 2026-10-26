---
name: trappole-tecniche
description: Trappole tecniche già incontrate dalla crew, con la soluzione - shell (bash, zsh), hook, ssh, SQLite, Python http.server, Swift, macOS (launchd, File Provider, sips), Playwright e test end-to-end, immagini ed EXIF, layout web (CLS), Node. Usala prima di scrivere script shell o hook, comandi ssh, test end-to-end, codice che tocca file di sistema, immagini o layout web, e quando qualcosa si comporta in modo strano o un test fallisce solo ogni tanto.
---

# Trappole tecniche

Ognuna è già costata tempo a qualcuno della crew. Una trappola nuova (sintomo → causa → cosa fare) va qui, in fondo.

- `while read …; do ssh …; done < lista`: ssh si mangia la lista → `ssh -n` o `read <&3 … 3< lista`.
- `ssh -n host 'bash -s' <<EOF` non esegue niente (-n = stdin da /dev/null): heredoc senza `-n`.
- `pgrep -f`/`pkill -f nome` dentro `ssh host '…'` trovano la propria shell: uccidi per pid, avvio e stop in
  chiamate ssh separate, ogni attesa con un timeout.
- Job lunghi (più di qualche minuto) sotto `nohup` o un servizio sul server, mai legati alla shell della sessione.
- zsh non spezza `$VAR` in parole: usa `| xargs` o `${=VAR}`.
- zsh su Mac: `log` è un builtin → `/usr/bin/log`; un risultato vuoto è sospetto finché una query nota non risponde.
- Bash con `set -e`: un passo che deve fermare lo script non sta in una lista `a && b && c` (lì un errore è ignorato):
  usa `if …; then …; fi`.
- Hook shell: mai finire con `[ cond ] && …` (cond falsa = exit 1 = blocca tutto in silenzio); `if …; fi` + `exit 0`.
- `… | tr -c 'A-Za-z0-9' '-'` su un nome: passalo senza newline (`printf "%s"`), o diventa un `-` finale.
- SQLite vivo: copialo CON il file `-wal` o aprilo read-only sul posto (`file:…?mode=ro`); una copia nuda perde
  gli ultimi minuti.
- Python `http.server` con molte richieste insieme: backlog di default 5 → `request_queue_size = 128` + retry nel client.
- Swift `URLSession.AsyncBytes.lines` scarta le righe vuote: mai per SSE o protocolli dove la riga vuota conta.
- Stringhe JS dentro stringhe Python non-raw: `\n` diventa un a capo vero; verifica il JS estratto con `node --check`.
- "Cifrato?" non si decide dai magic byte: controlla oltre l'header.
- Stato "online" di una VPN/mesh resta vero per minuti dopo che un peer si spegne: per acceso/spento interroga il
  dispositivo stesso (porta TCP, ping del mesh).
- Rinominare o spostare un'impostazione salvata (chiave, dominio, bundle ID): cerca la chiave anche negli script.
- Spostare un tipo in un altro modulo: cerca ogni file che lo usa e aggiungi l'import; poi build completa.
- Rimozioni in blocco da script: dopo, controlla il diff per dichiarazioni tolte che non erano nel bersaglio.
- Strumenti di "codice inutilizzato" = lista da verificare, non da cancellare; build + test dopo ogni lotto.
- Chrome headless non scende sotto 500 px di larghezza: uno screenshot a 414 è solo ritagliato (sembra un overflow).
  Misura `innerWidth` prima di giudicare un layout da telefono, o usa l'emulazione del dispositivo.
- macOS + Google Drive/iCloud (File Provider): un job di launchd con `/usr/bin/python3` non può nemmeno chiedere il
  permesso ("Platform binary prompting is Deny"): usa un Python non di sistema e fai premere Consenti una volta.
- File Provider: leggere da launchd un file non ancora scaricato dà `Resource deadlock avoided` (EDEADLK): saltalo
  e riprova dopo, mai trattarlo come cancellato; la cartella va resa "disponibile offline".
- Test di posizione con la rotella (Playwright `mouse.wheel`) rosso solo ogni tanto: lo scorrimento è animato e
  finisce dopo il clic → prima del clic aspetta che `scrollY` sia fermo per due frame e misura tutto in un solo
  `evaluate`.
- Screenshot di riferimento vecchio e test verde lo stesso: una tolleranza dell'1% di pixel non vede un'etichetta
  cambiata → dopo una modifica voluta alla UI rigenera i riferimenti e guardali; i testi li controllano le asserzioni.
- Server che risponde 413 a un file troppo grande e il client vede `ECONNRESET`: il server chiude mentre il client
  scrive ancora → decidi dalla dimensione dichiarata (`content-length`) prima di leggere il corpo.
- `sips` (macOS) aggiunge un blocco EXIF quando ridimensiona o ricomprime una foto: per togliere i metadati ridisegna
  l'immagine (canvas) o usa l'originale senza EXIF.
- Node `execFileSync` con output binario grande (es. screenshot via `adb exec-out screencap`): `ENOBUFS` oltre il
  milione di byte di default → `maxBuffer` grande.
- Salto della pagina (CLS) all'apertura: ciò che sta sotto un contenuto caricato dopo viene spinto giù → compare
  solo con i dati (`hidden` finché non c'è) o ha lo spazio riservato; trova chi si sposta con le `sources` delle
  `layout-shift`, non a occhio.
