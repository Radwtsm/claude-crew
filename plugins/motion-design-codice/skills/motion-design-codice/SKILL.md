---
name: motion-design-codice
description: Creare animazioni di motion design (reel, intro di logo, video di brand) generandole in codice con Node, canvas e ffmpeg, da consegnare in clip pronte per il montaggio. Usala quando l'utente dice "fammi un'animazione", "un reel animato", "motion graphics per il brand", "animazione del logo", "video senza After Effects", o quando un'animazione ha scatti, momenti fermi o forme che spariscono.
---

# Motion design in codice

## Prima di tutto chiedi
- Formato e durata (es. reel 9:16 1080×1920 30 fps), dove verrà pubblicato.
- Colori, font, logo del brand e cosa **non** si può modificare (il logo si usa così com'è).
- Stile di riferimento (un video o un'immagine) e se ci sono testi o solo grafica.
- Se il montaggio finale lo fa l'utente (Premiere/After Effects): allora consegna clip, non solo un video unico.

## Motore
- Node + `@napi-rs/canvas` per disegnare, `ffmpeg` per codificare.
- **Ogni fotogramma è una funzione pura del tempo** `draw(ctx, t)`: niente stato tra fotogrammi, così qualsiasi
  istante si può rigenerare, controllare o renderizzare in parallelo.
- File separati per: libreria (palette, font, easing, molle), sequenze, sfondo, render, foglio provini, analisi.
- Su Windows Python si chiama `py`.

## Movimento
- **Molle** (risposta chiusa di una molla smorzata) per ingressi e spostamenti: partenza decisa, arrivo morbido,
  overshoot appena percepibile. Tieni 3–4 preset (standard, veloce per le uscite, lento per spostamenti grandi,
  morbido) invece di valori sparsi.
- **Ease-in-out** morbido per morph di forme e linee che si disegnano.
- **Motion blur**: 4 sotto-fotogrammi su un otturatore a 180°, mediati. Rallenta il render: prevedi un'opzione
  senza blur per le anteprime.
- Sfalsamenti di 0,05–0,15 s tra elementi in serie.
- Niente rimbalzi cartoon se lo stile è elegante; ritmo rilassato, spazio tra le azioni.

## Continuità
- Stile "una forma che si trasforma": ogni scena nasce dalla geometria della precedente, niente tagli netti.
- Un elemento **non sparisce e riappare** durante una trasformazione: l'originale smette di essere disegnato nello
  stesso fotogramma in cui nascono i suoi eredi, con stessa posizione, dimensione e colore.
- Due forme che si scambiano condividono rotazione, scala e colore nell'istante dello scambio; le dissolvenze si
  sovrappongono (mai un fotogramma vuoto o doppio).
- Riempimenti bianchi grandi: farli crescere dal centro pieni, non in dissolvenza (in dissolvenza sembrano grigi).
- Se lo stile lo chiede, niente di fermo: respiri, rotazioni lente, galleggiamenti, piccolo push-in di camera.

## Controllo
- **Foglio provini** (contact sheet) dei fotogrammi prima del render completo.
- Uno script di **analisi** che misura quanto cambia l'immagine ogni 0,5 s: trova tratti fermi e scatti bruschi.
- Verifica durata, risoluzione e fps del file finale con `ffprobe`.

## Export
- Anteprima/social: MP4 H.264 `-crf 14 -pix_fmt yuv420p`.
- Montaggio: MOV ProRes 422 HQ 10 bit.
- Audio aggiunto dopo:
```
ffmpeg -i video.mp4 -i audio.wav -map 0:v -map 1:a -c:v copy -c:a aac -b:a 256k -shortest finale.mp4
```

## Reel Instagram
- Centro delle grafiche a (540, 960); area utile larga al massimo ~900 px.
- La griglia del profilo ritaglia il centro in 4:5 (1080×1350) e 3:4: il contenuto chiave sta tra y ~420 e ~1500.
- In basso e a destra ci sono didascalia e pulsanti dell'app: lasciali liberi.
- Per le altre misure di export vedi il plugin `grafica`.
