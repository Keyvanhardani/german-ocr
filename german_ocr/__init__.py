"""German OCR Package - Production-ready OCR for German documents.

This package provides:
- Local OCR using Ollama or HuggingFace backends
- Cloud OCR via api.german-ocr.de

Example (Local):
    >>> from german_ocr import GermanOCR
    >>> ocr = GermanOCR()
    >>> text = ocr.extract("invoice.png")

Example (Cloud):
    >>> from german_ocr import CloudClient
    >>> client = CloudClient(api_key="...")
    >>> result = client.analyze("rechnung.pdf", output_format="json")
    >>> print(result.text)

Entwickelt bei Keyvan.ai
"""

from german_ocr.ocr import GermanOCR
from german_ocr.extractor import (
    DocumentExtractor,
    InvoiceData,
    FormData,
    DocumentData,
    ExtractionResult
)
from german_ocr.cloud_client import (
    CloudClient,
    CloudResult,
    JobStatus,
    CloudError,
    AuthenticationError,
    InsufficientBalanceError,
    RateLimitError,
    ProcessingError,
)

__version__ = "0.4.0"
__all__ = [
    # Local OCR
    "GermanOCR",
    "DocumentExtractor",
    "InvoiceData",
    "FormData",
    "DocumentData",
    "ExtractionResult",
    # Cloud OCR
    "CloudClient",
    "CloudResult",
    "JobStatus",
    "CloudError",
    "AuthenticationError",
    "InsufficientBalanceError",
    "RateLimitError",
    "ProcessingError",
]
