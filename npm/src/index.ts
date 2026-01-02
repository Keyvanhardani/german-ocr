/**
 * German-OCR - High-performance German document OCR
 *
 * @packageDocumentation
 */

import fetch from 'node-fetch';
import FormData from 'form-data';
import * as fs from 'fs';
import * as path from 'path';

/**
 * Available OCR models
 */
export type Model = 'german-ocr' | 'german-ocr-pro' | 'german-ocr-ultra' | 'privacy-shield';

/**
 * API response for synchronous processing
 */
export interface AnalyzeResult {
  text: string;
  model_used: string;
  processing_time_ms: number;
  metadata?: Record<string, any>;
}

/**
 * API response for async job creation
 */
export interface JobResult {
  job_id: string;
  model: string;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  message?: string;
}

/**
 * Combined response type
 */
export type ApiResponse = AnalyzeResult | JobResult;

/**
 * Client options
 */
export interface ClientOptions {
  /** API endpoint (default: https://api.german-ocr.de) */
  endpoint?: string;
  /** Request timeout in ms (default: 60000) */
  timeout?: number;
}

/**
 * Analyze options
 */
export interface AnalyzeOptions {
  /** Custom prompt for structured extraction */
  prompt?: string;
  /** OCR model to use */
  model?: Model;
}

/**
 * German-OCR Cloud Client
 *
 * @example
 * ```typescript
 * import { GermanOCR } from 'german-ocr';
 *
 * const client = new GermanOCR('gocr_xxx', 'your_secret');
 * const result = await client.analyze('invoice.pdf');
 * console.log(result.text);
 * ```
 */
export class GermanOCR {
  private apiKey: string;
  private apiSecret: string;
  private endpoint: string;
  private timeout: number;

  /**
   * Create a new German-OCR client
   *
   * @param apiKey - Your API key (starts with gocr_)
   * @param apiSecret - Your API secret (64 characters)
   * @param options - Client options
   */
  constructor(apiKey: string, apiSecret: string, options: ClientOptions = {}) {
    if (!apiKey || !apiKey.startsWith('gocr_')) {
      throw new Error('Invalid API key. Must start with "gocr_"');
    }
    if (!apiSecret || apiSecret.length < 32) {
      throw new Error('Invalid API secret');
    }

    this.apiKey = apiKey;
    this.apiSecret = apiSecret;
    this.endpoint = options.endpoint || 'https://api.german-ocr.de';
    this.timeout = options.timeout || 60000;
  }

  /**
   * Analyze a document
   *
   * @param filePath - Path to the document (PDF, JPG, PNG)
   * @param options - Analysis options
   * @returns API response
   *
   * @example
   * ```typescript
   * // Simple extraction
   * const result = await client.analyze('invoice.pdf');
   *
   * // With custom prompt
   * const result = await client.analyze('invoice.pdf', {
   *   prompt: 'Extract invoice number and total amount as JSON',
   *   model: 'german-ocr-ultra'
   * });
   * ```
   */
  async analyze(filePath: string, options: AnalyzeOptions = {}): Promise<ApiResponse> {
    const absolutePath = path.resolve(filePath);

    if (!fs.existsSync(absolutePath)) {
      throw new Error(`File not found: ${filePath}`);
    }

    const form = new FormData();
    form.append('file', fs.createReadStream(absolutePath));
    form.append('model', options.model || 'german-ocr-pro');

    if (options.prompt) {
      form.append('prompt', options.prompt);
    }

    const authToken = `${this.apiKey}:${this.apiSecret}`;

    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), this.timeout);

    try {
      const response = await fetch(`${this.endpoint}/v1/analyze`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${authToken}`,
          ...form.getHeaders()
        },
        body: form,
        signal: controller.signal as any
      });

      clearTimeout(timeoutId);

      if (!response.ok && response.status !== 202) {
        const errorText = await response.text();
        throw new Error(`API Error (${response.status}): ${errorText}`);
      }

      return await response.json() as ApiResponse;

    } catch (error: any) {
      clearTimeout(timeoutId);

      if (error.name === 'AbortError') {
        throw new Error(`Request timeout after ${this.timeout}ms`);
      }
      throw error;
    }
  }

  /**
   * Analyze a document from a Buffer
   *
   * @param buffer - Document data as Buffer
   * @param filename - Original filename (for MIME type detection)
   * @param options - Analysis options
   * @returns API response
   */
  async analyzeBuffer(buffer: Buffer, filename: string, options: AnalyzeOptions = {}): Promise<ApiResponse> {
    const form = new FormData();
    form.append('file', buffer, { filename });
    form.append('model', options.model || 'german-ocr-pro');

    if (options.prompt) {
      form.append('prompt', options.prompt);
    }

    const authToken = `${this.apiKey}:${this.apiSecret}`;

    const response = await fetch(`${this.endpoint}/v1/analyze`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${authToken}`,
        ...form.getHeaders()
      },
      body: form
    });

    if (!response.ok && response.status !== 202) {
      const errorText = await response.text();
      throw new Error(`API Error (${response.status}): ${errorText}`);
    }

    return await response.json() as ApiResponse;
  }

  /**
   * Check if response is an async job
   */
  static isJobResult(response: ApiResponse): response is JobResult {
    return 'job_id' in response;
  }

  /**
   * Check if response is a direct result
   */
  static isAnalyzeResult(response: ApiResponse): response is AnalyzeResult {
    return 'text' in response;
  }
}

// Default export
export default GermanOCR;

// Named exports for convenience
export { GermanOCR as CloudClient };
