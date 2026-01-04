"""Ollama backend for German OCR using Qwen2-VL and Qwen3-VL models."""

import base64
import logging
from io import BytesIO
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import requests
from PIL import Image

from german_ocr.utils import load_image

logger = logging.getLogger(__name__)

# Available German-OCR models on Ollama
AVAILABLE_MODELS = {
    "german-ocr-turbo": {
        "name": "Keyvan/german-ocr-turbo",
        "display": "German-OCR Turbo",
        "size": "1.9GB",
        "base": "Qwen3-VL-2B",
        "speed": "~5s",
        "accuracy": "100%",
        "description": "Fastest model, optimized for speed and accuracy",
    },
    "german-ocr-2b": {
        "name": "Keyvan/german-ocr-2b",
        "display": "German-OCR 2B",
        "size": "1.5GB",
        "base": "Qwen3-VL-2B",
        "speed": "~5s",
        "accuracy": "100%",
        "description": "Compact model, optimized for edge/embedded deployment",
    },
    "german-ocr": {
        "name": "Keyvan/german-ocr",
        "display": "German-OCR v1",
        "size": "3.2GB",
        "base": "Qwen2.5-VL-3B",
        "speed": "~5-7s",
        "accuracy": "75%",
        "description": "Standard model with high accuracy",
    },
}

DEFAULT_MODEL = "german-ocr-turbo"


def list_available_models() -> Dict[str, Dict[str, str]]:
    """List all available German-OCR models."""
    return AVAILABLE_MODELS.copy()


def get_model_name(model_key: str) -> str:
    """Get the full Ollama model name from a short key."""
    if model_key in AVAILABLE_MODELS:
        return AVAILABLE_MODELS[model_key]["name"]
    return model_key


class OllamaBackend:
    """Ollama backend for OCR inference."""

    def __init__(
        self,
        model_name: str = "german-ocr-turbo",
        base_url: str = "http://localhost:11434",
        timeout: int = 120,
    ) -> None:
        self.model_name = get_model_name(model_name)
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self._verify_connection()

    def _verify_connection(self) -> None:
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
        buffer = BytesIO()
        image.save(buffer, format="PNG")
        return base64.b64encode(buffer.getvalue()).decode("utf-8")

    def extract(
        self,
        image: Union[str, Path, Image.Image],
        prompt: Optional[str] = None,
        structured: bool = False,
        output_format: str = "markdown",
    ) -> Union[str, Dict[str, Any]]:
        pil_image = load_image(image)
        image_b64 = self._image_to_base64(pil_image)

        if prompt is None:
            format_prompts = {
                "markdown": "Extrahiere den gesamten Text aus diesem Dokument im Markdown-Format.",
                "json": "Extrahiere den gesamten Text aus diesem Dokument als JSON.",
                "text": "Extrahiere den gesamten Text aus diesem Dokument als reinen Text.",
                "html": "Extrahiere den gesamten Text aus diesem Dokument als HTML.",
            }
            prompt = format_prompts.get(output_format, format_prompts["markdown"])

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
                    "format": output_format,
                    "confidence": 1.0,
                }
            return extracted_text

        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"OCR extraction failed: {e}") from e

    def extract_batch(
        self,
        images: List[Union[str, Path, Image.Image]],
        prompt: Optional[str] = None,
        structured: bool = False,
        output_format: str = "markdown",
    ) -> List[Union[str, Dict[str, Any]]]:
        results = []
        for i, image in enumerate(images):
            try:
                result = self.extract(
                    image, prompt=prompt, structured=structured, output_format=output_format
                )
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
        try:
            response = requests.get("http://localhost:11434/api/tags", timeout=2)
            response.raise_for_status()
            return True
        except Exception:
            return False

    @staticmethod
    def list_models() -> Dict[str, Dict[str, str]]:
        return list_available_models()
