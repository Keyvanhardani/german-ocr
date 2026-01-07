<?php
/**
 * German-OCR API - PHP cURL Beispiel (Async Job-Based)
 *
 * Dieses Skript zeigt, wie man Dokumente mit der German-OCR API
 * verarbeitet. Die API ist asynchron (Job-basiert):
 *
 * 1. POST /v1/analyze -> 202 + job_id (sofort)
 * 2. GET /v1/jobs/{id} -> polling bis status=completed
 *
 * Voraussetzungen:
 *   - PHP 7.4+ mit cURL-Extension
 *
 * Verwendung:
 *   php simple_curl.php <bildpfad> [prompt] [model]
 *   php simple_curl.php <bildpfad> --no-wait
 *   php simple_curl.php --status <job_id>
 *
 * Modelle: german-ocr-turbo, german-ocr-pro (Standard), german-ocr-ultra
 */

// === KONFIGURATION ===
define('API_BASE_URL', 'https://api.german-ocr.de');
define('API_KEY', getenv('GERMAN_OCR_API_KEY') ?: 'YOUR_API_KEY');
define('API_SECRET', getenv('GERMAN_OCR_API_SECRET') ?: 'YOUR_API_SECRET');

// Timeouts
define('TIMEOUT_SUBMIT', 30);      // Sekunden für Job-Submission
define('TIMEOUT_POLL', 10);        // Sekunden pro Poll-Request
define('MAX_POLL_ATTEMPTS', 120);  // Max. Versuche (= 4 Minuten bei 2s Intervall)
define('POLL_INTERVAL', 2);        // Sekunden zwischen Polls

// Modelle
define('MODELS', [
    'german-ocr-ultra' => ['name' => 'German-OCR Ultra', 'price' => '0,05 EUR'],
    'german-ocr-pro'   => ['name' => 'German-OCR Pro', 'price' => '0,05 EUR'],
    'german-ocr'       => ['name' => 'German-OCR Turbo', 'price' => '0,02 EUR'],
]);

/**
 * Sendet ein Dokument an die API und gibt die Job-ID zurueck.
 *
 * @param string $filePath Pfad zur Datei
 * @param string|null $prompt Optionaler Prompt
 * @param string $model Modell-Auswahl
 * @return string Job-ID
 * @throws Exception Bei Fehlern
 */
function submitJob(string $filePath, ?string $prompt = null, string $model = 'german-ocr-ultra'): string {
    if (!file_exists($filePath)) {
        throw new Exception("Datei nicht gefunden: $filePath");
    }

    $fileName = basename($filePath);
    $mimeType = mime_content_type($filePath) ?: 'application/octet-stream';

    // FormData
    $postData = [
        'file' => new CURLFile($filePath, $mimeType, $fileName),
        'model' => $model,
    ];

    if ($prompt) {
        $postData['prompt'] = $prompt;
    }

    // Auth Header
    $authToken = API_KEY . ':' . API_SECRET;

    $ch = curl_init();
    curl_setopt_array($ch, [
        CURLOPT_URL => API_BASE_URL . '/v1/analyze',
        CURLOPT_POST => true,
        CURLOPT_POSTFIELDS => $postData,
        CURLOPT_HTTPHEADER => ["Authorization: Bearer $authToken"],
        CURLOPT_RETURNTRANSFER => true,
        CURLOPT_TIMEOUT => TIMEOUT_SUBMIT,
        CURLOPT_SSL_VERIFYPEER => true,
    ]);

    $response = curl_exec($ch);

    if ($response === false) {
        $error = curl_error($ch);
        curl_close($ch);
        throw new Exception("cURL-Fehler: $error");
    }

    $httpCode = curl_getinfo($ch, CURLINFO_HTTP_CODE);
    curl_close($ch);

    // API gibt 202 Accepted zurueck!
    if ($httpCode !== 202) {
        $data = json_decode($response, true);
        $errorMsg = $data['error'] ?? $response;
        throw new Exception("API-Fehler ($httpCode): $errorMsg");
    }

    $data = json_decode($response, true);

    if (!isset($data['job_id'])) {
        throw new Exception("Keine Job-ID in Antwort");
    }

    return $data['job_id'];
}

/**
 * Fragt den Status eines Jobs ab.
 *
 * @param string $jobId Job-ID
 * @return array Job-Status und Ergebnis
 * @throws Exception Bei Fehlern
 */
function getJobStatus(string $jobId): array {
    $authToken = API_KEY . ':' . API_SECRET;

    $ch = curl_init();
    curl_setopt_array($ch, [
        CURLOPT_URL => API_BASE_URL . '/v1/jobs/' . urlencode($jobId),
        CURLOPT_HTTPHEADER => ["Authorization: Bearer $authToken"],
        CURLOPT_RETURNTRANSFER => true,
        CURLOPT_TIMEOUT => TIMEOUT_POLL,
        CURLOPT_SSL_VERIFYPEER => true,
    ]);

    $response = curl_exec($ch);

    if ($response === false) {
        $error = curl_error($ch);
        curl_close($ch);
        throw new Exception("cURL-Fehler: $error");
    }

    $httpCode = curl_getinfo($ch, CURLINFO_HTTP_CODE);
    curl_close($ch);

    if ($httpCode !== 200) {
        throw new Exception("Status-Abfrage fehlgeschlagen ($httpCode): $response");
    }

    $data = json_decode($response, true);

    if (json_last_error() !== JSON_ERROR_NONE) {
        throw new Exception("JSON-Fehler: " . json_last_error_msg());
    }

    return $data;
}

/**
 * Pollt den Job-Status bis zur Fertigstellung.
 *
 * @param string $jobId Job-ID
 * @return array Fertiges Ergebnis
 * @throws Exception Bei Timeout oder Fehler
 */
function pollJobStatus(string $jobId): array {
    $startTime = time();

    for ($attempt = 1; $attempt <= MAX_POLL_ATTEMPTS; $attempt++) {
        $elapsed = time() - $startTime;

        try {
            $status = getJobStatus($jobId);

            $state = $status['status'] ?? 'unknown';

            // Fortschritt anzeigen
            echo "\r   Status: $state (Versuch $attempt, {$elapsed}s)   ";

            if ($state === 'completed') {
                echo "\n";
                return $status;
            }

            if ($state === 'failed') {
                echo "\n";
                throw new Exception("Job fehlgeschlagen: " . ($status['error'] ?? 'Unbekannter Fehler'));
            }

            // Warten vor naechstem Poll
            sleep(POLL_INTERVAL);

        } catch (Exception $e) {
            // Bei Netzwerkfehlern weitermachen
            if ($attempt >= MAX_POLL_ATTEMPTS) {
                throw $e;
            }
            sleep(POLL_INTERVAL);
        }
    }

    throw new Exception("Timeout: Job nicht innerhalb von " . (MAX_POLL_ATTEMPTS * POLL_INTERVAL) . " Sekunden abgeschlossen");
}

/**
 * Analysiert ein Dokument (komplett mit Warten).
 *
 * @param string $filePath Pfad zur Datei
 * @param string|null $prompt Optionaler Prompt
 * @param string $model Modell-Auswahl
 * @param bool $wait Auf Ergebnis warten?
 * @return array|string Ergebnis oder Job-ID
 */
function analyzeDocument(string $filePath, ?string $prompt = null, string $model = 'german-ocr-ultra', bool $wait = true) {
    $fileName = basename($filePath);
    $modelInfo = MODELS[$model] ?? ['name' => $model, 'price' => '?'];

    echo "German-OCR API - Dokumentenanalyse\n";
    echo str_repeat('=', 50) . "\n";
    echo "Datei:  $fileName\n";
    echo "Modell: {$modelInfo['name']} ({$modelInfo['price']}/Seite)\n";
    if ($prompt) {
        echo "Prompt: $prompt\n";
    }
    echo str_repeat('-', 50) . "\n\n";

    // 1. Job senden
    echo "1. Sende Dokument...\n";
    $startTime = microtime(true);
    $jobId = submitJob($filePath, $prompt, $model);
    $submitTime = round((microtime(true) - $startTime) * 1000);
    echo "   Job-ID: $jobId\n";
    echo "   Gesendet in: {$submitTime}ms\n\n";

    if (!$wait) {
        echo "Fire-and-Forget Modus: Job laeuft im Hintergrund.\n";
        echo "Status abfragen mit: php simple_curl.php --status $jobId\n";
        return $jobId;
    }

    // 2. Auf Ergebnis warten
    echo "2. Warte auf Verarbeitung...\n";
    $result = pollJobStatus($jobId);
    $totalTime = round((microtime(true) - $startTime) * 1000);

    // 3. Ergebnis ausgeben
    echo "\n3. Ergebnis:\n";
    echo str_repeat('=', 50) . "\n";

    if (isset($result['result'])) {
        echo $result['result'] . "\n";
    }

    echo str_repeat('=', 50) . "\n\n";

    // Metadaten
    echo "Statistiken:\n";
    echo "   Modell:          " . ($result['model'] ?? 'N/A') . "\n";
    echo "   Gesamtzeit:      {$totalTime}ms\n";
    echo "   Verarbeitungszeit: " . ($result['processing_time_ms'] ?? 'N/A') . "ms\n";
    echo "   Tokens (in/out): " . ($result['tokens']['input'] ?? '?') . " / " . ($result['tokens']['output'] ?? '?') . "\n";
    echo "   Preis:           " . ($result['price_display'] ?? 'N/A') . "\n";

    if (isset($result['privacy'])) {
        echo "   Verarbeitung:    " . $result['privacy']['processing_location'] . "\n";
        echo "   DSGVO:           " . ($result['privacy']['gdpr_compliant'] ? 'Ja' : 'Nein') . "\n";
    }

    return $result;
}

/**
 * Hauptfunktion
 */
function main(): void {
    global $argv;

    // Hilfe anzeigen
    if (count($argv) < 2 || in_array($argv[1], ['-h', '--help'])) {
        echo "German-OCR API - PHP cURL Client\n";
        echo str_repeat('=', 50) . "\n\n";
        echo "Verwendung:\n";
        echo "  php simple_curl.php <datei> [prompt] [model]\n";
        echo "  php simple_curl.php <datei> --no-wait\n";
        echo "  php simple_curl.php --status <job_id>\n\n";
        echo "Modelle:\n";
        foreach (MODELS as $id => $info) {
            echo "  $id - {$info['name']} ({$info['price']}/Seite)\n";
        }
        echo "\nBeispiele:\n";
        echo "  php simple_curl.php rechnung.pdf\n";
        echo "  php simple_curl.php rechnung.jpg \"Extrahiere Rechnungsnummer\"\n";
        echo "  php simple_curl.php scan.pdf \"\" german-ocr-ultra\n";
        echo "  php simple_curl.php dokument.pdf --no-wait\n";
        exit(0);
    }

    // Status-Abfrage
    if ($argv[1] === '--status' && isset($argv[2])) {
        $jobId = $argv[2];
        echo "Status fuer Job: $jobId\n\n";
        try {
            $status = getJobStatus($jobId);
            echo json_encode($status, JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE) . "\n";
            exit($status['status'] === 'completed' ? 0 : 1);
        } catch (Exception $e) {
            echo "Fehler: " . $e->getMessage() . "\n";
            exit(1);
        }
    }

    // Dokument analysieren
    $filePath = $argv[1];
    $noWait = in_array('--no-wait', $argv);

    // Argumente parsen (ohne --no-wait)
    $args = array_values(array_filter($argv, fn($a) => $a !== '--no-wait'));
    $prompt = isset($args[2]) && $args[2] !== '' ? $args[2] : null;
    $model = $args[3] ?? 'german-ocr-ultra';

    try {
        $result = analyzeDocument($filePath, $prompt, $model, !$noWait);
        echo "\nFertig!\n";
        exit(0);
    } catch (Exception $e) {
        echo "\nFehler: " . $e->getMessage() . "\n";
        exit(1);
    }
}

// Ausfuehren
if (php_sapi_name() === 'cli') {
    main();
}
