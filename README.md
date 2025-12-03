# German-OCR

High-performance German document OCR using fine-tuned Qwen2-VL vision-language model.

[![PyPI version](https://badge.fury.io/py/german-ocr.svg)](https://badge.fury.io/py/german-ocr)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)

## Features

- **High Accuracy**: 100% accuracy on German invoice test data
- **Multiple Backends**: Ollama (fast, local) or HuggingFace Transformers
- **Easy to Use**: Simple Python API and CLI
- **Batch Processing**: Process multiple documents efficiently
- **Structured Output**: Get results as plain text or JSON with metadata

## Installation

```bash
# Basic installation (Ollama backend)
pip install german-ocr

# With HuggingFace backend
pip install german-ocr[hf]

# All features
pip install german-ocr[all]
```

## Quick Start

### Prerequisites

For Ollama backend (recommended):
```bash
# Install Ollama from https://ollama.ai
ollama pull german-ocr-turbo
```

### Python API

```python
from german_ocr import GermanOCR

# Initialize (auto-detects best available backend)
ocr = GermanOCR()

# Extract text from image
text = ocr.extract("invoice.png")
print(text)

# Get structured output
result = ocr.extract("invoice.png", structured=True)
print(result["text"])
print(result["confidence"])

# Batch processing
results = ocr.extract_batch(["doc1.png", "doc2.png", "doc3.png"])
for r in results:
    print(r["text"])
```

### Command Line

```bash
# Single image
german-ocr invoice.png

# Batch processing
german-ocr --batch documents/

# Specify backend
german-ocr --backend ollama invoice.png
german-ocr --backend huggingface invoice.png

# Output to file
german-ocr invoice.png -o result.txt

# JSON output
german-ocr invoice.png --json

# List available backends
german-ocr --list-backends
```

## Backends

### Ollama (Recommended)

Fast, local inference using Ollama:
- No GPU required (works on CPU)
- ~2-5 seconds per image
- Privacy-preserving (runs locally)

```python
ocr = GermanOCR(backend="ollama")
```

### HuggingFace Transformers

Full model with GPU acceleration:
- Requires GPU with 8GB+ VRAM
- Best accuracy
- Slower startup

```python
ocr = GermanOCR(backend="huggingface")
```

## Supported Document Types

- Invoices (Rechnungen)
- Receipts (Quittungen)
- Forms (Formulare)
- Letters (Briefe)
- Contracts (Verträge)
- Any German text document

## API Reference

### GermanOCR Class

```python
class GermanOCR:
    def __init__(
        self,
        backend: str = "auto",  # "auto", "ollama", "huggingface"
        model: str = None,      # Custom model name
        **kwargs
    )

    def extract(
        self,
        image: Union[str, Path, PIL.Image.Image],
        structured: bool = False
    ) -> Union[str, dict]

    def extract_batch(
        self,
        images: List[Union[str, Path]],
        structured: bool = False
    ) -> List[Union[str, dict]]

    @staticmethod
    def list_backends() -> List[str]
```

## Configuration

Environment variables:
- `OLLAMA_HOST`: Ollama server URL (default: http://localhost:11434)
- `GERMAN_OCR_MODEL`: Default model to use
- `GERMAN_OCR_BACKEND`: Default backend

## Performance

| Backend | Speed (per image) | GPU Required | Accuracy |
|---------|-------------------|--------------|----------|
| Ollama | 2-5s | No | 100% |
| HuggingFace | 1-3s | Yes (8GB+) | 100% |

## License

Apache 2.0 - See [LICENSE](LICENSE) for details.

## Author

**Keyvan Hardani**
- Website: [keyvan.ai](https://keyvan.ai)
- Email: hello@keyvan.ai
- GitHub: [@Keyvanhardani](https://github.com/Keyvanhardani)

## Links

- [PyPI Package](https://pypi.org/project/german-ocr/)
- [GitHub Repository](https://github.com/Keyvanhardani/german-ocr)
- [Model on HuggingFace](https://huggingface.co/neuralabs/german-ocr-turbo)
- [Ollama Model](https://ollama.ai/library/german-ocr-turbo)
