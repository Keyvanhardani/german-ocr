<?php
/**
 * German-OCR API - PHP Beispiel mit cURL (Async-Workflow)
 *
 * Dieses Skript zeigt, wie man ein Dokument an die German-OCR API sendet
 * und auf das Ergebnis wartet (Polling).
 *
 * Voraussetzungen:
 *   - PHP 7.4+ mit cURL-Extension
 *
 * Verwendung:
 *   php simple_curl.php <bildpfad> [prompt] [model]
 *   php simple_curl.php --status <job_id>
 */

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
 * Analysiert ein Dokument mit der German-OCR API (Async-Workflow)
 *
 * @param string $filePath Pfad zur Bilddatei
 * @param string|null $prompt Optionaler Prompt
 * @param string $model Modell-Auswahl (german-ocr, german-ocr-pro, german-ocr-ultra)
 * @param bool $waitForResult Auf Ergebnis warten (Polling)
 * @return array API-Antwort
 * @throws Exception Bei Fehlern
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

    // Prüfe ob Datei existiert
    if (!file_exists($filePath)) {
        throw new Exception("Datei nicht gefunden: $filePath");
    }

    // Prüfe cURL Extension
    if (!function_exists('curl_init')) {
        throw new Exception("cURL-Extension nicht verfügbar");
    }

    $fileName = basename($filePath);

    echo "📤 Sende Dokument an German-OCR API...\n";
    echo "   Datei: $fileName\n";
    echo "   Modell: $model\n";
    if ($prompt) {
        echo "   Prompt: $prompt\n";
    }
    echo "\n";

    // Job submitten
    $jobResult = submitJob($filePath, $prompt, $model);
    $jobId = $jobResult['job_id'] ?? null;

    if (!$jobId) {
        throw new Exception("Keine Job-ID erhalten");
    }

    echo "✅ Job erfolgreich gestartet!\n";
    echo "📋 Job-ID: $jobId\n";
    echo "🤖 Modell: " . ($jobResult['model'] ?? $model) . "\n";
    echo "\n";

    // Auf Ergebnis warten?
    if (!$waitForResult) {
        echo "ℹ️  Modus: Fire-and-Forget (--no-wait)\n";
        echo "   Ergebnis abrufen: php simple_curl.php --status $jobId\n";
        return $jobResult;
    }

    // Polling bis Ergebnis fertig
    echo "⏳ Warte auf Ergebnis...\n";
    return pollJobStatus($jobId);
}

/**
 * Submits einen OCR-Job an die API
 */
function submitJob($filePath, $prompt = null, $model = 'german-ocr-pro') {
    $fileName = basename($filePath);

    // FormData vorbereiten
    $postData = [
        'file' => new CURLFile($filePath, mime_content_type($filePath), $fileName),
        'model' => $model,
    ];

    if ($prompt) {
        $postData['prompt'] = $prompt;
    }

    // Auth-Header
    $authToken = API_KEY . ':' . API_SECRET;
    $headers = [
        'Authorization: Bearer ' . $authToken
    ];

    // cURL initialisieren
    $ch = curl_init();

    curl_setopt_array($ch, [
        CURLOPT_URL => API_ENDPOINT,
        CURLOPT_POST => true,
        CURLOPT_POSTFIELDS => $postData,
        CURLOPT_HTTPHEADER => $headers,
        CURLOPT_RETURNTRANSFER => true,
        CURLOPT_TIMEOUT => TIMEOUT_SUBMIT,
        CURLOPT_SSL_VERIFYPEER => true,
        CURLOPT_FOLLOWLOCATION => true
    ]);

    // Request senden
    $response = curl_exec($ch);

    // Fehlerbehandlung
    if ($response === false) {
        $error = curl_error($ch);
        $errno = curl_errno($ch);
        curl_close($ch);
        throw new Exception("cURL-Fehler ($errno): $error");
    }

    $httpCode = curl_getinfo($ch, CURLINFO_HTTP_CODE);
    curl_close($ch);

    // 202 = Job in Warteschlange (normal)
    if ($httpCode !== 202 && $httpCode !== 200) {
        throw new Exception("API-Fehler ($httpCode): $response");
    }

    // JSON dekodieren
    $result = json_decode($response, true);

    if (json_last_error() !== JSON_ERROR_NONE) {
        throw new Exception("JSON-Fehler: " . json_last_error_msg());
    }

    return $result;
}

/**
 * Pollt den Job-Status bis zum Abschluss
 */
function pollJobStatus($jobId) {
    $authToken = API_KEY . ':' . API_SECRET;
    $headers = [
        'Authorization: Bearer ' . $authToken
    ];

    $attempts = 0;
    $startTime = microtime(true);

    while ($attempts < MAX_POLL_ATTEMPTS) {
        $attempts++;

        // Status abfragen
        $ch = curl_init();
        curl_setopt_array($ch, [
            CURLOPT_URL => API_JOB_ENDPOINT . $jobId,
            CURLOPT_HTTPGET => true,
            CURLOPT_HTTPHEADER => $headers,
            CURLOPT_RETURNTRANSFER => true,
            CURLOPT_TIMEOUT => TIMEOUT_POLL,
            CURLOPT_SSL_VERIFYPEER => true,
        ]);

        $response = curl_exec($ch);
        $httpCode = curl_getinfo($ch, CURLINFO_HTTP_CODE);
        curl_close($ch);

        if ($httpCode !== 200) {
            throw new Exception("Status-Abfrage fehlgeschlagen ($httpCode): $response");
        }

        $status = json_decode($response, true);

        if (json_last_error() !== JSON_ERROR_NONE) {
            throw new Exception("JSON-Fehler: " . json_last_error_msg());
        }

        $jobStatus = $status['status'] ?? 'unknown';

        // Status-Fortschritt anzeigen
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

        // Warten vor nächster Abfrage
        sleep(POLL_INTERVAL);
    }

    throw new Exception("Timeout: Job nach " . (MAX_POLL_ATTEMPTS * POLL_INTERVAL) . " Sekunden nicht fertig");
}

/**
 * Ruft den Status eines bestehenden Jobs ab
 */
function getJobStatus($jobId) {
    // Prüfe Credentials
    if (API_KEY === 'YOUR_API_KEY' || API_SECRET === 'YOUR_API_SECRET') {
        throw new Exception("API-Credentials nicht konfiguriert!");
    }

    $authToken = API_KEY . ':' . API_SECRET;
    $headers = [
        'Authorization: Bearer ' . $authToken
    ];

    $ch = curl_init();
    curl_setopt_array($ch, [
        CURLOPT_URL => API_JOB_ENDPOINT . $jobId,
        CURLOPT_HTTPGET => true,
        CURLOPT_HTTPHEADER => $headers,
        CURLOPT_RETURNTRANSFER => true,
        CURLOPT_TIMEOUT => TIMEOUT_POLL,
        CURLOPT_SSL_VERIFYPEER => true,
    ]);

    $response = curl_exec($ch);
    $httpCode = curl_getinfo($ch, CURLINFO_HTTP_CODE);
    curl_close($ch);

    if ($httpCode !== 200) {
        throw new Exception("Status-Abfrage fehlgeschlagen ($httpCode): $response");
    }

    $status = json_decode($response, true);

    if (json_last_error() !== JSON_ERROR_NONE) {
        throw new Exception("JSON-Fehler: " . json_last_error_msg());
    }

    // Formatierte Ausgabe
    echo "📋 Job-ID: $jobId\n";
    echo "📊 Status: " . ($status['status'] ?? 'unknown') . "\n";

    if (($status['status'] ?? '') === 'completed') {
        echo "⏱️  Verarbeitungszeit: " . ($status['processing_time_ms'] ?? 'N/A') . "ms\n";
        echo "💰 Kosten: " . ($status['price_display'] ?? 'N/A') . "\n";
        echo "\n";
        echo "📄 Ergebnis:\n";
        echo str_repeat('─', 60) . "\n";
        echo $status['result'] ?? 'Kein Ergebnis';
        echo "\n";
        echo str_repeat('─', 60) . "\n";
    } elseif (($status['status'] ?? '') === 'failed') {
        echo "❌ Fehler: " . ($status['error'] ?? 'Unbekannt') . "\n";
    }

    return $status;
}

/**
 * Hauptfunktion
 */
function main() {
    global $argv;

    // Hilfe anzeigen
    if (count($argv) < 2 || in_array('--help', $argv) || in_array('-h', $argv)) {
        showHelp();
        exit(count($argv) < 2 ? 1 : 0);
    }

    try {
        // --status Mode: Bestehenden Job abfragen
        if ($argv[1] === '--status') {
            if (!isset($argv[2])) {
                throw new Exception("Job-ID erforderlich: php simple_curl.php --status <job_id>");
            }
            getJobStatus($argv[2]);
            exit(0);
        }

        // Normale Dokumentenanalyse
        $filePath = $argv[1];
        $prompt = isset($argv[2]) && $argv[2] !== '' && $argv[2] !== '--no-wait' ? $argv[2] : null;
        $model = 'german-ocr-pro';
        $waitForResult = true;

        // Optionen parsen
        for ($i = 2; $i < count($argv); $i++) {
            if ($argv[$i] === '--no-wait') {
                $waitForResult = false;
            } elseif (in_array($argv[$i], ['german-ocr', 'german-ocr-pro', 'german-ocr-ultra', 'local', 'cloud_fast', 'cloud'])) {
                $model = $argv[$i];
            }
        }

        analyzeDocument($filePath, $prompt, $model, $waitForResult);
        echo "\n";
        echo "✨ Fertig!\n";
        exit(0);

    } catch (Exception $e) {
        echo "\n";
        echo "💥 Fehler: " . $e->getMessage() . "\n";
        exit(1);
    }
}

function showHelp() {
    echo "German-OCR API - PHP cURL Demo\n";
    echo str_repeat('═', 50) . "\n\n";
    echo "Verwendung:\n";
    echo "  php simple_curl.php <bildpfad> [prompt] [model] [optionen]\n";
    echo "  php simple_curl.php --status <job_id>\n";
    echo "\n";
    echo "Argumente:\n";
    echo "  <bildpfad>    Pfad zur Bild- oder PDF-Datei\n";
    echo "  [prompt]      Optionaler Prompt für strukturierte Extraktion\n";
    echo "  [model]       Modell-Auswahl (siehe unten)\n";
    echo "\n";
    echo "Optionen:\n";
    echo "  --no-wait     Job starten ohne auf Ergebnis zu warten\n";
    echo "  --status      Status eines bestehenden Jobs abfragen\n";
    echo "  --help, -h    Diese Hilfe anzeigen\n";
    echo "\n";
    echo "Modelle:\n";
    echo "  german-ocr-ultra  Maximale Präzision (0,05 EUR/Seite)\n";
    echo "  german-ocr-pro    Schnell & zuverlässig (0,05 EUR/Seite) [Standard]\n";
    echo "  german-ocr        DSGVO-konform, lokal (0,02 EUR/Seite)\n";
    echo "\n";
    echo "Beispiele:\n";
    echo "  php simple_curl.php rechnung.jpg\n";
    echo "  php simple_curl.php rechnung.pdf \"Extrahiere Rechnungsnummer\" german-ocr-ultra\n";
    echo "  php simple_curl.php dokument.png --no-wait\n";
    echo "  php simple_curl.php --status abc123-def456\n";
    echo "\n";
    echo "Umgebungsvariablen:\n";
    echo "  GERMAN_OCR_API_KEY      API-Key (gocr_xxx)\n";
    echo "  GERMAN_OCR_API_SECRET   API-Secret\n";
    echo "\n";
}

// Nur ausführen wenn direkt aufgerufen
if (php_sapi_name() === 'cli' && isset($argv[0]) && basename($argv[0]) === basename(__FILE__)) {
    main();
}
