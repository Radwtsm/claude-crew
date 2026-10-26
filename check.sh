#!/bin/sh
# Controllo anti-fuga per un repo PUBBLICO: blocca IP, URL, email e segreti (README "Cosa NON ci va").
# Parole private in più (host, nomi): una regex per riga in ~/.config/claude-crew/parole-vietate, mai nel repo.
# Uso: sh check.sh  (lo lanciano il pre-commit in .githooks/ e la CI)
cd "$(dirname "$0")" || exit 1
p='([0-9]{1,3}\.){3}[0-9]{1,3}|https?://|[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+\.[A-Za-z.]{2,}'
p="$p|-----BEGIN|(api[_-]?key|token|password|secret)[\"' ]*[:=][\"' ]*[A-Za-z0-9/+_-]{8,}"
ok="https://(github\.com|raw\.githubusercontent\.com)/(\{\{REPO\}\}|Radwtsm/claude-crew|\{REPO\})"
files=$(git ls-files 2>/dev/null; git ls-files -o --exclude-standard 2>/dev/null)
[ -n "$files" ] || files=$(find . -type f -not -path './.git/*' -not -path './dist/*')
hits=$(echo "$files" | grep -vE '^(\./)?(\.github/workflows/|check\.sh$)' | xargs grep -nIE "$p" 2>/dev/null | grep -vE "$ok")
deny="$HOME/.config/claude-crew/parole-vietate"
if [ -s "$deny" ]; then
  more=$(echo "$files" | xargs grep -nIiE -f "$deny" 2>/dev/null)
  hits=$(printf '%s\n%s' "$hits" "$more" | sed '/^$/d')
fi
if [ -n "$hits" ]; then
  echo "$hits"
  echo "check.sh: possibile dato privato/segreto qui sopra, togli prima del commit" >&2
  exit 1
fi
# Contesto snello: i file letti a ogni sessione non ricrescono (limiti in byte in limiti-contesto.txt)
fuori=$(grep -vE '^(#|$)' limiti-contesto.txt | while read -r max f; do
  for x in $f; do
    if [ -f "$x" ]; then
      n=$(wc -c < "$x" | tr -d ' ')
      if [ "$n" -gt "$max" ]; then echo "$x: $n byte > $max"; fi
    fi
  done
done)
if [ -n "$fuori" ]; then
  echo "$fuori"
  echo "check.sh: file troppo lunghi; i dettagli in un file per tema letto quando serve (organizza-claude)" >&2
  exit 1
fi
exit 0
