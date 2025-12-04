"""HuggingFace Transformers backend for German OCR using Qwen2-VL."""

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import torch
from PIL import Image

from german_ocr.utils import load_image

logger = logging.getLogger(__name__)


class HuggingFaceBackend:
    """HuggingFace Transformers backend for OCR inference.

    This backend uses HuggingFace Transformers library to perform OCR
    using Qwen2-VL vision-language models fine-tuned for German documents.

    Args:
        model_name: HuggingFace model identifier
        device: Device to run inference on (auto, cuda, cpu, mps)
        quantization: Quantization mode (none, 4bit, 8bit)
    """

    def __init__(
        self,
        model_name: str = "Keyven/german-ocr",
        device: str = "auto",
        quantization: Optional[str] = None,
    ) -> None:
        """Initialize the HuggingFace backend."""
        self.model_name = model_name
        self.quantization = quantization
        self.device = self._get_device(device)

        logger.info(f"Loading model {model_name} on device {self.device}...")
        self._load_model()

    def _get_device(self, device: str) -> str:
        """Determine the device to use for inference.

        Args:
            device: Requested device (auto, cuda, cpu, mps)

        Returns:
            Device string
        """
        if device == "auto":
            if torch.cuda.is_available():
                return "cuda"
            elif torch.backends.mps.is_available():
                return "mps"
            else:
                return "cpu"
        return device

    def _load_model(self) -> None:
        """Load the model and processor.

        Raises:
            RuntimeError: If model loading fails
        """
        try:
            from transformers import Qwen2VLForConditionalGeneration, AutoProcessor

            # Load processor
            self.processor = AutoProcessor.from_pretrained(self.model_name)

            # Configure quantization if requested
            model_kwargs: Dict[str, Any] = {"device_map": "auto"}

            if self.quantization == "4bit":
                from transformers import BitsAndBytesConfig

                model_kwargs["quantization_config"] = BitsAndBytesConfig(
                    load_in_4bit=True,
                    bnb_4bit_compute_dtype=torch.float16,
                )
            elif self.quantization == "8bit":
                model_kwargs["load_in_8bit"] = True
            elif self.device != "cpu":
                model_kwargs["torch_dtype"] = torch.float16

            # Load Qwen2-VL model
            self.model = Qwen2VLForConditionalGeneration.from_pretrained(
                self.model_name, **model_kwargs
            )

            self.model.eval()
            logger.info("Model loaded successfully")

        except Exception as e:
            raise RuntimeError(f"Failed to load model {self.model_name}: {e}") from e

    def extract(
        self,
        image: Union[str, Path, Image.Image],
        prompt: Optional[str] = None,
        structured: bool = False,
        max_new_tokens: int = 512,
    ) -> Union[str, Dict[str, Any]]:
        """Extract text from an image using HuggingFace model.

        Args:
            image: Path to image file or PIL Image object
            prompt: Custom prompt for OCR (optional)
            structured: Whether to return structured output (dict)
            max_new_tokens: Maximum tokens to generate

        Returns:
            Extracted text as string or structured dict

        Raises:
            ValueError: If image is invalid
            RuntimeError: If OCR extraction fails
        """
        # Load image
        pil_image = load_image(image)

        # Prepare prompt (German for better results)
        if prompt is None:
            prompt = "Extrahiere den gesamten Text aus diesem Dokument im Markdown-Format."

        # Prepare inputs using Qwen2-VL chat format
        try:
            from qwen_vl_utils import process_vision_info

            messages = [{
                "role": "user",
                "content": [
                    {"type": "image", "image": pil_image},
                    {"type": "text", "text": prompt}
                ]
            }]

            text = self.processor.apply_chat_template(
                messages, tokenize=False, add_generation_prompt=True
            )
            image_inputs, video_inputs = process_vision_info(messages)
            inputs = self.processor(
                text=[text],
                images=image_inputs,
                videos=video_inputs,
                padding=True,
                return_tensors="pt"
            ).to(self.model.device)

            # Generate
            with torch.no_grad():
                outputs = self.model.generate(
                    **inputs,
                    max_new_tokens=max_new_tokens,
                    do_sample=False,
                )

            # Decode output
            generated_text = self.processor.batch_decode(
                outputs[:, inputs.input_ids.shape[1]:],
                skip_special_tokens=True
            )[0]

            if structured:
                return {
                    "text": generated_text,
                    "model": self.model_name,
                    "backend": "huggingface",
                    "confidence": 1.0,
                }
            return generated_text

        except Exception as e:
            raise RuntimeError(f"OCR extraction failed: {e}") from e

    def extract_batch(
        self,
        images: List[Union[str, Path, Image.Image]],
        prompt: Optional[str] = None,
        structured: bool = False,
        max_new_tokens: int = 512,
        batch_size: int = 1,
    ) -> List[Union[str, Dict[str, Any]]]:
        """Extract text from multiple images.

        Args:
            images: List of image paths or PIL Image objects
            prompt: Custom prompt for OCR (optional)
            structured: Whether to return structured output
            max_new_tokens: Maximum tokens to generate
            batch_size: Number of images to process at once

        Returns:
            List of extracted texts or structured dicts
        """
        results = []

        # Process in batches
        for i in range(0, len(images), batch_size):
            batch = images[i : i + batch_size]

            for j, image in enumerate(batch):
                try:
                    result = self.extract(
                        image,
                        prompt=prompt,
                        structured=structured,
                        max_new_tokens=max_new_tokens,
                    )
                    results.append(result)
                    logger.info(f"Processed image {i+j+1}/{len(images)}")
                except Exception as e:
                    logger.error(f"Failed to process image {i+j+1}: {e}")
                    if structured:
                        results.append(
                            {"text": "", "error": str(e), "backend": "huggingface"}
                        )
                    else:
                        results.append("")

        return results

    @staticmethod
    def is_available() -> bool:
        """Check if HuggingFace backend is available.

        Returns:
            True if transformers library is installed
        """
        try:
            import transformers  # noqa: F401

            return True
        except ImportError:
            return False
