<?php
/**
 * German-OCR API - Guzzle HTTP Client Beispiel (Async Job-Based)
 *
 * Dieses Skript zeigt, wie man die German-OCR API mit Guzzle verwendet.
 * Die API ist asynchron (Job-basiert):
 *
 * 1. POST /v1/analyze -> 202 + job_id (sofort)
 * 2. GET /v1/jobs/{id} -> polling bis status=completed
 *
 * Installation:
 *   composer require guzzlehttp/guzzle
 *
 * Verwendung:
 *   php guzzle_demo.php <bildpfad> [prompt] [model]
 *   php guzzle_demo.php <bildpfad> --no-wait
 *   php guzzle_demo.php --status <job_id>
 *   php guzzle_demo.php <datei1> <datei2> ... (Batch)
 *
 * Modelle: german-ocr-turbo, german-ocr-pro (Standard), german-ocr-ultra
 */

require_once __DIR__ . '/vendor/autoload.php';

use GuzzleHttp\Client;
use GuzzleHttp\Exception\RequestException;
use GuzzleHttp\Exception\ConnectException;
use GuzzleHttp\Promise;

// === KONFIGURATION ===
define('API_BASE_URL', 'https://api.german-ocr.de');
define('API_KEY', getenv('GERMAN_OCR_API_KEY') ?: 'YOUR_API_KEY');
define('API_SECRET', getenv('GERMAN_OCR_API_SECRET') ?: 'YOUR_API_SECRET');

// Timeouts
define('TIMEOUT_SUBMIT', 30);      // Sekunden fuer Job-Submission
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
 * Erstellt einen konfigurierten Guzzle Client.
 */
function createClient(int $timeout = TIMEOUT_SUBMIT): Client {
    $authToken = API_KEY . ':' . API_SECRET;

    return new Client([
        'base_uri' => API_BASE_URL,
        'timeout' => $timeout,
        'verify' => true,
        'http_errors' => false,
        'headers' => [
            'Authorization' => "Bearer $authToken",
        ],
    ]);
}

/**
 * Sendet ein Dokument an die API und gibt die Job-ID zurueck.
 */
function submitJob(string $filePath, ?string $prompt = null, string $model = 'german-ocr-ultra'): string {
    if (!file_exists($filePath)) {
        throw new Exception("Datei nicht gefunden: $filePath");
    }

    $client = createClient(TIMEOUT_SUBMIT);
    $fileName = basename($filePath);

    $multipart = [
        [
            'name' => 'file',
            'contents' => fopen($filePath, 'r'),
            'filename' => $fileName,
        ],
        [
            'name' => 'model',
            'contents' => $model,
        ],
    ];

    if ($prompt) {
        $multipart[] = [
            'name' => 'prompt',
            'contents' => $prompt,
        ];
    }

    $response = $client->post('/v1/analyze', [
        'multipart' => $multipart,
    ]);

    $statusCode = $response->getStatusCode();
    $body = (string) $response->getBody();

    // API gibt 202 Accepted zurueck!
    if ($statusCode !== 202) {
        $data = json_decode($body, true);
        $errorMsg = $data['error'] ?? $body;
        throw new Exception("API-Fehler ($statusCode): $errorMsg");
    }

    $data = json_decode($body, true);

    if (!isset($data['job_id'])) {
        throw new Exception("Keine Job-ID in Antwort");
    }

    return $data['job_id'];
}

/**
 * Fragt den Status eines Jobs ab.
 */
function getJobStatus(string $jobId): array {
    $client = createClient(TIMEOUT_POLL);

    $response = $client->get('/v1/jobs/' . urlencode($jobId));

    $statusCode = $response->getStatusCode();
    $body = (string) $response->getBody();

    if ($statusCode !== 200) {
        throw new Exception("Status-Abfrage fehlgeschlagen ($statusCode): $body");
    }

    $data = json_decode($body, true);

    if (json_last_error() !== JSON_ERROR_NONE) {
        throw new Exception("JSON-Fehler: " . json_last_error_msg());
    }

    return $data;
}

/**
 * Pollt den Job-Status bis zur Fertigstellung.
 */
function pollJobStatus(string $jobId): array {
    $startTime = time();

    for ($attempt = 1; $attempt <= MAX_POLL_ATTEMPTS; $attempt++) {
        $elapsed = time() - $startTime;

        try {
            $status = getJobStatus($jobId);
            $state = $status['status'] ?? 'unknown';

            echo "\r   Status: $state (Versuch $attempt, {$elapsed}s)   ";

            if ($state === 'completed') {
                echo "\n";
                return $status;
            }

            if ($state === 'failed') {
                echo "\n";
                throw new Exception("Job fehlgeschlagen: " . ($status['error'] ?? 'Unbekannter Fehler'));
            }

            sleep(POLL_INTERVAL);

        } catch (Exception $e) {
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
 */
function analyzeDocument(string $filePath, ?string $prompt = null, string $model = 'german-ocr-ultra', bool $wait = true) {
    $fileName = basename($filePath);
    $modelInfo = MODELS[$model] ?? ['name' => $model, 'price' => '?'];

    echo "German-OCR API - Dokumentenanalyse (Guzzle)\n";
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
        echo "Status abfragen mit: php guzzle_demo.php --status $jobId\n";
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
    echo "   Modell:            " . ($result['model'] ?? 'N/A') . "\n";
    echo "   Gesamtzeit:        {$totalTime}ms\n";
    echo "   Verarbeitungszeit: " . ($result['processing_time_ms'] ?? 'N/A') . "ms\n";
    echo "   Tokens (in/out):   " . ($result['tokens']['input'] ?? '?') . " / " . ($result['tokens']['output'] ?? '?') . "\n";
    echo "   Preis:             " . ($result['price_display'] ?? 'N/A') . "\n";

    if (isset($result['privacy'])) {
        echo "   Verarbeitung:      " . $result['privacy']['processing_location'] . "\n";
        echo "   DSGVO:             " . ($result['privacy']['gdpr_compliant'] ? 'Ja' : 'Nein') . "\n";
    }

    return $result;
}

/**
 * Batch-Verarbeitung mit parallelem Job-Submission.
 */
function processBatch(array $filePaths, string $model = 'german-ocr-ultra'): array {
    echo "German-OCR API - Batch-Verarbeitung (Guzzle Async)\n";
    echo str_repeat('=', 60) . "\n";
    echo "Dokumente: " . count($filePaths) . "\n";
    echo "Modell:    " . (MODELS[$model]['name'] ?? $model) . "\n";
    echo str_repeat('-', 60) . "\n\n";

    $client = createClient(TIMEOUT_SUBMIT);
    $startTime = microtime(true);

    // 1. Alle Jobs parallel einreichen
    echo "1. Sende alle Dokumente...\n";
    $promises = [];
    $jobMap = [];

    foreach ($filePaths as $index => $filePath) {
        if (!file_exists($filePath)) {
            echo "   [$index] SKIP: Datei nicht gefunden: $filePath\n";
            continue;
        }

        $fileName = basename($filePath);

        $multipart = [
            ['name' => 'file', 'contents' => fopen($filePath, 'r'), 'filename' => $fileName],
            ['name' => 'model', 'contents' => $model],
        ];

        $promises[$index] = $client->postAsync('/v1/analyze', [
            'multipart' => $multipart,
        ]);

        $jobMap[$index] = $filePath;
    }

    // Warten auf alle Submissions
    $results = Promise\Utils::settle($promises)->wait();
    $submitTime = round((microtime(true) - $startTime) * 1000);

    // Job-IDs extrahieren
    $jobs = [];
    foreach ($results as $index => $result) {
        $fileName = basename($jobMap[$index]);

        if ($result['state'] === 'fulfilled') {
            $response = $result['value'];
            if ($response->getStatusCode() === 202) {
                $data = json_decode($response->getBody(), true);
                $jobId = $data['job_id'] ?? null;
                if ($jobId) {
                    $jobs[$index] = ['job_id' => $jobId, 'file' => $fileName, 'status' => 'pending'];
                    echo "   [$index] $fileName -> Job: $jobId\n";
                }
            } else {
                echo "   [$index] $fileName -> FEHLER (HTTP {$response->getStatusCode()})\n";
            }
        } else {
            echo "   [$index] $fileName -> FEHLER: {$result['reason']->getMessage()}\n";
        }
    }

    echo "\n   Alle Jobs gesendet in: {$submitTime}ms\n\n";

    // 2. Alle Jobs pollen bis fertig
    echo "2. Warte auf Verarbeitung...\n";
    $pendingJobs = $jobs;
    $completedJobs = [];
    $pollClient = createClient(TIMEOUT_POLL);

    for ($round = 1; $round <= MAX_POLL_ATTEMPTS && !empty($pendingJobs); $round++) {
        $elapsed = round(microtime(true) - $startTime);
        $pending = count($pendingJobs);
        $completed = count($completedJobs);
        echo "\r   Runde $round: $completed fertig, $pending ausstehend ({$elapsed}s)   ";

        // Parallel pollen
        $pollPromises = [];
        foreach ($pendingJobs as $index => $job) {
            $pollPromises[$index] = $pollClient->getAsync('/v1/jobs/' . urlencode($job['job_id']));
        }

        $pollResults = Promise\Utils::settle($pollPromises)->wait();

        foreach ($pollResults as $index => $result) {
            if ($result['state'] === 'fulfilled') {
                $response = $result['value'];
                if ($response->getStatusCode() === 200) {
                    $data = json_decode($response->getBody(), true);
                    $status = $data['status'] ?? 'unknown';

                    if ($status === 'completed' || $status === 'failed') {
                        $completedJobs[$index] = array_merge($pendingJobs[$index], $data);
                        unset($pendingJobs[$index]);
                    }
                }
            }
        }

        if (!empty($pendingJobs)) {
            sleep(POLL_INTERVAL);
        }
    }

    echo "\n\n";

    // 3. Ergebnisse ausgeben
    echo "3. Ergebnisse:\n";
    echo str_repeat('=', 60) . "\n";

    $successful = 0;
    $failed = 0;

    foreach ($completedJobs as $index => $job) {
        $status = $job['status'] ?? 'unknown';
        $file = $job['file'];

        if ($status === 'completed') {
            $successful++;
            $preview = substr($job['result'] ?? '', 0, 50);
            $preview = str_replace("\n", ' ', $preview);
            echo "[$index] $file\n";
            echo "       Text: $preview...\n";
        } else {
            $failed++;
            echo "[$index] $file -> FEHLER: " . ($job['error'] ?? 'Unbekannt') . "\n";
        }
    }

    // Nicht fertig gewordene Jobs
    foreach ($pendingJobs as $index => $job) {
        $failed++;
        echo "[$index] {$job['file']} -> TIMEOUT\n";
    }

    echo str_repeat('=', 60) . "\n\n";

    $totalTime = round((microtime(true) - $startTime) * 1000);

    echo "Statistiken:\n";
    echo "   Gesamt:         " . count($filePaths) . " Dokumente\n";
    echo "   Erfolgreich:    $successful\n";
    echo "   Fehlgeschlagen: $failed\n";
    echo "   Gesamtzeit:     {$totalTime}ms\n";

    if ($successful > 0) {
        echo "   Durchsatz:      " . round($successful / ($totalTime / 1000), 2) . " Dok/s\n";
    }

    return [
        'total' => count($filePaths),
        'successful' => $successful,
        'failed' => $failed,
        'total_time_ms' => $totalTime,
        'jobs' => $completedJobs,
    ];
}

/**
 * Hauptfunktion
 */
function main(): void {
    global $argv;

    // Pruefe Guzzle
    if (!class_exists('GuzzleHttp\Client')) {
        echo "Fehler: Guzzle nicht installiert.\n";
        echo "Bitte ausfuehren: composer require guzzlehttp/guzzle\n";
        exit(1);
    }

    // Hilfe anzeigen
    if (count($argv) < 2 || in_array($argv[1], ['-h', '--help'])) {
        echo "German-OCR API - Guzzle HTTP Client\n";
        echo str_repeat('=', 50) . "\n\n";
        echo "Verwendung:\n";
        echo "  php guzzle_demo.php <datei> [prompt] [model]\n";
        echo "  php guzzle_demo.php <datei> --no-wait\n";
        echo "  php guzzle_demo.php --status <job_id>\n";
        echo "  php guzzle_demo.php <datei1> <datei2> ... (Batch)\n\n";
        echo "Modelle:\n";
        foreach (MODELS as $id => $info) {
            echo "  $id - {$info['name']} ({$info['price']}/Seite)\n";
        }
        echo "\nBeispiele:\n";
        echo "  php guzzle_demo.php rechnung.pdf\n";
        echo "  php guzzle_demo.php rechnung.jpg \"Extrahiere Rechnungsnummer\"\n";
        echo "  php guzzle_demo.php doc1.pdf doc2.pdf doc3.pdf (Batch)\n";
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

    try {
        $noWait = in_array('--no-wait', $argv);
        $args = array_values(array_filter($argv, fn($a) => $a !== '--no-wait' && $a !== $argv[0]));

        // Batch-Modus: Mehrere Dateien
        if (count($args) > 1 && file_exists($args[1] ?? '')) {
            $allFiles = true;
            foreach ($args as $arg) {
                if (!file_exists($arg)) {
                    $allFiles = false;
                    break;
                }
            }

            if ($allFiles) {
                $stats = processBatch($args);
                echo "\nBatch " . ($stats['failed'] > 0 ? "mit Fehlern" : "erfolgreich") . " abgeschlossen!\n";
                exit($stats['failed'] > 0 ? 1 : 0);
            }
        }

        // Einzelner Request
        $filePath = $args[0];
        $prompt = isset($args[1]) && $args[1] !== '' ? $args[1] : null;
        $model = $args[2] ?? 'german-ocr-ultra';

        analyzeDocument($filePath, $prompt, $model, !$noWait);
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
