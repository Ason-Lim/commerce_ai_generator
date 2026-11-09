import argparse
from datetime import datetime
import json
from pathlib import Path
from .engine import check_installation, read_image, read_pdf


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--check', action='store_true')
    parser.add_argument('--input', type=Path)
    parser.add_argument('--output', type=Path)
    parser.add_argument('--pages', default='1')
    parser.add_argument('--language', default='kor+eng')
    parser.add_argument('--tessdata', type=Path)
    parser.add_argument('--psm', type=int, default=3)
    args = parser.parse_args()
    if args.check:
        print(json.dumps(check_installation(args.language, args.tessdata), ensure_ascii=False, indent=2))
        return
    if not args.input:
        parser.error('--input or --check is required')
    output = args.output or Path('ocr_results') / datetime.now().strftime('%Y%m%d_%H%M%S_%f')
    output.mkdir(parents=True, exist_ok=False)
    if args.input.suffix.lower() == '.pdf':
        result = read_pdf(args.input, [int(n) for n in args.pages.split(',')],
                          language=args.language, psm=args.psm, tessdata=args.tessdata)
        text = '\n\n'.join('PAGE %s\n%s' % (p['page'], p['text']) for p in result['pages'])
    else:
        result = read_image(args.input, args.language, args.psm, args.tessdata)
        text = result['text']
    (output / 'result.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    (output / 'text.txt').write_text(text, encoding='utf-8')
    print('RESULT=' + str(output.resolve()) + '; API_CALLS=0; FIELD_VALIDATION=NOT_PERFORMED')


if __name__ == '__main__':
    main()
