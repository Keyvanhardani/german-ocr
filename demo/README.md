# German-OCR 3.1 — Live Form Filler Demo

Interaktive Browser-Demo: deutsche Rechnung hochladen → strukturiertes JSON
in Sekunden. Läuft komplett lokal über Ollama, kein Cloud-Aufruf.

## Voraussetzungen

```bash
ollama pull Keyvan/german-ocr-3.1
# CORS für Browser-Zugriff freigeben (PowerShell/Bash):
export OLLAMA_ORIGINS=*    # bash
# bzw. unter Windows:
[Environment]::SetEnvironmentVariable('OLLAMA_ORIGINS','*','User')
```

## Starten

1. `index.html` im Browser öffnen (Doppelklick oder `file://`)
2. **Demo-Bild laden** klicken (oder eigene Rechnung droppen)
3. **Extrahieren starten** — Formular füllt sich live
4. Live-Latenz wird neben dem Status angezeigt

Backend ist hardcodiert auf `http://localhost:11434` mit Modell
`Keyvan/german-ocr-3.1`. Falls Ollama auf anderem Port läuft, in
`index.html` die Zeile `OLLAMA_URL` anpassen.

## Files

| Datei | Zweck |
|---|---|
| `index.html` | Single-Page Demo (kein Build-Step) |
| `demo_invoice.png` | Beispiel-Rechnung zum Testen |
| `thumbnail_linkedin.png` | Video-Miniaturbild (1280×720) |

## Was du im Demo siehst

- Links: leeres Eingabe-Formular (Rechnungsnr, Sender, IBAN, Beträge, Positionen)
- Rechts: Drag-Drop-Zone für Bild-Upload + Live-Status + Roh-JSON
- Felder füllen sich Zeichen-für-Zeichen mit Type-On-Animation
- Tabellenzeilen werden grün markiert wenn extrahiert

## Companion-Modell

Für reine Text-Aufgaben (Übersetzen, Zusammenfassen, Chat, formelle Briefe):
[`Keyvan/german-text-3.1`](https://ollama.com/Keyvan/german-text-3.1)

## Hinweis

Latenzen variieren stark je nach Hardware:
- GPU (RTX-Class): wenige Sekunden
- CPU only: 10–30 Sekunden je nach Bild + Prozessor

Apache 2.0 — kommerzielle Nutzung mit Attribution erlaubt.
