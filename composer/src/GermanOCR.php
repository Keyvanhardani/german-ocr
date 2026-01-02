<?php

declare(strict_types=1);

namespace GermanOCR;

use GuzzleHttp\Client;
use GuzzleHttp\Exception\GuzzleException;
use GuzzleHttp\Exception\RequestException;

/**
 * German-OCR Cloud Client
 *
 * High-performance German document OCR - Local & Cloud API
 *
 * @package GermanOCR
 * @author Keyvan.ai
 * @license Apache-2.0
 *
 * @example
 * ```php
 * use GermanOCR\GermanOCR;
 *
 * $client = new GermanOCR('gocr_xxx', 'your_secret');
 * $result = $client->analyze('invoice.pdf');
 * echo $result['text'];
 * ```
 */
class GermanOCR
{
    private string $apiKey;
    private string $apiSecret;
    private string $endpoint;
    private int $timeout;
    private Client $client;

    /**
     * Available OCR models
     */
    public const MODEL_TURBO = 'german-ocr';
    public const MODEL_PRO = 'german-ocr-pro';
    public const MODEL_ULTRA = 'german-ocr-ultra';
    public const MODEL_PRIVACY = 'privacy-shield';

    /**
     * Create a new German-OCR client
     *
     * @param string $apiKey Your API key (starts with gocr_)
     * @param string $apiSecret Your API secret (64 characters)
     * @param array $options Client options
     *   - endpoint: API endpoint (default: https://api.german-ocr.de)
     *   - timeout: Request timeout in seconds (default: 60)
     *
     * @throws \InvalidArgumentException If credentials are invalid
     */
    public function __construct(string $apiKey, string $apiSecret, array $options = [])
    {
        if (empty($apiKey) || strpos($apiKey, 'gocr_') !== 0) {
            throw new \InvalidArgumentException('Invalid API key. Must start with "gocr_"');
        }
        if (empty($apiSecret) || strlen($apiSecret) < 32) {
            throw new \InvalidArgumentException('Invalid API secret');
        }

        $this->apiKey = $apiKey;
        $this->apiSecret = $apiSecret;
        $this->endpoint = $options['endpoint'] ?? 'https://api.german-ocr.de';
        $this->timeout = $options['timeout'] ?? 60;

        $this->client = new Client([
            'base_uri' => $this->endpoint,
            'timeout' => $this->timeout,
            'verify' => true,
            'http_errors' => false
        ]);
    }

    /**
     * Analyze a document
     *
     * @param string $filePath Path to the document (PDF, JPG, PNG)
     * @param array $options Analysis options
     *   - prompt: Custom prompt for structured extraction
     *   - model: OCR model (default: german-ocr-pro)
     *
     * @return array API response
     *   For direct result: ['text' => '...', 'model_used' => '...', 'processing_time_ms' => ...]
     *   For async job: ['job_id' => '...', 'model' => '...', 'status' => '...']
     *
     * @throws \InvalidArgumentException If file not found
     * @throws GermanOCRException On API errors
     *
     * @example
     * ```php
     * // Simple extraction
     * $result = $client->analyze('invoice.pdf');
     *
     * // With custom prompt
     * $result = $client->analyze('invoice.pdf', [
     *     'prompt' => 'Extract invoice number and total as JSON',
     *     'model' => GermanOCR::MODEL_ULTRA
     * ]);
     * ```
     */
    public function analyze(string $filePath, array $options = []): array
    {
        $absolutePath = realpath($filePath);

        if ($absolutePath === false || !file_exists($absolutePath)) {
            throw new \InvalidArgumentException("File not found: $filePath");
        }

        $multipart = [
            [
                'name' => 'file',
                'contents' => fopen($absolutePath, 'r'),
                'filename' => basename($absolutePath)
            ],
            [
                'name' => 'model',
                'contents' => $options['model'] ?? self::MODEL_PRO
            ]
        ];

        if (!empty($options['prompt'])) {
            $multipart[] = [
                'name' => 'prompt',
                'contents' => $options['prompt']
            ];
        }

        return $this->sendRequest($multipart);
    }

    /**
     * Analyze a document from raw data
     *
     * @param string $data Raw file data
     * @param string $filename Original filename (for MIME type detection)
     * @param array $options Analysis options
     *
     * @return array API response
     *
     * @throws GermanOCRException On API errors
     */
    public function analyzeData(string $data, string $filename, array $options = []): array
    {
        $multipart = [
            [
                'name' => 'file',
                'contents' => $data,
                'filename' => $filename
            ],
            [
                'name' => 'model',
                'contents' => $options['model'] ?? self::MODEL_PRO
            ]
        ];

        if (!empty($options['prompt'])) {
            $multipart[] = [
                'name' => 'prompt',
                'contents' => $options['prompt']
            ];
        }

        return $this->sendRequest($multipart);
    }

    /**
     * Send the API request
     *
     * @param array $multipart Multipart form data
     * @return array API response
     * @throws GermanOCRException On API errors
     */
    private function sendRequest(array $multipart): array
    {
        $authToken = $this->apiKey . ':' . $this->apiSecret;

        try {
            $response = $this->client->post('/v1/analyze', [
                'headers' => [
                    'Authorization' => "Bearer $authToken"
                ],
                'multipart' => $multipart
            ]);

            $statusCode = $response->getStatusCode();
            $body = (string) $response->getBody();

            // 200 = direct result, 202 = async job
            if ($statusCode !== 200 && $statusCode !== 202) {
                throw new GermanOCRException("API Error ($statusCode): $body", $statusCode);
            }

            $result = json_decode($body, true);

            if (json_last_error() !== JSON_ERROR_NONE) {
                throw new GermanOCRException("JSON decode error: " . json_last_error_msg());
            }

            return $result;

        } catch (RequestException $e) {
            $message = $e->getMessage();
            if ($e->hasResponse()) {
                $message = (string) $e->getResponse()->getBody();
            }
            throw new GermanOCRException("Request failed: $message", 0, $e);
        }
    }

    /**
     * Check if response is an async job
     *
     * @param array $response API response
     * @return bool
     */
    public static function isJobResult(array $response): bool
    {
        return isset($response['job_id']);
    }

    /**
     * Check if response is a direct result
     *
     * @param array $response API response
     * @return bool
     */
    public static function isAnalyzeResult(array $response): bool
    {
        return isset($response['text']);
    }
}
