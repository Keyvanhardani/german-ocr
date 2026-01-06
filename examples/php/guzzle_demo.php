<?php
/**
 * German-OCR API - Guzzle HTTP Client Beispiel (Async-Workflow)
 *
 * Dieses Skript zeigt, wie man die German-OCR API mit Guzzle verwendet
 * und auf das Ergebnis wartet (Polling).
 *
 * Installation:
 *   composer require guzzlehttp/guzzle
 *
 * Verwendung:
 *   php guzzle_demo.php <bildpfad> [prompt] [model]
 *   php guzzle_demo.php <datei1> <datei2> ... (Batch)
 */

require_once __DIR__ . '/vendor/autoload.php';

use GuzzleHttp\Client;
use GuzzleHttp\Exception\RequestException;
use GuzzleHttp\Exception\ConnectException;

// API-Konfiguration
define('API_ENDPOINT', 'https://api.german-ocr.de/v1/analyze');
define('API_JOB_ENDPOINT', 'https://api.german-ocr.de/v1/jobs/');
define('API_KEY', getenv('GERMAN_OCR_API_KEY') ?: 'YOUR_API_KEY');
define('API_SECRET', getenv('GERMAN_OCR_API_SECRET') ?: 'YOUR_API_SECRET');

// Timeout-Konfiguration (Sekunden)
define('TIMEOUT_SUBMIT', 30);     // Timeout für Job-Submit
define('TIMEOUT_POLL', 5);        // Timeout für Status-Abfrage
define('MAX_POLL_ATTEMPTS', 60);  // Max. Wartezeit: 60 * 2s = 2 Minuten
define('POLL_INTERVAL', 2);       // Sekunden zwischen Status-Abfragen

/**
 * Analysiert ein Dokument mit der German-OCR API (Guzzle + Async Polling)
 */
function analyzeDocument($filePath, $prompt = null, $model = 'german-ocr-pro', $waitForResult = true) {
    // Prüfe Credentials
    if (API_KEY === 'YOUR_API_KEY' || API_SECRET === 'YOUR_API_SECRET') {
        throw new Exception(
            "API-Credentials nicht konfiguriert!\n" .
            "   Setze Umgebungsvariablen:\n" .
            "   export GERMAN_OCR_API_KEY='gocr_xxx'\n" .
            "   export GERMAN_OCR_API_SECRET='xxx'"
        );
    }

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

    // Job submitten
    $jobResult = submitJobGuzzle($filePath, $prompt, $model);
    $jobId = $jobResult['job_id'] ?? null;

    if (!$jobId) {
        throw new Exception("Keine Job-ID erhalten");
    }

    echo "✅ Job erfolgreich gestartet!\n";
    echo "📋 Job-ID: $jobId\n";
    echo "🤖 Modell: " . ($jobResult['model'] ?? $model) . "\n";
    echo "\n";

    if (!$waitForResult) {
        echo "ℹ️  Modus: Fire-and-Forget (--no-wait)\n";
        return $jobResult;
    }

    echo "⏳ Warte auf Ergebnis...\n";
    return pollJobStatusGuzzle($jobId);
}

/**
 * Submits einen OCR-Job an die API (Guzzle)
 */
function submitJobGuzzle($filePath, $prompt = null, $model = 'german-ocr-pro') {
    $fileName = basename($filePath);

    $client = new Client([
        'timeout' => TIMEOUT_SUBMIT,
        'verify' => true,
        'http_errors' => false
    ]);

    $authToken = API_KEY . ':' . API_SECRET;

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

    try {
        $response = $client->request('POST', API_ENDPOINT, [
            'headers' => [
                'Authorization' => "Bearer $authToken"
            ],
            'multipart' => $multipart
        ]);

        $statusCode = $response->getStatusCode();

        if ($statusCode !== 202 && $statusCode !== 200) {
            $body = (string) $response->getBody();
            throw new Exception("API-Fehler ($statusCode): $body");
        }

        $result = json_decode($response->getBody(), true);

        if (json_last_error() !== JSON_ERROR_NONE) {
            throw new Exception("JSON-Fehler: " . json_last_error_msg());
        }

        return $result;

    } catch (ConnectException $e) {
        throw new Exception("Verbindungsfehler: " . $e->getMessage());
    } catch (RequestException $e) {
        $msg = $e->getMessage();
        if ($e->hasResponse()) {
            $msg .= " - " . (string) $e->getResponse()->getBody();
        }
        throw new Exception("Request-Fehler: $msg");
    }
}

/**
 * Pollt den Job-Status bis zum Abschluss (Guzzle)
 */
function pollJobStatusGuzzle($jobId) {
    $client = new Client([
        'timeout' => TIMEOUT_POLL,
        'verify' => true,
        'http_errors' => false
    ]);

    $authToken = API_KEY . ':' . API_SECRET;
    $attempts = 0;
    $startTime = microtime(true);

    while ($attempts < MAX_POLL_ATTEMPTS) {
        $attempts++;

        try {
            $response = $client->request('GET', API_JOB_ENDPOINT . $jobId, [
                'headers' => [
                    'Authorization' => "Bearer $authToken"
                ]
            ]);

            $statusCode = $response->getStatusCode();

            if ($statusCode !== 200) {
                throw new Exception("Status-Abfrage fehlgeschlagen ($statusCode)");
            }

            $status = json_decode($response->getBody(), true);

            if (json_last_error() !== JSON_ERROR_NONE) {
                throw new Exception("JSON-Fehler: " . json_last_error_msg());
            }

            $jobStatus = $status['status'] ?? 'unknown';

            $elapsed = round(microtime(true) - $startTime, 1);
            echo "\r   Status: $jobStatus ({$elapsed}s)...";

            if ($jobStatus === 'completed') {
                $totalTime = round((microtime(true) - $startTime) * 1000);
                echo "\n\n";
                echo "✅ Erfolgreich verarbeitet!\n";
                echo "⏱️  Gesamtzeit: {$totalTime}ms\n";
                echo "📊 Verarbeitungszeit: " . ($status['processing_time_ms'] ?? 'N/A') . "ms\n";
                echo "💰 Kosten: " . ($status['price_display'] ?? 'N/A') . "\n";
                echo "\n";
                echo "📄 Ergebnis:\n";
                echo str_repeat('─', 60) . "\n";
                echo $status['result'] ?? 'Kein Ergebnis';
                echo "\n";
                echo str_repeat('─', 60) . "\n";

                return $status;
            }

            if ($jobStatus === 'failed') {
                throw new Exception("Job fehlgeschlagen: " . ($status['error'] ?? 'Unbekannter Fehler'));
            }

            sleep(POLL_INTERVAL);

        } catch (ConnectException $e) {
            echo "\n⚠️  Verbindungsfehler, versuche erneut...\n";
            sleep(POLL_INTERVAL);
        }
    }

    throw new Exception("Timeout: Job nach " . (MAX_POLL_ATTEMPTS * POLL_INTERVAL) . " Sekunden nicht fertig");
}

/**
 * Batch-Verarbeitung mit Guzzle (asynchron + Polling)
 */
function processBatch(array $filePaths, $model = 'german-ocr-pro') {
    if (API_KEY === 'YOUR_API_KEY' || API_SECRET === 'YOUR_API_SECRET') {
        throw new Exception("API-Credentials nicht konfiguriert!");
    }

    echo "🚀 Starte Batch-Verarbeitung mit Guzzle...\n";
    echo "   Dokumente: " . count($filePaths) . "\n";
    echo "   Modell: $model\n";
    echo "\n";

    $client = new Client([
        'timeout' => TIMEOUT_SUBMIT,
        'verify' => true,
        'http_errors' => false
    ]);

    $authToken = API_KEY . ':' . API_SECRET;
    $promises = [];
    $startTime = microtime(true);

    echo "📤 Phase 1: Jobs submitten...\n";
    foreach ($filePaths as $index => $filePath) {
        if (!file_exists($filePath)) {
            echo "   ⚠️  [$index] Datei nicht gefunden: $filePath\n";
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
                'contents' => $model
            ]
        ];

        $promises[$index] = $client->requestAsync('POST', API_ENDPOINT, [
            'headers' => [
                'Authorization' => "Bearer $authToken"
            ],
            'multipart' => $multipart
        ]);
    }

    $submitResults = \GuzzleHttp\Promise\Utils::settle($promises)->wait();

    $jobIds = [];
    foreach ($submitResults as $index => $result) {
        $fileName = basename($filePaths[$index]);
        if ($result['state'] === 'fulfilled') {
            $response = $result['value'];
            $statusCode = $response->getStatusCode();
            if ($statusCode === 202 || $statusCode === 200) {
                $data = json_decode($response->getBody(), true);
                if (isset($data['job_id'])) {
                    $jobIds[$index] = $data['job_id'];
                    echo "   ✓ [$index] $fileName → Job " . substr($data['job_id'], 0, 8) . "...\n";
                }
            } else {
                echo "   ✗ [$index] $fileName → HTTP $statusCode\n";
            }
        } else {
            echo "   ✗ [$index] $fileName → Fehler\n";
        }
    }

    echo "\n";
    echo "⏳ Phase 2: Auf Ergebnisse warten...\n";

    $pollClient = new Client([
        'timeout' => TIMEOUT_POLL,
        'verify' => true,
        'http_errors' => false
    ]);

    $results = [];
    $pending = $jobIds;
    $attempts = 0;

    while (!empty($pending) && $attempts < MAX_POLL_ATTEMPTS) {
        $attempts++;

        foreach ($pending as $index => $jobId) {
            $response = $pollClient->request('GET', API_JOB_ENDPOINT . $jobId, [
                'headers' => ['Authorization' => "Bearer $authToken"]
            ]);

            if ($response->getStatusCode() === 200) {
                $status = json_decode($response->getBody(), true);
                $jobStatus = $status['status'] ?? 'unknown';

                if ($jobStatus === 'completed' || $jobStatus === 'failed') {
                    $results[$index] = $status;
                    unset($pending[$index]);
                }
            }
        }

        if (!empty($pending)) {
            $elapsed = round(microtime(true) - $startTime, 1);
            echo "   ⏳ " . count($pending) . " Jobs ausstehend ({$elapsed}s)...\r";
            sleep(POLL_INTERVAL);
        }
    }

    $totalTime = round((microtime(true) - $startTime) * 1000);

    echo "\n\n";
    echo "📊 Batch-Ergebnisse:\n";
    echo str_repeat('═', 70) . "\n";

    $successful = 0;
    $failed = 0;

    foreach ($filePaths as $index => $filePath) {
        $fileName = basename($filePath);

        if (isset($results[$index])) {
            $status = $results[$index];
            if (($status['status'] ?? '') === 'completed') {
                $successful++;
                echo "✅ [$index] $fileName\n";
                echo "   ⏱️  " . ($status['processing_time_ms'] ?? 'N/A') . "ms\n";
                if (isset($status['result'])) {
                    $preview = substr($status['result'], 0, 60);
                    $preview = str_replace("\n", ' ', $preview);
                    echo "   📄 $preview...\n";
                }
            } else {
                $failed++;
                echo "❌ [$index] $fileName (failed)\n";
            }
        } else {
            $failed++;
            echo "❌ [$index] $fileName (timeout/fehler)\n";
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
        'total_time' => $totalTime,
        'results' => $results
    ];
}

/**
 * Hauptfunktion
 */
function main() {
    global $argv;

    if (count($argv) < 2 || in_array('--help', $argv) || in_array('-h', $argv)) {
        showHelpGuzzle();
        exit(count($argv) < 2 ? 1 : 0);
    }

    try {
        if (!class_exists('GuzzleHttp\Client')) {
            throw new Exception(
                "Guzzle nicht installiert.\n" .
                "   Bitte ausführen: composer require guzzlehttp/guzzle"
            );
        }

        $files = [];
        $prompt = null;
        $model = 'german-ocr-pro';
        $waitForResult = true;

        for ($i = 1; $i < count($argv); $i++) {
            $arg = $argv[$i];

            if ($arg === '--no-wait') {
                $waitForResult = false;
            } elseif (in_array($arg, ['german-ocr', 'german-ocr-pro', 'german-ocr-ultra', 'local', 'cloud_fast', 'cloud'])) {
                $model = $arg;
            } elseif (file_exists($arg)) {
                $files[] = $arg;
            } elseif (count($files) === 1 && $prompt === null) {
                $prompt = $arg;
            }
        }

        if (empty($files)) {
            throw new Exception("Keine gültigen Dateien angegeben");
        }

        if (count($files) > 1) {
            echo "📁 Batch-Modus: " . count($files) . " Dateien\n\n";
            $stats = processBatch($files, $model);

            echo "\n";
            if ($stats['failed'] > 0) {
                echo "⚠️  Batch abgeschlossen mit Fehlern\n";
                exit(1);
            } else {
                echo "✨ Batch erfolgreich abgeschlossen!\n";
            }

        } else {
            analyzeDocument($files[0], $prompt, $model, $waitForResult);
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

function showHelpGuzzle() {
    echo "German-OCR API - Guzzle HTTP Demo\n";
    echo str_repeat('═', 50) . "\n\n";
    echo "Verwendung:\n";
    echo "  Einzelne Datei:\n";
    echo "    php guzzle_demo.php <bildpfad> [prompt] [model] [optionen]\n";
    echo "\n";
    echo "  Batch-Verarbeitung:\n";
    echo "    php guzzle_demo.php <datei1> <datei2> ... [model]\n";
    echo "\n";
    echo "Modelle:\n";
    echo "  german-ocr-ultra  Maximale Präzision (0,05 EUR/Seite)\n";
    echo "  german-ocr-pro    Schnell & zuverlässig (0,05 EUR/Seite) [Standard]\n";
    echo "  german-ocr        DSGVO-konform, lokal (0,02 EUR/Seite)\n";
    echo "\n";
    echo "Optionen:\n";
    echo "  --no-wait     Job starten ohne auf Ergebnis zu warten\n";
    echo "  --help, -h    Diese Hilfe anzeigen\n";
    echo "\n";
    echo "Umgebungsvariablen:\n";
    echo "  GERMAN_OCR_API_KEY      API-Key (gocr_xxx)\n";
    echo "  GERMAN_OCR_API_SECRET   API-Secret\n";
    echo "\n";
    echo "Installation:\n";
    echo "  composer require guzzlehttp/guzzle\n";
    echo "\n";
}

if (php_sapi_name() === 'cli') {
    main();
}
