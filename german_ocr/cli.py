"""Command Line Interface for German OCR."""

import argparse
import json
import os
import sys
from pathlib import Path
from typing import List, Optional

from german_ocr import GermanOCR, CloudClient, CloudError


def find_images_in_directory(directory: Path) -> List[Path]:
    """Find all image files in a directory.

    Args:
        directory: Directory to search

    Returns:
        List of image file paths
    """
    image_extensions = {".png", ".jpg", ".jpeg", ".bmp", ".tiff", ".webp"}
    images = []

    for ext in image_extensions:
        images.extend(directory.glob(f"*{ext}"))
        images.extend(directory.glob(f"*{ext.upper()}"))

    return sorted(images)


def process_single_image(
    ocr: GermanOCR,
    image_path: Path,
    structured: bool,
    output_file: Optional[Path] = None,
) -> None:
    """Process a single image and print or save results.

    Args:
        ocr: GermanOCR instance
        image_path: Path to image file
        structured: Whether to output structured JSON
        output_file: Optional output file path
    """
    try:
        result = ocr.extract(image_path, structured=structured)

        if structured:
            output = json.dumps(result, indent=2, ensure_ascii=False)
        else:
            output = result

        if output_file:
            output_file.write_text(output, encoding="utf-8")
            print(f"Results saved to {output_file}")
        else:
            print(output)

    except Exception as e:
        print(f"Error processing {image_path}: {e}", file=sys.stderr)
        sys.exit(1)


def process_batch(
    ocr: GermanOCR,
    images: List[Path],
    structured: bool,
    output_file: Optional[Path] = None,
) -> None:
    """Process multiple images and print or save results.

    Args:
        ocr: GermanOCR instance
        images: List of image paths
        structured: Whether to output structured JSON
        output_file: Optional output file path
    """
    try:
        print(f"Processing {len(images)} images...")
        results = ocr.extract_batch(images, structured=structured)

        if structured:
            output_data = [
                {"image": str(img), "result": result}
                for img, result in zip(images, results)
            ]
            output = json.dumps(output_data, indent=2, ensure_ascii=False)
        else:
            output_data = [
                f"=== {img.name} ===\n{result}\n" for img, result in zip(images, results)
            ]
            output = "\n".join(output_data)

        if output_file:
            output_file.write_text(output, encoding="utf-8")
            print(f"Results saved to {output_file}")
        else:
            print(output)

    except Exception as e:
        print(f"Error processing batch: {e}", file=sys.stderr)
        sys.exit(1)


def main() -> None:
    """Main entry point for the CLI."""
    parser = argparse.ArgumentParser(
        description="German OCR - Extract text from images using DeepSeek models",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
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

  # Process batch with structured output
  german-ocr --batch folder/ --structured --output results.json
        """,
    )

    parser.add_argument(
        "input",
        type=str,
        nargs="?",
        help="Path to image file or directory (with --batch)",
    )

    parser.add_argument(
        "--batch",
        action="store_true",
        help="Process all images in the specified directory",
    )

    parser.add_argument(
        "--backend",
        type=str,
        choices=["auto", "ollama", "huggingface", "hf"],
        default="auto",
        help="OCR backend to use (default: auto)",
    )

    parser.add_argument(
        "--model",
        type=str,
        choices=["german-ocr-turbo", "german-ocr"],
        default="german-ocr-turbo",
        help="Model to use: german-ocr-turbo (fastest, 1.9GB) or german-ocr (3.2GB)",
    )
    
    parser.add_argument(
        "--format",
        type=str,
        choices=["markdown", "json", "text", "html"],
        default="markdown",
        help="Output format for OCR extraction (default: markdown)",
    )
    
    parser.add_argument(
        "--list-models",
        action="store_true",
        help="List available German-OCR models and exit",
    )

    parser.add_argument(
        "--device",
        type=str,
        choices=["auto", "cuda", "cpu", "mps"],
        default="auto",
        help="Device for HuggingFace backend (default: auto)",
    )

    parser.add_argument(
        "--quantization",
        type=str,
        choices=["none", "4bit", "8bit"],
        help="Quantization mode for HuggingFace backend",
    )

    parser.add_argument(
        "--structured",
        action="store_true",
        help="Output structured JSON with metadata",
    )

    parser.add_argument(
        "--output",
        "-o",
        type=str,
        help="Output file path (default: stdout)",
    )

    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable verbose logging",
    )

    parser.add_argument(
        "--list-backends",
        action="store_true",
        help="List available backends and exit",
    )

    # Cloud-Optionen
    parser.add_argument(
        "--cloud",
        action="store_true",
        help="Use German-OCR Cloud API instead of local processing",
    )

    parser.add_argument(
        "--api-key",
        type=str,
        help="API key for cloud processing (or set GERMAN_OCR_API_KEY)",
    )

    parser.add_argument(
        "--output-format",
        type=str,
        choices=["json", "markdown", "text", "n8n"],
        default="text",
        help="Output format for cloud processing (default: text)",
    )

    parser.add_argument(
        "--prompt",
        type=str,
        help="Custom prompt for extraction",
    )

    args = parser.parse_args()

    # List backends if requested
    if args.list_backends:
        backends = GermanOCR.list_available_backends()
        print("Available backends:")
        for backend, available in backends.items():
            status = "[OK]" if available else "[--]"
            print(f"  {status} {backend}")
        sys.exit(0)
    
    # List models if requested
    if args.list_models:
        from german_ocr.ollama_backend import list_available_models
        models = list_available_models()
        print("Available German-OCR models:")
        print()
        for key, info in models.items():
            print(f"  {key}:")
            print(f"    Name: {info['name']}")
            print(f"    Size: {info['size']}")
            print(f"    Base: {info['base']}")
            print(f"    Speed: {info['speed']}")
            print(f"    Accuracy: {info['accuracy']}")
            print()
        sys.exit(0)

    # Validate input was provided
    if args.input is None:
        parser.error("the following arguments are required: input")

    # Validate input path
    input_path = Path(args.input)
    if not input_path.exists():
        print(f"Error: {input_path} does not exist", file=sys.stderr)
        sys.exit(1)

    # Prepare output file
    output_file = Path(args.output) if args.output else None

    # Cloud processing
    if args.cloud:
        try:
            api_key = args.api_key or os.environ.get("GERMAN_OCR_API_KEY")
            if not api_key:
                print("Error: API key required for cloud processing.", file=sys.stderr)
                print("Set GERMAN_OCR_API_KEY or use --api-key", file=sys.stderr)
                sys.exit(1)

            client = CloudClient(api_key=api_key)

            if args.verbose:
                print(f"Using Cloud API: {client.base_url}", file=sys.stderr)

            def on_progress(status):
                if status.total_pages > 1:
                    print(
                        f"  Seite {status.current_page}/{status.total_pages} - {status.phase}",
                        file=sys.stderr
                    )

            result = client.analyze(
                file=input_path,
                prompt=args.prompt,
                output_format=args.output_format,
                on_progress=on_progress if args.verbose else None,
            )

            output = result.text

            if output_file:
                output_file.write_text(output, encoding="utf-8")
                print(f"Results saved to {output_file}")
            else:
                print(output)

            sys.exit(0)

        except CloudError as e:
            print(f"Cloud Error: {e.message}", file=sys.stderr)
            sys.exit(1)
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)

    # Initialize local OCR
    try:
        log_level = "DEBUG" if args.verbose else "INFO"
        ocr = GermanOCR(
            backend=args.backend,
            model_name=args.model,
            device=args.device,
            quantization=args.quantization,
            log_level=log_level,
        )

        # Print backend info if verbose
        if args.verbose:
            info = ocr.get_backend_info()
            print(f"Backend: {info['backend']}", file=sys.stderr)
            if "model" in info:
                print(f"Model: {info['model']}", file=sys.stderr)
            if "device" in info:
                print(f"Device: {info['device']}", file=sys.stderr)
            print("", file=sys.stderr)

    except Exception as e:
        print(f"Error initializing OCR: {e}", file=sys.stderr)
        sys.exit(1)

    # Process input
    if args.batch:
        if not input_path.is_dir():
            print(f"Error: {input_path} is not a directory", file=sys.stderr)
            sys.exit(1)

        images = find_images_in_directory(input_path)
        if not images:
            print(f"No images found in {input_path}", file=sys.stderr)
            sys.exit(1)

        process_batch(ocr, images, args.structured, output_file)
    else:
        if not input_path.is_file():
            print(f"Error: {input_path} is not a file", file=sys.stderr)
            sys.exit(1)

        process_single_image(ocr, input_path, args.structured, output_file)


if __name__ == "__main__":
    main()
