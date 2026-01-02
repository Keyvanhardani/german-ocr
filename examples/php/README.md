# German-OCR API - PHP Demo-Skripte

Funktionierende Beispiele für die Integration der German-OCR API in PHP-Anwendungen.

## Voraussetzungen

- PHP 7.4+ installiert
- cURL-Extension aktiviert
- Composer (für Guzzle-Demo)

## Installation

### Native cURL (simple_curl.php)

Keine Installation nötig - cURL ist standardmäßig in PHP enthalten.

```bash
# cURL-Extension prüfen
php -m | grep curl
```

Falls nicht vorhanden:
```bash
# Ubuntu/Debian
sudo apt-get install php-curl

# Windows (in php.ini aktivieren)
extension=curl
```

### Guzzle HTTP Client (guzzle_demo.php)

```bash
# Composer installieren (falls nicht vorhanden)
# https://getcomposer.org/download/

# Dependencies installieren
composer install

# Oder Guzzle manuell hinzufügen
composer require guzzlehttp/guzzle
```

---

## Verfügbare Demos

### 1. Simple cURL Demo - Natives PHP

Upload mit nativem PHP cURL ohne externe Dependencies.

**Datei:** `simple_curl.php`

```bash
# Einfacher Upload
php simple_curl.php rechnung.jpg

# Mit Prompt für strukturierte Ausgabe
php simple_curl.php rechnung.pdf "Extrahiere Rechnungsnummer und Datum"

# Mit spezifischem Modell
php simple_curl.php rechnung.jpg "" german-ocr-ultra
```

**Features:**
- Native cURL-Implementierung
- Keine externen Dependencies
- CURLFile für sichere Datei-Uploads
- Timeout-Handling (60 Sekunden)
- Antwortzeit-Messung
- SSL-Verifizierung
- Umfassende Fehlerbehandlung

**Beispiel-Ausgabe:**
```
📤 Sende Dokument an German-OCR API...
   Datei: rechnung.jpg
   Modell: german-ocr-pro

✅ Erfolgreich verarbeitet!
⏱️  Antwortzeit: 1234ms

📄 Ergebnis:
────────────────────────────────────────────────────────
{
    "text": "Rechnung\nRechnungsnummer: 2025-001234...",
    "model_used": "German-OCR Pro",
    "processing_time_ms": 1200
}
────────────────────────────────────────────────────────
```

---

### 2. Guzzle Demo - Modern HTTP Client

Upload mit Guzzle HTTP Client - empfohlen für moderne PHP-Anwendungen.

**Datei:** `guzzle_demo.php`

```bash
# Einzelne Datei
php guzzle_demo.php rechnung.jpg

# Mit Prompt
php guzzle_demo.php rechnung.pdf "Extrahiere Rechnungsnummer und Datum"

# Batch-Verarbeitung (mehrere Dateien parallel)
php guzzle_demo.php rechnung1.jpg rechnung2.pdf rechnung3.jpg
```

**Features:**
- Moderner HTTP Client mit Promise-Support
- Synchrone und asynchrone Verarbeitung
- Batch-Modus für mehrere Dateien
- Automatische Retry-Logik möglich
- Exception-Handling für verschiedene Fehlertypen
- PSR-7 HTTP Messages

**Beispiel-Ausgabe (Batch):**
```
🚀 Starte Batch-Verarbeitung mit Guzzle (async)...
   Dokumente: 3
   Modell: german-ocr-pro (schnell und zuverlässig)

📊 Batch-Ergebnisse:
══════════════════════════════════════════════════════════════════
✅ [0] rechnung1.jpg
   📄 Text: Rechnung Nr. 2025-001234...
✅ [1] rechnung2.pdf
   📄 Text: Lieferschein vom 22.12.2025...
✅ [2] rechnung3.jpg
   📄 Text: Angebot Nr. 2025-567...
══════════════════════════════════════════════════════════════════

📈 Statistiken:
   Gesamt:          3 Dokumente
   Erfolgreich:     3 ✅
   Fehlgeschlagen:  0 ❌
   Gesamtzeit:      1500ms
   Ø Pro Dokument:  500ms
   Durchsatz:       2.00 Dok/s
```

---

## API-Konfiguration

Die Zugangsdaten sind bereits in den Skripten hinterlegt:

```php
define('API_ENDPOINT', 'https://api.german-ocr.de/v1/analyze');
define('API_KEY', getenv('GERMAN_OCR_API_KEY') ?: 'YOUR_API_KEY');
define('API_SECRET', getenv('GERMAN_OCR_API_SECRET') ?: 'YOUR_API_SECRET');
```

**Für produktiven Einsatz:** Credentials aus Umgebungsvariablen laden:

```php
// Mit getenv()
define('API_ENDPOINT', getenv('GERMAN_OCR_ENDPOINT') ?: 'https://api.german-ocr.de/v1/analyze');
define('API_KEY', getenv('GERMAN_OCR_API_KEY'));
define('API_SECRET', getenv('GERMAN_OCR_API_SECRET'));

// Mit $_ENV (PHP 7.1+)
define('API_KEY', $_ENV['GERMAN_OCR_API_KEY'] ?? null);
```

---

## Modell-Optionen

| Modell | Beschreibung | Geschwindigkeit | Qualität |
|--------|--------------|-----------------|----------|
| `german-ocr-ultra` | Maximale Präzision für komplexe Dokumente | ⚡⚡ | ⭐⭐⭐ |
| `german-ocr-pro` | Schnell und zuverlässig | ⚡⚡⚡ | ⭐⭐ |
| `german-ocr` | Lokal auf eigenen Servern | ⚡ | ⭐⭐ |

---

## Integration in eigene Anwendungen

### WordPress Plugin

```php
<?php
// wp-german-ocr.php
require_once __DIR__ . '/simple_curl.php';

function german_ocr_process_attachment($attachment_id) {
    $file_path = get_attached_file($attachment_id);

    try {
        $result = analyzeDocument($file_path);

        // OCR-Text als Post-Meta speichern
        update_post_meta($attachment_id, 'ocr_text', $result['text']);
        update_post_meta($attachment_id, 'ocr_model', $result['model_used']);

        return $result;

    } catch (Exception $e) {
        error_log('German-OCR Error: ' . $e->getMessage());
        return false;
    }
}

// Hook für neue Uploads
add_action('add_attachment', 'german_ocr_process_attachment');
```

### Laravel Integration

```php
<?php
// app/Services/GermanOcrService.php
namespace App\Services;

use GuzzleHttp\Client;

class GermanOcrService
{
    private $client;

    public function __construct()
    {
        $this->client = new Client([
            'base_uri' => config('services.german_ocr.endpoint'),
            'timeout' => 60,
        ]);
    }

    public function analyze($filePath, $prompt = null, $model = 'german-ocr-pro')
    {
        $multipart = [
            [
                'name' => 'file',
                'contents' => fopen($filePath, 'r'),
                'filename' => basename($filePath)
            ],
            [
                'name' => 'model',
                'contents' => $model
            ]
        ];

        if ($prompt) {
            $multipart[] = [
                'name' => 'prompt',
                'contents' => $prompt
            ];
        }

        $authToken = config('services.german_ocr.key') . ':' . config('services.german_ocr.secret');

        $response = $this->client->post('/v1/analyze', [
            'headers' => [
                'Authorization' => "Bearer $authToken"
            ],
            'multipart' => $multipart
        ]);

        return json_decode($response->getBody(), true);
    }
}
```

```php
// config/services.php
return [
    'german_ocr' => [
        'endpoint' => env('GERMAN_OCR_ENDPOINT', 'https://api.german-ocr.de'),
        'key' => env('GERMAN_OCR_API_KEY'),
        'secret' => env('GERMAN_OCR_API_SECRET'),
    ],
];
```

### Symfony Integration

```php
<?php
// src/Service/GermanOcrService.php
namespace App\Service;

use GuzzleHttp\Client;
use Symfony\Component\DependencyInjection\ParameterBag\ParameterBagInterface;

class GermanOcrService
{
    private Client $client;
    private array $config;

    public function __construct(ParameterBagInterface $params)
    {
        $this->config = $params->get('german_ocr');

        $this->client = new Client([
            'base_uri' => $this->config['endpoint'],
            'timeout' => 60,
        ]);
    }

    public function analyze(string $filePath, ?string $prompt = null): array
    {
        // Implementierung wie Laravel-Beispiel
    }
}
```

### Vanilla PHP REST API

```php
<?php
// api/ocr.php
header('Content-Type: application/json');

require_once __DIR__ . '/../simple_curl.php';

if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
    http_response_code(405);
    echo json_encode(['error' => 'POST required']);
    exit;
}

if (!isset($_FILES['file'])) {
    http_response_code(400);
    echo json_encode(['error' => 'Keine Datei']);
    exit;
}

$file = $_FILES['file'];
$prompt = $_POST['prompt'] ?? null;
$model = $_POST['model'] ?? 'german-ocr-pro';

try {
    // Temporäre Datei verwenden
    $result = analyzeDocument($file['tmp_name'], $prompt, $model);
    echo json_encode($result);

} catch (Exception $e) {
    http_response_code(500);
    echo json_encode(['error' => $e->getMessage()]);
}
```

---

## Fehlerbehandlung

### cURL-Fehler

```php
if (curl_errno($ch)) {
    $error = curl_error($ch);
    $errno = curl_errno($ch);
    curl_close($ch);

    switch ($errno) {
        case CURLE_OPERATION_TIMEDOUT:
            throw new Exception("Timeout nach 60 Sekunden");
        case CURLE_COULDNT_CONNECT:
            throw new Exception("Verbindung fehlgeschlagen");
        case CURLE_SSL_CERTPROBLEM:
            throw new Exception("SSL-Zertifikatsfehler");
        default:
            throw new Exception("cURL-Fehler ($errno): $error");
    }
}
```

### Guzzle Exceptions

```php
use GuzzleHttp\Exception\ConnectException;
use GuzzleHttp\Exception\RequestException;

try {
    $response = $client->request('POST', $endpoint, [...]);

} catch (ConnectException $e) {
    // Verbindungsfehler
    echo "Verbindung fehlgeschlagen: " . $e->getMessage();

} catch (RequestException $e) {
    // HTTP-Fehler (4xx, 5xx)
    if ($e->hasResponse()) {
        $statusCode = $e->getResponse()->getStatusCode();
        $body = (string) $e->getResponse()->getBody();
        echo "API-Fehler ($statusCode): $body";
    }
}
```

---

## Performance-Tipps

1. **Guzzle für Batch:** Bei mehreren Dateien asynchrone Guzzle-Requests verwenden
2. **Connection Pooling:** Guzzle Client wiederverwenden
3. **Modell-Wahl:** `german-ocr-pro` für beste Balance zwischen Geschwindigkeit und Qualität
4. **Timeout anpassen:** Bei großen PDFs Timeout erhöhen
5. **Memory Limit:** Bei großen Dateien `memory_limit` erhöhen

```php
// Memory Limit erhöhen
ini_set('memory_limit', '512M');

// Timeout erhöhen
curl_setopt($ch, CURLOPT_TIMEOUT, 120); // 2 Minuten
```

---

## Troubleshooting

### "Call to undefined function curl_init()"
```bash
# Ubuntu/Debian
sudo apt-get install php-curl
sudo systemctl restart apache2

# Windows: php.ini bearbeiten
extension=curl
```

### "Class 'GuzzleHttp\Client' not found"
```bash
composer require guzzlehttp/guzzle
```

### "Failed to open stream: Permission denied"
Datei-Berechtigungen prüfen:
```bash
chmod 644 rechnung.jpg
```

### "SSL certificate problem: unable to get local issuer certificate"
Nur für Entwicklung (NICHT für Produktion):
```php
curl_setopt($ch, CURLOPT_SSL_VERIFYPEER, false);
```

### "Maximum execution time exceeded"
In php.ini:
```ini
max_execution_time = 120
```

Oder im Skript:
```php
set_time_limit(120);
```

---

## Support

- Dokumentation: https://german-ocr.de/docs
- Support: support@keyvan.ai
- Issues: https://github.com/Keyvanhardani/German-OCR-Enterprise-Platform/issues

---

**Entwickelt von Keyvan.ai** | Powered by German-OCR
