"""Local Tesseract OCR. No GPT API calls."""
from .engine import check_installation, read_image, read_pdf

__all__ = ['check_installation', 'read_image', 'read_pdf']
