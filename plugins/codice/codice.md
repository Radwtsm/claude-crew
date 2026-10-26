# Codice

Regole comuni della crew (plugin `codice`). Le regole tue e il CLAUDE.md del progetto vincono dove sono più precise.

## Stile
- Il codice nuovo si legge come quello intorno: stessa densità di commenti, stessi nomi, stessi idiomi.
- Nomi per quello che le cose sono davvero; quando lo scope cresce, rinomina (con alias/symlink di compatibilità
  durante il passaggio).
- Riusa l'implementazione migliore che esiste già invece di scriverne una seconda; prima di scrivere uno strumento,
  cerca (`grep -ril <tema>`) se c'è già.
- Un file che uno script del repo scrive di solito si modifica CON quello script, o leggendo prima come lo scrive
  (encoding, BOM, permessi).
- Prima di parsare un formato: leggi il codice che lo scrive e valida su un campione buono prima dei dati veri.
- Prima di aggiungere flag a una CLI, leggi il suo usage.
- Chiavi e hash fissati (host key, checksum) si copiano dalla fonte verificata, mai scritti a memoria.
- Prima di rinominare codici/chiavi usati come dati, cerca nel codice chi li confronta come stringhe (prefissi,
  uguaglianze) e prova in locale.
- Modifiche da portare tra branch o linee diverse: porta i singoli pezzi, mai copiare il file intero.

## Commenti
- Pochi e brevi: solo il perché non ovvio (vincolo nascosto, invariante sottile), mai cosa fa il codice.
- Mai numeri di bug/issue nei commenti: quel contesto va nel commit e nel tracker.
- Prima del commit rileggi i commenti aggiunti nella sessione e togli quelli che ripetono il commit o l'ovvio.

## Segreti
- Mai in codice, repo, documenti, fixture di test, commit o output in chat: si leggono da un file di segreti o dal
  portachiavi.
- Un segreto finito fuori è rubato: va ruotato, non solo cancellato.

## Test
- Mai dati personali reali: fixture/demo generate e deterministiche. Un test che mostra contenuti (screenshot,
  anteprima, simulatore) solo con contenuti finti o oscurati.
- Un bug segnalato = prima un test che fallisce, poi il fix. Un test che fallisce non riproduce il bug finché non è
  provato che tocca la cosa giusta.
- Testa solo ciò che la modifica tocca; tutto solo quando serve.
- Mai modificare codice mentre i test girano in background.
- Codice di sync verso dati veri: spento negli ambienti di test/simulatore prima della prima esecuzione.

## Regole con controllo automatico
- Le regole che contano (flussi UI, nomi, config) hanno una spec scritta e un lint/check che fallisce sulle violazioni
  NUOVE (quelle note in una baseline che può solo calare), agganciato a hook + pre-commit.
- I percorsi che attivano un hook coprono ogni cartella che il suo check esamina.

## Git
- Default: chiedi prima di commit e push. Un progetto personale può dire nel suo CLAUDE.md che si committa e pusha
  da soli dopo la verifica.
- Force-push, `reset --hard`, riscritture della storia: sempre chiedere.
- Un commit che completa parte di un task cita il suo ID.
- Messaggi di commit brevi e asciutti; niente descrizioni lunghe.
- Committare un solo file con altro già in stage: `git commit -- <path>` o controlla `git diff --cached --stat`.
- Dopo aver modificato un `.gitignore`: `git status -uall` prima di `git add -A`.
- Mai `--no-verify` per far passare un segreto vero.

## Codice di terzi
- Fonte ufficiale, firmato (Mac notarizzato, Windows Authenticode valido) oppure fissato a versione/commit + hash.
  Add-on in chiaro (skill, script) letti per intero prima di installarli. Dai il comando di verifica.
  Mai suggerire di aggirare Gatekeeper/SmartScreen.

## Trappole tecniche
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
