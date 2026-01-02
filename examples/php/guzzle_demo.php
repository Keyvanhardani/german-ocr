<?php
/**
 * German-OCR API - Guzzle HTTP Client Beispiel (PHP)
 *
 * Dieses Skript zeigt, wie man die German-OCR API
 * mit dem Guzzle HTTP Client verwendet.
 *
 * Installation:
 *   composer require guzzlehttp/guzzle
 *
 * Verwendung:
 *   php guzzle_demo.php <bildpfad> [prompt] [model]
 */

require_once __DIR__ . '/vendor/autoload.php';

use GuzzleHttp\Client;
use GuzzleHttp\Exception\RequestException;
use GuzzleHttp\Exception\ConnectException;

// API-Konfiguration
define('API_ENDPOINT', 'https://api.german-ocr.de/v1/analyze');
define('API_KEY', 'gocr_079a85fb');
define('API_SECRET', '7c3fafb5efedcad69ba991ca1e96bce7f4929d769b4f1349fa0a28e98f4a462c');

/**
 * Analysiert ein Dokument mit der German-OCR API (Guzzle)
 *
 * @param string $filePath Pfad zur Bilddatei
 * @param string|null $prompt Optionaler Prompt
 * @param string $model Modell-Auswahl (german-ocr, german-ocr-pro, german-ocr-ultra)
 * @return array API-Antwort
 * @throws Exception Bei Fehlern
 */
function analyzeDocument($filePath, $prompt = null, $model = 'german-ocr-pro') {
    // Prüfe ob Datei existiert
    if (!file_exists($filePath)) {
        throw new Exception("Datei nicht gefunden: $filePath");
    }

    $fileName = basename($filePath);

    echo "📤 Sende Dokument an German-OCR API (Guzzle)...\n";
    echo "   Datei: $fileName\n";
    echo "   Modell: $model\n";
    if ($prompt) {
        echo "   Prompt: $prompt\n";
    }
    echo "\n";

    // Guzzle Client erstellen
    $client = new Client([
        'timeout' => 60.0,
        'verify' => true, // SSL-Verifizierung
        'http_errors' => false // Fehler manuell behandeln
    ]);

    // Auth-Header
    $authToken = API_KEY . ':' . API_SECRET;

    // Multipart-FormData vorbereiten
    $multipart = [
        [
            'name' => 'file',
            'contents' => fopen($filePath, 'r'),
            'filename' => $fileName
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

    // Request senden und Zeit messen
    $startTime = microtime(true);

    try {
        $response = $client->request('POST', API_ENDPOINT, [
            'headers' => [
                'Authorization' => "Bearer $authToken"
            ],
            'multipart' => $multipart
        ]);

        $responseTime = round((microtime(true) - $startTime) * 1000);

        // HTTP-Statuscode prüfen
        $statusCode = $response->getStatusCode();

        if ($statusCode !== 200) {
            $body = (string) $response->getBody();
            throw new Exception("API-Fehler ($statusCode): $body");
        }

        // JSON dekodieren
        $result = json_decode($response->getBody(), true);

        if (json_last_error() !== JSON_ERROR_NONE) {
            throw new Exception("JSON-Fehler: " . json_last_error_msg());
        }

        // Ergebnis ausgeben
        echo "✅ Erfolgreich verarbeitet!\n";
        echo "⏱️  Antwortzeit: {$responseTime}ms\n";
        echo "\n";
        echo "📄 Ergebnis:\n";
        echo str_repeat('─', 60) . "\n";
        echo json_encode($result, JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES);
        echo "\n";
        echo str_repeat('─', 60) . "\n";

        return $result;

    } catch (ConnectException $e) {
        $responseTime = round((microtime(true) - $startTime) * 1000);
        echo "❌ Verbindungsfehler nach {$responseTime}ms:\n";
        echo "   " . $e->getMessage() . "\n";
        throw $e;

    } catch (RequestException $e) {
        $responseTime = round((microtime(true) - $startTime) * 1000);
        echo "❌ Request-Fehler nach {$responseTime}ms:\n";
        echo "   " . $e->getMessage() . "\n";

        if ($e->hasResponse()) {
            $body = (string) $e->getResponse()->getBody();
            echo "   Antwort: $body\n";
        }

        throw $e;

    } catch (Exception $e) {
        $responseTime = round((microtime(true) - $startTime) * 1000);
        echo "❌ Fehler nach {$responseTime}ms:\n";
        echo "   " . $e->getMessage() . "\n";
        throw $e;
    }
}

/**
 * Batch-Verarbeitung mit Guzzle (asynchron)
 *
 * @param array $filePaths Array von Dateipfaden
 * @return array Batch-Statistiken
 */
function processBatch(array $filePaths) {
    echo "🚀 Starte Batch-Verarbeitung mit Guzzle (async)...\n";
    echo "   Dokumente: " . count($filePaths) . "\n";
    echo "   Modell: german-ocr-pro (schnell und zuverlässig)\n";
    echo "\n";

    $client = new Client([
        'timeout' => 60.0,
        'verify' => true
    ]);

    $authToken = API_KEY . ':' . API_SECRET;
    $promises = [];
    $startTime = microtime(true);

    // Promises für alle Dateien erstellen
    foreach ($filePaths as $index => $filePath) {
        if (!file_exists($filePath)) {
            echo "⚠️  [$index] Datei nicht gefunden: $filePath\n";
            continue;
        }

        $fileName = basename($filePath);

        $multipart = [
            [
                'name' => 'file',
                'contents' => fopen($filePath, 'r'),
                'filename' => $fileName
            ],
            [
                'name' => 'model',
                'contents' => 'german-ocr-pro'
            ]
        ];

        // Asynchronen Request erstellen
        $promises[$index] = $client->requestAsync('POST', API_ENDPOINT, [
            'headers' => [
                'Authorization' => "Bearer $authToken"
            ],
            'multipart' => $multipart
        ]);
    }

    // Alle Promises abwarten
    $results = \GuzzleHttp\Promise\Utils::settle($promises)->wait();
    $totalTime = round((microtime(true) - $startTime) * 1000);

    // Ergebnisse auswerten
    $successful = 0;
    $failed = 0;

    echo "📊 Batch-Ergebnisse:\n";
    echo str_repeat('═', 70) . "\n";

    foreach ($results as $index => $result) {
        $fileName = basename($filePaths[$index]);

        if ($result['state'] === 'fulfilled') {
            $response = $result['value'];
            if ($response->getStatusCode() === 200) {
                $successful++;
                echo "✅ [$index] $fileName\n";

                $data = json_decode($response->getBody(), true);
                if (isset($data['text'])) {
                    $preview = substr($data['text'], 0, 60);
                    $preview = str_replace("\n", ' ', $preview);
                    echo "   📄 Text: $preview...\n";
                }
            } else {
                $failed++;
                echo "❌ [$index] $fileName (HTTP {$response->getStatusCode()})\n";
            }
        } else {
            $failed++;
            $reason = $result['reason'];
            echo "❌ [$index] $fileName\n";
            echo "   ⚠️  Fehler: {$reason->getMessage()}\n";
        }
    }

    echo str_repeat('═', 70) . "\n";
    echo "\n";
    echo "📈 Statistiken:\n";
    echo "   Gesamt:          " . count($filePaths) . " Dokumente\n";
    echo "   Erfolgreich:     $successful ✅\n";
    echo "   Fehlgeschlagen:  $failed ❌\n";
    echo "   Gesamtzeit:      {$totalTime}ms\n";

    if ($successful > 0) {
        $avgTime = round($totalTime / count($filePaths));
        echo "   Ø Pro Dokument:  {$avgTime}ms\n";
        echo "   Durchsatz:       " . round(count($filePaths) / ($totalTime / 1000), 2) . " Dok/s\n";
    }

    return [
        'total' => count($filePaths),
        'successful' => $successful,
        'failed' => $failed,
        'total_time' => $totalTime
    ];
}

/**
 * Hauptfunktion
 */
function main() {
    global $argv;

    if (count($argv) < 2) {
        echo "❌ Fehler: Keine Datei(en) angegeben\n";
        echo "\n";
        echo "Verwendung:\n";
        echo "  Einzelne Datei:\n";
        echo "    php guzzle_demo.php <bildpfad> [prompt] [model]\n";
        echo "\n";
        echo "  Batch-Verarbeitung:\n";
        echo "    php guzzle_demo.php <datei1> <datei2> <datei3> ...\n";
        echo "\n";
        echo "Beispiele:\n";
        echo "  php guzzle_demo.php rechnung.jpg\n";
        echo "  php guzzle_demo.php rechnung.pdf \"Extrahiere Rechnungsnummer\"\n";
        echo "  php guzzle_demo.php doc1.jpg doc2.jpg doc3.pdf (Batch)\n";
        echo "\n";
        echo "Modell-Optionen: german-ocr-ultra, german-ocr-pro (Standard), german-ocr\n";
        exit(1);
    }

    try {
        // Prüfe ob Composer Autoloader existiert
        if (!class_exists('GuzzleHttp\Client')) {
            throw new Exception(
                "Guzzle nicht installiert.\n" .
                "   Bitte ausführen: composer require guzzlehttp/guzzle"
            );
        }

        // Batch-Modus wenn mehrere Dateien
        if (count($argv) > 2 && file_exists($argv[2])) {
            $filePaths = array_slice($argv, 1);
            $stats = processBatch($filePaths);

            echo "\n";
            if ($stats['failed'] > 0) {
                echo "⚠️  Batch abgeschlossen mit Fehlern\n";
                exit(1);
            } else {
                echo "✨ Batch erfolgreich abgeschlossen!\n";
            }

        } else {
            // Einzelner Request
            $filePath = $argv[1];
            $prompt = isset($argv[2]) && $argv[2] !== '' ? $argv[2] : null;
            $model = isset($argv[3]) ? $argv[3] : 'german-ocr-pro';

            analyzeDocument($filePath, $prompt, $model);
            echo "\n";
            echo "✨ Fertig!\n";
        }

        exit(0);

    } catch (Exception $e) {
        echo "\n";
        echo "💥 Fehler: " . $e->getMessage() . "\n";
        exit(1);
    }
}

// Nur ausführen wenn direkt aufgerufen
if (php_sapi_name() === 'cli') {
    main();
}
