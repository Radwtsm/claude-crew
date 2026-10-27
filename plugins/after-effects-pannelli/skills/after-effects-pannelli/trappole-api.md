# After Effects: trappole dell'API (le più costose)

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
