#!/usr/bin/env python3
"""
German-OCR Model Selection Example

Demonstrates how to select different OCR models:
- german-ocr - DSGVO-compliant, local processing
- german-ocr-pro - Fast cloud processing
- german-ocr-ultra - Maximum precision

Get your API credentials at: https://app.german-ocr.de
"""

import os
from german_ocr import CloudClient

API_KEY = os.environ.get("GERMAN_OCR_API_KEY", "your_api_key")
API_SECRET = os.environ.get("GERMAN_OCR_API_SECRET", "your_api_secret")


def main():
    client = CloudClient(
        api_key=API_KEY,
        api_secret=API_SECRET,
    )

    document = "invoice.pdf"

    # German-OCR Turbo - Local processing, DSGVO-compliant
    # Best for: Privacy-sensitive documents
    print("=== German-OCR Turbo ===")
    result = client.analyze(document, model="german-ocr")
    print(f"Processing: {result.processing_time_ms}ms")
    print(f"Text: {result.text[:100]}...\n")

    # German-OCR Pro - Fast cloud processing (default)
    # Best for: General business documents
    print("=== German-OCR Pro ===")
    result = client.analyze(document, model="german-ocr-pro")
    print(f"Processing: {result.processing_time_ms}ms")
    print(f"Text: {result.text[:100]}...\n")

    # German-OCR Ultra - Maximum precision
    # Best for: Complex documents with tables, forms
    print("=== German-OCR Ultra ===")
    result = client.analyze(document, model="german-ocr-ultra")
    print(f"Processing: {result.processing_time_ms}ms")
    print(f"Text: {result.text[:100]}...\n")

    client.close()


if __name__ == "__main__":
    main()
