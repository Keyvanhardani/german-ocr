<?php
/**
 * German-OCR API - Einfaches PHP Beispiel (cURL)
 *
 * Dieses Skript zeigt, wie man ein einzelnes Dokument
 * mit nativem PHP cURL an die German-OCR API sendet.
 *
 * Voraussetzungen:
 *   - PHP 7.4+ mit cURL-Extension
 *
 * Verwendung:
 *   php simple_curl.php <bildpfad> [prompt] [model]
 */

// API-Konfiguration
define('API_ENDPOINT', 'https://api.german-ocr.de/v1/analyze');
define('API_KEY', getenv('GERMAN_OCR_API_KEY') ?: 'YOUR_API_KEY');
define('API_SECRET', getenv('GERMAN_OCR_API_SECRET') ?: 'YOUR_API_SECRET');

/**
 * Analysiert ein Dokument mit der German-OCR API
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
        CURLOPT_TIMEOUT => 60,
        CURLOPT_SSL_VERIFYPEER => true,
        CURLOPT_FOLLOWLOCATION => true
    ]);

    // Request senden und Zeit messen
    $startTime = microtime(true);
    $response = curl_exec($ch);
    $responseTime = round((microtime(true) - $startTime) * 1000);

    // Fehlerbehandlung
    if ($response === false) {
        $error = curl_error($ch);
        $errno = curl_errno($ch);
        curl_close($ch);
        throw new Exception("cURL-Fehler ($errno): $error");
    }

    $httpCode = curl_getinfo($ch, CURLINFO_HTTP_CODE);
    curl_close($ch);

    if ($httpCode !== 200) {
        throw new Exception("API-Fehler ($httpCode): $response");
    }

    // JSON dekodieren
    $result = json_decode($response, true);

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
}

/**
 * Hauptfunktion
 */
function main() {
    global $argv;

    // Kommandozeilenargumente prüfen
    if (count($argv) < 2) {
        echo "❌ Fehler: Kein Bildpfad angegeben\n";
        echo "\n";
        echo "Verwendung:\n";
        echo "  php simple_curl.php <bildpfad> [prompt] [model]\n";
        echo "\n";
        echo "Beispiele:\n";
        echo "  php simple_curl.php rechnung.jpg\n";
        echo "  php simple_curl.php rechnung.pdf \"Extrahiere Rechnungsnummer und Datum\"\n";
        echo "  php simple_curl.php rechnung.jpg \"\" german-ocr-ultra\n";
        echo "\n";
        echo "Modell-Optionen:\n";
        echo "  german-ocr-ultra  - Maximale Präzision\n";
        echo "  german-ocr-pro    - Schnell und zuverlässig (Standard)\n";
        echo "  german-ocr        - DSGVO-konform, lokale Verarbeitung\n";
        exit(1);
    }

    $filePath = $argv[1];
    $prompt = isset($argv[2]) && $argv[2] !== '' ? $argv[2] : null;
    $model = isset($argv[3]) ? $argv[3] : 'german-ocr-pro';

    try {
        analyzeDocument($filePath, $prompt, $model);
        echo "\n";
        echo "✨ Fertig!\n";
        exit(0);

    } catch (Exception $e) {
        echo "\n";
        echo "💥 Fehler: " . $e->getMessage() . "\n";
        exit(1);
    }
}

// Nur ausführen wenn direkt aufgerufen
if (php_sapi_name() === 'cli' && isset($argv[0]) && basename($argv[0]) === basename(__FILE__)) {
    main();
}
