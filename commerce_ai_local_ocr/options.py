"""Experimental option linkage for light product panels with blue selected radio.

No fixed product, price, weight, or screenshot coordinates. OCR and visual
heuristics produce evidence candidates, never verified product facts.
"""
import argparse
from datetime import datetime
import hashlib
import json
from pathlib import Path
import re
import tempfile
from PIL import Image, ImageChops, ImageOps
from .engine import read_image


def panel_box(image):
    thumb = image.convert('RGB').resize((256, max(1, round(image.height * 256 / image.width))))
    w, h = thumb.size
    runs = []
    for x in range(w):
        light = sum(min(thumb.getpixel((x, y))) >= 205 for y in range(h)) / h
        if light >= .68:
            if not runs or x > runs[-1][-1] + 1:
                runs.append([])
            runs[-1].append(x)
    runs = [r for r in runs if len(r) >= w * .20]
    if not runs:
        raise ValueError('No wide light-background panel candidate; manual region needed')
    run = max(runs, key=len)
    return [round(run[0] * image.width / w), 0, round((run[-1] + 1) * image.width / w), image.height]


def ink_image(image):
    # Minimum RGB channel retains red/blue text that neutral-gray detection missed.
    r, g, b = image.convert('RGB').split()
    return ImageChops.darker(ImageChops.darker(r, g), b).point(lambda v: 0 if v < 190 else 255)


def lines_from_words(words):
    groups = {}
    for word in words:
        groups.setdefault(tuple(word['line_key']), []).append(word)
    lines = []
    for key, words in groups.items():
        x = min(w['bbox_px'][0] for w in words)
        y = min(w['bbox_px'][1] for w in words)
        right = max(w['bbox_px'][0] + w['bbox_px'][2] for w in words)
        bottom = max(w['bbox_px'][1] + w['bbox_px'][3] for w in words)
        lines.append({'text': ' '.join(w['text'] for w in words), 'bbox': [x, y, right, bottom], 'line_key':list(key)})
    return sorted(lines, key=lambda line: line['bbox'][1])


def price(text):
    compact = re.sub(r'\s+', '', text)
    if '당' in compact or re.search(r'[?？]\s*\d',compact):
        return None
    matches = re.findall(r'(?<![\d.,])(\d{1,3}(?:[,.]\d{3})+|\d+)원', compact)
    values = [int(v.replace(',', '').replace('.', '')) for v in matches]
    return values[0] if len(values) == 1 else None


def weight(text):
    found = re.findall(r'(?<![\d.])(\d+(?:\.\d+)?)\s*kg\b', text, re.I)
    return float(found[0]) if len(found) == 1 and float(found[0]) > 0 else None


def box_quantity(text):
    matches = re.findall(r'[x×]\s*(\d+)\s*박\s*스', text, re.I)
    return int(matches[0]) if len(matches) == 1 and int(matches[0]) > 0 else None


def option_title(text):
    # Boundary detection must not depend on successful box-count recognition.
    return '(' in text and re.search(r'[x×]', text, re.I) is not None


def amount_candidate(text):
    if '당' in text or re.search(r'100\s*[g8]',text,re.I) or re.search(r'[?？]\s*\d',text):
        return None
    amounts = re.findall(r'(?<![\d.,])(\d{1,3}(?:[,.]\d{3})+)(?![\d.,])', text)
    return int(amounts[0].replace(',','').replace('.','')) if len(amounts)==1 else None


def blue_dots(image, left, top, right, bottom):
    """Small dense blue components in the strip left of the option title only."""
    pix = image.convert('RGB').load()
    points = set()
    for y in range(top, bottom):
        for x in range(left, right):
            r, g, b = pix[x, y]
            if b > 130 and b > r + 50 and b > g + 15:
                points.add((x, y))
    results = []
    max_side = max(20, round(image.width * .02))
    while points:
        start = points.pop()
        stack, component = [start], [start]
        while stack:
            x, y = stack.pop()
            for neighbor in ((x-1,y), (x+1,y), (x,y-1), (x,y+1)):
                if neighbor in points:
                    points.remove(neighbor)
                    stack.append(neighbor)
                    component.append(neighbor)
        xs, ys = zip(*component)
        w, h = max(xs)-min(xs)+1, max(ys)-min(ys)+1
        if 4 <= w <= max_side and 4 <= h <= max_side and .65 <= w/h <= 1.5 and len(component)/(w*h) >= .50:
            results.append([min(xs), min(ys), max(xs)+1, max(ys)+1])
    return results


def selection_states(counts):
    if sum(counts) == 1 and counts.count(1) == 1:
        return [c == 1 for c in counts]
    return [None for _ in counts]


def option_end(rows, start):
    """Return an explicit end button, a conservative shipping boundary, or hold."""
    for i in range(start,len(rows)):
        compact=re.sub(r'\s+','',rows[i]['text'])
        if re.search(r'옵션.*보기',compact):
            return i,'EXPLICIT_OPTIONS_BUTTON'
        if '옵션' in compact and i+1<len(rows):
            next_text=re.sub(r'\s+','',rows[i+1]['text'])
            a,b=rows[i]['bbox'],rows[i+1]['bbox']
            if '보기' in next_text and 0<=b[1]-a[3]<=max(a[3]-a[1],b[3]-b[1])*2:
                return i,'EXPLICIT_OPTIONS_BUTTON_SPLIT_LINES'
    # A shipping section bounds candidates but does not prove all options were read.
    for i in range(start,len(rows)):
        compact=re.sub(r'[\s|:：]','',rows[i]['text'])
        if compact in ('무료배송','배송정보','배송안내'):
            return i,'SHIPPING_FALLBACK_REQUIRES_REVIEW'
    return None,'END_BOUNDARY_UNRESOLVED'


def save_hold(out, source, image, panel, reason):
    result={'schema_version': '3.4','source_name':source.name,
        'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),
        'source_size_px':list(image.size),'panel_bbox_xyxy_px':panel,'options':[],
        'selected_option_id':None,'status':'UNRESOLVED_REQUIRES_REVIEW',
        'reason':reason,'API_CALLS':0,'ocr_recognition_calls':1,
        'field_validation':'NOT_PERFORMED','human_review':'PENDING'}
    (out/'options.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    (out/'options.md').write_text('# 옵션 연결 보류\n\n'+reason+'\n\n원본 및 panel_text.txt를 확인해야 합니다. API 호출은 없습니다.\n',encoding='utf-8')
    return result


def extract(image_path, output, tessdata=None):
    source = Path(image_path).expanduser().resolve(strict=True)
    image = Image.open(source).convert('RGB')
    panel = panel_box(image)
    out = Path(output)
    out.mkdir(parents=True, exist_ok=False)
    def scan_panel(box):
        rgb=image.crop(box);rgb.save(out/'panel_source.png')
        ink_image(rgb).resize((rgb.width*2,rgb.height*2),Image.Resampling.LANCZOS).save(out/'panel_ink.png')
        return read_image(out/'panel_ink.png',psm=6,tessdata=tessdata)
    scan=scan_panel(panel);base_calls=1;discovery=None
    def has_heading(row):
        text=re.sub(r'\s+','',row['text'])
        return '수량' in text and ('중량' in text or '색상' in text)
    rows=lines_from_words(scan['words'])
    if sum(has_heading(r) for r in rows)!=1:
        # A light-column heuristic can cut into a text column. Find a heading in
        # sparse full-page OCR before trying a new panel; never guess coordinates.
        ink_image(image).resize((image.width*2,image.height*2),Image.Resampling.LANCZOS).save(out/'panel_discovery_ink.png')
        sparse=read_image(out/'panel_discovery_ink.png',psm=11,tessdata=tessdata);base_calls+=1
        headings=[r for r in lines_from_words(sparse['words']) if has_heading(r)]
        discovery={'method':'FULL_PAGE_SPARSE_HEADING','heading_candidates':headings}
        if len(headings)==1:
            new=[max(0,int(headings[0]['bbox'][0]/2)-20),0,image.width,image.height]
            if new!=panel:
                panel=new;scan=scan_panel(panel);base_calls+=1;rows=lines_from_words(scan['words'])
            # Preserve the paragraph OCR text; attach independently read heading
            # evidence only to a spatially overlapping row.
            head=headings[0];hy=head['bbox'][1]/2
            nearest=min(rows,key=lambda r:abs(r['bbox'][1]/2-hy)) if rows else None
            if nearest and abs(nearest['bbox'][1]/2-hy)<=max(12,(head['bbox'][3]-head['bbox'][1])/2):
                nearest['heading_sparse_raw']=head['text']
                nearest['heading_sparse_source_bbox']=[v/2 for v in head['bbox']]

    for row in rows:
        row['source_bbox']=[panel[0]+row['bbox'][0]/2,row['bbox'][1]/2,
                            panel[0]+row['bbox'][2]/2,row['bbox'][3]/2]
    (out / 'panel_ocr.json').write_text(json.dumps(scan,ensure_ascii=False,indent=2),encoding='utf-8')
    (out / 'panel_text.txt').write_text('\n'.join(r['text'] for r in rows),encoding='utf-8')
    (out / 'diagnostics.json').write_text(json.dumps({'source_name':source.name,
        'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),
        'source_size_px':list(image.size),'panel_bbox_xyxy_px':panel,'ocr_engine':scan['engine'],
        'rows':rows,'panel_discovery':discovery,'base_ocr_calls':base_calls,'API_CALLS':0},ensure_ascii=False,indent=2),encoding='utf-8')
    from .inline_offer import is_inline_heading,extract_inline
    from .offer_rows import extract_offers
    inline_headings=[r for r in rows if is_inline_heading(r['text'])]
    colors=[i for i,r in enumerate(rows) if '색상' in re.sub(r'\s+','',r['text']) and '수량' in re.sub(r'\s+','',r['text'])]
    if len(inline_headings)==1:
        result=extract_inline(source,image,panel,rows,inline_headings[0],out,tessdata)
    elif len(inline_headings)>1:
        result=save_hold(out,source,image,panel,'MULTIPLE_INLINE_SUMMARIES_UNRESOLVED')
    elif len(colors)==1:
        from .variant_quantity import extract_quantity_variants
        result=extract_quantity_variants(source,image,panel,rows,scan,colors[0],out,tessdata)
    else:
        result=extract_offers(source,image,panel,rows,scan,out,tessdata)
    result['ocr_recognition_calls']+=base_calls-1
    result['panel_discovery']=discovery
    (out/'options.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    return result


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--input',type=Path,required=True)
    p.add_argument('--output',type=Path)
    p.add_argument('--tessdata',type=Path)
    a=p.parse_args()
    out=a.output or Path('ocr_results')/('options_'+datetime.now().strftime('%Y%m%d_%H%M%S_%f'))
    result=extract(a.input,out,a.tessdata)
    for o in result['options']: print(o['id'],'WEIGHT_KG='+str(o['weight_kg']),'PACK_QUANTITY='+str(o.get('pack_quantity',o.get('box_quantity'))),'PACK_UNIT='+str(o.get('pack_unit','박스' if o.get('box_quantity') else None)),'PRICE_KRW='+str(o['price_krw']),'SELECTED='+str(o['selected']))
    print('RESULT='+str(out.resolve())+'; STATUS='+result['status']+'; API_CALLS=0')


if __name__=='__main__': main()
