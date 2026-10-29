# Codice

Regole comuni di Pleyades (plugin `codice`). Le regole tue e il CLAUDE.md del progetto vincono dove sono più
precise; su segreti e codice di terzi solo per stringere.

## Prima di toccare
- Ogni scelta ha una fonte (una persona, un punto del codice, un progetto d'esempio); senza è un'assunzione: scritta
  come tale e confermata prima. «Verificato» ≠ «supposto»; un supposto non diventa mai regola.
- Prima di cambiare un'area: la funzione intera e chi ha cambiato quelle righe e perché (`git log -L`, ticket).
- Prima di confrontare due implementazioni, leggile intere (una regola sta anche nei dati, non solo nel codice).

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
- Testa solo ciò che la modifica tocca; tutto solo quando serve. Uno strumento che installa o aggiorna per tutti ha
  test automatici della logica, con i servizi esterni sostituibili.
- Mai modificare codice mentre i test girano in background.
- Codice di sync verso dati veri: spento negli ambienti di test/simulatore prima della prima esecuzione.

## Regole con controllo automatico
- Le regole che contano (flussi UI, nomi, config) hanno una spec scritta e un lint/check che fallisce sulle violazioni
  NUOVE (quelle note in una baseline che può solo calare), agganciato a hook + pre-commit.
- I percorsi che attivano un hook coprono ogni cartella che il suo check esamina.

## Git
- Default: chiedi prima di commit e push. Un progetto personale può dire nel suo CLAUDE.md che si committa e pusha
  da soli dopo la verifica, solo se un pre-commit (segreti, lint, test) può fermare il commit.
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
Stanno nella skill `trappole-tecniche` (stesso plugin): si legge prima di shell, hook, ssh, test end-to-end, SQLite,
immagini, layout web, launchd/File Provider, o quando qualcosa si comporta in modo strano. Una trappola nuova va lì.
