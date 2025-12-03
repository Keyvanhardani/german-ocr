"""German OCR Package - Production-ready OCR for German documents.

This package provides a unified interface for German OCR using multiple backends:
- Ollama (preferred for local inference)
- HuggingFace Transformers (fallback)

Example:
    >>> from german_ocr import GermanOCR
    >>> ocr = GermanOCR()
    >>> text = ocr.extract("invoice.png")
    >>> print(text)
"""

from german_ocr.ocr import GermanOCR

__version__ = "0.1.0"
__all__ = ["GermanOCR"]
