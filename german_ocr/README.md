# German OCR

Production-ready Python package for German OCR with automatic backend selection.

## Features

- **Multiple Backends**: Automatic selection between Ollama and HuggingFace Transformers
- **Simple API**: Extract text from images with just a few lines of code
- **Batch Processing**: Process multiple images efficiently
- **CLI Tool**: Command-line interface for quick OCR tasks
- **Type-Safe**: Full type hints for better IDE support
- **Well-Tested**: Comprehensive test coverage with pytest

## Installation

### Basic Installation

```bash
pip install -e .
```

### With HuggingFace Backend

```bash
pip install -e ".[huggingface]"
```

### Full Installation (All Backends + Development Tools)

```bash
pip install -e ".[all]"
```

## Quick Start

### Python API

```python
from german_ocr import GermanOCR

# Initialize with auto-detection
ocr = GermanOCR()

# Extract text from an image
text = ocr.extract("invoice.png")
print(text)

# Get structured output
result = ocr.extract("document.jpg", structured=True)
print(f"Text: {result['text']}")
print(f"Backend: {result['backend']}")

# Batch processing
images = ["img1.png", "img2.png", "img3.png"]
results = ocr.extract_batch(images)
for i, text in enumerate(results):
    print(f"Image {i+1}: {text}")
```

### Command Line Interface

```bash
# Extract text from a single image
german-ocr invoice.png

# Process all images in a directory
german-ocr --batch images/

# Use specific backend
german-ocr --backend ollama document.jpg

# Get structured JSON output
german-ocr --structured invoice.png

# Save results to file
german-ocr invoice.png --output result.txt

# List available backends
german-ocr --list-backends
```

## Backend Configuration

### Ollama (Recommended)

Install Ollama and pull the DeepSeek model:

```bash
# Install Ollama from https://ollama.ai
# Pull the DeepSeek OCR model
ollama pull deepseek-ocr
```

Then use the Ollama backend:

```python
ocr = GermanOCR(backend="ollama", model_name="deepseek-ocr")
```

### HuggingFace Transformers

Install the HuggingFace dependencies:

```bash
pip install -e ".[huggingface]"
```

Use the HuggingFace backend:

```python
ocr = GermanOCR(
    backend="huggingface",
    model_name="deepseek-ai/deepseek-vl-1.3b-chat",
    device="cuda",  # or "cpu", "mps"
    quantization="4bit"  # optional: "4bit", "8bit"
)
```

## Advanced Usage

### Custom Prompts

```python
custom_prompt = "Extract the invoice number and total amount from this image."
result = ocr.extract("invoice.png", prompt=custom_prompt)
```

### Backend Information

```python
# Check which backends are available
backends = GermanOCR.list_available_backends()
print(f"Ollama available: {backends['ollama']}")
print(f"HuggingFace available: {backends['huggingface']}")

# Get current backend info
ocr = GermanOCR()
info = ocr.get_backend_info()
print(f"Using backend: {info['backend']}")
print(f"Model: {info['model']}")
```

### Error Handling

```python
from german_ocr import GermanOCR

try:
    ocr = GermanOCR()
    text = ocr.extract("document.png")
except FileNotFoundError as e:
    print(f"Image not found: {e}")
except RuntimeError as e:
    print(f"OCR failed: {e}")
```

## Development

### Running Tests

```bash
# Install development dependencies
pip install -e ".[dev]"

# Run tests
pytest tests/german_ocr/

# Run with coverage
pytest --cov=german_ocr tests/german_ocr/
```

### Code Quality

```bash
# Format code
black german_ocr/

# Lint code
ruff check german_ocr/

# Type checking
mypy german_ocr/
```

## API Reference

### GermanOCR Class

#### `__init__(backend, model_name, device, quantization, log_level)`

Initialize the OCR instance.

**Parameters:**
- `backend` (str): Backend to use ('auto', 'ollama', 'huggingface')
- `model_name` (str, optional): Model name for the backend
- `device` (str): Device for HF backend ('auto', 'cuda', 'cpu', 'mps')
- `quantization` (str, optional): Quantization mode ('4bit', '8bit')
- `log_level` (str): Logging level ('DEBUG', 'INFO', 'WARNING', 'ERROR')

#### `extract(image, prompt, structured, **kwargs)`

Extract text from a single image.

**Parameters:**
- `image` (str | Path | PIL.Image): Image to process
- `prompt` (str, optional): Custom prompt for OCR
- `structured` (bool): Return structured dict instead of string
- `**kwargs`: Backend-specific parameters

**Returns:**
- `str` or `dict`: Extracted text or structured result

#### `extract_batch(images, prompt, structured, **kwargs)`

Extract text from multiple images.

**Parameters:**
- `images` (list): List of images to process
- `prompt` (str, optional): Custom prompt for OCR
- `structured` (bool): Return structured dicts
- `**kwargs`: Backend-specific parameters

**Returns:**
- `list`: List of extracted texts or structured results

#### `get_backend_info()`

Get information about the current backend.

**Returns:**
- `dict`: Backend information

#### `list_available_backends()` (static)

List all available backends and their status.

**Returns:**
- `dict`: Mapping of backend names to availability

## License

Apache-2.0

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
