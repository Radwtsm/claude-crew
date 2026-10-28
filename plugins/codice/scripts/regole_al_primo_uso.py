#!/usr/bin/env python3
"""Hook PostToolUse del plugin codice: le regole del codice (codice.md + architettura.md, ~6 KB) entrano nel contesto
solo la prima volta che Claude modifica un file di codice in una sessione, non a ogni avvio (token = priorità: una
sessione su documenti o regole non le paga). Una volta per sessione; `--se-manca-python3` = seconda voce per Windows.
"""
import json, os, subprocess, sys, tempfile

CODICE = {".py", ".sh", ".js", ".mjs", ".cjs", ".ts", ".tsx", ".jsx", ".swift", ".go", ".rs", ".c", ".h", ".cpp",
          ".hpp", ".cs", ".java", ".kt", ".rb", ".php", ".dart", ".ps1", ".bat", ".sql", ".lua", ".jsx", ".jsxinc",
          ".html", ".css", ".scss", ".vue", ".svelte", ".yml", ".yaml", ".toml", ".gradle", ".dockerfile"}
NOMI = {"Dockerfile", "Makefile", "docker-compose.yml", "package.json"}
QUI = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def main():
    if "--se-manca-python3" in sys.argv:
        try:
            if subprocess.run(["python3", "-c", "pass"], capture_output=True, timeout=10).returncode == 0:
                return
        except (OSError, subprocess.SubprocessError):
            pass
    try:
        dati = json.load(sys.stdin)
    except ValueError:
        return
    path = (dati.get("tool_input") or {}).get("file_path") or (dati.get("tool_input") or {}).get("notebook_path") or ""
    nome = os.path.basename(path)
    if os.path.splitext(nome)[1].lower() not in CODICE and nome not in NOMI:
        return
    segno = os.path.join(tempfile.gettempdir(), f"crew-codice-{dati.get('session_id', 'x')}")
    if os.path.exists(segno):
        return
    open(segno, "w").close()
    testo = "\n\n".join(open(os.path.join(QUI, f), encoding="utf-8").read() for f in ("codice.md", "architettura.md"))
    print(json.dumps({"hookSpecificOutput": {"hookEventName": "PostToolUse", "additionalContext":
                      "Regole del codice della crew (caricate al primo file di codice di questa sessione):\n\n" + testo}},
                     ensure_ascii=False))


if __name__ == "__main__":
    main()
