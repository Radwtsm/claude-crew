---
name: server-minecraft
description: Gestire un server Minecraft Java (Paper, Purpur, Fabric, Forge/NeoForge) - installazione, avvio con flag JVM giusti, plugin e mod, backup, prestazioni (lag, TPS, RAM), lettura di crash report e log, whitelist e permessi, aggiornamento di versione. Usala quando si parla di server Minecraft, plugin Paper/Spigot, mod server-side, lag del server o crash.
---

# Server Minecraft

## Prima di tutto chiedi (se non lo sai già)
- Versione di Minecraft e tipo di server (Paper/Purpur = plugin; Fabric/Forge/NeoForge = mod; non si mischiano).
- Dove gira (PC di casa, VPS, hosting con pannello) e quanta RAM ha la macchina.
- Quanti giocatori insieme, e se è Java, Bedrock o entrambi (Geyser).

## Scelte di base
- Vanilla con plugin → **Paper** (o Purpur). Modpack → il loader del modpack, stessa versione esatta del client.
- Java: 1.20.5+ vuole Java 21; 1.18–1.20.4 Java 17. Controlla con `java -version`.
- RAM: 4–6 GB per pochi giocatori vanilla, 6–10 GB per modpack; mai tutta la RAM della macchina (lascia 1–2 GB al
  sistema). `-Xms` = `-Xmx`.
- Flag di avvio: quelli di Aikar per Paper (generatore ufficiale su flags.sh di PaperMC); non inventarli.
- `eula.txt` → `eula=true` solo dopo che l'utente ha accettato l'EULA di Mojang.

## Sicurezza
- `online-mode=true` (salvo proxy Velocity/BungeeCord configurato bene). Whitelist attiva per server tra amici.
- Porta aperta solo 25565 (o quella del server); RCON e console mai esposti su Internet.
- Plugin e mod solo da Hangar, Modrinth, SpigotMC, CurseForge o il sito dell'autore; mai jar "crackati".
- L'operatore (`op`) solo a chi gestisce il server; per il resto LuckPerms.

## Backup
- Prima di ogni aggiornamento, plugin nuovo o modifica al mondo: backup delle cartelle `world*` + `plugins/` o `mods/`
  + `config/`, con il server fermo o dopo `save-off` + `save-all flush` (poi `save-on`).
- Backup automatici con data nel nome, tenere gli ultimi N, e almeno una copia fuori dalla macchina.
- Un backup vale solo se si è provato a ripristinarlo una volta.

## Prestazioni (lag)
1. Misura prima: `/tps` (o `/mspt`), poi **spark** (`/spark profiler`, 2–5 minuti durante il lag) e leggi il report.
2. Cause tipiche: troppe entità (farm, item a terra), redstone/hopper, chunk generati al volo, view-distance alta, un
   plugin/mod lento nel profilo.
3. Leve: `simulation-distance` 4–6 e `view-distance` 6–10, pre-generare il mondo (Chunky) con un bordo, limiti
   entità nei config di Paper; RAM in più raramente è la cura.

## Crash e errori
- Leggi `logs/latest.log` e la cartella `crash-reports/`: cerca la prima riga `Caused by` e i nomi di mod/plugin
  nello stack trace.
- "Mod/plugin X richiede Y" o `NoSuchMethodError` → versioni non allineate: controlla versione del gioco e dipendenze.
- Server che non parte dopo un aggiornamento → ripristina il backup, aggiorna un pezzo alla volta.

## Aggiornare la versione
- Aspetta che tutti i plugin/mod importanti supportino la nuova versione. Backup, aggiorna il jar del server, avvia
  una volta su una copia del mondo, poi sul mondo vero. Mai tornare a una versione più vecchia sullo stesso mondo.
