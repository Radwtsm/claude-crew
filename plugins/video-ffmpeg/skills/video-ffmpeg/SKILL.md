---
name: video-ffmpeg
description: Lavori sui video - tagliare, unire, comprimere, convertire formati, estrarre audio, sottotitoli, cambiare risoluzione o fps, video per YouTube/TikTok/Instagram/Discord, registrazioni di gameplay (OBS), montaggio (DaVinci Resolve, Premiere, CapCut). Comandi ffmpeg pronti e spiegati. Usala quando si parla di video, clip, registrazioni, codec o dimensioni dei file video.
---

# Video e ffmpeg

## Prima di tutto chiedi (se non lo sai già)
- Dove va il video (YouTube, TikTok/Reels, Discord, archivio) e su che sistema lavora l'utente (Windows/Mac).
- Se preferisce un programma con interfaccia: allora passi nel programma, non comandi.

## Regole
- Mai sovrascrivere l'originale: il risultato va in un file nuovo (`-n` evita di sovrascrivere per sbaglio).
- Prima di comprimere o convertire un video lungo, prova su 20 secondi (`-t 20`) e fai controllare il risultato.
- Nomi di file con spazi tra virgolette. Dai un comando per riga.
- ffmpeg solo dal sito ufficiale (ffmpeg.org) o da un gestore pacchetti (winget, Homebrew).

## Comandi tipo
Tagliare senza ricodificare (veloce, taglio sul fotogramma chiave più vicino):
```
ffmpeg -n -ss 00:01:30 -to 00:02:45 -i "in.mp4" -c copy "taglio.mp4"
```
Comprimere per condividere (H.264, buona qualità; CRF più alto = file più piccolo):
```
ffmpeg -n -i "in.mp4" -c:v libx264 -crf 23 -preset slow -c:a aac -b:a 160k "out.mp4"
```
Verticale 1080×1920 per TikTok/Reels da un video orizzontale (ritaglio centrale):
```
ffmpeg -n -i "in.mp4" -vf "crop=ih*9/16:ih,scale=1080:1920" -c:a copy "verticale.mp4"
```
Solo audio:
```
ffmpeg -n -i "in.mp4" -vn -c:a libmp3lame -q:a 2 "audio.mp3"
```
Unire clip con lo stesso formato: file `lista.txt` con righe `file 'clip1.mp4'`, poi
```
ffmpeg -n -f concat -safe 0 -i lista.txt -c copy "unito.mp4"
```
Sottotitoli incollati nel video:
```
ffmpeg -n -i "in.mp4" -vf "subtitles=sub.srt" -c:a copy "con-sub.mp4"
```

## Riferimenti rapidi
- YouTube: MP4, H.264, 1080p o 4K, fps uguali alla registrazione. Discord senza Nitro: file piccoli → abbassa CRF
  o risoluzione, non i fps del gameplay.
- OBS per gameplay: registra in MKV (non si corrompe se crasha), poi "Remux" in MP4; encoder hardware (NVENC,
  Apple VT) se disponibile.
- Video da telefono che risulta "girato" o in HDR sbiadito: chiedi il modello e verifica con
  `ffprobe -hide_banner "in.mp4"` prima di correggere.
