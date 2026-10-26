---
name: after-effects-pannelli
description: Costruire un pannello (plugin CEP) per After Effects con interfaccia HTML/JS che crea layer, keyframe con curve, testi animati, effetti, maschere ed espressioni via ExtendScript. Usala quando l'utente dice "voglio un plugin per After Effects", "un pannello per AE", "uno script che crea animazioni in AE", "estensione CEP", o quando un pannello AE dà errori come "L'oggetto non è valido" o "fuori gamma".
---

# Pannelli per After Effects (CEP + ExtendScript)

Regole imparate costruendo un pannello completo per AE 2026. Legenda: ✅ verificato in AE · ⚠️ da verificare
nella propria versione.

## Prima di tutto chiedi
- Versione di After Effects e sistema (Windows/Mac).
- Se nel progetto aperto c'è lavoro suo: **non creare né modificare niente lì**. Per provare serve un **progetto
  vuoto con una comp 1920×1080 senza layer**; prima di creare qualcosa controlla davvero
  (`app.project.numItems`, `app.project.file`), non fidarti solo della risposta.
- Se vuole scrivere lui il codice o se lo scrivi tu.

## Setup ✅
- AE 2026 = runtime **CEP 12**, pannello su **Chromium 99**; lato AE **ExtendScript ES3** (niente `let/const`,
  arrow, `JSON` nativo, `forEach`, virgole finali).
- Cartella delle estensioni dell'utente: Windows `%APPDATA%\Adobe\CEP\extensions\<nome>`, Mac
  `~/Library/Application Support/Adobe/CEP/extensions/<nome>`. Sviluppa nella tua cartella e collegala con una
  junction/symlink: AE legge i file senza copiarli.
- File minimi: `CSXS/manifest.xml` (Host `AEFT` versione `[15.0,99.9]`, `MainPath`, `ScriptPath` al `.jsx`,
  `Type Panel`), `.debug` con `<Host Name="AEFT" Port="8088" />`, `index.html`, `jsx/host.jsx`.
- Estensione non firmata = serve il **flag di debug**, che l'utente imposta da solo (è un'impostazione di
  sicurezza). Windows, in PowerShell:
```
reg add "HKCU\Software\Adobe\CSXS.12" /v PlayerDebugMode /t REG_SZ /d 1 /f
```
  Mac, nel Terminale: `defaults write com.adobe.CSXS.12 PlayerDebugMode 1`. Poi **chiudere del tutto AE** e
  riaprirlo. Se il pannello non compare, il log (Windows `%TEMP%\CEP12-AEFT.log`) dice
  `Signature verification failed`: il flag non è attivo.
- Nessuna libreria: basta un wrapper su `window.__adobe_cep__.evalScript(script, callback)`. Fuori da AE quell'oggetto
  non esiste: gestiscilo, così il pannello si prova anche in un browser.

## Architettura che funziona
- Ogni funzione = **parametri + `build(valori)` → scena JSON** (layer, tracce di keyframe, effetti…). La stessa
  scena viene disegnata nell'anteprima su canvas e mandata ad AE: anteprima e risultato non divergono.
- Verso AE: `evalScript("applica(" + JSON.stringify(JSON.stringify(scena)) + ")")`, in ExtendScript
  `eval("(" + testo + ")")`.
- Progetta su 1920×1080 con origine al centro e scala in AE per `k = min(w/1920, h/1080)`: funziona anche in 9:16.
- Una sola funzione d'ingresso che restituisce `"OK:..."` o `"ERR:..."`, sempre dentro `try/catch` e
  `beginUndoGroup … finally endUndoGroup`.

## Trappole dell'API (le più costose)
- ✅ **Riferimenti non più validi**: dopo aver aggiunto o spostato elementi in un gruppo (es. contenuto di una forma)
  i riferimenti ai fratelli possono rompersi ("L'oggetto non è valido"). Imposta i valori **subito dopo** aver
  creato l'elemento, per riusarlo **rileggilo per `matchName`**, fai i `moveTo` **per ultimi**.
- ✅ **Keyframe sullo stesso istante** = AE ne crea uno solo, poi `setInterpolationTypeAtKey` fallisce con
  "valore N fuori gamma". Prima di creare keyframe: ordina per tempo e unisci i duplicati.
- **Curve**: un `cubic-bezier(x1,y1,x2,y2)` diventa influenza uscita `x1·100`, velocità uscita
  `Δvalore·y1/(x1·Δt)`; influenza ingresso `(1−x2)·100`, velocità ingresso `Δvalore·(1−y2)/((1−x2)·Δt)`.
  Overshoot = y fuori da 0..1. Proprietà spaziali (posizione): 1 `KeyframeEase`, velocità lungo il percorso; le
  altre: una per dimensione (`Scale` ne ha 3 anche su layer 2D). Prima `setInterpolationTypeAtKey(BEZIER)` e
  `setTemporalEaseAtKey`, poi gli eventuali `HOLD`.
- **Ordine in un gruppo di forma**: percorso → Trim Paths → Stroke → Fill → Repeater (i modificatori agiscono sui
  percorsi sopra). `addProperty` non garantisce l'ordine: riordina.
- **Repeater**: ruota/scala attorno all'Anchor; per un'orbita `Position = Anchor = [−raggio, 0]`. Due repeater in
  fila = griglia.
- **Morph** = keyframe sul tracciato con lo **stesso numero di vertici** in ogni forma (campiona il perimetro a
  passo costante partendo dall'alto).
- **Testo per lettera/parola/riga**: Text Animator + **Expression Selector**; l'espressione calcola la quantità con
  `textIndex`, `textTotal`, `time`, e la stessa formula va replicata nell'anteprima. Togli il Range Selector di
  default. Metti ritardo/durata/sfalsamento in **Slider Control** letti con `effect("nome")(1)`: l'utente li cambia
  in AE. Font = nome PostScript (`app.fonts.allFonts`).
- ⚠️ **Effetti**: `addProperty(matchName)`; se torna `null` l'effetto non c'è. Imposta i parametri per indice
  **in `try/catch` uno per uno** e mostra un avviso invece di bloccare tutto. Verifica gli indici
  (`fx.property(i).name`). Valori in pixel × `k`, colori `[r,g,b]` 0..1.
- I colori di un **Gradient Fill** di forma non si impostano da script: usa `ADBE Ramp` su un solido.
- ⚠️ **Maschere**: `ADBE Mask Parade` → `ADBE Mask Atom` (`ADBE Mask Shape/Feather/Offset/Opacity`, `inverted`);
  dimensioni in % di `layer.sourceRectAtTime()`.
- ⚠️ **3D**: `threeDLayer = true`; camera solo se non c'è (`instanceof CameraLayer`); per muovere più layer insieme
  un null 3D con `anchorPoint [0,0,0]` e figli con `setParentWithJump` (il normale `parent =` compensa i valori).
- **Layer selezionati**: keyframe relativi al valore attuale (`valueAtTime(t0,false)`); posizione nel tempo:
  dal cursore, fino al cursore, inizio o fine del layer. La selezione si legge con un polling (~800 ms).
- 🧪 **Spostare keyframe esistenti** (strumenti tipo "ease", "inverti", "sfalsa"): non esiste `moveKey`. Leggi
  tutto (valore, interpolazioni, ease, tangenti spaziali, roving), **rimuovi tutti** quelli da spostare (indici
  decrescenti), **poi** riaggiungili e ritrovali con `nearestKeyIndex(t)` (gli indici cambiano a ogni `addKey`).
  Invertire nel tempo = scambiare entrata e uscita. Quante `KeyframeEase` passare: leggilo da
  `keyOutTemporalEase(i).length`, non indovinarlo.
- **Espressioni** che devono valere per numeri e array: `add()`/`mul()` invece di `+`/`*`.
- ⚠️ **Parametri di effetti con gruppi** (Fractal Noise, 4-Color Gradient): l'indice è incerto. Cerca per nome
  (inglese e lingua di AE), poi matchName, poi indice.
- **Transizioni di "camera"** su un adjustment layer: Motion Tile (output 300%, bordi specchiati) e poi
  Transform (otturatore proprio per il motion blur); keyframe che accelerano fino al taglio, salto con HOLD,
  poi frenano.
- **Rollback**: dopo un errore `app.executeCommand(16)` (Annulla) **solo se sono stati creati layer**, altrimenti
  annulleresti un'azione precedente dell'utente.

## Anteprima su canvas
- Stesse formule dell'host (bezier, ordine delle lettere); al posto di `random()` un hash deterministico.
- Dichiara quando è approssimata (wiggle, effetti pixel): mai promettere pixel-perfect.
- Proteggi l'interpolazione da keyframe sullo stesso tempo; per i loop metti un tetto alla durata d'anteprima.

## Interfaccia
- Look Adobe scuro (sfondo ~`#1d1d1d`, blu `#2680eb`, raggio 4px, pulsanti a pillola). Anteprima sempre visibile.
- Molti preset: sezioni → categorie → ricerca globale → preferiti; due viste (libreria / modifica) se stretto,
  affiancate se largo. Il pulsante principale dice cosa farà ("Applica ai layer selezionati").
- Errori in rosso con il **testo originale di AE**: l'utente lo copia e te lo manda.
- Prova a 320, 440 e 900 px di larghezza.
- **Risorse di terzi** (texture, immagini): leggi la licenza prima. Molte (es. Texturelabs) vietano di includerle in
  plugin o template: il pannello le legge da una cartella dell'utente, che le scarica da sé.

## Come provare
1. Pannello in un normale browser (server statico locale) per layout ed errori JS.
2. Per ogni preset e ogni opzione: `build`, disegno a più tempi, `JSON.stringify`, controllo keyframe doppi.
3. Prova a secco dell'host in Node con un AE finto (oggetti `Proxy` che rispondono a tutto): trova errori di
   codice, non quelli dell'API vera. Attento ai cicli `while (x.property(...))`, con un finto sono infiniti.
   Con `vm` gli array creati fuori dal contesto falliscono `instanceof Array` dentro: crea i dati nel contesto.
4. Dentro AE dalla porta di debug 8088 (protocollo DevTools): ricarica il pannello, rivaluta l'host con
   `$.evalFile(...)`, leggi lo stato. Creare layer solo nel progetto vuoto concordato.

## Checklist prima di consegnare
- Pannello aperto, nessun errore in console, tutti i preset provati.
- Niente keyframe doppi; ogni creazione in un undo group; rollback solo se ci sono layer nuovi.
- Pixel scalati con `k` (prova anche una comp verticale); parametri effetto con avviso se falliscono.
- Il progetto dell'utente non è stato toccato; backup zip prima dei cambi grandi.
