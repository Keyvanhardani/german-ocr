"""
German-OCR-Turbo-FC Document Extractor
Strukturierte Datenextraktion aus deutschen Dokumenten
Entwickelt von Keyvan (Keyvan.ai)
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Optional, Union, Any
from dataclasses import dataclass, field

try:
    import ollama
except ImportError:
    ollama = None


@dataclass
class InvoiceData:
    """Strukturierte Rechnungsdaten"""
    type: str = "invoice"
    invoice_number: str = ""
    date: str = ""
    sender: Dict[str, str] = field(default_factory=dict)
    recipient: Dict[str, str] = field(default_factory=dict)
    items: List[Dict[str, Any]] = field(default_factory=list)
    totals: Dict[str, float] = field(default_factory=dict)
    raw_json: Dict = field(default_factory=dict)


@dataclass
class FormData:
    """Strukturierte Formulardaten"""
    type: str = "form"
    title: str = ""
    fields: List[Dict[str, Any]] = field(default_factory=list)
    raw_json: Dict = field(default_factory=dict)


@dataclass
class DocumentData:
    """Allgemeine Dokumentdaten"""
    type: str = "document"
    doc_type: str = ""
    fields: List[Dict[str, Any]] = field(default_factory=list)
    raw_json: Dict = field(default_factory=dict)


@dataclass
class ExtractionResult:
    """Ergebnis einer Extraktion"""
    success: bool
    data: Union[InvoiceData, FormData, DocumentData, None] = None
    raw_response: str = ""
    error: Optional[str] = None


class DocumentExtractor:
    """
    Extrahiert strukturierte Daten aus deutschen Dokumenten.

    Verwendet German-OCR-Turbo-FC fuer JSON-Output.

    Beispiel:
        extractor = DocumentExtractor()
        result = extractor.extract("rechnung.png")

        if result.success:
            print(f"Rechnungsnummer: {result.data.invoice_number}")
            print(f"Gesamtbetrag: {result.data.totals.get('total')} EUR")
    """

    DEFAULT_MODEL = "Keyvan/german-ocr-turbo-fc"

    def __init__(
        self,
        model: str = DEFAULT_MODEL,
        host: Optional[str] = None
    ):
        """
        Initialisiert den Document Extractor.

        Args:
            model: Ollama Modellname (Standard: Keyvan/german-ocr-turbo-fc)
            host: Optional - Ollama Host URL
        """
        if ollama is None:
            raise ImportError("ollama package not installed. Run: pip install ollama")

        self.model = model
        self.host = host
        self._client = ollama.Client(host=host) if host else None

    def _call_ollama(self, prompt: str, image_path: str) -> str:
        """Ruft Ollama mit Bild auf"""
        messages = [{
            'role': 'user',
            'content': prompt,
            'images': [image_path]
        }]

        if self._client:
            response = self._client.chat(model=self.model, messages=messages)
        else:
            response = ollama.chat(model=self.model, messages=messages)

        return response['message']['content']

    def _parse_json(self, content: str) -> Optional[Dict]:
        """Extrahiert JSON aus der Antwort"""
        # Entferne ```json und ``` Markdown
        if '```json' in content:
            content = content.split('```json')[1].split('```')[0]
        elif '```' in content:
            content = content.split('```')[1].split('```')[0]

        # Versuche JSON zu parsen
        try:
            return json.loads(content.strip())
        except json.JSONDecodeError:
            # Fallback: Suche nach JSON-Objekt
            json_match = re.search(r'\{[\s\S]*\}', content)
            if json_match:
                try:
                    return json.loads(json_match.group())
                except json.JSONDecodeError:
                    pass

        return None

    def _to_invoice_data(self, data: Dict) -> InvoiceData:
        """Konvertiert Dict zu InvoiceData"""
        return InvoiceData(
            type=data.get('type', 'invoice'),
            invoice_number=data.get('invoice_number', ''),
            date=data.get('date', ''),
            sender=data.get('sender', {}),
            recipient=data.get('recipient', {}),
            items=data.get('items', []),
            totals=data.get('totals', {}),
            raw_json=data
        )

    def _to_form_data(self, data: Dict) -> FormData:
        """Konvertiert Dict zu FormData"""
        return FormData(
            type=data.get('type', 'form'),
            title=data.get('title', ''),
            fields=data.get('fields', []),
            raw_json=data
        )

    def _to_document_data(self, data: Dict) -> DocumentData:
        """Konvertiert Dict zu DocumentData"""
        return DocumentData(
            type=data.get('type', 'document'),
            doc_type=data.get('doc_type', ''),
            fields=data.get('fields', []),
            raw_json=data
        )

    def extract(
        self,
        image_path: Union[str, Path],
        prompt: Optional[str] = None
    ) -> ExtractionResult:
        """
        Extrahiert strukturierte Daten aus einem Dokument.

        Args:
            image_path: Pfad zum Bild
            prompt: Optional - Eigener Prompt (Standard: automatisch)

        Returns:
            ExtractionResult mit strukturierten Daten
        """
        image_path = str(image_path)

        if not Path(image_path).exists():
            return ExtractionResult(
                success=False,
                error=f"Datei nicht gefunden: {image_path}"
            )

        if prompt is None:
            prompt = "Analysiere dieses Dokument und extrahiere alle Daten als JSON"

        try:
            # Ollama aufrufen
            raw_response = self._call_ollama(prompt, image_path)

            # JSON parsen
            data = self._parse_json(raw_response)

            if data is None:
                return ExtractionResult(
                    success=False,
                    raw_response=raw_response,
                    error="Konnte JSON nicht parsen"
                )

            # Typ erkennen und konvertieren
            doc_type = data.get('type', 'document')

            if doc_type == 'invoice':
                result_data = self._to_invoice_data(data)
            elif doc_type == 'form':
                result_data = self._to_form_data(data)
            else:
                result_data = self._to_document_data(data)

            return ExtractionResult(
                success=True,
                data=result_data,
                raw_response=raw_response
            )

        except Exception as e:
            return ExtractionResult(
                success=False,
                error=str(e)
            )

    def extract_invoice(
        self,
        image_path: Union[str, Path]
    ) -> ExtractionResult:
        """
        Extrahiert Rechnungsdaten.

        Args:
            image_path: Pfad zur Rechnung

        Returns:
            ExtractionResult mit InvoiceData
        """
        return self.extract(
            image_path,
            prompt="Extrahiere alle Rechnungsdaten als JSON"
        )

    def extract_form(
        self,
        image_path: Union[str, Path]
    ) -> ExtractionResult:
        """
        Extrahiert Formulardaten.

        Args:
            image_path: Pfad zum Formular

        Returns:
            ExtractionResult mit FormData
        """
        return self.extract(
            image_path,
            prompt="Extrahiere alle Formularfelder als JSON"
        )

    def to_dict(self, result: ExtractionResult) -> Dict:
        """Konvertiert ExtractionResult zu Dict"""
        if result.data:
            return result.data.raw_json
        return {}

    def to_json(self, result: ExtractionResult, indent: int = 2) -> str:
        """Konvertiert ExtractionResult zu JSON-String"""
        return json.dumps(self.to_dict(result), indent=indent, ensure_ascii=False)
