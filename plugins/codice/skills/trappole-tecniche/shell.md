# Trappole: Shell, ssh e hook

Letto da `SKILL.md` prima di: script bash/zsh/Git Bash, comandi ssh, hook, heredoc, file di config scritti da script.

- `while read …; do ssh …; done < lista`: ssh si mangia la lista → `ssh -n` o `read <&3 … 3< lista`.
- `ssh -n host 'bash -s' <<EOF` non esegue niente (-n = stdin da /dev/null): heredoc senza `-n`.
- `pgrep -f`/`pkill -f nome` dentro `ssh host '…'` trovano la propria shell: uccidi per pid, avvio e stop in
  chiamate ssh separate, ogni attesa con un timeout.
- Job lunghi (più di qualche minuto) sotto `nohup` o un servizio sul server, mai legati alla shell della sessione.
- zsh non spezza `$VAR` in parole: usa `| xargs` o `${=VAR}`.
- zsh su Mac: `log` è un builtin → `/usr/bin/log`; un risultato vuoto è sospetto finché una query nota non risponde.
- Bash con `set -e`: un passo che deve fermare lo script non sta in una lista `a && b && c` (lì un errore è ignorato):
  usa `if …; then …; fi`.
- Hook shell: mai finire con `[ cond ] && …` (cond falsa = exit 1 = blocca tutto in silenzio); `if …; fi` + `exit 0`.
- `… | tr -c 'A-Za-z0-9' '-'` su un nome: passalo senza newline (`printf "%s"`), o diventa un `-` finale.
- Git Bash su Windows: un percorso `C:\…` scritto dentro `sed 's#…#…#'` o dentro una stringa Python/JS si rovina
  in silenzio: `\b`, `\c`, `\t`, `\n` diventano caratteri di controllo (`cartella\blender` → `cartella⌫lender`) e il
  file sembra a posto finché non lo apri. Usa barre `/`, stringhe raw (`r"C:\…"`) o uno strumento di modifica dei
  file invece della shell; dopo, controlla con `grep -c $'\x08'` o `cat -A` che non ci siano caratteri strani.
- Script Python in `<<'EOF'` che contiene un altro heredoc → la prima riga `EOF` del testo chiude quello esterno e
  la shell esegue il resto → delimitatore diverso fuori (`<<'PYEOF'`) o scrivi prima un file.
- Regole nuove che non arrivano mai su una macchina → il blocco di config si aggiunge "solo se manca"
  (`grep -q BEGIN || cat >>`) → riscrivi il blocco tra i marcatori a ogni esecuzione.
