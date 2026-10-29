# Trappole: Server, rete e servizi

Letto da `SKILL.md` prima di: SQLite, server HTTP, VPN/mesh, Docker e firewall, Cloudflare, API pubbliche, versioni di terzi.

- SQLite vivo: copialo CON il file `-wal` o aprilo read-only sul posto (`file:…?mode=ro`); una copia nuda perde
  gli ultimi minuti.
- Python `http.server` con molte richieste insieme: backlog di default 5 → `request_queue_size = 128` + retry nel client.
- Stato "online" di una VPN/mesh resta vero per minuti dopo che un peer si spegne: per acceso/spento interroga il
  dispositivo stesso (porta TCP, ping del mesh).
- Server che risponde 413 a un file troppo grande e il client vede `ECONNRESET`: il server chiude mentre il client
  scrive ancora → decidi dalla dimensione dichiarata (`content-length`) prima di leggere il corpo.
- Container senza DNS dopo averli isolati dalla LAN (DROP verso le reti private in `DOCKER-USER`) → il DNS passa dal
  router → `dns:` pubblici nel compose; con br_netfilter anche i container della stessa rete passano da
  `DOCKER-USER`: prima un RETURN con sorgente e destinazione nella loro sottorete.
- Calendario, Contatti o app (CalDAV/WebDAV) dietro Cloudflare Access che non si collegano → non sanno fare il login
  da browser → application *Bypass* solo sui percorsi DAV/app, protetti dal login del servizio con 2FA; crea Access
  prima di pubblicare l'hostname, così non resta mai aperto.
- Versione "pubblicata da 2 settimane" che invece è nuova → la data di un tag su Docker Hub è l'ultima
  ricompilazione, non il rilascio → guarda la data della release del progetto (GitHub releases).
- Overpass/Nominatim (OpenStreetMap) che rispondono 429/502/504 → servizio pubblico carico → una richiesta al
  secondo con un User-Agent, nuovi tentativi con attesa crescente, mai un loop stretto.
- Nextcloud Talk: le menzioni arrivano come `{mention-user1}` nel testo, il nome sta in `messageParameters` → un
  programma (o un Claude) che legge solo `message` non sa chi è taggato → risolvi i segnaposto coi parametri.
- Dato cambiato direttamente (database, file di config) e la verifica dice «non funziona» → il servizio lo tiene
  ancora in cache e il test misura la cache → riavvia (o svuota la cache di) chi lo legge, poi verifica.
