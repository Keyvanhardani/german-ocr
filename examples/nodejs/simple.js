/**
 * German-OCR API - Einfaches Node.js Beispiel
 *
 * Dieses Skript zeigt, wie man ein einzelnes Dokument
 * an die German-OCR API sendet und das Ergebnis empfängt.
 *
 * Installation:
 *   npm install node-fetch form-data
 *
 * Verwendung:
 *   node simple.js <bildpfad>
 */

const fs = require('fs');
const path = require('path');
const FormData = require('form-data');
const fetch = require('node-fetch');

// API-Konfiguration
const API_CONFIG = {
  endpoint: 'https://api.german-ocr.de/v1/analyze',
  apiKey: 'gocr_079a85fb',
  apiSecret: '7c3fafb5efedcad69ba991ca1e96bce7f4929d769b4f1349fa0a28e98f4a462c'
};

/**
 * Analysiert ein Dokument mit der German-OCR API
 * @param {string} filePath - Pfad zur Bilddatei
 * @param {string} prompt - Optionaler Prompt für strukturierte Ausgabe
 * @param {string} model - Modell-Auswahl (german-ocr, german-ocr-pro, german-ocr-ultra)
 * @returns {Promise<Object>} - API-Antwort
 */
async function analyzeDocument(filePath, prompt = null, model = 'german-ocr-pro') {
  // Prüfe ob Datei existiert
  if (!fs.existsSync(filePath)) {
    throw new Error(`Datei nicht gefunden: ${filePath}`);
  }

  // FormData vorbereiten
  const form = new FormData();
  form.append('file', fs.createReadStream(filePath));

  if (prompt) {
    form.append('prompt', prompt);
  }

  form.append('model', model);

  // Auth-Header vorbereiten
  const authToken = `${API_CONFIG.apiKey}:${API_CONFIG.apiSecret}`;

  console.log('📤 Sende Dokument an German-OCR API...');
  console.log(`   Datei: ${path.basename(filePath)}`);
  console.log(`   Modell: ${model}`);
  if (prompt) {
    console.log(`   Prompt: ${prompt}`);
  }
  console.log('');

  const startTime = Date.now();

  try {
    const response = await fetch(API_CONFIG.endpoint, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${authToken}`,
        ...form.getHeaders()
      },
      body: form
    });

    const responseTime = Date.now() - startTime;

    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`API-Fehler (${response.status}): ${errorText}`);
    }

    const result = await response.json();

    console.log('✅ Erfolgreich verarbeitet!');
    console.log(`⏱️  Antwortzeit: ${responseTime}ms`);
    console.log('');
    console.log('📄 Ergebnis:');
    console.log('─'.repeat(60));
    console.log(JSON.stringify(result, null, 2));
    console.log('─'.repeat(60));

    return result;

  } catch (error) {
    const responseTime = Date.now() - startTime;
    console.error('❌ Fehler bei der Verarbeitung:');
    console.error(`   ${error.message}`);
    console.error(`   Antwortzeit: ${responseTime}ms`);
    throw error;
  }
}

/**
 * Hauptfunktion
 */
async function main() {
  // Kommandozeilenargumente prüfen
  const args = process.argv.slice(2);

  if (args.length === 0) {
    console.log('❌ Fehler: Kein Bildpfad angegeben');
    console.log('');
    console.log('Verwendung:');
    console.log('  node simple.js <bildpfad> [prompt] [model]');
    console.log('');
    console.log('Beispiele:');
    console.log('  node simple.js rechnung.jpg');
    console.log('  node simple.js rechnung.pdf "Extrahiere Rechnungsnummer und Datum"');
    console.log('  node simple.js rechnung.jpg "" german-ocr-ultra');
    console.log('');
    console.log('Modell-Optionen:');
    console.log('  german-ocr-ultra  - Maximale Präzision');
    console.log('  german-ocr-pro    - Schnell und zuverlässig (Standard)');
    console.log('  german-ocr        - DSGVO-konform, lokale Verarbeitung');
    process.exit(1);
  }

  const filePath = args[0];
  const prompt = args[1] || null;
  const model = args[2] || 'german-ocr-pro';

  try {
    await analyzeDocument(filePath, prompt, model);
    console.log('');
    console.log('✨ Fertig!');
  } catch (error) {
    console.log('');
    console.log('💥 Abbruch aufgrund von Fehler');
    process.exit(1);
  }
}

// Nur ausführen wenn direkt aufgerufen
if (require.main === module) {
  main();
}

module.exports = { analyzeDocument };
