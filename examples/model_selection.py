#!/usr/bin/env python3
"""
German-OCR Model Selection Example

Demonstrates how to select different OCR models:
- German-OCR Turbo (local) - 0.02 EUR/page, DSGVO-compliant
- German-OCR Pro (cloud_fast) - 0.05 EUR/page, fast cloud
- German-OCR Ultra (cloud) - 0.05 EUR/page, maximum precision

Get your API credentials at: https://portal.german-ocr.de
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
    print("=== German-OCR Turbo (local) ===")
    result = client.analyze(document, model="local")
    print(f"Price: 0.02 EUR/page")
    print(f"Processing: {result.processing_time_ms}ms")
    print(f"Text: {result.text[:100]}...\n")

    # German-OCR Pro - Fast cloud processing (default)
    # Best for: General business documents
    print("=== German-OCR Pro (cloud_fast) ===")
    result = client.analyze(document, model="cloud_fast")
    print(f"Price: 0.05 EUR/page")
    print(f"Processing: {result.processing_time_ms}ms")
    print(f"Text: {result.text[:100]}...\n")

    # German-OCR Ultra - Maximum precision
    # Best for: Complex documents with tables, forms
    print("=== German-OCR Ultra (cloud) ===")
    result = client.analyze(document, model="cloud")
    print(f"Price: 0.05 EUR/page")
    print(f"Processing: {result.processing_time_ms}ms")
    print(f"Text: {result.text[:100]}...\n")

    client.close()


if __name__ == "__main__":
    main()
