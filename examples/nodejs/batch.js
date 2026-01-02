/**
 * German-OCR API - Batch-Verarbeitung (Node.js)
 *
 * Dieses Skript zeigt, wie man mehrere Dokumente
 * parallel verarbeiten kann.
 *
 * Installation:
 *   npm install node-fetch form-data
 *
 * Verwendung:
 *   node batch.js <datei1> <datei2> <datei3> ...
 */

const fs = require('fs');
const path = require('path');
const FormData = require('form-data');
const fetch = require('node-fetch');

// API-Konfiguration
const API_CONFIG = {
  endpoint: 'https://api.german-ocr.de/v1/analyze',
  apiKey: process.env.GERMAN_OCR_API_KEY || 'YOUR_API_KEY',
  apiSecret: process.env.GERMAN_OCR_API_SECRET || 'YOUR_API_SECRET'
};

/**
 * Analysiert ein einzelnes Dokument
 * @param {string} filePath - Pfad zur Bilddatei
 * @param {number} index - Index in der Batch
 * @returns {Promise<Object>} - Ergebnis mit Statistiken
 */
async function processDocument(filePath, index) {
  const fileName = path.basename(filePath);

  // Prüfe ob Datei existiert
  if (!fs.existsSync(filePath)) {
    return {
      index,
      fileName,
      success: false,
      error: 'Datei nicht gefunden',
      responseTime: 0
    };
  }

  // FormData vorbereiten
  const form = new FormData();
  form.append('file', fs.createReadStream(filePath));
  form.append('model', 'german-ocr-pro'); // Schnell und zuverlässig für Batch

  // Auth-Header
  const authToken = `${API_CONFIG.apiKey}:${API_CONFIG.apiSecret}`;

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
      return {
        index,
        fileName,
        success: false,
        error: `API-Fehler (${response.status}): ${errorText}`,
        responseTime
      };
    }

    const result = await response.json();

    return {
      index,
      fileName,
      success: true,
      result,
      responseTime,
      textLength: result.text ? result.text.length : 0
    };

  } catch (error) {
    const responseTime = Date.now() - startTime;
    return {
      index,
      fileName,
      success: false,
      error: error.message,
      responseTime
    };
  }
}

/**
 * Verarbeitet mehrere Dokumente parallel
 * @param {string[]} filePaths - Array von Dateipfaden
 * @returns {Promise<Object>} - Batch-Statistiken
 */
async function processBatch(filePaths) {
  console.log('🚀 Starte Batch-Verarbeitung...');
  console.log(`   Dokumente: ${filePaths.length}`);
  console.log(`   Modell: german-ocr-pro (schnell und zuverlässig)`);
  console.log('');

  const batchStartTime = Date.now();

  // Alle Dokumente parallel verarbeiten
  const promises = filePaths.map((filePath, index) =>
    processDocument(filePath, index)
  );

  const results = await Promise.all(promises);
  const totalTime = Date.now() - batchStartTime;

  // Statistiken berechnen
  const successful = results.filter(r => r.success);
  const failed = results.filter(r => !r.success);
  const avgResponseTime = successful.length > 0
    ? Math.round(successful.reduce((sum, r) => sum + r.responseTime, 0) / successful.length)
    : 0;
  const totalTextLength = successful.reduce((sum, r) => sum + (r.textLength || 0), 0);

  // Ergebnisse ausgeben
  console.log('📊 Batch-Ergebnisse:');
  console.log('═'.repeat(70));

  results.forEach((result) => {
    const status = result.success ? '✅' : '❌';
    const time = `${result.responseTime}ms`;
    console.log(`${status} [${result.index + 1}] ${result.fileName} (${time})`);

    if (!result.success) {
      console.log(`   ⚠️  Fehler: ${result.error}`);
    } else if (result.result && result.result.text) {
      const preview = result.result.text.substring(0, 60).replace(/\n/g, ' ');
      console.log(`   📄 Text: ${preview}...`);
    }
  });

  console.log('═'.repeat(70));
  console.log('');
  console.log('📈 Statistiken:');
  console.log(`   Gesamt:          ${results.length} Dokumente`);
  console.log(`   Erfolgreich:     ${successful.length} ✅`);
  console.log(`   Fehlgeschlagen:  ${failed.length} ❌`);
  console.log(`   Gesamtzeit:      ${totalTime}ms`);
  console.log(`   Ø Pro Dokument:  ${avgResponseTime}ms`);
  console.log(`   Zeichen total:   ${totalTextLength}`);
  console.log(`   Durchsatz:       ${(results.length / (totalTime / 1000)).toFixed(2)} Dok/s`);

  return {
    total: results.length,
    successful: successful.length,
    failed: failed.length,
    totalTime,
    avgResponseTime,
    results
  };
}

/**
 * Hauptfunktion
 */
async function main() {
  const args = process.argv.slice(2);

  if (args.length === 0) {
    console.log('❌ Fehler: Keine Dateien angegeben');
    console.log('');
    console.log('Verwendung:');
    console.log('  node batch.js <datei1> <datei2> <datei3> ...');
    console.log('');
    console.log('Beispiele:');
    console.log('  node batch.js rechnung1.jpg rechnung2.jpg rechnung3.pdf');
    console.log('  node batch.js docs/*.jpg');
    console.log('');
    process.exit(1);
  }

  try {
    const stats = await processBatch(args);

    console.log('');
    if (stats.failed > 0) {
      console.log('⚠️  Batch abgeschlossen mit Fehlern');
      process.exit(1);
    } else {
      console.log('✨ Batch erfolgreich abgeschlossen!');
    }
  } catch (error) {
    console.error('');
    console.error('💥 Kritischer Fehler:', error.message);
    process.exit(1);
  }
}

// Nur ausführen wenn direkt aufgerufen
if (require.main === module) {
  main();
}

module.exports = { processBatch, processDocument };
