---
name: blender-riga-di-comando
description: Usare Blender da script Python senza aprire l'interfaccia, per costruire scene, materiali e render (Cycles su GPU) in modo ripetibile. Usala quando l'utente dice "fammi un render in Blender", "crea la scena 3D", "modella questo oggetto", "render realistico", "lancia Blender da script", o quando un render esce troppo scuro, bruciato, sfocato o "di gesso".
---

# Blender da riga di comando

## Prima di tutto chiedi
- Versione di Blender e dove è installato; scheda video (per scegliere OptiX, CUDA, HIP o Metal).
- Dove salvare script, `.blend` e render: una cartella del progetto, **mai** una cartella temporanea.
- Misure reali dell'oggetto e riferimenti (foto, schizzi): si parte da quelli, non da forme inventate.
- Prima delle scelte grosse (approccio, tempi di render, servizi a pagamento) chiedi e di' i costi.

## Lancio
```
blender --background --python script.py -- arg1 arg2
```
Su Windows il percorso completo di `blender.exe` tra virgolette. Gli argomenti dello script:
`sys.argv[sys.argv.index("--")+1:]`. Render lunghi: lanciali in background e aspetta la fine, non controllare
in continuazione.

## Scheletro di una scena
- Parti da zero: `bpy.ops.wm.read_factory_settings(use_empty=True)`.
- Costruisci in **metri** (mm × 1e-3): luci e profondità di campo dipendono dalle distanze reali.
- Mondo: `world.use_nodes = True`, colore del nodo Background.
- Luci `AREA` e camere orientate verso il soggetto: `(target - loc).to_track_quat('-Z', 'Y').to_euler()`.
- Cycles: `samples`, `denoiser = 'OPENIMAGEDENOISE'`, `view_transform = 'AgX'` (con look `AgX - Base Contrast`).
- GPU:
```
pr = bpy.context.preferences.addons['cycles'].preferences
pr.compute_device_type = 'OPTIX'   # 'CUDA' su NVIDIA vecchie, 'HIP' AMD, 'METAL' Mac
pr.refresh_devices()
for d in pr.devices: d.use = (d.type == pr.compute_device_type)
bpy.context.scene.cycles.device = 'GPU'
```
  Il warning sui dispositivi di altri produttori è innocuo.
- Salva il render (`render.filepath`, `bpy.ops.render.render(write_still=True)`) **e** il `.blend`.

## Insidie
- Il Python di Blender **non ha PIL/Pillow**: prepara immagini e geometria nel Python di sistema e passale a
  Blender in JSON.
- Camere macro: il `clip_start` di default (0,1 m) taglia tutto → `0.002`.
- Profondità di campo macro: f/22–32 per avere l'oggetto a fuoco; f/6 è troppo sfocato.
- Luci in Watt con la scala reale: una softbox a 30 cm vuole pochi Watt (~7 W); troppi bruciano i bianchi.
- Materiali sottili: l'Alpha del Principled non vale sul ramo Translucent → `Mix(Transparent, shader, alpha)`.
- Nodo Mix in modalità colore: usa `inputs[6]` / `inputs[7]`, non i nomi "A"/"B".
- Principled 4.x+: `Sheen Weight`, `Subsurface Weight/Radius/Scale` (i nomi vecchi non esistono più).
- `bmesh`: non scorrere tutte le facce a ogni oggetto aggiunto (diventa lentissimo); prendi le facce dai vertici
  appena creati e fai `to_mesh` una volta sola per materiale.
- Una shell aperta dentro una cartella ne blocca lo spostamento: sposta da fuori.

## Realismo (fili, tessuti, oggetti fini)
- Mappe alpha/bump su un piano danno un aspetto piatto "di gesso": per fili e tessuti meglio **tubi 3D veri**.
- Tubi da polilinee con `bmesh`: anelli di 8–14 lati, vettore di riferimento costante per tubo (niente torsioni
  spurie), estremità arrotondate con due anelli extra.
- Torsione senza cuciture: UV = (lunghezza d'arco, angolo/2π), fase `u/passo + n_capi·v` con `n_capi` intero,
  `0.5 + 0.5·sin(2π·fase)` in un nodo Bump e a scurire i solchi.
- Cotone: roughness ~0,95, Sheen ~0,6, un po' di Subsurface e Translucent. Fibre sporgenti corte e piegate:
  troppo lunghe o dritte sembrano aghi.

## Come lavorare
- **Guarda sempre il render** prima di dire "fatto" (anche un'anteprima a bassi campioni): è lì che si vedono gli
  errori di forma.
- Prevedi un'opzione "anteprima veloce" (32–48 campioni, una camera) e fai i render finali a parte.
- Mostra un'anteprima dopo ogni passo e di' con onestà i limiti ("sembra gesso, non cotone").
- Se l'utente dice "non mi piace", fermati e chiedi cosa cambiare prima di rifinire.
