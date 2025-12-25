"""
Tests für den German-OCR Cloud Client.

Entwickelt bei Keyvan.ai
"""

import os
import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

from german_ocr.cloud_client import (
    CloudClient,
    CloudResult,
    JobStatus,
    CloudError,
    AuthenticationError,
    InsufficientBalanceError,
    RateLimitError,
    ProcessingError,
)


class TestCloudClientInit:
    """Tests für die Initialisierung des CloudClient."""

    def test_init_with_api_key(self):
        """Test: Initialisierung mit API-Key."""
        client = CloudClient(api_key="test-key")
        assert client.api_key == "test-key"
        assert client.base_url == "https://api.german-ocr.de"

    def test_init_with_env_var(self):
        """Test: Initialisierung mit Umgebungsvariable."""
        with patch.dict(os.environ, {"GERMAN_OCR_API_KEY": "env-key"}):
            client = CloudClient()
            assert client.api_key == "env-key"

    def test_init_without_api_key_raises(self):
        """Test: Fehler wenn kein API-Key vorhanden."""
        with patch.dict(os.environ, {}, clear=True):
            # Entferne GERMAN_OCR_API_KEY falls vorhanden
            os.environ.pop("GERMAN_OCR_API_KEY", None)
            with pytest.raises(AuthenticationError):
                CloudClient()

    def test_init_with_custom_base_url(self):
        """Test: Initialisierung mit eigener Base-URL."""
        client = CloudClient(api_key="test-key", base_url="https://custom.api.de")
        assert client.base_url == "https://custom.api.de"

    def test_init_strips_trailing_slash(self):
        """Test: Trailing Slash wird entfernt."""
        client = CloudClient(api_key="test-key", base_url="https://api.de/")
        assert client.base_url == "https://api.de"


class TestJobStatus:
    """Tests für JobStatus Dataclass."""

    def test_from_dict(self):
        """Test: JobStatus.from_dict()."""
        data = {
            "job_id": "abc-123",
            "status": "processing",
            "progress": {
                "current_page": 2,
                "total_pages": 5,
                "phase": "scanning",
            }
        }
        status = JobStatus.from_dict(data)
        assert status.job_id == "abc-123"
        assert status.status == "processing"
        assert status.current_page == 2
        assert status.total_pages == 5
        assert status.phase == "scanning"

    def test_is_completed(self):
        """Test: is_completed Property."""
        completed = JobStatus(job_id="1", status="completed")
        pending = JobStatus(job_id="2", status="pending")
        assert completed.is_completed is True
        assert pending.is_completed is False

    def test_is_failed(self):
        """Test: is_failed Property."""
        failed = JobStatus(job_id="1", status="failed", error="Test error")
        pending = JobStatus(job_id="2", status="pending")
        assert failed.is_failed is True
        assert pending.is_failed is False


class TestCloudResult:
    """Tests für CloudResult Dataclass."""

    def test_from_job_response(self):
        """Test: CloudResult.from_job_response()."""
        data = {
            "job_id": "abc-123",
            "result": '{"invoice_number": "12345"}',
            "output_format": "json",
            "page_count": 3,
            "processing_time_ms": 1500,
        }
        result = CloudResult.from_job_response(data)
        assert result.job_id == "abc-123"
        assert result.text == '{"invoice_number": "12345"}'
        assert result.output_format == "json"
        assert result.pages == 3
        assert result.processing_time_ms == 1500


class TestCloudClientMethods:
    """Tests für CloudClient Methoden (mit Mocking)."""

    @pytest.fixture
    def client(self):
        """Erstellt einen Client für Tests."""
        return CloudClient(api_key="test-key")

    def test_headers(self, client):
        """Test: _headers() generiert korrekte Headers."""
        headers = client._headers()
        assert headers["Authorization"] == "Bearer test-key"
        assert "User-Agent" in headers

    @patch("requests.Session.request")
    def test_submit_success(self, mock_request, client):
        """Test: submit() erfolgreich."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "job_id": "job-123",
            "status": "pending"
        }
        mock_request.return_value = mock_response

        # Erstelle temporäre Testdatei
        test_file = Path(__file__).parent / "test_image.png"
        test_file.write_bytes(b"fake image data")

        try:
            job = client.submit(test_file, output_format="json")
            assert job.job_id == "job-123"
            assert job.status == "pending"
        finally:
            test_file.unlink()

    @patch("requests.Session.request")
    def test_get_job(self, mock_request, client):
        """Test: get_job() erfolgreich."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "job_id": "job-123",
            "status": "completed",
            "progress": {"current_page": 1, "total_pages": 1}
        }
        mock_request.return_value = mock_response

        status = client.get_job("job-123")
        assert status.job_id == "job-123"
        assert status.is_completed

    @patch("requests.Session.request")
    def test_cancel_job(self, mock_request, client):
        """Test: cancel_job() erfolgreich."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"status": "cancelled"}
        mock_request.return_value = mock_response

        result = client.cancel_job("job-123")
        assert result is True

    @patch("requests.Session.request")
    def test_error_401_raises_auth_error(self, mock_request, client):
        """Test: 401 wirft AuthenticationError."""
        mock_response = Mock()
        mock_response.status_code = 401
        mock_request.return_value = mock_response

        with pytest.raises(AuthenticationError):
            client.get_job("job-123")

    @patch("requests.Session.request")
    def test_error_402_raises_balance_error(self, mock_request, client):
        """Test: 402 wirft InsufficientBalanceError."""
        mock_response = Mock()
        mock_response.status_code = 402
        mock_request.return_value = mock_response

        with pytest.raises(InsufficientBalanceError):
            client.get_job("job-123")

    @patch("requests.Session.request")
    def test_error_429_raises_rate_limit_error(self, mock_request, client):
        """Test: 429 wirft RateLimitError."""
        mock_response = Mock()
        mock_response.status_code = 429
        mock_response.text = '{"message": "Too many requests", "retry_after": 30}'
        mock_response.json.return_value = {"message": "Too many requests", "retry_after": 30}
        mock_request.return_value = mock_response

        with pytest.raises(RateLimitError) as exc_info:
            client.get_job("job-123")
        assert exc_info.value.retry_after == 30


class TestOutputFormats:
    """Tests für Output-Format Validierung."""

    @pytest.fixture
    def client(self):
        return CloudClient(api_key="test-key")

    def test_valid_formats(self, client):
        """Test: Gültige Formate werden akzeptiert."""
        valid_formats = ["json", "markdown", "md", "text", "n8n"]
        for fmt in valid_formats:
            # Sollte keinen Fehler werfen
            assert fmt.lower() in client.OUTPUT_FORMATS or fmt == "md"

    def test_invalid_format_raises(self, client):
        """Test: Ungültiges Format wirft Fehler."""
        with pytest.raises(ValueError) as exc_info:
            # Erstelle temporäre Testdatei
            test_file = Path(__file__).parent / "test_image.png"
            test_file.write_bytes(b"fake image data")
            try:
                client.submit(test_file, output_format="invalid")
            finally:
                test_file.unlink()
        assert "Ungültiges Output-Format" in str(exc_info.value)


class TestFileValidation:
    """Tests für Datei-Validierung."""

    @pytest.fixture
    def client(self):
        return CloudClient(api_key="test-key")

    def test_file_not_found_raises(self, client):
        """Test: Nicht existierende Datei wirft Fehler."""
        with pytest.raises(FileNotFoundError):
            client.submit("/nicht/existierend.pdf")

    def test_invalid_extension_raises(self, client):
        """Test: Ungültige Dateiendung wirft Fehler."""
        test_file = Path(__file__).parent / "test.xyz"
        test_file.write_bytes(b"test data")
        try:
            with pytest.raises(ValueError) as exc_info:
                client.submit(test_file)
            assert "Ungültiges Dateiformat" in str(exc_info.value)
        finally:
            test_file.unlink()

    def test_valid_extensions(self, client):
        """Test: Gültige Dateiendungen werden akzeptiert."""
        valid_extensions = ["png", "jpg", "jpeg", "pdf", "webp", "tiff", "bmp"]
        for ext in valid_extensions:
            assert ext in client.ALLOWED_EXTENSIONS


class TestContextManager:
    """Tests für Context Manager Support."""

    def test_context_manager(self):
        """Test: with-Statement funktioniert."""
        with CloudClient(api_key="test-key") as client:
            assert client.api_key == "test-key"
        # Session sollte geschlossen sein


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
