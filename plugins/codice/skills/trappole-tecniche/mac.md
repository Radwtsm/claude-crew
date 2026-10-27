# Trappole: macOS

Letto da `SKILL.md` prima di: launchd, File Provider (iCloud/Drive), sips.

- macOS + Google Drive/iCloud (File Provider): un job di launchd con `/usr/bin/python3` non può nemmeno chiedere il
  permesso ("Platform binary prompting is Deny"): usa un Python non di sistema e fai premere Consenti una volta.
- File Provider: leggere da launchd un file non ancora scaricato dà `Resource deadlock avoided` (EDEADLK): saltalo
  e riprova dopo, mai trattarlo come cancellato; la cartella va resa "disponibile offline".
- `sips` (macOS) aggiunge un blocco EXIF quando ridimensiona o ricomprime una foto: per togliere i metadati ridisegna
  l'immagine (canvas) o usa l'originale senza EXIF.
