"""
German-OCR Cloud Client - API-Wrapper für api.german-ocr.de

Einfacher Client zum Senden von Dokumenten an die German-OCR Cloud API.

Beispiel:
    from german_ocr import CloudClient

    client = CloudClient(api_key="dein-api-key")
    result = client.analyze("rechnung.pdf", output_format="json")
    print(result.text)

Entwickelt bei Keyvan.ai
"""

import os
import time
import logging
from pathlib import Path
from typing import Optional, Union, BinaryIO, Callable, Any
from dataclasses import dataclass, field

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logger = logging.getLogger(__name__)


# =============================================================================
# Exceptions
# =============================================================================

class CloudError(Exception):
    """Basis-Exception für Cloud-API-Fehler."""
    def __init__(self, message: str, code: Optional[str] = None):
        self.message = message
        self.code = code
        super().__init__(message)


class AuthenticationError(CloudError):
    """API-Key ungültig oder fehlt."""
    def __init__(self, message: str = "API-Key ungültig oder fehlt"):
        super().__init__(message, code="AUTH_ERROR")


class InsufficientBalanceError(CloudError):
    """Nicht genug Guthaben."""
    def __init__(self, message: str = "Nicht genug Guthaben"):
        super().__init__(message, code="INSUFFICIENT_BALANCE")


class RateLimitError(CloudError):
    """Rate Limit überschritten."""
    def __init__(self, message: str = "Rate Limit überschritten", retry_after: int = 60):
        self.retry_after = retry_after
        super().__init__(message, code="RATE_LIMIT")


class ProcessingError(CloudError):
    """Verarbeitungsfehler."""
    def __init__(self, message: str, job_id: Optional[str] = None):
        self.job_id = job_id
        super().__init__(message, code="PROCESSING_ERROR")


# =============================================================================
# Data Classes
# =============================================================================

@dataclass
class JobStatus:
    """Status eines OCR-Jobs."""
    job_id: str
    status: str  # pending, processing, completed, failed, cancelled
    current_page: int = 0
    total_pages: int = 0
    phase: str = ""  # scanning, processing, done
    error: Optional[str] = None

    @property
    def is_completed(self) -> bool:
        return self.status == "completed"

    @property
    def is_failed(self) -> bool:
        return self.status == "failed"

    @property
    def is_pending(self) -> bool:
        return self.status in ("pending", "processing")

    @classmethod
    def from_dict(cls, data: dict) -> "JobStatus":
        progress = data.get("progress", {})
        return cls(
            job_id=data.get("job_id", ""),
            status=data.get("status", "unknown"),
            current_page=progress.get("current_page", 0),
            total_pages=progress.get("total_pages", 0),
            phase=progress.get("phase", ""),
            error=data.get("error"),
        )


@dataclass
class CloudResult:
    """Ergebnis einer Cloud-OCR-Analyse."""
    job_id: str
    text: str
    output_format: str
    pages: int = 1
    processing_time_ms: int = 0
    raw_response: dict = field(default_factory=dict)

    @classmethod
    def from_job_response(cls, data: dict) -> "CloudResult":
        return cls(
            job_id=data.get("job_id", ""),
            text=data.get("result", ""),
            output_format=data.get("output_format", "text"),
            pages=data.get("page_count", 1),
            processing_time_ms=data.get("processing_time_ms", 0),
            raw_response=data,
        )


# =============================================================================
# Cloud Client
# =============================================================================

class CloudClient:
    """
    German-OCR Cloud API Client.

    Sendet Bilder/PDFs an die German-OCR Cloud API zur Verarbeitung.

    Beispiel:
        # Einfache Analyse
        client = CloudClient(api_key="...")
        result = client.analyze("rechnung.pdf")
        print(result.text)

        # Mit Optionen
        result = client.analyze(
            file="dokument.png",
            prompt="Extrahiere alle Rechnungsdaten",
            output_format="json"
        )

        # Async mit Progress-Callback
        def on_progress(status):
            print(f"Seite {status.current_page}/{status.total_pages}")

        result = client.analyze("grosses_dokument.pdf", on_progress=on_progress)
    """

    DEFAULT_BASE_URL = "https://api.german-ocr.de"
    DEFAULT_TIMEOUT = 60
    DEFAULT_POLL_INTERVAL = 1.0
    DEFAULT_MAX_WAIT = 600  # 10 Minuten für große PDFs

    # Unterstützte Output-Formate
    OUTPUT_FORMATS = {"json", "markdown", "md", "text", "n8n"}

    # Unterstützte Dateiformate
    ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "pdf", "webp", "tiff", "bmp"}

    def __init__(
        self,
        api_key: Optional[str] = None,
        api_secret: Optional[str] = None,
        base_url: Optional[str] = None,
        timeout: int = DEFAULT_TIMEOUT,
        max_retries: int = 3,
    ):
        """
        Initialisiert den Cloud-Client.

        Args:
            api_key: API-Key (z.B. gocr_xxxxxxxx).
                     Falls nicht angegeben, wird GERMAN_OCR_API_KEY verwendet.
            api_secret: API-Secret (64 Zeichen).
                        Falls nicht angegeben, wird GERMAN_OCR_API_SECRET verwendet.
            base_url: Basis-URL der API (Standard: https://api.german-ocr.de)
            timeout: Request-Timeout in Sekunden
            max_retries: Maximale Anzahl automatischer Wiederholungen
        """
        self.api_key = api_key or os.environ.get("GERMAN_OCR_API_KEY")
        self.api_secret = api_secret or os.environ.get("GERMAN_OCR_API_SECRET")

        if not self.api_key:
            raise AuthenticationError(
                "API-Key erforderlich. Setze GERMAN_OCR_API_KEY oder übergebe api_key."
            )
        if not self.api_secret:
            raise AuthenticationError(
                "API-Secret erforderlich. Setze GERMAN_OCR_API_SECRET oder übergebe api_secret."
            )

        self.base_url = (
            base_url or
            os.environ.get("GERMAN_OCR_BASE_URL") or
            self.DEFAULT_BASE_URL
        ).rstrip("/")
        self.timeout = timeout

        # Session mit Retry-Logik
        self._session = requests.Session()
        retry_strategy = Retry(
            total=max_retries,
            backoff_factor=0.5,
            status_forcelist=[500, 502, 503, 504],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self._session.mount("https://", adapter)
        self._session.mount("http://", adapter)

        logger.info(f"CloudClient initialisiert: {self.base_url}")

    def _headers(self) -> dict:
        """Erstellt die HTTP-Headers."""
        return {
            "Authorization": f"Bearer {self.api_key}:{self.api_secret}",
            "User-Agent": "german-ocr-python/0.5.0",
        }

    def _request(self, method: str, endpoint: str, **kwargs) -> dict:
        """Führt einen API-Request aus."""
        url = f"{self.base_url}/v1{endpoint}"

        if "headers" not in kwargs:
            kwargs["headers"] = {}
        kwargs["headers"].update(self._headers())

        if "timeout" not in kwargs:
            kwargs["timeout"] = self.timeout

        try:
            response = self._session.request(method, url, **kwargs)
        except requests.exceptions.Timeout:
            raise CloudError("Request Timeout", code="TIMEOUT")
        except requests.exceptions.ConnectionError:
            raise CloudError("Verbindungsfehler zur API", code="CONNECTION_ERROR")

        # Error Handling
        if response.status_code == 401:
            raise AuthenticationError()
        elif response.status_code == 402:
            raise InsufficientBalanceError()
        elif response.status_code == 403:
            raise AuthenticationError("Zugriff verweigert")
        elif response.status_code == 429:
            data = response.json() if response.text else {}
            raise RateLimitError(
                data.get("message", "Rate Limit überschritten"),
                retry_after=data.get("retry_after", 60),
            )
        elif response.status_code >= 400:
            data = response.json() if response.text else {}
            raise CloudError(
                data.get("error", f"HTTP {response.status_code}"),
                code=data.get("code"),
            )

        return response.json()

    def _prepare_file(
        self,
        file: Union[str, Path, BinaryIO, bytes],
        filename: Optional[str] = None,
    ) -> tuple:
        """Bereitet die Datei für den Upload vor."""
        if isinstance(file, (str, Path)):
            path = Path(file)
            if not path.exists():
                raise FileNotFoundError(f"Datei nicht gefunden: {file}")

            with open(path, "rb") as f:
                file_data = f.read()
            filename = filename or path.name
        elif isinstance(file, bytes):
            file_data = file
            filename = filename or "document.pdf"
        else:
            # BinaryIO
            file_data = file.read()
            filename = filename or getattr(file, "name", "document.pdf")

        # Dateiendung prüfen
        ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
        if ext not in self.ALLOWED_EXTENSIONS:
            raise ValueError(
                f"Ungültiges Dateiformat: {ext}. "
                f"Erlaubt: {', '.join(self.ALLOWED_EXTENSIONS)}"
            )

        # MIME-Type
        mime_types = {
            "png": "image/png",
            "jpg": "image/jpeg",
            "jpeg": "image/jpeg",
            "pdf": "application/pdf",
            "webp": "image/webp",
            "tiff": "image/tiff",
            "bmp": "image/bmp",
        }
        content_type = mime_types.get(ext, "application/octet-stream")

        return filename, file_data, content_type

    # Verfügbare Modelle
    MODELS = {
        "local": "German-OCR Turbo - Lokal, DSGVO-konform",
        "cloud_fast": "German-OCR Pro - Schnelle Cloud",
        "cloud": "German-OCR Ultra - Maximale Präzision",
    }

    def submit(
        self,
        file: Union[str, Path, BinaryIO, bytes],
        prompt: Optional[str] = None,
        output_format: str = "text",
        model: str = "cloud_fast",
        filename: Optional[str] = None,
        # Backward compatibility
        provider: Optional[str] = None,
    ) -> JobStatus:
        """
        Sendet ein Dokument zur Verarbeitung.

        Args:
            file: Dateipfad, Datei-Objekt oder Bytes
            prompt: Optionaler Prompt für die Extraktion
            output_format: Ausgabeformat (json, markdown, text, n8n)
            model: OCR-Modell
                   - "local": German-OCR Turbo - Lokal, DSGVO
                   - "cloud_fast": German-OCR Pro - Schnelle Cloud
                   - "cloud": German-OCR Ultra - Maximale Präzision
            filename: Dateiname (optional)
            provider: DEPRECATED - Verwende "model" stattdessen

        Returns:
            JobStatus mit job_id
        """
        # Backward compatibility: provider -> model
        if provider is not None:
            logger.warning("Parameter 'provider' ist veraltet. Bitte 'model' verwenden.")
            model = provider

        # Modell validieren
        if model not in self.MODELS:
            raise ValueError(
                f"Ungültiges Modell: {model}. "
                f"Erlaubt: {', '.join(self.MODELS.keys())}"
            )

        # Output-Format validieren
        output_format = output_format.lower()
        if output_format == "md":
            output_format = "markdown"
        if output_format not in self.OUTPUT_FORMATS:
            raise ValueError(
                f"Ungültiges Output-Format: {output_format}. "
                f"Erlaubt: {', '.join(self.OUTPUT_FORMATS)}"
            )

        # Datei vorbereiten
        filename, file_data, content_type = self._prepare_file(file, filename)

        # Request bauen
        files = {"file": (filename, file_data, content_type)}
        data = {"model": model}
        if prompt:
            data["prompt"] = prompt

        # Senden
        response = self._request("POST", "/analyze", files=files, data=data)

        return JobStatus(
            job_id=response["job_id"],
            status=response.get("status", "pending"),
        )

    def get_job(self, job_id: str) -> JobStatus:
        """
        Ruft den Status eines Jobs ab.

        Args:
            job_id: ID des Jobs

        Returns:
            JobStatus mit aktuellem Status
        """
        response = self._request("GET", f"/jobs/{job_id}")
        return JobStatus.from_dict(response)

    def cancel_job(self, job_id: str) -> bool:
        """
        Bricht einen laufenden Job ab.

        Args:
            job_id: ID des Jobs

        Returns:
            True wenn erfolgreich
        """
        try:
            response = self._request("DELETE", f"/jobs/{job_id}")
            return response.get("status") == "cancelled"
        except CloudError:
            return False

    def wait_for_result(
        self,
        job_id: str,
        poll_interval: float = DEFAULT_POLL_INTERVAL,
        max_wait: float = DEFAULT_MAX_WAIT,
        on_progress: Optional[Callable[[JobStatus], None]] = None,
    ) -> CloudResult:
        """
        Wartet auf das Ergebnis eines Jobs.

        Args:
            job_id: ID des Jobs
            poll_interval: Abfrageintervall in Sekunden
            max_wait: Maximale Wartezeit in Sekunden
            on_progress: Callback für Status-Updates

        Returns:
            CloudResult mit dem Ergebnis
        """
        start_time = time.time()

        while True:
            job = self.get_job(job_id)

            # Progress-Callback
            if on_progress:
                on_progress(job)

            if job.is_completed:
                # Ergebnis aus der Job-Response
                response = self._request("GET", f"/jobs/{job_id}")
                return CloudResult.from_job_response(response)

            if job.is_failed:
                raise ProcessingError(
                    job.error or "Verarbeitung fehlgeschlagen",
                    job_id=job_id,
                )

            # Timeout prüfen
            elapsed = time.time() - start_time
            if elapsed >= max_wait:
                raise CloudError(
                    f"Timeout nach {max_wait} Sekunden",
                    code="TIMEOUT",
                )

            time.sleep(poll_interval)

    def analyze(
        self,
        file: Union[str, Path, BinaryIO, bytes],
        prompt: Optional[str] = None,
        output_format: str = "text",
        model: str = "cloud_fast",
        filename: Optional[str] = None,
        poll_interval: float = DEFAULT_POLL_INTERVAL,
        max_wait: float = DEFAULT_MAX_WAIT,
        on_progress: Optional[Callable[[JobStatus], None]] = None,
        # Backward compatibility
        provider: Optional[str] = None,
    ) -> CloudResult:
        """
        Analysiert ein Dokument und wartet auf das Ergebnis.

        Kombination aus submit() und wait_for_result().

        Args:
            file: Dateipfad, Datei-Objekt oder Bytes
            prompt: Optionaler Prompt für die Extraktion
            output_format: Ausgabeformat (json, markdown, text, n8n)
            model: OCR-Modell
                   - "local": German-OCR Turbo - Lokal, DSGVO
                   - "cloud_fast": German-OCR Pro - Schnelle Cloud
                   - "cloud": German-OCR Ultra - Maximale Präzision
            filename: Dateiname (optional)
            poll_interval: Abfrageintervall in Sekunden
            max_wait: Maximale Wartezeit in Sekunden
            on_progress: Callback für Status-Updates
            provider: DEPRECATED - Verwende "model" stattdessen

        Returns:
            CloudResult mit dem Ergebnis

        Beispiel:
            result = client.analyze(
                "rechnung.pdf",
                prompt="Extrahiere Rechnungsnummer und Betrag",
                model="cloud_fast"  # German-OCR Pro
            )
            print(result.text)
        """
        # Backward compatibility
        if provider is not None:
            model = provider

        job = self.submit(
            file=file,
            prompt=prompt,
            output_format=output_format,
            model=model,
            filename=filename,
        )

        logger.info(f"Job gestartet: {job.job_id}")

        return self.wait_for_result(
            job_id=job.job_id,
            poll_interval=poll_interval,
            max_wait=max_wait,
            on_progress=on_progress,
        )

    def get_balance(self) -> dict:
        """Ruft den aktuellen Kontostand ab."""
        return self._request("GET", "/balance")

    def get_usage(self) -> dict:
        """Ruft die Nutzungsstatistik ab."""
        return self._request("GET", "/usage")

    def __enter__(self):
        """Context Manager Support."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Schließt die Session."""
        self._session.close()

    def close(self):
        """Schließt die Session."""
        self._session.close()
