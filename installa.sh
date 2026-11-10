#!/bin/bash
# La riga unica (Mac, Linux): scarica la guida `pleyades-cli` (Pleyades tools) e la lancia. Si può rilanciare: salta ciò che c'è già.
#   curl -fsSL https://raw.githubusercontent.com/Radwtsm/claude-crew/main/installa.sh | bash
# Con un progetto a cui sei stato invitato:
#   curl -fsSL https://raw.githubusercontent.com/Radwtsm/claude-crew/main/installa.sh | bash -s -- PROPRIETARIO/REPO
# Con un invito dell'app Pleiadi (la riga del messaggio): il codice in una variabile, mai negli argomenti
#   curl -fsSL …/installa.sh | INVITO='XXXXX-XXXXX-XXXXX-XXXXX' STUDIO='studio.nome.org' bash
#   su Mac installa solo l'app Pleiadi e la apre col codice; PLEYADES_COMPLETO=1 fa anche il resto (la guida)
# Qui solo ciò che serve a far partire Python; tutto il resto (Claude Code, GitHub, plugin, progetti, Nextcloud)
# lo fa crew.py, uguale su Mac, Linux e Windows.
set -u
tempo() { local s=$(( $(date +%s) - $1 )); [ $s -ge 60 ] && printf '%d:%02d' $((s/60)) $((s%60)) || printf '%d s' $s; }
giro=(✦ ✧ ⋆ · ⋆ ✧)  # la stella che pulsa (Pleyades tools); array: il bash 3.2 del Mac taglia male i caratteri UTF-8
A='\033[38;5;153m'; F='\033[38;5;61m'; Z='\033[0m'  # azzurro stella, blu fioco (marchio Pleyades)
# Con l'invito su Mac (A90, owner 02/11): solo l'app, niente strumenti di Apple, password o domande; il resto si prepara
# dopo, se serve (PLEYADES_COMPLETO=1 = la guida completa di prima). Scaricata con curl: niente quarantena, quindi
# Gatekeeper non la ferma; installata solo se firmata dalla squadra (come crew.py installa_app_mac).
RELEASE_APP="$(dirname https://github.com/Radwtsm/claude-crew)/pleiadi-app/releases/latest/download"  # come crew.py APP_RELEASE
solo_app() (  # sottoshell: la trap pulisce la cartella temporanea a ogni uscita
  codice=$(printf '%s' "$INVITO" | tr -d '[:space:]' | tr '[:lower:]' '[:upper:]')
  if ! printf '%s' "$codice" | grep -Eq '^[A-HJ-NP-Z2-9]{5}(-[A-HJ-NP-Z2-9]{5}){3}$'; then
    printf "  ✗ Il codice dell'invito non è giusto: copia di nuovo la riga intera dal messaggio.\n"; exit 1
  fi
  printf "\n  ${A}Pleiadi Studio${Z} · preparo il computer (circa un minuto, non devi fare niente)\n\n"
  cartella="${PLEYADES_APP_DIR:-$HOME/Applications}"  # PLEYADES_APP_DIR: i test, in una cartella da buttare
  if [ -z "${PLEYADES_APP_DIR:-}" ] && [ -d /Applications/Pleiadi.app ] || [ -d "$cartella/Pleiadi.app" ]; then
    printf "  ✓ Pleiadi c'è già (si aggiorna da sola)\n"
  else
    tmp=$(mktemp -d); trap 'rm -rf "$tmp"' EXIT
    printf '  … Scarico Pleiadi\n'
    if ! curl -fsSL "$RELEASE_APP/Pleiadi.app.tar.gz" -o "$tmp/app.tar.gz" ||
       ! tar -xzf "$tmp/app.tar.gz" -C "$tmp" || [ ! -d "$tmp/Pleiadi.app" ]; then
      printf '  ✗ Non riesco a scaricare Pleiadi: controlla internet e incolla di nuovo la stessa riga.\n'; exit 1
    fi
    printf '  … Controllo che sia quella della squadra\n'
    if ! codesign --verify --deep --strict \
         -R='anchor apple generic and certificate leaf[subject.OU] = "4KLXZKJMRY"' "$tmp/Pleiadi.app" 2>/dev/null; then
      printf "  ✗ Il file scaricato non ha la firma della squadra: non lo installo. Avvisa chi ti ha invitato.\n"; exit 1
    fi
    printf '  … Installo Pleiadi (nella tua cartella Applicazioni: niente password)\n'
    mkdir -p "$cartella" && ditto "$tmp/Pleiadi.app" "$cartella/Pleiadi.app" ||
      { printf "  ✗ L'installazione non è andata: incolla di nuovo la stessa riga.\n"; exit 1; }
    # registrata subito: senza, il primo `open pleiadi://` non sa ancora a chi darlo
    [ -z "${PLEYADES_APP_DIR:-}" ] && /System/Library/Frameworks/CoreServices.framework/Frameworks/LaunchServices.framework/Support/lsregister \
      -f "$cartella/Pleiadi.app" 2>/dev/null
    printf '  ✓ Pleiadi installata\n'
  fi
  [ "${PLEYADES_NON_APRIRE:-}" = 1 ] && exit 0  # i test: installa e controlla, senza aprire l'app
  # il link apre l'app col codice già scritto; entra solo chi preme la freccia (accesso.rs → link_aperto)
  open "pleiadi://invito/$codice" 2>/dev/null || open "$cartella/Pleiadi.app"
  printf "\n  ✓ Pleiadi è aperta: premi la freccia per entrare. Puoi chiudere questa finestra.\n\n"
)
if [ -n "${INVITO:-}" ] && [ "${PLEYADES_COMPLETO:-}" != 1 ] && [ "$(uname)" = Darwin ]; then
  solo_app; exit $?
fi
if [ "$(uname)" = Darwin ] && ! xcode-select -p >/dev/null 2>&1; then
  if [ "${PLEYADES_SI:-}" != 1 ]; then  # PLEYADES_SI=1: chi lancia da script, senza domanda
    printf '→ Mancano gli strumenti di Apple (git e python3, circa 1 GB): li installo da Apple (softwareupdate)?\n'
    printf '  Installo? [S/N] '
    r=''; read -r r </dev/tty 2>/dev/null
    case "$r" in
      [sSyY]*) ;;
      *) printf 'Niente installato. A mano: nel Terminale `xcode-select --install`, poi incolla di nuovo la stessa riga.\n'
         exit 0 ;;
    esac
  fi
  # come Homebrew: gli strumenti di Apple da softwareupdate (minuti) invece della finestra (che stima anche 35 h)
  printf '→ Installo gli strumenti di Apple (git e python3, circa 1 GB).\n'
  printf '  NON scrivere niente finché non compare «Password del Mac»: quello che scrivi prima resta visibile.\n'
  printf '  Se è aperta la finestra «Scarico il software» di un tentativo precedente, premi «Interrompi»: ne basta uno.\n'
  segnale=/tmp/.com.apple.dt.CommandLineTools.installondemand.in-progress
  elenco=$(mktemp); log=$(mktemp)
  trap 'stty echo </dev/tty 2>/dev/null; rm -f "$segnale" "$elenco" "$log"' EXIT INT
  touch "$segnale"
  stty -echo 2>/dev/null </dev/tty  # 28/10: chi scrive la password in anticipo non la lascia sullo schermo
  softwareupdate -l >"$elenco" 2>&1 & pid=$!; t0=$(date +%s); i=0
  while kill -0 $pid 2>/dev/null; do  # riga di stato live: la ricerca dura 1-2 minuti senza scritte
    printf "\r  ${A}%s${Z} cerco il pacchetto di Apple ${F}· %s (di solito 1-2 min)${Z}\033[K" "${giro[i++%6]}" "$(tempo $t0)"
    sleep 0.2
  done
  printf '\r\033[K'
  nome=$(sed -n 's/^ *\* Label: //p' "$elenco" | grep 'Command Line Tools' | tail -1)
  mb=$(grep -A1 "Label: $nome" "$elenco" | grep -o 'Size: [0-9]*' | grep -o '[0-9]*' | head -1); mb=$(( ${mb:-0} / 1024 ))
  perl -MPOSIX -e 'tcflush(0, TCIFLUSH)' </dev/tty 2>/dev/null  # butta ciò che è stato scritto in anticipo
  stty echo 2>/dev/null </dev/tty
  if [ -n "$nome" ] && sudo -k && sudo -v -p '→ Password del Mac (quella con cui accendi il computer; mentre scrivi non si vede niente): '; then
    [ $mb -gt 0 ] && printf '  %s · %d MB\n' "$nome" $mb
    prima=$(sudo du -sk /Library/Updates 2>/dev/null | cut -f1); prima=${prima:-0}
    sudo softwareupdate -i "$nome" --verbose >"$log" 2>&1 & pid=$!; t0=$(date +%s); i=0
    while kill -0 $pid 2>/dev/null; do  # percentuale dal programma, se la scrive; se no dai MB già scaricati
      pc=$(tr '\r' '\n' <"$log" | grep -oE '[0-9]{1,3}(\.[0-9]+)?%' | tail -1 | cut -d. -f1 | tr -d %)
      if [ -z "$pc" ] && [ $mb -gt 0 ]; then
        ora=$(sudo -n du -sk /Library/Updates 2>/dev/null | cut -f1)
        [ -n "$ora" ] && pc=$(( (ora - prima) * 100 / (mb * 1024) ))
      fi
      fase='scarico'; grep -qi 'install' "$log" && fase='installo'
      s=$(( $(date +%s) - t0 )); resto=''
      if [ -n "$pc" ] && [ "$pc" -gt 0 ]; then
        [ "$pc" -gt 100 ] && pc=100
        n=$(( pc * 16 / 100 )); barra="$(printf '%*s' $n '' | tr ' ' '━')$(printf '%*s' $((16 - n)) '' | tr ' ' '─')"  # sta in 80 colonne
        [ "$pc" -ge 3 ] && [ $s -ge 5 ] && [ "$pc" -lt 100 ] && resto=" · ~$(( (s * (100 - pc) / pc + 59) / 60 )) min"
        printf "\r  ${A}%s${Z} %s gli strumenti di Apple  ${A}%s${Z} %3d%%${F}  %s%s${Z}\033[K" \
          "${giro[i++%6]}" "$fase" "$barra" "$pc" "$(tempo $t0)" "$resto"
      else
        printf "\r  ${A}%s${Z} %s gli strumenti di Apple${F}  %s (di solito 5-15 min)${Z}\033[K" \
          "${giro[i++%6]}" "$fase" "$(tempo $t0)"
      fi
      sleep 0.5
    done
    wait $pid; esito=$?
    printf '\r\033[K'
  else
    esito=1
  fi
  if [ $esito -eq 0 ] && xcode-select -p >/dev/null 2>&1; then
    printf '  ✓ strumenti di Apple installati in %s\n' "$(tempo $t0)"
  else
    tail -3 "$log" 2>/dev/null | sed 's/^/  /'
    xcode-select --install 2>/dev/null
    printf '→ Non ci sono riuscito dal Terminale: si è aperta la finestra di Apple. Premi «Installa», aspetta la fine,\n'
    printf '  poi incolla di nuovo la stessa riga.\n'
    exit 1
  fi
fi
if ! command -v python3 >/dev/null || ! command -v git >/dev/null; then  # git: anche Linux (commit firmato, poi crew.py)
  printf '❌ manca python3 o git: installali (es. sudo apt install python3 git) e rilancia la stessa riga.\n'
  exit 1
fi
# A122: crew.py solo con la firma della squadra anche alla prima installazione (come crew.py scarica_firmato): chi
# entrasse nell'account GitHub non manda codice ai PC nuovi senza la chiave. File e firma dallo stesso commit.
# Verifica minisign (Ed25519 su BLAKE2b-512) in Python puro, chiavi qui: mai il codice appena scaricato a fidarsi di sé.
# La prova da zero cambia CREW_RAW/CREW_GIT con le copie locali (CREW_GIT vuoto = main).
CREW_RAW=https://raw.githubusercontent.com/Radwtsm/claude-crew
CREW_GIT=https://github.com/Radwtsm/claude-crew.git
read -r -d '' FIRMA_PY <<'PY'
import base64, hashlib, sys
CHIAVI = ["dW50cnVzdGVkIGNvbW1lbnQ6IG1pbmlzaWduIHB1YmxpYyBrZXk6IDA5RDYyOERGMTU1RTM0OUMKUldTY05GNFYzeWpXQ2FJQU1TT1gwQ2xvV0w3ZVNzUVlYVEZLQnZMMHNIRWtFQ3dGelV4Mm84Mk0K",
          "dW50cnVzdGVkIGNvbW1lbnQ6IG1pbmlzaWduIHB1YmxpYyBrZXk6IEU4MjFERURBRDdGQTQ5M0EKUldRNlNmclgydDRoNkFnVmcrRkFUa1AwMDQwSmJFMUtpb2NOR21pWndMYzNjSnZiTlg4SlA3eDYK"]
q, l = 2**255 - 19, 2**252 + 27742317777372353535851937790883648493
d, radice = -121665 * pow(121666, q - 2, q) % q, pow(2, (q - 1) // 4, q)
def piu(P, Q):
    (x1, y1, z1, t1), (x2, y2, z2, t2) = P, Q
    a, b = (y1 - x1) * (y2 - x2) % q, (y1 + x1) * (y2 + x2) % q
    c, e = 2 * t1 * t2 * d % q, 2 * z1 * z2 % q
    return ((b - a) * (e - c) % q, (e + c) * (b + a) % q, (e - c) * (e + c) % q, (b - a) * (b + a) % q)
def per(P, n):
    R = (0, 1, 1, 0)
    while n:
        R, P, n = (piu(R, P) if n & 1 else R), piu(P, P), n >> 1
    return R
def punto(b):
    y = int.from_bytes(b, "little"); s, y = y >> 255, y & ((1 << 255) - 1)
    x2 = (y * y - 1) * pow(d * y * y + 1, q - 2, q) % q
    x = pow(x2, (q + 3) // 8, q); x = x if (x * x - x2) % q == 0 else x * radice % q
    if y >= q or (x * x - x2) % q or (x == 0 and s):
        return None
    x = q - x if x & 1 != s else x
    return (x, y, 1, x * y % q)
def ed25519_ok(pk, firma, msg):
    A, R, s = punto(pk), punto(firma[:32]), int.from_bytes(firma[32:], "little")
    if A is None or R is None or s >= l:
        return False
    G = punto((4 * pow(5, q - 2, q) % q).to_bytes(32, "little"))
    h = int.from_bytes(hashlib.sha512(firma[:32] + pk + msg).digest(), "little") % l
    P, Q = per(G, s), piu(R, per(A, h))
    return (P[0] * Q[2] - Q[0] * P[2]) % q == 0 and (P[1] * Q[2] - Q[1] * P[2]) % q == 0
def ok(chiave, firma, dati):
    try:
        pk = base64.b64decode(base64.b64decode(chiave).decode().splitlines()[1])
        s = base64.b64decode(base64.b64decode(firma).decode().splitlines()[1])
    except (ValueError, IndexError, UnicodeDecodeError):
        return False
    if len(pk) != 42 or len(s) != 74 or pk[:2] != b"Ed" or s[:2] not in (b"ED", b"Ed") or s[2:10] != pk[2:10]:
        return False
    return ed25519_ok(pk[10:], s[10:], hashlib.blake2b(dati).digest() if s[:2] == b"ED" else dati)
dati, firma = open(sys.argv[1], "rb").read(), open(sys.argv[2]).read().strip()
sys.exit(0 if any(ok(c, firma, dati) for c in CHIAVI) else 1)
PY
scarica_firmato() {  # $1 = file di claude-crew, $2 = dove: solo se la firma vale
  local rif=main t
  [ -n "$CREW_GIT" ] && t=$(git ls-remote -- "$CREW_GIT" refs/heads/main 2>/dev/null | cut -f1)
  printf '%s' "${t:-}" | grep -Eq '^[0-9a-f]{40}$' && rif=$t
  curl -fsSL "$CREW_RAW/$rif/$1" -o "$2.tmp" && curl -fsSL "$CREW_RAW/$rif/$1.sig" -o "$2.sig.tmp" || {
    rm -f "$2.tmp" "$2.sig.tmp"; printf '❌ non riesco a scaricare %s: controlla internet e rilancia la stessa riga.\n' "$1"; return 1; }
  if ! python3 -c "$FIRMA_PY" "$2.tmp" "$2.sig.tmp"; then
    rm -f "$2.tmp" "$2.sig.tmp"; printf '❌ %s non ha la firma della squadra: non lo uso. Avvisa chi ti ha invitato.\n' "$1"; return 1
  fi
  rm -f "$2.sig.tmp"; mv "$2.tmp" "$2"
}
mkdir -p "$HOME/.crew"
scarica_firmato crew.py "$HOME/.crew/crew.py" || exit 1
[ -n "${STUDIO:-}" ] && set -- "$@" "--studio=$STUDIO"  # INVITO arriva a crew.py per ambiente, che lo toglie subito
term=/dev/$(ps -o tty= -p $$ 2>/dev/null | tr -d ' ')  # il terminale vero: da /dev/tty Claude Code (Bun) non legge su macOS
# aprirlo davvero: senza terminale (lanciata da un programma) /dev/tty è leggibile ma non si apre
( : <"$term" ) 2>/dev/null || term=/dev/tty
if ( : <"$term" ) 2>/dev/null; then
  exec python3 "$HOME/.crew/crew.py" guida "$@" <"$term"
fi
exec python3 "$HOME/.crew/crew.py" guida "$@"
