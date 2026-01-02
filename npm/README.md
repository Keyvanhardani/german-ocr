# German-OCR

High-performance German document OCR - Local & Cloud API

[![npm version](https://badge.fury.io/js/german-ocr.svg)](https://www.npmjs.com/package/german-ocr)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)

## Installation

```bash
npm install german-ocr
```

## Quick Start

Get your API credentials at [app.german-ocr.de](https://app.german-ocr.de)

```javascript
const { GermanOCR } = require('german-ocr');

// Initialize client
const client = new GermanOCR('gocr_xxxxxxxx', 'your_64_char_secret');

// Analyze a document
const result = await client.analyze('invoice.pdf');
console.log(result.text);
```

## TypeScript Support

Full TypeScript support with type definitions included:

```typescript
import { GermanOCR, Model, AnalyzeResult } from 'german-ocr';

const client = new GermanOCR('gocr_xxx', 'secret');

// With custom prompt and model
const result = await client.analyze('invoice.pdf', {
  prompt: 'Extract invoice number and total as JSON',
  model: 'german-ocr-ultra'
});
```

## Models

| Model | Description | Speed | Quality |
|-------|-------------|-------|---------|
| `german-ocr-ultra` | Maximum precision for complex documents | ⚡⚡ | ⭐⭐⭐ |
| `german-ocr-pro` | Fast and reliable (default) | ⚡⚡⚡ | ⭐⭐ |
| `german-ocr` | GDPR-compliant, local processing | ⚡ | ⭐⭐ |
| `privacy-shield` | PII redaction before processing | ⚡⚡ | ⭐⭐⭐ |

## API Reference

### Constructor

```typescript
new GermanOCR(apiKey: string, apiSecret: string, options?: ClientOptions)
```

**Options:**
- `endpoint`: API endpoint (default: `https://api.german-ocr.de`)
- `timeout`: Request timeout in ms (default: `60000`)

### analyze(filePath, options?)

Analyze a document file.

```typescript
const result = await client.analyze('document.pdf', {
  prompt: 'Extract all text',      // Optional custom prompt
  model: 'german-ocr-pro'          // Optional model selection
});
```

### analyzeBuffer(buffer, filename, options?)

Analyze a document from a Buffer (useful for streams/uploads).

```typescript
const buffer = fs.readFileSync('document.pdf');
const result = await client.analyzeBuffer(buffer, 'document.pdf');
```

## Response Types

The API can return two types of responses:

### Direct Result (HTTP 200)
```typescript
interface AnalyzeResult {
  text: string;
  model_used: string;
  processing_time_ms: number;
}
```

### Async Job (HTTP 202)
```typescript
interface JobResult {
  job_id: string;
  model: string;
  status: 'pending' | 'processing' | 'completed' | 'failed';
}
```

Use helper methods to check response type:
```typescript
if (GermanOCR.isAnalyzeResult(result)) {
  console.log(result.text);
} else if (GermanOCR.isJobResult(result)) {
  console.log('Job started:', result.job_id);
}
```

## Error Handling

```typescript
try {
  const result = await client.analyze('invoice.pdf');
} catch (error) {
  if (error.message.includes('API Error (401)')) {
    console.error('Invalid credentials');
  } else if (error.message.includes('timeout')) {
    console.error('Request timed out');
  } else {
    console.error('Error:', error.message);
  }
}
```

## Environment Variables

For production, use environment variables:

```javascript
const client = new GermanOCR(
  process.env.GERMAN_OCR_API_KEY,
  process.env.GERMAN_OCR_API_SECRET
);
```

## License

Apache 2.0 - See [LICENSE](LICENSE)

## Links

- [Documentation](https://german-ocr.de/docs)
- [API Portal](https://app.german-ocr.de)
- [GitHub](https://github.com/Keyvanhardani/german-ocr)
