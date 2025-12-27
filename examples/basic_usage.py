#!/usr/bin/env python3
"""
German-OCR Basic Usage Example

Demonstrates simple document analysis with the Cloud API.

Get your API credentials at: https://app.german-ocr.de
"""

import os
from german_ocr import CloudClient

# API credentials from environment or direct
API_KEY = os.environ.get("GERMAN_OCR_API_KEY", "your_api_key")
API_SECRET = os.environ.get("GERMAN_OCR_API_SECRET", "your_api_secret")


def main():
    # Initialize client
    client = CloudClient(
        api_key=API_KEY,
        api_secret=API_SECRET,
    )

    # Simple text extraction
    result = client.analyze("invoice.pdf")
    print("Extracted Text:")
    print(result.text)
    print(f"\nProcessing time: {result.processing_time_ms}ms")
    print(f"Model used: {result.model}")

    client.close()


if __name__ == "__main__":
    main()
