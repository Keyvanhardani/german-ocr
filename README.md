<p align="center">
  <img src="docs/logo-german-ocr.png" alt="German-OCR Logo" width="450"/>
</p>

<p align="center">
  <strong>High-performance German document OCR - Local & Cloud</strong>
</p>

<p align="center">
  <a href="https://pypi.org/project/german-ocr/"><img src="https://badge.fury.io/py/german-ocr.svg" alt="PyPI version"></a>
  <a href="https://opensource.org/licenses/Apache-2.0"><img src="https://img.shields.io/badge/License-Apache%202.0-blue.svg" alt="License"></a>
  <a href="https://www.python.org/downloads/"><img src="https://img.shields.io/badge/python-3.9+-blue.svg" alt="Python 3.9+"></a>
  <a href="https://portal.german-ocr.de"><img src="https://img.shields.io/badge/Cloud-API-green" alt="Cloud API"></a>
</p>

---

## Features

| Feature | Local | Cloud |
|---------|-------|-------|
| **German Documents** | Invoices, contracts, forms | All document types |
| **Output Formats** | Markdown, JSON, text | JSON, Markdown, text, n8n |
| **PDF Support** | Images only | Up to 50 pages |
| **Privacy** | 100% local | DSGVO-konform (Frankfurt) |
| **Speed** | ~5s/page | ~2-3s/page |

## Installation

```bash
pip install german-ocr
```

## Quick Start

### Option 1: Cloud API (Recommended)

No GPU required. Get your API key at [portal.german-ocr.de](https://portal.german-ocr.de)

```python
from german_ocr import CloudClient

client = CloudClient(api_key="your-api-key")

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

### Option 2: Local (Ollama)

Requires [Ollama](https://ollama.ai) installed.

```bash
# Install model
ollama pull Keyvan/german-ocr-turbo
```

```python
from german_ocr import GermanOCR

ocr = GermanOCR()
text = ocr.extract("invoice.png")
print(text)
```

## CLI Usage

### Cloud

```bash
# Set API key
export GERMAN_OCR_API_KEY="your-api-key"

# Extract text
german-ocr --cloud invoice.pdf

# JSON output
german-ocr --cloud --output-format json invoice.pdf

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

## Cloud API

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

client = CloudClient(api_key="...")

def on_progress(status):
    print(f"Page {status.current_page}/{status.total_pages}")

result = client.analyze(
    "large_document.pdf",
    on_progress=on_progress
)
```

### Async Processing

```python
# Submit job
job = client.submit("document.pdf", output_format="json")
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

## Local Models

| Model | Size | Speed | Best For |
|-------|------|-------|----------|
| [german-ocr-turbo](https://ollama.com/Keyvan/german-ocr-turbo) | 1.9 GB | ~5s | Recommended |
| [german-ocr](https://ollama.com/Keyvan/german-ocr) | 3.2 GB | ~7s | Standard |

## Pricing

| Tier | Pages/Month | Price |
|------|-------------|-------|
| Developer | 50 | Free |
| Startup | 1,000 | 29 EUR |
| Business | 5,000 | 99 EUR |
| Enterprise | 30,000+ | Contact |

Get started at [portal.german-ocr.de](https://portal.german-ocr.de)

## License

Apache 2.0 - See [LICENSE](LICENSE) for details.

## Author

**Keyvan Hardani** - [keyvan.ai](https://keyvan.ai)

---

<p align="center">
  Made with love in Germany
</p>
