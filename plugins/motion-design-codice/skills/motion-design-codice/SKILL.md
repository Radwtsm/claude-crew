---
name: motion-design-codice
description: Motion design generato in codice (Node, canvas, ffmpeg): reel, intro di logo, video di brand in clip pronte. Usala per "fammi un'animazione", "reel animato", "animazione del logo", "video senza After Effects", o animazioni con scatti o forme che spariscono.
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
- **Irregolare ≠ casuale**: se il cliente chiede linee «irregolari» o «non all'unisono», varia poche cose
  misurate (fase, lunghezze dei tratti, ritardi) su forme pulite; rumore o armoniche sovrapposte sembrano fatte a caso.
- Un passaggio da onda a forma che si aggroviglia: fai rientrare le linee in un punto e fai sbocciare le forme da lì.

## Continuità
- Stile "una forma che si trasforma": ogni scena nasce dalla geometria della precedente, niente tagli netti.
- Un elemento **non sparisce e riappare** durante una trasformazione: l'originale smette di essere disegnato nello
  stesso fotogramma in cui nascono i suoi eredi, con stessa posizione, dimensione e colore.
- Due forme che si scambiano condividono rotazione, scala e colore nell'istante dello scambio; le dissolvenze si
  sovrappongono (mai un fotogramma vuoto o doppio).
- Riempimenti bianchi grandi: farli crescere dal centro pieni, non in dissolvenza (in dissolvenza sembrano grigi).
- Se lo stile lo chiede, niente di fermo: respiri, rotazioni lente, galleggiamenti, piccolo push-in di camera.
- Titolo-parola tra due scene: una linea sottile esce sotto la parola e diventa l'elemento con cui parte la scena
  dopo (si raccoglie in un punto = il nucleo, o resta come base di una fila): niente stacco.

## Metodo per una revisione grande
- Prima i **fotogrammi chiave fissi** di tutte le scene da rifare (uno per momento, su una tavola), approvati
  dall'utente; poi si anima e si renderizza.
- Scrivi ogni micro-scena come funzione `(ctx, p, vita)`: `p` 0→1 = avanzamento, `vita` = orologio lento per il
  respiro. Il fotogramma approvato è la posa `p = 1`: animarla dopo non richiede di ridisegnarla.
- Una scena per volta (o due), approvata prima di passare alla successiva.

## Controllo
- **Foglio provini** (contact sheet) dei fotogrammi prima del render completo.
- Uno script di **analisi** che misura quanto cambia l'immagine ogni 0,5 s: trova tratti fermi e scatti bruschi.
- Verifica durata, risoluzione e fps del file finale con `ffprobe`.

## Insidie
- Foglio provini che mescola fotogrammi di prove diverse → i fermi immagine vecchi con lo stesso prefisso restano
  nella cartella → un prefisso per prova e cancella i fermi dopo aver fatto il foglio.
- Un punto che cala di luce nel raccordo con una dissolvenza dal nero → disegnarlo sopra il nero con alpha = quota
  della dissolvenza non somma a 1 → tienilo pieno per quasi tutta la dissolvenza (alpha `min(1, 4·nero)`), con
  stessa posizione e misura dell'elemento sotto.

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
- Parola sola grande (titolo): dimensione calcolata dalla larghezza massima (~860 px) **compresa la spaziatura**,
  così resta intera sul telefono qualunque sia la parola.
- Per le altre misure di export vedi il plugin `grafica`.
