# Security Policy

## Unterstützte Versionen

Die folgenden Versionen von German-OCR werden aktuell mit Sicherheitsupdates unterstützt:

| Version | Status | Unterstützung |
| ------- | ------ | ------------- |
| Cloud API (Ultra/Pro/Turbo) | Aktiv | :white_check_mark: |
| Python SDK (latest) | Aktiv | :white_check_mark: |
| Node.js SDK (latest) | Aktiv | :white_check_mark: |
| PHP SDK (latest) | Aktiv | :white_check_mark: |
| Ollama Integration | Aktiv | :white_check_mark: |
| llama.cpp Integration | Aktiv | :white_check_mark: |

Wir empfehlen, immer die neueste Version der SDKs zu verwenden.

## Sicherheitsmeldung

Wir nehmen die Sicherheit von German-OCR sehr ernst. Wenn Sie eine Sicherheitslücke entdecken, bitten wir Sie, diese verantwortungsvoll zu melden.

### So melden Sie eine Sicherheitslücke

1. **E-Mail**: Senden Sie eine E-Mail an **security@german-ocr.de**
2. **Betreff**: Verwenden Sie "[SECURITY] Kurze Beschreibung des Problems"
3. **Inhalt**: Beschreiben Sie die Schwachstelle so detailliert wie möglich:
   - Art der Schwachstelle
   - Betroffene Komponente (Cloud API, SDK, lokale Installation)
   - Schritte zur Reproduktion
   - Potenzielle Auswirkungen
   - Falls vorhanden: Lösungsvorschlag

### Was Sie erwarten können

| Schritt | Zeitrahmen |
| ------- | ---------- |
| Bestätigung des Eingangs | Innerhalb von 48 Stunden |
| Erste Bewertung | Innerhalb von 5 Werktagen |
| Statusupdate | Mindestens alle 7 Tage |
| Behebung kritischer Lücken | Höchste Priorität |

### Nach der Meldung

- **Akzeptiert**: Wir arbeiten an einem Fix und informieren Sie, sobald dieser verfügbar ist. Nach Veröffentlichung des Fixes werden Sie (falls gewünscht) in unserer Security Hall of Fame erwähnt.
- **Abgelehnt**: Wir erklären Ihnen, warum die Meldung nicht als Sicherheitslücke eingestuft wurde.

## Datenschutz & DSGVO

German-OCR bietet DSGVO-konforme Verarbeitung:

- **Cloud Turbo**: Verarbeitung ausschließlich in Frankfurt (Deutschland)
- **Lokale Installation**: Vollständig offline-fähig via Ollama oder llama.cpp
- **Keine Datenspeicherung**: Dokumente werden nach der Verarbeitung nicht gespeichert

## Best Practices für Nutzer

1. **API-Keys schützen**: Speichern Sie API-Keys niemals im Quellcode
2. **HTTPS verwenden**: Alle API-Aufrufe nur über HTTPS
3. **Lokale Verarbeitung**: Für sensible Dokumente empfehlen wir die lokale Installation
4. **Updates**: Halten Sie SDKs und lokale Installationen aktuell

## Kontakt

- Website: [german-ocr.de](https://german-ocr.de)
- Security: security@german-ocr.de
- GitHub: [github.com/Keyvanhardani/german-ocr](https://github.com/Keyvanhardani/german-ocr)
