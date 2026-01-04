"""Utility functions for the German OCR package."""

import logging
from pathlib import Path
from typing import Union

from PIL import Image

logger = logging.getLogger(__name__)


def load_image(image_input: Union[str, Path, Image.Image]) -> Image.Image:
    """Load an image from a file path or return the PIL Image as-is.

    Args:
        image_input: Path to image file or PIL Image object

    Returns:
        PIL Image object

    Raises:
        FileNotFoundError: If the image file does not exist
        ValueError: If the image cannot be loaded or is invalid
    """
    if isinstance(image_input, Image.Image):
        return image_input

    image_path = Path(image_input)
    if not image_path.exists():
        raise FileNotFoundError(f"Image file not found: {image_path}")

    try:
        image = Image.open(image_path)
        # Verify that the image can be loaded
        image.verify()
        # Reopen after verify (verify closes the file)
        image = Image.open(image_path)
        return image
    except Exception as e:
        raise ValueError(f"Failed to load image from {image_path}: {e}") from e


def setup_logging(level: str = "INFO") -> None:
    """Configure logging for the package.

    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def validate_backend(backend: str) -> str:
    """Validate and normalize backend name.

    Args:
        backend: Backend name to validate

    Returns:
        Normalized backend name

    Raises:
        ValueError: If backend is not supported
    """
    valid_backends = {"ollama", "huggingface", "hf", "llamacpp", "llama.cpp", "llama-cpp", "auto"}
    backend_lower = backend.lower()

    if backend_lower not in valid_backends:
        raise ValueError(
            f"Unsupported backend: {backend}. "
            f"Valid options: ollama, huggingface, llamacpp, auto"
        )

    # Normalize HuggingFace variants
    if backend_lower in {"huggingface", "hf"}:
        return "huggingface"

    # Normalize llama.cpp variants
    if backend_lower in {"llamacpp", "llama.cpp", "llama-cpp"}:
        return "llamacpp"

    return backend_lower
