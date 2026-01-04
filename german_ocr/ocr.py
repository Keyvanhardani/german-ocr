"""Main GermanOCR class with automatic backend selection."""

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from PIL import Image

from german_ocr.utils import setup_logging, validate_backend

logger = logging.getLogger(__name__)


class GermanOCR:
    """Production-ready German OCR with automatic backend selection.

    This class provides a unified interface for German OCR with support for
    multiple backends (Ollama, HuggingFace, llama.cpp). It automatically selects
    the best available backend or allows manual selection.

    Args:
        backend: Backend to use ('auto', 'ollama', 'huggingface', 'hf', 'llamacpp', 'llama.cpp')
        model_name: Model name for the selected backend
        device: Device selection ('auto', 'cuda', 'cpu', 'mps', 'metal', 'vulkan', 'openvino')
        quantization: Quantization mode for HF backend ('none', '4bit', '8bit')
        n_gpu_layers: GPU layers for llama.cpp (-1=all, 0=CPU only)
        log_level: Logging level ('DEBUG', 'INFO', 'WARNING', 'ERROR')

    Example:
        >>> ocr = GermanOCR()  # Auto-detect best backend
        >>> text = ocr.extract("invoice.png")
        >>> print(text)

        >>> # Use specific backend
        >>> ocr = GermanOCR(backend="ollama", model_name="Keyvan/german-ocr")
        >>> results = ocr.extract_batch(["img1.png", "img2.png"])
    """

    def __init__(
        self,
        backend: str = "auto",
        model_name: Optional[str] = None,
        device: str = "auto",
        quantization: Optional[str] = None,
        n_gpu_layers: int = -1,
        model_dir: Optional[str] = None,
        log_level: str = "INFO",
    ) -> None:
        """Initialize GermanOCR with the specified backend."""
        setup_logging(log_level)

        # Store config
        self.device = device
        self.n_gpu_layers = n_gpu_layers
        self.model_dir = model_dir

        # Validate and normalize backend
        backend = validate_backend(backend)

        # Auto-detect backend if needed
        if backend == "auto":
            backend = self._detect_backend()
            logger.info(f"Auto-detected backend: {backend}")

        self.backend_name = backend
        self._backend: Optional[Any] = None

        # Initialize the selected backend
        if backend == "ollama":
            self._init_ollama(model_name)
        elif backend == "huggingface":
            self._init_huggingface(model_name, device, quantization)
        elif backend == "llamacpp":
            self._init_llamacpp(model_name, device, n_gpu_layers, model_dir)
        else:
            raise ValueError(f"Unsupported backend: {backend}")

        logger.info(f"GermanOCR initialized with {backend} backend")

    def _detect_backend(self) -> str:
        """Auto-detect the best available backend.

        Priority order:
        1. Ollama (fastest for local inference, easy setup)
        2. llama.cpp (best for CPU/Edge, GGUF models)
        3. HuggingFace (fallback, requires GPU)

        Returns:
            Backend name

        Raises:
            RuntimeError: If no backend is available
        """
        from german_ocr.hf_backend import HuggingFaceBackend
        from german_ocr.ollama_backend import OllamaBackend

        try:
            from german_ocr.llamacpp_backend import LlamaCppBackend
            has_llamacpp = True
        except ImportError:
            has_llamacpp = False

        if OllamaBackend.is_available():
            logger.info("Ollama backend detected and available")
            return "ollama"

        if has_llamacpp and LlamaCppBackend.is_available():
            logger.info("llama.cpp backend detected and available")
            return "llamacpp"

        if HuggingFaceBackend.is_available():
            logger.info("HuggingFace backend detected and available")
            return "huggingface"

        raise RuntimeError(
            "No OCR backend available. Please install one of:\n"
            "  - Ollama: https://ollama.ai (recommended)\n"
            "  - llama.cpp: pip install llama-cpp-python\n"
            "  - HuggingFace: pip install transformers torch"
        )

    def _init_ollama(self, model_name: Optional[str]) -> None:
        """Initialize Ollama backend.

        Args:
            model_name: Ollama model name (optional)
        """
        from german_ocr.ollama_backend import OllamaBackend

        default_model = "german-ocr-turbo"
        model = model_name if model_name else default_model

        try:
            self._backend = OllamaBackend(model_name=model)
            logger.info(f"Initialized Ollama backend with model: {model}")
        except Exception as e:
            raise RuntimeError(f"Failed to initialize Ollama backend: {e}") from e

    def _init_huggingface(
        self,
        model_name: Optional[str],
        device: str,
        quantization: Optional[str],
    ) -> None:
        """Initialize HuggingFace backend.

        Args:
            model_name: HuggingFace model identifier (optional)
            device: Device to use for inference
            quantization: Quantization mode
        """
        from german_ocr.hf_backend import HuggingFaceBackend

        default_model = "Keyven/german-ocr"
        model = model_name if model_name else default_model

        try:
            self._backend = HuggingFaceBackend(
                model_name=model, device=device, quantization=quantization
            )
            logger.info(f"Initialized HuggingFace backend with model: {model}")
        except Exception as e:
            raise RuntimeError(f"Failed to initialize HuggingFace backend: {e}") from e

    def _init_llamacpp(
        self,
        model_name: Optional[str],
        device: str,
        n_gpu_layers: int,
        model_dir: Optional[str],
    ) -> None:
        """Initialize llama.cpp backend.

        Args:
            model_name: Model identifier (e.g., 'german-ocr-2b')
            device: Device selection ('auto', 'cuda', 'cpu', 'metal', 'vulkan', 'openvino')
            n_gpu_layers: GPU layers to offload (-1=all, 0=CPU)
            model_dir: Custom model directory
        """
        from german_ocr.llamacpp_backend import LlamaCppBackend

        default_model = "german-ocr-2b"
        model = model_name if model_name else default_model

        try:
            self._backend = LlamaCppBackend(
                model_name=model,
                device=device,
                n_gpu_layers=n_gpu_layers,
                model_dir=model_dir,
            )
            logger.info(f"Initialized llama.cpp backend with model: {model}")
        except Exception as e:
            raise RuntimeError(f"Failed to initialize llama.cpp backend: {e}") from e

    def extract(
        self,
        image: Union[str, Path, Image.Image],
        prompt: Optional[str] = None,
        structured: bool = False,
        **kwargs: Any,
    ) -> Union[str, Dict[str, Any]]:
        """Extract text from an image.

        Args:
            image: Path to image file or PIL Image object
            prompt: Custom prompt for OCR (optional)
            structured: Whether to return structured output with metadata
            **kwargs: Additional backend-specific parameters

        Returns:
            Extracted text as string, or dict if structured=True

        Raises:
            ValueError: If image is invalid
            RuntimeError: If OCR extraction fails

        Example:
            >>> text = ocr.extract("invoice.png")
            >>> result = ocr.extract("invoice.png", structured=True)
            >>> print(result['text'], result['confidence'])
        """
        if self._backend is None:
            raise RuntimeError("Backend not initialized")

        try:
            return self._backend.extract(
                image=image, prompt=prompt, structured=structured, **kwargs
            )
        except Exception as e:
            logger.error(f"OCR extraction failed: {e}")
            raise

    def extract_batch(
        self,
        images: List[Union[str, Path, Image.Image]],
        prompt: Optional[str] = None,
        structured: bool = False,
        **kwargs: Any,
    ) -> List[Union[str, Dict[str, Any]]]:
        """Extract text from multiple images.

        Args:
            images: List of image paths or PIL Image objects
            prompt: Custom prompt for OCR (optional)
            structured: Whether to return structured output
            **kwargs: Additional backend-specific parameters

        Returns:
            List of extracted texts or structured dicts

        Example:
            >>> images = ["img1.png", "img2.png", "img3.png"]
            >>> results = ocr.extract_batch(images)
            >>> for i, text in enumerate(results):
            ...     print(f"Image {i+1}: {text[:50]}...")
        """
        if self._backend is None:
            raise RuntimeError("Backend not initialized")

        try:
            return self._backend.extract_batch(
                images=images, prompt=prompt, structured=structured, **kwargs
            )
        except Exception as e:
            logger.error(f"Batch OCR extraction failed: {e}")
            raise

    def get_backend_info(self) -> Dict[str, Any]:
        """Get information about the current backend.

        Returns:
            Dictionary with backend details

        Example:
            >>> info = ocr.get_backend_info()
            >>> print(f"Using {info['backend']} with {info['model']}")
        """
        info = {"backend": self.backend_name}

        if hasattr(self._backend, "model_name"):
            info["model"] = self._backend.model_name

        if hasattr(self._backend, "device"):
            info["device"] = self._backend.device

        return info

    @staticmethod
    def list_available_backends() -> Dict[str, bool]:
        """List all available backends and their status.

        Returns:
            Dictionary mapping backend names to availability status

        Example:
            >>> backends = GermanOCR.list_available_backends()
            >>> print(f"Ollama available: {backends['ollama']}")
            >>> print(f"llama.cpp available: {backends['llamacpp']}")
            >>> print(f"HuggingFace available: {backends['huggingface']}")
        """
        from german_ocr.hf_backend import HuggingFaceBackend
        from german_ocr.ollama_backend import OllamaBackend

        result = {
            "ollama": OllamaBackend.is_available(),
            "huggingface": HuggingFaceBackend.is_available(),
        }

        try:
            from german_ocr.llamacpp_backend import LlamaCppBackend
            result["llamacpp"] = LlamaCppBackend.is_available()
        except ImportError:
            result["llamacpp"] = False

        return result

    @staticmethod
    def list_models() -> Dict[str, Dict[str, str]]:
        """List all available German-OCR models for Ollama backend.

        Returns:
            Dictionary of available models with their details
        """
        from german_ocr.ollama_backend import list_available_models
        return list_available_models()
