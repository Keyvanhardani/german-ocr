# German-OCR API - PHP Demo-Skripte

Funktionierende Beispiele fuer die Integration der German-OCR API in PHP-Anwendungen.

## API-Architektur: Async Job-Based

Die German-OCR API arbeitet **asynchron** mit Job-IDs:

```
1. POST /v1/analyze  →  202 Accepted + job_id (sofort!)
2. GET /v1/jobs/{id} →  Status polling bis completed
3. Ergebnis abrufen  →  result + Metadaten
```

**Warum async?** OCR-Verarbeitung kann je nach Dokument 2-30 Sekunden dauern. Mit dem Job-System:
- Keine HTTP-Timeouts
- Keine blockierten Verbindungen
- Fire-and-Forget moeglich
- Batch-Verarbeitung einfacher

---

## Voraussetzungen

- PHP 7.4+ installiert
- cURL-Extension aktiviert
- Composer (fuer Guzzle-Demo)

## Installation

### Native cURL (simple_curl.php)

Keine Installation noetig - cURL ist standardmaessig in PHP enthalten.

```bash
# cURL-Extension pruefen
php -m | grep curl
```

### Guzzle HTTP Client (guzzle_demo.php)

```bash
cd sdk/demos/php
composer require guzzlehttp/guzzle
```

---

## Verfuegbare Demos

### 1. Simple cURL Demo

**Datei:** `simple_curl.php`

```bash
# Standard-Analyse (wartet auf Ergebnis)
php simple_curl.php rechnung.pdf

# Mit Prompt
php simple_curl.php rechnung.jpg "Extrahiere Rechnungsnummer"

# Mit spezifischem Modell
php simple_curl.php rechnung.pdf "" german-ocr-pro

# Fire-and-Forget (nur Job senden, nicht warten)
php simple_curl.php rechnung.pdf --no-wait

# Job-Status abfragen
php simple_curl.php --status abc-123-def-456
```

**Beispiel-Ausgabe:**
```
German-OCR API - Dokumentenanalyse
==================================================
Datei:  rechnung.pdf
Modell: German-OCR Ultra (0,05 EUR/Seite)
--------------------------------------------------

1. Sende Dokument...
   Job-ID: 535f7dde-8578-4236-95a6-1f110da1e5d1
   Gesendet in: 245ms

2. Warte auf Verarbeitung...
   Status: completed (Versuch 3, 6s)

3. Ergebnis:
==================================================
RECHNUNG Nr. 2026-001
Datum: 07.01.2026
Kunde: Max Mustermann GmbH
...
==================================================

Statistiken:
   Modell:            German-OCR Ultra
   Gesamtzeit:        6234ms
   Verarbeitungszeit: 2101ms
   Tokens (in/out):   2623 / 91
   Preis:             0,05 EUR
   Verarbeitung:      EU (Frankfurt)
   DSGVO:             Ja

Fertig!
```

---

### 2. Guzzle Demo (mit Batch-Support)

**Datei:** `guzzle_demo.php`

```bash
# Einzelne Datei
php guzzle_demo.php rechnung.pdf

# Batch-Verarbeitung (mehrere Dateien parallel!)
php guzzle_demo.php doc1.pdf doc2.pdf doc3.pdf

# Fire-and-Forget
php guzzle_demo.php rechnung.pdf --no-wait

# Status abfragen
php guzzle_demo.php --status abc-123-def-456
```

**Batch-Beispiel:**
```
German-OCR API - Batch-Verarbeitung (Guzzle Async)
============================================================
Dokumente: 3
Modell:    German-OCR Ultra
------------------------------------------------------------

1. Sende alle Dokumente...
   [0] rechnung1.pdf -> Job: abc-123
   [1] rechnung2.pdf -> Job: def-456
   [2] rechnung3.jpg -> Job: ghi-789

   Alle Jobs gesendet in: 892ms

2. Warte auf Verarbeitung...
   Runde 3: 3 fertig, 0 ausstehend (8s)

3. Ergebnisse:
============================================================
[0] rechnung1.pdf
       Text: RECHNUNG Nr. 2026-001...
[1] rechnung2.pdf
       Text: Lieferschein vom 07.01.2026...
[2] rechnung3.jpg
       Text: Angebot Nr. 2026-567...
============================================================

Statistiken:
   Gesamt:         3 Dokumente
   Erfolgreich:    3
   Fehlgeschlagen: 0
   Gesamtzeit:     8234ms
   Durchsatz:      0.36 Dok/s
```

---

## API-Konfiguration

### Umgebungsvariablen (empfohlen)

```bash
export GERMAN_OCR_API_KEY="gocr_xxx"
export GERMAN_OCR_API_SECRET="your_secret"
```

Die Skripte laden Credentials automatisch aus Umgebungsvariablen:

```php
define('API_KEY', getenv('GERMAN_OCR_API_KEY') ?: 'YOUR_API_KEY');
define('API_SECRET', getenv('GERMAN_OCR_API_SECRET') ?: 'YOUR_API_SECRET');
```

---

## Modelle

| Modell | Beschreibung | Preis | Empfehlung |
|--------|--------------|-------|------------|
| `german-ocr-ultra` | Maximale Praezision | 0,05 EUR/Seite | **Standard** |
| `german-ocr-pro` | Schnell und zuverlaessig | 0,05 EUR/Seite | Hoher Durchsatz |
| `german-ocr` | Lokal, DSGVO-optimal | 0,02 EUR/Seite | Sensible Daten |

---

## API Flow im Detail

### Schritt 1: Job senden

```php
$response = $client->post('/v1/analyze', [
    'headers' => ['Authorization' => "Bearer $key:$secret"],
    'multipart' => [
        ['name' => 'file', 'contents' => fopen($path, 'r'), 'filename' => $name],
        ['name' => 'model', 'contents' => 'german-ocr-ultra'],
    ],
]);

// Response: 202 Accepted
// {"job_id": "abc-123", "status": "pending", "model": "German-OCR Ultra"}
```

### Schritt 2: Status pollen

```php
do {
    $status = $client->get("/v1/jobs/$jobId", [
        'headers' => ['Authorization' => "Bearer $key:$secret"],
    ]);

    $data = json_decode($status->getBody(), true);

    if ($data['status'] === 'completed') {
        return $data['result'];  // OCR-Text
    }

    if ($data['status'] === 'failed') {
        throw new Exception($data['error']);
    }

    sleep(2);  // 2 Sekunden warten

} while ($data['status'] === 'pending' || $data['status'] === 'processing');
```

### Response bei Fertigstellung

```json
{
    "job_id": "abc-123",
    "status": "completed",
    "result": "RECHNUNG Nr. 2026-001\nDatum: 07.01.2026...",
    "model": "German-OCR Ultra",
    "tokens": {"input": 2623, "output": 91},
    "processing_time_ms": 2101,
    "price_display": "0,05 EUR",
    "privacy": {
        "processing_location": "EU (Frankfurt)",
        "gdpr_compliant": true,
        "local_processing": false
    }
}
```

---

## Integration in Frameworks

### Laravel Service

```php
<?php
// app/Services/GermanOcrService.php
namespace App\Services;

use GuzzleHttp\Client;

class GermanOcrService
{
    private Client $client;
    private string $authToken;

    public function __construct()
    {
        $key = config('services.german_ocr.key');
        $secret = config('services.german_ocr.secret');

        $this->authToken = "$key:$secret";
        $this->client = new Client([
            'base_uri' => 'https://api.german-ocr.de',
            'timeout' => 30,
        ]);
    }

    public function analyze(string $filePath, ?string $prompt = null): array
    {
        // 1. Job senden
        $jobId = $this->submitJob($filePath, $prompt);

        // 2. Auf Ergebnis warten
        return $this->pollUntilComplete($jobId);
    }

    private function submitJob(string $filePath, ?string $prompt): string
    {
        $multipart = [
            ['name' => 'file', 'contents' => fopen($filePath, 'r')],
            ['name' => 'model', 'contents' => 'german-ocr-ultra'],
        ];

        if ($prompt) {
            $multipart[] = ['name' => 'prompt', 'contents' => $prompt];
        }

        $response = $this->client->post('/v1/analyze', [
            'headers' => ['Authorization' => "Bearer {$this->authToken}"],
            'multipart' => $multipart,
        ]);

        $data = json_decode($response->getBody(), true);
        return $data['job_id'];
    }

    private function pollUntilComplete(string $jobId, int $maxAttempts = 60): array
    {
        for ($i = 0; $i < $maxAttempts; $i++) {
            $response = $this->client->get("/v1/jobs/$jobId", [
                'headers' => ['Authorization' => "Bearer {$this->authToken}"],
            ]);

            $data = json_decode($response->getBody(), true);

            if ($data['status'] === 'completed') {
                return $data;
            }

            if ($data['status'] === 'failed') {
                throw new \Exception($data['error'] ?? 'Job fehlgeschlagen');
            }

            sleep(2);
        }

        throw new \Exception('Timeout: Job nicht rechtzeitig abgeschlossen');
    }
}
```

---

## Timeout-Konfiguration

Die SDKs verwenden folgende Timeouts:

| Einstellung | Wert | Beschreibung |
|-------------|------|--------------|
| `TIMEOUT_SUBMIT` | 30s | Fuer Job-Submission |
| `TIMEOUT_POLL` | 10s | Fuer Status-Abfragen |
| `MAX_POLL_ATTEMPTS` | 120 | Max. Poll-Versuche |
| `POLL_INTERVAL` | 2s | Zeit zwischen Polls |

**Maximale Wartezeit:** 120 × 2s = **4 Minuten**

---

## Troubleshooting

### "API-Fehler (202): ..."

Das ist **kein Fehler**! 202 ist der korrekte Response-Code. Die alten Skripte erwarteten faelschlicherweise 200.

### Job bleibt auf "pending"

- Pruefe API-Auslastung
- Erhoehe `MAX_POLL_ATTEMPTS`
- Nutze `--no-wait` und pruefe spaeter

### Timeout bei grossen Dateien

```php
define('TIMEOUT_SUBMIT', 60);      // Erhoehen
define('MAX_POLL_ATTEMPTS', 180);  // Laenger warten
```

---

## Support

- Dokumentation: https://german-ocr.de/docs
- Support: support@keyvan.ai
- GitHub: https://github.com/Keyvanhardani/German-OCR-Enterprise-Platform

---

**Entwickelt von Keyvan.ai** | German-OCR Enterprise Platform
