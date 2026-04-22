<p align="center">
  <img src="docs/icon.png" alt="German-OCR Logo" width="150"/>
</p>

<h1 align="center">German-OCR</h1>

<p align="center">
  <strong>High-performance German document OCR - Local & Cloud</strong>
</p>

<p align="center">
  <a href="https://pypi.org/project/german-ocr/"><img src="https://badge.fury.io/py/german-ocr.svg" alt="PyPI version"></a>
  <a href="https://www.npmjs.com/package/german-ocr"><img src="https://badge.fury.io/js/german-ocr.svg" alt="npm version"></a>
  <a href="https://packagist.org/packages/keyvan/german-ocr"><img src="https://img.shields.io/packagist/v/keyvan/german-ocr" alt="Packagist"></a>
  <a href="https://opensource.org/licenses/Apache-2.0"><img src="https://img.shields.io/badge/License-Apache%202.0-blue.svg" alt="License"></a>
  <a href="https://app.german-ocr.de"><img src="https://img.shields.io/badge/Cloud-API-green" alt="Cloud API"></a>
</p>

<p align="center">
  <a href="https://huggingface.co/Keyven"><img src="https://img.shields.io/badge/🤗%20Hugging%20Face-Models-yellow" alt="Hugging Face"></a>
  <a href="https://ollama.com/Keyvan"><img src="https://img.shields.io/badge/🦙%20Ollama-Models-blue" alt="Ollama"></a>
  <img src="https://img.shields.io/badge/llama.cpp-GGUF-orange" alt="llama.cpp">
</p>

---

> ### 🆕 German-OCR-3 v0.2 — released April 2026
>
> Compact, local-first German document Vision-OCR on a fresh Qwen3.5 architecture. **Zero hallucination on 200+ anonymized German invoices**, 100 % valid JSON output, Apache 2.0.
>
> ```bash
> # Default edition (2.7 GB) — best quality, 4–6 GB VRAM
> ollama pull Keyvan/german-ocr-3
>
> # Edge edition (1.0 GB) — CPU / mobile / batch
> ollama pull Keyvan/german-ocr-nano
> ```
>
> 🤗 **Hugging Face (GGUF bundle)** · [Keyven/german-ocr-3](https://huggingface.co/Keyven/german-ocr-3)
> 🦙 **Ollama Hub** · [Keyvan/german-ocr-3](https://ollama.com/Keyvan/german-ocr-3) · [Keyvan/german-ocr-nano](https://ollama.com/Keyvan/german-ocr-nano)
> 🌐 **Hosted API (Premium · EU-hosted)** · [german-ocr.de](https://german-ocr.de)

---


## 🚀 Supported Backends

<p align="center">
  <a href="https://huggingface.co/Keyven">
    <img src="https://huggingface.co/front/assets/huggingface_logo-noborder.svg" alt="Hugging Face" width="50">
  </a>
  &nbsp;&nbsp;&nbsp;&nbsp;
  <a href="https://ollama.com/Keyvan">
    <img src="https://ollama.com/public/ollama.png" alt="Ollama" width="50">
  </a>
  &nbsp;&nbsp;&nbsp;&nbsp;
  <a href="https://github.com/ggerganov/llama.cpp">
    <img src="https://user-images.githubusercontent.com/1991296/230134379-7181e485-c521-4d23-a0d6-f7b3b61ba524.png" alt="llama.cpp" width="50">
  </a>
</p>

<p align="center">
  <strong>Hugging Face</strong> &nbsp;•&nbsp; <strong>Ollama</strong> &nbsp;•&nbsp; <strong>llama.cpp</strong>
</p>

---

## ✨ Features

| Feature | Local | Cloud (v1) | Cloud (v2) |
|---------|-------|------------|------------|
| **German Documents** | Invoices, contracts, forms | All document types | Structured extraction |
| **Output Formats** | Markdown, JSON, text | JSON, Markdown, text, n8n | Typed JSON fields |
| **PDF Support** | Images only | Up to 50 pages | Up to 50 pages |
| **Privacy** | 100% local | DSGVO-konform (Frankfurt) | DSGVO-konform (Frankfurt) |
| **Speed** | ~5s/page | ~2-3s/page (async) | Instant (synchronous) |
| **Backends** | Ollama, llama.cpp, HuggingFace | Cloud API | Cloud API |
| **Hardware** | CPU, GPU, NPU (CUDA/Metal/Vulkan/OpenVINO) | Managed | Managed |

## 📦 Installation

### Python
```bash
pip install german-ocr
```

### Node.js
```bash
npm install german-ocr
```

### PHP
```bash
composer require keyvan/german-ocr
```

---

## ⚡ Quick Start

### Option 1: ☁️ Cloud API (Recommended)

No GPU required. Get your API credentials at [app.german-ocr.de](https://app.german-ocr.de)

```python
from german_ocr import CloudClient

# API Key + Secret (Secret is only shown once at creation!)
client = CloudClient(
    api_key="gocr_xxxxxxxx",
    api_secret="your_64_char_secret_here"
)

# Simple extraction
result = client.analyze("invoice.pdf")
print(result.text)

# Structured JSON output
result = client.analyze(
    "invoice.pdf",
    prompt="Extrahiere Rechnungsnummer und Gesamtbetrag",
    output_format="json"
)
print(result.text)
```

### Node.js

```javascript
const { GermanOCR } = require('german-ocr');

const client = new GermanOCR(
    process.env.GERMAN_OCR_API_KEY,
    process.env.GERMAN_OCR_API_SECRET
);

const result = await client.analyze('invoice.pdf', {
    model: 'german-ocr-ultra'
});
console.log(result.text);
```

### PHP

```php
<?php
use GermanOCR\GermanOCR;

$client = new GermanOCR(
    getenv('GERMAN_OCR_API_KEY'),
    getenv('GERMAN_OCR_API_SECRET')
);

$result = $client->analyze('invoice.pdf', [
    'model' => GermanOCR::MODEL_ULTRA
]);
echo $result['text'];
```

### Option 2: 🦙 Local (Ollama)

Requires [Ollama](https://ollama.ai) installed.

```bash
# v0.2 (recommended — new default)
ollama pull Keyvan/german-ocr-3
# or edge / CPU edition
ollama pull Keyvan/german-ocr-nano
# legacy (v1, still works — auto-upgrades to v0.2 content)
ollama pull Keyvan/german-ocr
```

```python
from german_ocr import GermanOCR

ocr = GermanOCR()
text = ocr.extract("invoice.png")
print(text)
```

### Option 3: 🔧 Local (llama.cpp)

For maximum control and edge deployment with GGUF models.

```bash
# Install with GPU support (CUDA)
CMAKE_ARGS="-DGGML_CUDA=on" pip install german-ocr[llamacpp]

# Or CPU only
pip install german-ocr[llamacpp]
```

```python
from german_ocr import GermanOCR

# Auto-detect best device (GPU/CPU)
ocr = GermanOCR(backend="llamacpp")
text = ocr.extract("invoice.png")

# Force CPU only
ocr = GermanOCR(backend="llamacpp", n_gpu_layers=0)

# Full GPU acceleration
ocr = GermanOCR(backend="llamacpp", n_gpu_layers=-1)
```

## ☁️ Cloud Models

| Model | Parameter | Best For |
|-------|-----------|----------|
| **German-OCR Ultra** | `german-ocr-ultra` | Maximale Präzision, Strukturerkennung |
| **German-OCR Pro** | `german-ocr-pro` | Balance aus Speed & Qualität |
| **German-OCR Turbo** | `german-ocr` | DSGVO-konform, lokale Verarbeitung in DE |
| **Privacy Shield** | `privacy-shield` | PII-Erkennung & Anonymisierung |

### Model Selection

```python
from german_ocr import CloudClient

client = CloudClient(
    api_key="gocr_xxxxxxxx",
    api_secret="your_64_char_secret_here"
)

# German-OCR Ultra - Maximale Präzision
result = client.analyze("dokument.pdf", model="german-ocr-ultra")

# German-OCR Pro - Schnelle Cloud (Standard)
result = client.analyze("dokument.pdf", model="german-ocr-pro")

# German-OCR Turbo - Lokal, DSGVO-konform
result = client.analyze("dokument.pdf", model="german-ocr")

# Privacy Shield - PII detection & anonymization
result = client.analyze("dokument.pdf", model="privacy-shield")
```

---

## 🆕 German-OCR v2 — Premium Structured Extraction

v2 is a **synchronous** premium API that returns structured JSON instantly — no job polling needed.

**Base URL:** `https://api.german-ocr.de/v2/analyze` &nbsp;|&nbsp; **Price:** €0.10/page

### v2 Templates

| Template | Use Case | Key Fields |
|----------|----------|------------|
| `general` | Auto-detect document type | `document_type`, `sender`, `amounts`, `iban`, `full_text` |
| `invoice` | German invoices | `rechnungssteller`, `rechnungsnummer`, `positionen`, `gesamtbetrag`, `iban` |
| `delivery-notes` | Delivery notes | `belegnummer`, `belegdatum`, `empfaenger`, `positionen` |
| `document-intelligence` | Bounding box extraction | Field coordinates for visual annotation |

### v2 Quick Start (Python)

```python
import httpx

response = httpx.post(
    "https://api.german-ocr.de/v2/analyze",
    headers={"Authorization": f"Bearer {api_key}:{api_secret}"},
    files={"file": open("invoice.pdf", "rb")},
    data={"template": "invoice"}
)
result = response.json()
print(result["result"]["rechnungsnummer"])  # "2024-001"
print(result["result"]["gesamtbetrag"])     # "1.499,99"
```

> **Note:** v2 uses `template` (not `model`!) as the parameter name.

---

## 💻 CLI Usage

### Cloud

```bash
# Set API credentials (Secret shown only once at creation!)
export GERMAN_OCR_API_KEY="gocr_xxxxxxxx"
export GERMAN_OCR_API_SECRET="your_64_char_secret_here"

# Extract text (uses German-OCR Pro by default)
german-ocr --cloud invoice.pdf

# Use German-OCR Turbo (DSGVO-konform, lokal)
german-ocr --cloud --model german-ocr invoice.pdf

# JSON output with German-OCR Ultra
german-ocr --cloud --model german-ocr-ultra --output-format json invoice.pdf

# With custom prompt
german-ocr --cloud --prompt "Extrahiere alle Betraege" invoice.pdf
```

### Local

```bash
# Single image
german-ocr invoice.png

# Batch processing
german-ocr --batch ./invoices/

# JSON output
german-ocr --format json invoice.png
```

## 🔌 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/v1/analyze` | POST | OCR analysis (async, needs polling) |
| `/v1/jobs/{id}` | GET | Job status + result |
| `/v1/jobs/{id}` | DELETE | Cancel job |
| `/v1/models` | GET | List available models |
| `/v1/balance` | GET | Account balance |
| `/v1/usage` | GET | Usage statistics |
| `/v2/analyze` | POST | Premium analysis (sync, instant) |
| `/v2/models` | GET | List v2 templates |

> Full API documentation: [german-ocr.de/docs](https://german-ocr.de/docs)

### Output Formats

| Format | Description |
|--------|-------------|
| `text` | Plain text (default) |
| `json` | Structured JSON |
| `markdown` | Formatted Markdown |
| `n8n` | n8n-compatible format |

### Progress Tracking

```python
from german_ocr import CloudClient

client = CloudClient(
    api_key="gocr_xxxxxxxx",
    api_secret="your_64_char_secret"
)

def on_progress(status):
    print(f"Page {status.current_page}/{status.total_pages}")

result = client.analyze(
    "large_document.pdf",
    on_progress=on_progress
)
```

### Async Processing (v1)

```python
# Submit job with German-OCR Pro
job = client.submit("document.pdf", model="german-ocr-pro", output_format="json")
print(f"Job ID: {job.job_id}")

# Check status
status = client.get_job(job.job_id)
print(f"Status: {status.status}")

# Wait for result
result = client.wait_for_result(job.job_id)

# Cancel job
client.cancel_job(job.job_id)
```

### Account Info

```python
# Check balance
balance = client.get_balance()
print(f"Balance: {balance}")

# Usage statistics
usage = client.get_usage()
print(f"Usage: {usage}")
```

## 🔗 Integrations

| Category | Platforms |
|----------|-----------|
| **Automation** | Zapier, Make.com, n8n |
| **CMS** | WordPress Plugin, Magento 2, TYPO3, Shopify |
| **Frameworks** | Laravel, Symfony, Django, Flask, Spring Boot, .NET, Ruby on Rails |

## 🏠 Local Models

### 🦙 Ollama Models

| Model | Size | Speed | Best For |
|-------|------|-------|----------|
| [german-ocr-turbo](https://ollama.com/Keyvan/german-ocr-turbo) | 1.9 GB | ~5s | Recommended |
| [german-ocr](https://ollama.com/Keyvan/german-ocr) | 3.2 GB | ~7s | Standard |

### 🤗 GGUF Models (llama.cpp / Hugging Face)

| Model | Size | Speed | Best For |
|-------|------|-------|----------|
| [german-ocr-2b](https://huggingface.co/Keyven/german-ocr-2b-gguf) | 1.5 GB | ~5s (GPU) / ~25s (CPU) | Edge/Embedded |
| [german-ocr-turbo](https://huggingface.co/Keyven/german-ocr-turbo-gguf) | 1.9 GB | ~5s (GPU) / ~20s (CPU) | Best accuracy |

**Hardware Support:**
- CUDA (NVIDIA GPUs)
- Metal (Apple Silicon)
- Vulkan (AMD/Intel/NVIDIA)
- OpenVINO (Intel NPU)
- CPU (all platforms)

## 💰 Pricing

See current pricing at [app.german-ocr.de](https://app.german-ocr.de)

## 📄 License

Apache 2.0 - See [LICENSE](LICENSE) for details.

## 👤 Author

**Keyvan Hardani** - [keyvan.ai](https://keyvan.ai)

---

<p align="center">
  Made with ❤️ in Germany 🇩🇪
</p>

<p align="center">
  <a href="https://github.com/Keyvanhardani/german-ocr">⭐ Star us on GitHub!</a>
</p>
