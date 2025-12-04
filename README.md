<p align="center">
  <img src="https://raw.githubusercontent.com/Keyvanhardani/german-ocr/main/docs/logo.png" alt="German-OCR Logo" width="200"/>
</p>

<h1 align="center">German-OCR</h1>

<p align="center">
  <strong>High-performance German document OCR using fine-tuned Qwen2-VL vision-language model</strong>
</p>

<p align="center">
  <a href="https://pypi.org/project/german-ocr/"><img src="https://badge.fury.io/py/german-ocr.svg" alt="PyPI version"></a>
  <a href="https://opensource.org/licenses/Apache-2.0"><img src="https://img.shields.io/badge/License-Apache%202.0-blue.svg" alt="License"></a>
  <a href="https://www.python.org/downloads/"><img src="https://img.shields.io/badge/python-3.9+-blue.svg" alt="Python 3.9+"></a>
  <a href="https://huggingface.co/Keyven/german-ocr"><img src="https://img.shields.io/badge/%F0%9F%A4%97-HuggingFace-yellow" alt="HuggingFace"></a>
  <a href="https://ollama.com/Keyvan/german-ocr"><img src="https://img.shields.io/badge/Ollama-Available-green" alt="Ollama"></a>
</p>

<p align="center">
  <img src="https://raw.githubusercontent.com/Keyvanhardani/german-ocr/main/docs/demo.gif" alt="Demo" width="600"/>
</p>

---

## Features

| Feature | Description |
|---------|-------------|
| **High Accuracy** | 100% accuracy on German invoice test data |
| **Multiple Backends** | Ollama (fast, local) or HuggingFace Transformers |
| **Easy to Use** | Simple Python API and CLI |
| **Batch Processing** | Process multiple documents efficiently |
| **Structured Output** | Get results as plain text or JSON with metadata |
| **Privacy-First** | Runs completely locally - your documents never leave your machine |

## Model Variants

| Model | Size | Base | Speed | Best For |
|-------|------|------|-------|----------|
| [Keyvan/german-ocr](https://ollama.com/Keyvan/german-ocr) | ~4 GB | Qwen2-VL-2B | ~2-5s | Fast local inference |
| [Keyven/german-ocr](https://huggingface.co/Keyven/german-ocr) | 4.4 GB | Qwen2-VL-2B | ~1-3s | GPU acceleration |
| [Keyven/german-ocr-3b](https://huggingface.co/Keyven/german-ocr-3b) | 7.5 GB | Qwen2.5-VL-3B | ~3-5s | Higher accuracy |

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
ollama pull Keyvan/german-ocr
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

| Document Type | German | Status |
|---------------|--------|--------|
| Invoices | Rechnungen | Excellent |
| Receipts | Quittungen | Excellent |
| Forms | Formulare | Good |
| Letters | Briefe | Good |
| Contracts | Vertraege | Good |
| Any German text | - | Good |

## Performance Benchmarks

| Backend | Speed (per image) | GPU Required | VRAM | Accuracy |
|---------|-------------------|--------------|------|----------|
| Ollama | 2-5s | No | - | 100% |
| Ollama (GPU) | 1-2s | Optional | 4GB+ | 100% |
| HuggingFace | 1-3s | Yes | 8GB+ | 100% |
| HuggingFace (4-bit) | 2-4s | Yes | 4GB+ | 99% |

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
| Variable | Description | Default |
|----------|-------------|---------|
| `OLLAMA_HOST` | Ollama server URL | `http://localhost:11434` |
| `GERMAN_OCR_MODEL` | Default model to use | Auto-detect |
| `GERMAN_OCR_BACKEND` | Default backend | Auto-detect |

## Architecture

```
german-ocr/
+-- german_ocr/
|   +-- __init__.py      # Package entry point
|   +-- ocr.py           # Main GermanOCR class
|   +-- ollama_backend.py # Ollama integration
|   +-- hf_backend.py    # HuggingFace integration
|   +-- cli.py           # Command-line interface
|   +-- utils.py         # Utility functions
+-- tests/               # Test suite
+-- docs/                # Documentation
+-- pyproject.toml       # Project configuration
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

Apache 2.0 - See [LICENSE](LICENSE) for details.

## Author

**Keyvan Hardani**

<p>
  <a href="https://keyvan.ai"><img src="https://img.shields.io/badge/Website-keyvan.ai-blue?style=flat-square" alt="Website"></a>
  <a href="https://www.linkedin.com/in/keyvanhardani/"><img src="https://img.shields.io/badge/LinkedIn-keyvanhardani-blue?style=flat-square&logo=linkedin" alt="LinkedIn"></a>
  <a href="https://github.com/Keyvanhardani"><img src="https://img.shields.io/badge/GitHub-Keyvanhardani-black?style=flat-square&logo=github" alt="GitHub"></a>
</p>

## Links

| Resource | Link |
|----------|------|
| PyPI Package | [pypi.org/project/german-ocr](https://pypi.org/project/german-ocr/) |
| GitHub Repository | [github.com/Keyvanhardani/german-ocr](https://github.com/Keyvanhardani/german-ocr) |
| HuggingFace Model | [huggingface.co/Keyven/german-ocr](https://huggingface.co/Keyven/german-ocr) |
| Ollama Model | [ollama.com/Keyvan/german-ocr](https://ollama.com/Keyvan/german-ocr) |

---

<p align="center">
  Made with love in Germany
</p>
