<?php

declare(strict_types=1);

namespace GermanOCR;

/**
 * German-OCR Exception
 *
 * @package GermanOCR
 */
class GermanOCRException extends \Exception
{
    /**
     * @param string $message Error message
     * @param int $code HTTP status code or error code
     * @param \Throwable|null $previous Previous exception
     */
    public function __construct(string $message = "", int $code = 0, ?\Throwable $previous = null)
    {
        parent::__construct($message, $code, $previous);
    }
}
