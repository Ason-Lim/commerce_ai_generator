"""Conservative layout heuristic: neutral dark text on a light background.

This is a candidate detector, not a semantic segmenter. Photos, colored text,
and option headings can be missed. Never use absence as evidence of absence.
"""
import hashlib
import json
from pathlib import Path
import tempfile
from .engine import read_image


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def detect_regions(image):
    from PIL import Image
    width, height = image.size
    ratio = min(1.0, 1024 / width)
    small = image.convert('RGB').resize((max(1, round(width * ratio)), max(1, round(height * ratio))))
    w, h = small.size
    pix = small.load()
    hits = []
    for y in range(h):
        white = 0
        dark = []
        for x in range(w):
            rgb = pix[x, y]
            white += min(rgb) >= 205
            if max(rgb) < 175 and max(rgb) - min(rgb) < 55:
                dark.append(x)
        if white / w >= .70 and len(dark) >= max(3, w * .003) and len(dark) / w <= .30:
            hits.append((y, min(dark), max(dark)))
    groups = []
    # Join nearby rows into multi-line context blocks, not separate word crops.
    gap = max(12, round(42 * ratio))
    for row in hits:
        if not groups or row[0] - groups[-1][-1][0] > gap:
            groups.append([])
        groups[-1].append(row)
    regions = []
    for rows in groups:
        if rows[-1][0] - rows[0][0] < 5:
            continue
        # Wider margins preserve adjacent colored words and headings when possible.
        left = max(0, int(min(r[1] for r in rows) / ratio) - 80)
        right = min(width, int((max(r[2] for r in rows) + 1) / ratio) + 80)
        top = max(0, int(rows[0][0] / ratio) - 24)
        bottom = min(height, int((rows[-1][0] + 1) / ratio) + 24)
        regions.append([left, top, right, bottom])
    return regions


def map_word(word, region, scale):
    x, y, w, h = word['bbox_px']
    return dict(word, source_bbox_px=[region[0] + x / scale, region[1] + y / scale,
                                      w / scale, h / scale])


def prepare(image_path, output, tessdata=None, max_regions=8):
    from PIL import Image, ImageOps
    source = Path(image_path).expanduser().resolve(strict=True)
    output = Path(output)
    if not 1 <= max_regions <= 16:
        raise ValueError('max_regions must be 1..16')
    with Image.open(source) as opened:
        image = opened.convert('RGB')
    boxes = detect_regions(image)
    output.mkdir(parents=True, exist_ok=False)
    baseline = read_image(source, tessdata=tessdata)
    (output / 'baseline.json').write_text(json.dumps(baseline, ensure_ascii=False, indent=2), encoding='utf-8')
    regions = []
    for i, box in enumerate(boxes[:max_regions], 1):
        rid = 'R%03d' % i
        original = image.crop(box)
        original.save(output / (rid + '_source.png'))
        processed = ImageOps.autocontrast(ImageOps.grayscale(original))
        processed = processed.resize((processed.width * 2, processed.height * 2), Image.Resampling.LANCZOS)
        retry_path = output / (rid + '_retry.png')
        processed.save(retry_path)
        retry = read_image(retry_path, psm=6, tessdata=tessdata)
        # Remove machine-specific temporary paths; retain original location and transform.
        retry['source'] = source.name
        retry['words'] = [map_word(w, box, 2) for w in retry['words']]
        record = {'id': rid, 'source_bbox_xyxy_px': box, 'scale': 2,
                  'image': rid + '_source.png', 'image_sha256': digest(output / (rid + '_source.png')),
                  'processed_image': rid + '_retry.png', 'ocr': retry,
                  'review_status': 'REVIEW_REQUIRED',
                  'reason': 'OCR text is unverified; confidence cannot establish factual correctness.'}
        regions.append(record)
    bundle = {'schema_version': 2, 'source_name': source.name, 'source_sha256': digest(source),
              'source_size_px': list(image.size), 'regions': regions,
              'detector': 'light_background_neutral_text_rows_v1',
              'coverage': 'PARTIAL_CANDIDATES_ONLY', 'detected_regions': len(boxes),
              'omitted_region_count': max(0, len(boxes) - max_regions),
              'field_validation': 'NOT_PERFORMED', 'API_CALLS': 0,
              'note': 'No factual corrections, product-field inference, or automatic approvals.'}
    (output / 'bundle.json').write_text(json.dumps(bundle, ensure_ascii=False, indent=2), encoding='utf-8')
    (output / 'text.txt').write_text('\n\n'.join(r['id'] + '\n' + r['ocr']['text'] for r in regions), encoding='utf-8')
    return bundle
