# German-OCR API - Node.js Demo-Skripte

Funktionierende Beispiele für die Integration der German-OCR API in Node.js-Anwendungen.

## Voraussetzungen

- Node.js 14+ installiert
- npm oder yarn

## Installation

```bash
# Dependencies installieren
npm install node-fetch form-data

# Oder mit yarn
yarn add node-fetch form-data
```

## Verfügbare Demos

### 1. Simple Demo - Einzelner Request

Zeigt den grundlegenden Upload eines einzelnen Dokuments.

**Datei:** `simple.js`

```bash
# Einfacher Upload
node simple.js rechnung.jpg

# Mit Prompt für strukturierte Ausgabe
node simple.js rechnung.pdf "Extrahiere Rechnungsnummer und Datum"

# Mit spezifischem Provider
node simple.js rechnung.jpg "" cloud
```

**Features:**
- Datei-Upload mit FormData
- Antwortzeit-Messung
- Fehlerbehandlung
- Formatierte JSON-Ausgabe
- Deutsche Kommandozeilen-Ausgaben

**Beispiel-Ausgabe:**
```
📤 Sende Dokument an German-OCR API...
   Datei: rechnung.jpg
   Provider: cloud_fast

✅ Erfolgreich verarbeitet!
⏱️  Antwortzeit: 1234ms

📄 Ergebnis:
────────────────────────────────────────────────────────
{
  "text": "Rechnung\nRechnungsnummer: 2025-001234...",
  "provider_used": "cloud",
  "processing_time_ms": 1200
}
────────────────────────────────────────────────────────
```

---

### 2. Batch Demo - Parallele Verarbeitung

Verarbeitet mehrere Dokumente gleichzeitig mit `Promise.all`.

**Datei:** `batch.js`

```bash
# Mehrere Dateien parallel
node batch.js rechnung1.jpg rechnung2.pdf rechnung3.jpg

# Mit Glob-Pattern (Shell-Expansion)
node batch.js docs/*.jpg
```

**Features:**
- Parallele Requests für maximale Geschwindigkeit
- Pro-Datei Statistiken
- Gesamtzeit und Durchsatz-Berechnung
- Fehlertoleranz (ein fehlgeschlagener Request bricht nicht ab)
- Detaillierte Ausgabe aller Ergebnisse

**Beispiel-Ausgabe:**
```
🚀 Starte Batch-Verarbeitung...
   Dokumente: 3
   Provider: cloud_fast (optimiert für Geschwindigkeit)

📊 Batch-Ergebnisse:
══════════════════════════════════════════════════════════════════
✅ [1] rechnung1.jpg (1234ms)
   📄 Text: Rechnung Nr. 2025-001234...
✅ [2] rechnung2.pdf (1456ms)
   📄 Text: Lieferschein vom 22.12.2025...
✅ [3] rechnung3.jpg (1123ms)
   📄 Text: Angebot Nr. 2025-567...
══════════════════════════════════════════════════════════════════

📈 Statistiken:
   Gesamt:          3 Dokumente
   Erfolgreich:     3 ✅
   Fehlgeschlagen:  0 ❌
   Gesamtzeit:      1500ms
   Ø Pro Dokument:  1271ms
   Zeichen total:   1234
   Durchsatz:       2.00 Dok/s
```

---

## API-Konfiguration

Die Zugangsdaten sind bereits in den Skripten hinterlegt:

```javascript
const API_CONFIG = {
  endpoint: 'https://api.german-ocr.de/v1/analyze',
  apiKey: 'gocr_079a85fb',
  apiSecret: '7c3fafb5efedcad69ba991ca1e96bce7f4929d769b4f1349fa0a28e98f4a462c'
};
```

**Für produktiven Einsatz:** Credentials aus Umgebungsvariablen laden:

```javascript
const API_CONFIG = {
  endpoint: process.env.GERMAN_OCR_ENDPOINT || 'https://api.german-ocr.de/v1/analyze',
  apiKey: process.env.GERMAN_OCR_API_KEY,
  apiSecret: process.env.GERMAN_OCR_API_SECRET
};
```

---

## Provider-Optionen

| Modell | Beschreibung | Geschwindigkeit | Qualität |
|--------|--------------|-----------------|----------|
| `german-ocr-ultra` | Maximale Präzision für komplexe Dokumente | ⚡⚡ | ⭐⭐⭐ |
| `german-ocr-pro` | Schnell und zuverlässig | ⚡⚡⚡ | ⭐⭐ |
| `german-ocr` | Lokal auf eigenen Servern | ⚡ | ⭐⭐ |

---

## Integration in eigene Anwendungen

### Als Modul verwenden

```javascript
const { analyzeDocument } = require('./simple.js');

async function myApp() {
  try {
    const result = await analyzeDocument(
      'dokument.pdf',
      'Extrahiere alle Rechnungspositionen',
      'cloud'
    );

    console.log('OCR-Text:', result.text);
    console.log('Provider:', result.provider_used);
  } catch (error) {
    console.error('Fehler:', error.message);
  }
}
```

### Express.js Integration

```javascript
const express = require('express');
const multer = require('multer');
const { analyzeDocument } = require('./simple.js');

const app = express();
const upload = multer({ dest: 'uploads/' });

app.post('/ocr', upload.single('file'), async (req, res) => {
  try {
    const result = await analyzeDocument(req.file.path);
    res.json(result);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

app.listen(3000);
```

---

## Fehlerbehandlung

Beide Skripte enthalten umfassende Fehlerbehandlung:

- Datei nicht gefunden
- API-Fehler (4xx/5xx)
- Netzwerk-Timeouts
- Ungültiges JSON
- Auth-Fehler

**Beispiel:**
```
❌ Fehler bei der Verarbeitung:
   API-Fehler (401): Invalid API credentials
   Antwortzeit: 234ms
```

---

## Performance-Tipps

1. **Batch-Verarbeitung:** Für mehrere Dateien immer `batch.js` verwenden
2. **Provider-Wahl:** `cloud_fast` für maximale Geschwindigkeit
3. **Parallele Requests:** Maximal 10-20 parallele Requests empfohlen
4. **Timeout:** Standard 60s, bei großen PDFs ggf. erhöhen

---

## Troubleshooting

### "Cannot find module 'node-fetch'"
```bash
npm install node-fetch form-data
```

### "ENOENT: no such file or directory"
Prüfe ob Dateipfad korrekt ist (absolute oder relative Pfade möglich).

### "API-Fehler (401)"
API-Credentials prüfen - Key und Secret müssen korrekt sein.

### "Timeout nach 60000ms"
Bei großen PDFs Timeout erhöhen:
```javascript
const response = await fetch(API_CONFIG.endpoint, {
  // ... andere Optionen
  timeout: 120000 // 2 Minuten
});
```

---

## Support

- Dokumentation: https://german-ocr.de/docs
- Support: support@keyvan.ai
- Issues: https://github.com/Keyvanhardani/German-OCR-Enterprise-Platform/issues

---

**Entwickelt von Keyvan.ai** | Powered by German-OCR
