"""llama.cpp backend for German OCR using llama-cpp-python.

Supports:
- CPU inference (default)
- CUDA/GPU acceleration (NVIDIA)
- Metal (Apple Silicon)
- Vulkan (AMD/Intel/NVIDIA)
- OpenVINO (Intel NPU)

Installation:
    pip install llama-cpp-python

For GPU/NPU support:
    # CUDA (NVIDIA)
    CMAKE_ARGS="-DGGML_CUDA=on" pip install llama-cpp-python

    # Metal (Apple Silicon)
    CMAKE_ARGS="-DGGML_METAL=on" pip install llama-cpp-python

    # Vulkan (AMD/Intel/NVIDIA)
    CMAKE_ARGS="-DGGML_VULKAN=on" pip install llama-cpp-python

    # OpenVINO (Intel NPU)
    CMAKE_ARGS="-DGGML_OPENVINO=on" pip install llama-cpp-python
"""

import base64
import logging
import os
import shutil
import subprocess
import tempfile
from io import BytesIO
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from PIL import Image

from german_ocr.utils import load_image

logger = logging.getLogger(__name__)

# Model registry for llama.cpp GGUF models
LLAMACPP_MODELS = {
    "german-ocr-2b": {
        "engine": "German-OCR-Engine.2B.gguf",
        "mmproj": "German-OCR-Worker-2B.gguf",
        "size": "1.5GB",
        "base": "Qwen3-VL-2B",
        "context": 8192,
        "description": "Compact and fast, optimized for CPU/Edge",
        "hf_repo": "Keyven/german-ocr-2b-gguf",
    },
    "german-ocr-turbo": {
        "engine": "German-OCR-Turbo-Engine.gguf",
        "mmproj": "German-OCR-Turbo-Worker.gguf",
        "size": "1.9GB",
        "base": "Qwen3-VL-2B",
        "context": 8192,
        "description": "Turbo version with enhanced accuracy",
        "hf_repo": "Keyvan/german-ocr-turbo-gguf",
    },
}

DEFAULT_MODEL = "german-ocr-2b"


def get_model_paths(model_key: str, model_dir: Optional[Path] = None) -> Dict[str, Path]:
    """Get paths to model files.

    Args:
        model_key: Model identifier from LLAMACPP_MODELS
        model_dir: Directory containing model files (optional)

    Returns:
        Dict with 'engine' and 'mmproj' paths
    """
    if model_key not in LLAMACPP_MODELS:
        raise ValueError(f"Unknown model: {model_key}. Available: {list(LLAMACPP_MODELS.keys())}")

    model_info = LLAMACPP_MODELS[model_key]

    # Search paths
    search_dirs = []
    if model_dir:
        search_dirs.append(Path(model_dir))

    # Default search locations
    search_dirs.extend([
        Path.home() / ".cache" / "german-ocr" / model_key,
        Path.home() / ".german-ocr" / "models" / model_key,
        Path(__file__).parent.parent / "models" / model_key,
    ])

    for dir_path in search_dirs:
        engine_path = dir_path / model_info["engine"]
        mmproj_path = dir_path / model_info["mmproj"]

        if engine_path.exists() and mmproj_path.exists():
            return {"engine": engine_path, "mmproj": mmproj_path}

    raise FileNotFoundError(
        f"Model files not found for '{model_key}'.\n"
        f"Expected files:\n"
        f"  - {model_info['engine']}\n"
        f"  - {model_info['mmproj']}\n"
        f"Download from HuggingFace: {model_info.get('hf_repo', 'N/A')}"
    )


class LlamaCppBackend:
    """llama.cpp backend for vision-language OCR inference.

    This backend uses llama-cpp-python or subprocess to llama-mtmd-cli
    for multimodal (vision) model inference.

    Args:
        model_name: Model identifier (e.g., 'german-ocr-2b')
        model_dir: Custom directory containing model files
        n_gpu_layers: Number of layers to offload to GPU (-1 = all, 0 = CPU only)
        n_ctx: Context size (default: 8192)
        n_threads: Number of CPU threads (default: auto)
        device: Device selection ('auto', 'cuda', 'cpu', 'metal', 'vulkan')
        verbose: Enable verbose logging
    """

    def __init__(
        self,
        model_name: str = DEFAULT_MODEL,
        model_dir: Optional[Union[str, Path]] = None,
        n_gpu_layers: int = -1,
        n_ctx: int = 8192,
        n_threads: Optional[int] = None,
        device: str = "auto",
        verbose: bool = False,
    ) -> None:
        self.model_name = model_name
        self.n_gpu_layers = n_gpu_layers
        self.n_ctx = n_ctx
        self.n_threads = n_threads or os.cpu_count() or 4
        self.device = self._detect_device() if device == "auto" else device
        self.verbose = verbose

        # Get model paths
        model_dir_path = Path(model_dir) if model_dir else None
        try:
            self.model_paths = get_model_paths(model_name, model_dir_path)
        except FileNotFoundError as e:
            logger.warning(f"Model files not found: {e}")
            self.model_paths = None

        # Try to initialize llama-cpp-python, fallback to subprocess
        self._llama = None
        self._use_subprocess = False
        self._llama_cli_path = None

        self._init_backend()

        logger.info(
            f"LlamaCpp backend initialized: model={model_name}, "
            f"device={self.device}, gpu_layers={self.n_gpu_layers}"
        )

    def _detect_device(self) -> str:
        """Auto-detect best available device."""
        # Check for CUDA
        try:
            import torch
            if torch.cuda.is_available():
                return "cuda"
        except ImportError:
            pass

        # Check for Metal (macOS)
        import platform
        if platform.system() == "Darwin":
            return "metal"

        # Check for OpenVINO/NPU (Intel)
        if os.environ.get("GGML_OPENVINO"):
            return "openvino"

        # Check for Vulkan
        if os.environ.get("GGML_VULKAN"):
            return "vulkan"

        return "cpu"

    def _init_backend(self) -> None:
        """Initialize the inference backend."""
        # For vision models, llama-cpp-python support is limited
        # We use subprocess to llama-mtmd-cli for reliable inference

        self._llama_cli_path = self._find_llama_cli()

        if self._llama_cli_path:
            self._use_subprocess = True
            logger.info(f"Using llama-mtmd-cli: {self._llama_cli_path}")
        else:
            # Try native llama-cpp-python (experimental for vision)
            try:
                from llama_cpp import Llama
                logger.warning(
                    "llama-cpp-python vision support is experimental. "
                    "For best results, install llama-mtmd-cli."
                )
            except ImportError:
                raise RuntimeError(
                    "No llama.cpp backend available.\n"
                    "Install llama-cpp-python: pip install llama-cpp-python\n"
                    "Or provide llama-mtmd-cli in PATH"
                )

    def _find_llama_cli(self) -> Optional[Path]:
        """Find llama-mtmd-cli executable."""
        # Check PATH
        which = shutil.which("llama-mtmd-cli")
        if which:
            return Path(which)

        # Common locations
        search_paths = [
            Path.home() / ".local" / "bin" / "llama-mtmd-cli",
            Path("/usr/local/bin/llama-mtmd-cli"),
            Path("D:/German OCR Engine/llama-mtmd-cli.exe"),
            Path("C:/llama.cpp/build/bin/llama-mtmd-cli.exe"),
        ]

        for path in search_paths:
            if path.exists():
                return path

        return None

    def _image_to_temp_file(self, image: Image.Image) -> str:
        """Save image to temporary file."""
        temp_file = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
        image.save(temp_file.name, format="PNG")
        return temp_file.name

    def extract(
        self,
        image: Union[str, Path, Image.Image],
        prompt: Optional[str] = None,
        structured: bool = False,
        output_format: str = "text",
        max_tokens: int = 500,
        temperature: float = 0.1,
    ) -> Union[str, Dict[str, Any]]:
        """Extract text from image using llama.cpp.

        Args:
            image: Image path or PIL Image
            prompt: Custom extraction prompt
            structured: Return structured output with metadata
            output_format: Output format ('text', 'markdown', 'json')
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature

        Returns:
            Extracted text or structured dict
        """
        if self.model_paths is None:
            raise RuntimeError("Model files not found. Please download the model first.")

        pil_image = load_image(image)

        # Default prompts per format
        if prompt is None:
            prompts = {
                "text": "Transcribe all text from this image exactly as shown:",
                "markdown": "Extract all text from this document in markdown format:",
                "json": (
                    "Extract text and structure from this document as JSON with fields: "
                    "raw_text, document_type, structured_data (invoice_number, date, amounts, etc.)"
                ),
            }
            prompt = prompts.get(output_format, prompts["text"])

        if self._use_subprocess:
            result = self._extract_subprocess(pil_image, prompt, max_tokens, temperature)
        else:
            result = self._extract_native(pil_image, prompt, max_tokens, temperature)

        if structured:
            return {
                "text": result,
                "model": self.model_name,
                "backend": "llama.cpp",
                "device": self.device,
                "format": output_format,
            }
        return result

    def _extract_subprocess(
        self,
        image: Image.Image,
        prompt: str,
        max_tokens: int,
        temperature: float,
    ) -> str:
        """Extract using llama-mtmd-cli subprocess."""
        # Save image to temp file
        temp_image = self._image_to_temp_file(image)

        try:
            cmd = [
                str(self._llama_cli_path),
                "-m", str(self.model_paths["engine"]),
                "--mmproj", str(self.model_paths["mmproj"]),
                "--image", temp_image,
                "-p", prompt,
                "-n", str(max_tokens),
                "--temp", str(temperature),
            ]

            # GPU layers
            if self.n_gpu_layers != 0:
                cmd.extend(["-ngl", str(self.n_gpu_layers)])

            # Threads
            cmd.extend(["-t", str(self.n_threads)])

            if self.verbose:
                logger.debug(f"Running: {' '.join(cmd)}")

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=120,
                encoding="utf-8",
                errors="replace",
            )

            # Extract text from stdout (logs go to stderr)
            return result.stdout.strip()

        finally:
            # Cleanup temp file
            try:
                os.unlink(temp_image)
            except Exception:
                pass

    def _extract_native(
        self,
        image: Image.Image,
        prompt: str,
        max_tokens: int,
        temperature: float,
    ) -> str:
        """Extract using native llama-cpp-python (experimental)."""
        raise NotImplementedError(
            "Native llama-cpp-python vision support not yet implemented. "
            "Please use subprocess mode with llama-mtmd-cli."
        )

    def extract_batch(
        self,
        images: List[Union[str, Path, Image.Image]],
        prompt: Optional[str] = None,
        structured: bool = False,
        output_format: str = "text",
    ) -> List[Union[str, Dict[str, Any]]]:
        """Extract text from multiple images."""
        results = []
        for i, img in enumerate(images):
            try:
                result = self.extract(img, prompt, structured, output_format)
                results.append(result)
                logger.info(f"Processed {i+1}/{len(images)}")
            except Exception as e:
                logger.error(f"Failed image {i+1}: {e}")
                results.append({"text": "", "error": str(e)} if structured else "")
        return results

    @staticmethod
    def is_available() -> bool:
        """Check if llama.cpp backend is available."""
        # Check for llama-mtmd-cli
        if shutil.which("llama-mtmd-cli"):
            return True

        # Check known paths
        known_paths = [
            Path("D:/German OCR Engine/llama-mtmd-cli.exe"),
            Path.home() / ".local" / "bin" / "llama-mtmd-cli",
        ]
        for path in known_paths:
            if path.exists():
                return True

        # Check for llama-cpp-python
        try:
            import llama_cpp
            return True
        except ImportError:
            pass

        return False

    @staticmethod
    def get_device_info() -> Dict[str, Any]:
        """Get information about available compute devices."""
        info = {
            "cpu": True,
            "cpu_threads": os.cpu_count(),
            "cuda": False,
            "metal": False,
            "vulkan": False,
            "openvino": False,
        }

        # CUDA
        try:
            import torch
            info["cuda"] = torch.cuda.is_available()
            if info["cuda"]:
                info["cuda_devices"] = [
                    torch.cuda.get_device_name(i)
                    for i in range(torch.cuda.device_count())
                ]
        except ImportError:
            pass

        # Metal (Apple Silicon)
        import platform
        if platform.system() == "Darwin":
            info["metal"] = True

        # OpenVINO (Intel NPU)
        try:
            import openvino
            info["openvino"] = True
        except ImportError:
            pass

        return info

    @staticmethod
    def list_models() -> Dict[str, Dict[str, str]]:
        """List available llama.cpp models."""
        return LLAMACPP_MODELS.copy()
