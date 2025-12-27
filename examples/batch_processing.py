#!/usr/bin/env python3
"""
German-OCR Batch Processing Example

Demonstrates processing multiple documents efficiently.

Get your API credentials at: https://app.german-ocr.de
"""

import os
from pathlib import Path
from german_ocr import CloudClient, CloudError

API_KEY = os.environ.get("GERMAN_OCR_API_KEY", "your_api_key")
API_SECRET = os.environ.get("GERMAN_OCR_API_SECRET", "your_api_secret")


def main():
    client = CloudClient(
        api_key=API_KEY,
        api_secret=API_SECRET,
    )

    # Process all PDFs in a directory
    documents_dir = Path("./invoices")

    if not documents_dir.exists():
        print(f"Directory {documents_dir} not found. Creating sample...")
        documents_dir.mkdir(exist_ok=True)
        print(f"Please add PDF files to {documents_dir.absolute()}")
        return

    pdf_files = list(documents_dir.glob("*.pdf"))
    print(f"Found {len(pdf_files)} PDF files\n")

    results = []
    for pdf_file in pdf_files:
        print(f"Processing: {pdf_file.name}")
        try:
            result = client.analyze(
                str(pdf_file),
                model="cloud_fast",  # German-OCR Pro for good speed/quality
                output_format="json",
            )
            results.append({
                "file": pdf_file.name,
                "status": "success",
                "text_length": len(result.text),
                "processing_ms": result.processing_time_ms,
            })
            print(f"  OK: {len(result.text)} chars, {result.processing_time_ms}ms")
        except CloudError as e:
            results.append({
                "file": pdf_file.name,
                "status": "error",
                "error": str(e),
            })
            print(f"  ERROR: {e}")

    # Summary
    print("\n" + "=" * 50)
    print("BATCH PROCESSING SUMMARY")
    print("=" * 50)
    success = sum(1 for r in results if r["status"] == "success")
    print(f"Processed: {len(results)} files")
    print(f"Success: {success}")
    print(f"Errors: {len(results) - success}")

    client.close()


if __name__ == "__main__":
    main()
