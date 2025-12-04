"""Ollama backend for German OCR using Qwen2-VL models."""

import base64
import logging
from io import BytesIO
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import requests
from PIL import Image

from german_ocr.utils import load_image

logger = logging.getLogger(__name__)


class OllamaBackend:
    """Ollama backend for OCR inference.

    This backend uses Ollama's API to perform OCR on images using
    Qwen2-VL vision-language models fine-tuned for German documents.

    Args:
        model_name: Name of the Ollama model to use
        base_url: Base URL of the Ollama server
        timeout: Request timeout in seconds
    """

    def __init__(
        self,
        model_name: str = "Keyvan/german-ocr",
        base_url: str = "http://localhost:11434",
        timeout: int = 120,
    ) -> None:
        """Initialize the Ollama backend."""
        self.model_name = model_name
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self._verify_connection()

    def _verify_connection(self) -> None:
        """Verify connection to Ollama server.

        Raises:
            ConnectionError: If Ollama server is not reachable
        """
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            response.raise_for_status()
            logger.info(f"Successfully connected to Ollama at {self.base_url}")
        except requests.exceptions.RequestException as e:
            raise ConnectionError(
                f"Failed to connect to Ollama server at {self.base_url}. "
                f"Make sure Ollama is running. Error: {e}"
            ) from e

    def _verify_model(self) -> bool:
        """Check if the specified model is available.

        Returns:
            True if model is available, False otherwise
        """
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            response.raise_for_status()
            data = response.json()
            available_models = [model["name"] for model in data.get("models", [])]
            return self.model_name in available_models
        except Exception as e:
            logger.warning(f"Failed to verify model availability: {e}")
            return False

    def _image_to_base64(self, image: Image.Image) -> str:
        """Convert PIL Image to base64 string.

        Args:
            image: PIL Image object

        Returns:
            Base64 encoded string
        """
        buffer = BytesIO()
        image.save(buffer, format="PNG")
        return base64.b64encode(buffer.getvalue()).decode("utf-8")

    def extract(
        self,
        image: Union[str, Path, Image.Image],
        prompt: Optional[str] = None,
        structured: bool = False,
    ) -> Union[str, Dict[str, Any]]:
        """Extract text from an image using Ollama.

        Args:
            image: Path to image file or PIL Image object
            prompt: Custom prompt for OCR (optional)
            structured: Whether to return structured output (dict)

        Returns:
            Extracted text as string or structured dict

        Raises:
            ValueError: If image is invalid
            RuntimeError: If OCR extraction fails
        """
        # Load and prepare image
        pil_image = load_image(image)
        image_b64 = self._image_to_base64(pil_image)

        # Prepare prompt (German for better results)
        if prompt is None:
            if structured:
                prompt = (
                    "Extrahiere den gesamten Text aus diesem Dokument. "
                    "Gib das Ergebnis strukturiert im Markdown-Format aus."
                )
            else:
                prompt = "Extrahiere den gesamten Text aus diesem Dokument im Markdown-Format."

        # Make request to Ollama
        payload = {
            "model": self.model_name,
            "prompt": prompt,
            "images": [image_b64],
            "stream": False,
        }

        try:
            response = requests.post(
                f"{self.base_url}/api/generate",
                json=payload,
                timeout=self.timeout,
            )
            response.raise_for_status()
            result = response.json()

            extracted_text = result.get("response", "").strip()

            if structured:
                return {
                    "text": extracted_text,
                    "model": self.model_name,
                    "backend": "ollama",
                    "confidence": 1.0,  # Ollama doesn't provide confidence scores
                }
            return extracted_text

        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"OCR extraction failed: {e}") from e

    def extract_batch(
        self,
        images: List[Union[str, Path, Image.Image]],
        prompt: Optional[str] = None,
        structured: bool = False,
    ) -> List[Union[str, Dict[str, Any]]]:
        """Extract text from multiple images.

        Args:
            images: List of image paths or PIL Image objects
            prompt: Custom prompt for OCR (optional)
            structured: Whether to return structured output

        Returns:
            List of extracted texts or structured dicts
        """
        results = []
        for i, image in enumerate(images):
            try:
                result = self.extract(image, prompt=prompt, structured=structured)
                results.append(result)
                logger.info(f"Processed image {i+1}/{len(images)}")
            except Exception as e:
                logger.error(f"Failed to process image {i+1}: {e}")
                if structured:
                    results.append({"text": "", "error": str(e), "backend": "ollama"})
                else:
                    results.append("")
        return results

    @staticmethod
    def is_available() -> bool:
        """Check if Ollama backend is available.

        Returns:
            True if Ollama is running and accessible
        """
        try:
            response = requests.get("http://localhost:11434/api/tags", timeout=2)
            response.raise_for_status()
            return True
        except Exception:
            return False
