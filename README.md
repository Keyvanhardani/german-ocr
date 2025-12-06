<p align="center">
  <img src="docs/logo-german-ocr.png" alt="German-OCR Logo" width="450"/>
</p>

<p align="center">
  <strong>High-performance German document OCR using fine-tuned Qwen2-VL and Qwen3-VL vision-language models</strong>
</p>

<p align="center">
  <a href="https://pypi.org/project/german-ocr/"><img src="https://badge.fury.io/py/german-ocr.svg" alt="PyPI version"></a>
  <a href="https://opensource.org/licenses/Apache-2.0"><img src="https://img.shields.io/badge/License-Apache%202.0-blue.svg" alt="License"></a>
  <a href="https://www.python.org/downloads/"><img src="https://img.shields.io/badge/python-3.9+-blue.svg" alt="Python 3.9+"></a>
  <a href="https://huggingface.co/Keyven/german-ocr"><img src="https://img.shields.io/badge/%F0%9F%A4%97-HuggingFace-yellow" alt="HuggingFace"></a>
  <a href="https://ollama.com/Keyvan/german-ocr-turbo"><img src="https://img.shields.io/badge/Ollama-Turbo-green" alt="Ollama"></a>
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
| **Multiple Output Formats** | Markdown, JSON, HTML, or plain text |
| **Easy to Use** | Simple Python API and CLI |
| **Batch Processing** | Process multiple documents efficiently |
| **Structured Output** | Get results as plain text or JSON with metadata |
| **Privacy-First** | Runs completely locally - your documents never leave your machine |

## Model Variants

| Model | Size | Base | Speed | Accuracy | Best For |
|-------|------|------|-------|----------|----------|
| [Keyvan/german-ocr-turbo](https://ollama.com/Keyvan/german-ocr-turbo) | 1.9 GB | Qwen3-VL-2B | ~5s | 100% | Fastest, recommended |
| [Keyvan/german-ocr](https://ollama.com/Keyvan/german-ocr) | 3.2 GB | Qwen2.5-VL-3B | ~5-7s | 75% | Standard model |
| [Keyven/german-ocr](https://huggingface.co/Keyven/german-ocr) | 4.4 GB | Qwen2-VL-2B | ~1-3s | 100% | GPU acceleration |

## Installation

```bash
pip install german-ocr
```

## Quick Start

```bash
# Install Turbo model (fastest, recommended)
ollama pull Keyvan/german-ocr-turbo
```

### Python API

```python
from german_ocr import GermanOCR

# Initialize with Turbo model (default)
ocr = GermanOCR()

# Extract text from image
text = ocr.extract("invoice.png")
print(text)

# Different output formats
text_md = ocr.extract("invoice.png", output_format="markdown")
text_json = ocr.extract("invoice.png", output_format="json")

# List available models
models = GermanOCR.list_models()
```

### Command Line

```bash
# Single image (uses Turbo by default)
german-ocr invoice.png

# Use specific model
german-ocr --model german-ocr-turbo invoice.png

# Different output formats
german-ocr --format json invoice.png

# List available models
german-ocr --list-models
```

## Performance Benchmarks

Tested on RTX 4060 8GB with 5x warm runs:

| Model | Size | Time | Accuracy |
|-------|------|------|----------|
| **German-OCR Turbo** | 1.9GB | 5.0s | 100% |
| German-OCR v1 | 3.2GB | 5.5s | 75% |
| DeepSeek-OCR | 6.7GB | 15.8s | 70% |
| MiniCPM-V | 5.5GB | 8.9s | 67% |
| LLaVA 7B | 4.7GB | 3.9s | 0% |

**German-OCR Turbo is 3x faster than DeepSeek-OCR!**

[View full benchmark results](https://german-ocr.github.io)

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
| Benchmark Results | [german-ocr.github.io](https://german-ocr.github.io) |
| Ollama Turbo | [ollama.com/Keyvan/german-ocr-turbo](https://ollama.com/Keyvan/german-ocr-turbo) |
| Ollama Standard | [ollama.com/Keyvan/german-ocr](https://ollama.com/Keyvan/german-ocr) |
| HuggingFace Model | [huggingface.co/Keyven/german-ocr](https://huggingface.co/Keyven/german-ocr) |

---

<p align="center">
  Made with love in Germany
</p>
