# German-OCR PHP SDK

High-performance German document OCR - Local & Cloud API

[![Packagist Version](https://img.shields.io/packagist/v/keyvan/german-ocr)](https://packagist.org/packages/keyvan/german-ocr)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![PHP Version](https://img.shields.io/badge/php-%3E%3D7.4-blue)](https://php.net)

## Installation

```bash
composer require keyvan/german-ocr
```

## Quick Start

Get your API credentials at [app.german-ocr.de](https://app.german-ocr.de)

```php
<?php

require_once 'vendor/autoload.php';

use GermanOCR\GermanOCR;

// Initialize client
$client = new GermanOCR('gocr_xxxxxxxx', 'your_64_char_secret');

// Analyze a document
$result = $client->analyze('invoice.pdf');
echo $result['text'];
```

## Models

| Model | Constant | Description |
|-------|----------|-------------|
| `german-ocr-ultra` | `GermanOCR::MODEL_ULTRA` | Maximum precision |
| `german-ocr-pro` | `GermanOCR::MODEL_PRO` | Fast and reliable (default) |
| `german-ocr` | `GermanOCR::MODEL_TURBO` | GDPR-compliant, local |
| `privacy-shield` | `GermanOCR::MODEL_PRIVACY` | PII redaction |

## Usage Examples

### Simple Extraction

```php
$result = $client->analyze('invoice.pdf');
echo $result['text'];
```

### With Custom Prompt

```php
$result = $client->analyze('invoice.pdf', [
    'prompt' => 'Extract invoice number and total amount as JSON',
    'model' => GermanOCR::MODEL_ULTRA
]);

$data = json_decode($result['text'], true);
echo "Invoice: " . $data['invoice_number'];
```

### From Raw Data (Uploads)

```php
// For file uploads
$data = file_get_contents($_FILES['document']['tmp_name']);
$filename = $_FILES['document']['name'];

$result = $client->analyzeData($data, $filename, [
    'model' => GermanOCR::MODEL_PRO
]);
```

### Response Handling

```php
$result = $client->analyze('invoice.pdf');

if (GermanOCR::isAnalyzeResult($result)) {
    // Direct result
    echo $result['text'];
    echo "Processed in: " . $result['processing_time_ms'] . "ms";
} elseif (GermanOCR::isJobResult($result)) {
    // Async job
    echo "Job started: " . $result['job_id'];
    echo "Status: " . $result['status'];
}
```

## Error Handling

```php
use GermanOCR\GermanOCR;
use GermanOCR\GermanOCRException;

try {
    $result = $client->analyze('invoice.pdf');
} catch (GermanOCRException $e) {
    echo "API Error: " . $e->getMessage();
    echo "Status Code: " . $e->getCode();
} catch (\InvalidArgumentException $e) {
    echo "Invalid input: " . $e->getMessage();
}
```

## Configuration

```php
$client = new GermanOCR('gocr_xxx', 'secret', [
    'endpoint' => 'https://api.german-ocr.de',  // Custom endpoint
    'timeout' => 120                             // Timeout in seconds
]);
```

## Environment Variables

For production, use environment variables:

```php
$client = new GermanOCR(
    getenv('GERMAN_OCR_API_KEY'),
    getenv('GERMAN_OCR_API_SECRET')
);
```

## Laravel Integration

Create a service provider:

```php
// app/Providers/GermanOCRServiceProvider.php
namespace App\Providers;

use GermanOCR\GermanOCR;
use Illuminate\Support\ServiceProvider;

class GermanOCRServiceProvider extends ServiceProvider
{
    public function register()
    {
        $this->app->singleton(GermanOCR::class, function ($app) {
            return new GermanOCR(
                config('services.german_ocr.key'),
                config('services.german_ocr.secret')
            );
        });
    }
}
```

Usage in controllers:

```php
use GermanOCR\GermanOCR;

class InvoiceController extends Controller
{
    public function process(Request $request, GermanOCR $ocr)
    {
        $result = $ocr->analyze($request->file('invoice')->path());
        return response()->json($result);
    }
}
```

## License

Apache 2.0 - See [LICENSE](LICENSE)

## Links

- [Documentation](https://german-ocr.de/docs)
- [API Portal](https://app.german-ocr.de)
- [GitHub](https://github.com/Keyvanhardani/german-ocr)
