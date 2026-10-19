import argparse
from datetime import datetime
from pathlib import Path
from .regions import prepare


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--input', type=Path, required=True)
    p.add_argument('--output', type=Path)
    p.add_argument('--tessdata', type=Path)
    p.add_argument('--max-regions', type=int, default=8)
    a = p.parse_args()
    out = a.output or Path('ocr_results') / ('regions_' + datetime.now().strftime('%Y%m%d_%H%M%S_%f'))
    result = prepare(a.input, out, a.tessdata, a.max_regions)
    print('BUNDLE=' + str((out / 'bundle.json').resolve()))
    for region in result['regions']:
        print(region['id'], region['source_bbox_xyxy_px'], region['ocr']['text'].replace('\n', ' / '))
    print('API_CALLS=0; COVERAGE=PARTIAL; FIELD_VALIDATION=NOT_PERFORMED')


if __name__ == '__main__':
    main()
