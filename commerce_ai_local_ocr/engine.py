"""Python 3.9+; image OCR uses only the standard library and Tesseract."""
import csv
import io
import os
from pathlib import Path
import shutil
import subprocess
import tempfile


def _binary():
    override = os.environ.get('TESSERACT_CMD')
    candidates = [override] if override else [shutil.which('tesseract'),
                                            '/opt/homebrew/bin/tesseract',
                                            '/usr/local/bin/tesseract']
    for candidate in candidates:
        if candidate and Path(candidate).is_file() and os.access(candidate, os.X_OK):
            return str(candidate)
    raise RuntimeError('Tesseract not found. Run: brew install tesseract tesseract-lang')


def _run(args, timeout=120):
    result = subprocess.run([_binary()] + args, capture_output=True,
                            text=True, encoding='utf-8', timeout=timeout)
    if result.returncode:
        raise RuntimeError('Tesseract failed: ' + result.stderr.strip()[:1200])
    return result.stdout


def _data_args(tessdata):
    return ['--tessdata-dir', str(Path(tessdata).expanduser().resolve())] if tessdata else []


def check_installation(language='kor+eng', tessdata=None):
    languages = _run(_data_args(tessdata) + ['--list-langs']).splitlines()
    missing = [item for item in language.split('+') if item not in languages]
    if missing:
        raise RuntimeError('Missing OCR languages: ' + ', '.join(missing) +
                           '. Run: brew install tesseract-lang')
    return {'binary': _binary(), 'version': _run(['--version']).splitlines()[0],
            'language': language, 'status': 'READY', 'API_CALLS': 0}


def _parse(tsv):
    if not tsv.startswith('level\tpage_num\t'):
        raise RuntimeError('Tesseract did not produce TSV')
    words, lines = [], {}
    for row in csv.DictReader(io.StringIO(tsv), delimiter='\t', quoting=csv.QUOTE_NONE):
        text = (row.get('text') or '').strip()
        if row.get('level') != '5' or not text:
            continue
        line = tuple(int(row[k]) for k in ('page_num', 'block_num', 'par_num', 'line_num'))
        words.append({'text': text, 'confidence': float(row['conf']),
                      'bbox_px': [int(row[k]) for k in ('left', 'top', 'width', 'height')]})
        lines.setdefault(line, []).append(text)
    return '\n'.join(' '.join(parts) for parts in lines.values()), words


def read_image(image, language='kor+eng', psm=3, tessdata=None, timeout=120):
    path = Path(image).expanduser().resolve(strict=True)
    if not path.is_file():
        raise ValueError('Image must be a file')
    if path.suffix.lower() not in ('.png', '.jpg', '.jpeg', '.tif', '.tiff', '.bmp', '.pnm', '.webp'):
        raise ValueError('Use PNG/JPEG/TIFF/BMP/PNM/WebP. Convert HEIC to PNG first.')
    if not isinstance(psm, int) or not 3 <= psm <= 13:
        raise ValueError('psm must be an integer from 3 to 13')
    installation = check_installation(language, tessdata)
    tsv = _run([str(path), 'stdout', '-l', language, '--psm', str(psm)] +
               _data_args(tessdata) + ['-c', 'tessedit_create_tsv=1'], timeout)
    text, words = _parse(tsv)
    return {'source': str(path), 'text': text, 'words': words,
            'engine': installation['version'], 'language': language, 'psm': psm,
            'status': 'OCR_EXTRACTED_UNVERIFIED' if words else 'NO_TEXT_DETECTED',
            'field_validation': 'NOT_PERFORMED', 'API_CALLS': 0}


def read_pdf(pdf, pages=(1,), dpi=200, language='kor+eng', psm=3, tessdata=None):
    """Render only explicitly selected pages; one-based page numbers."""
    try:
        import pymupdf as fitz
    except ImportError:
        try:
            import fitz
        except ImportError as exc:
            raise RuntimeError('PDF support requires: python -m pip install PyMuPDF') from exc
    if not 72 <= dpi <= 400:
        raise ValueError('dpi must be 72..400')
    selected = list(pages)
    if not selected:
        raise ValueError('Select at least one page')
    source = Path(pdf).expanduser().resolve(strict=True)
    results = []
    with fitz.open(source) as doc, tempfile.TemporaryDirectory() as tmp:
        if any(type(n) is not int or n < 1 or n > len(doc) for n in selected):
            raise ValueError('PDF page number outside range')
        for number in selected:
            image = Path(tmp) / 'page.png'
            doc[number - 1].get_pixmap(matrix=fitz.Matrix(dpi / 72, dpi / 72), alpha=False).save(image)
            result = read_image(image, language, psm, tessdata)
            result.update(source=str(source), page=number, dpi=dpi)
            results.append(result)
    return {'source': str(source), 'pages': results, 'API_CALLS': 0,
            'field_validation': 'NOT_PERFORMED'}
