#!/bin/bash
# La riga unica (Mac, Linux): scarica la guida `pleyades-cli` (Pleyades tools) e la lancia. Si può rilanciare: salta ciò che c'è già.
#   curl -fsSL https://raw.githubusercontent.com/Radwtsm/claude-crew/main/installa.sh | bash
# Con un progetto a cui sei stato invitato:
#   curl -fsSL https://raw.githubusercontent.com/Radwtsm/claude-crew/main/installa.sh | bash -s -- PROPRIETARIO/REPO
# Qui solo ciò che serve a far partire Python; tutto il resto (Claude Code, GitHub, plugin, progetti, Nextcloud)
# lo fa crew.py, uguale su Mac, Linux e Windows.
set -u
tempo() { local s=$(( $(date +%s) - $1 )); [ $s -ge 60 ] && printf '%d:%02d' $((s/60)) $((s%60)) || printf '%d s' $s; }
giro=(✦ ✧ ⋆ · ⋆ ✧)  # la stella che pulsa (Pleyades tools); array: il bash 3.2 del Mac taglia male i caratteri UTF-8
A='\033[38;5;153m'; F='\033[38;5;61m'; Z='\033[0m'  # azzurro stella, blu fioco (marchio Pleyades)
if [ "$(uname)" = Darwin ] && ! xcode-select -p >/dev/null 2>&1; then
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
        n=$(( pc / 5 )); barra="$(printf '%*s' $n '' | tr ' ' '━')$(printf '%*s' $((20 - n)) '' | tr ' ' '─')"
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
if ! command -v python3 >/dev/null; then
  printf '❌ manca python3: installalo (es. sudo apt install python3 git) e rilancia la stessa riga.\n'
  exit 1
fi
mkdir -p "$HOME/.crew"
if ! curl -fsSL https://raw.githubusercontent.com/Radwtsm/claude-crew/main/crew.py -o "$HOME/.crew/crew.py.tmp"; then
  printf '❌ non riesco a scaricare la guida: controlla internet e rilancia la stessa riga.\n'
  exit 1
fi
mv "$HOME/.crew/crew.py.tmp" "$HOME/.crew/crew.py"
if [ -r /dev/tty ]; then
  exec python3 "$HOME/.crew/crew.py" guida "$@" </dev/tty
fi
exec python3 "$HOME/.crew/crew.py" guida "$@"
