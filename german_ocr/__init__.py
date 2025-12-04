"""German OCR Package - Production-ready OCR for German documents.

This package provides a unified interface for German OCR using multiple backends:
- Ollama (preferred for local inference) - ollama.com/Keyvan/german-ocr
- HuggingFace Transformers (GPU) - huggingface.co/Keyven/german-ocr

Based on fine-tuned Qwen2-VL vision-language models.

Example:
    >>> from german_ocr import GermanOCR
    >>> ocr = GermanOCR()
    >>> text = ocr.extract("invoice.png")
    >>> print(text)
"""

from german_ocr.ocr import GermanOCR

__version__ = "0.2.0"
__all__ = ["GermanOCR"]
