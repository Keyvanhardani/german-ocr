#!/usr/bin/env python3
"""
German-OCR JSON Extraction Example

Demonstrates structured data extraction from invoices.

Get your API credentials at: https://app.german-ocr.de
"""

import os
import json
from german_ocr import CloudClient

API_KEY = os.environ.get("GERMAN_OCR_API_KEY", "your_api_key")
API_SECRET = os.environ.get("GERMAN_OCR_API_SECRET", "your_api_secret")


def main():
    client = CloudClient(
        api_key=API_KEY,
        api_secret=API_SECRET,
    )

    # Extract structured invoice data
    result = client.analyze(
        "invoice.pdf",
        model="cloud",  # German-OCR Ultra for best structure recognition
        prompt="Extrahiere als JSON: rechnungsnummer, datum, absender, empfaenger, positionen, netto, mwst, brutto",
        output_format="json",
    )

    print("Extracted Invoice Data:")
    print("-" * 40)

    try:
        data = json.loads(result.text)
        print(json.dumps(data, indent=2, ensure_ascii=False))
    except json.JSONDecodeError:
        print(result.text)

    print(f"\nProcessing time: {result.processing_time_ms}ms")
    print(f"Cost: {result.price_display}")

    client.close()


if __name__ == "__main__":
    main()
