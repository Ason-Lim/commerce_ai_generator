"""Bounded storefront OCR candidates, with independent units and review holds.

All coordinates come from the current image and OCR. No product-specific values.
"""
import hashlib
import json
import re
from PIL import Image, ImageOps
from .engine import read_image
from .options import (ink_image, option_end, blue_dots, selection_states,
                      price, amount_candidate, save_hold)
from .inline_offer import red_text_bands, leading_price


def compact(text):
    return re.sub(r'\s+', '', text)


def mass(text):
    found = re.findall(r'(?<![\d.])(\d+(?:\.\d+)?)\s*(kg|g)\b', text, re.I)
    if len(found) != 1 or float(found[0][0]) <= 0:
        return None
    n, unit = found[0]
    return float(n) / (1000 if unit.lower() == 'g' else 1)


def pack(text):
    matches = re.findall(r'[x×]\s*(\d+)\s*(박\s*스|개)', text, re.I)
    return (int(matches[0][0]), compact(matches[0][1])) if len(matches) == 1 and int(matches[0][0]) > 0 else None


def fruit_range(text):
    matches = re.findall(r'(\d+)\s*[~～〜-]\s*(\d+)\s*과', text)
    if len(matches) != 1:
        return None
    low, high = map(int, matches[0])
    return [low, high] if 0 < low <= high else None


def title_candidate(text):
    # Row discovery precedes value parsing. Ikg x THEA must not disappear merely
    # because both numeric values were read as letters. Never coerce I -> 1.
    shape = re.search(r'[x×]', text, re.I) is not None
    cue = re.search(r'\d|(?:k?g)\b|박\s*스|개', text, re.I) is not None
    return shape and cue


def unique(values):
    values = {v for v in values if v is not None}
    return next(iter(values)) if len(values) == 1 else None


def discount(text):
    t = compact(text)
    if '쿠폰' in t:
        return '쿠폰할인'
    if '와우' in t:
        return '와우할인'
    return '할인' if '할인' in t else None


def clamp(box, image):
    return [max(0, int(box[0])), max(0, int(box[1])),
            min(image.width, int(box[2])), min(image.height, int(box[3]))]


def retry(image, box, name, out, tessdata, language='kor+eng', psm=7, scale=3, bicubic=False):
    box = clamp(box, image)
    image.crop(box).save(out / (name+'_source.png'))
    crop = ImageOps.grayscale(image.crop(box))
    crop.resize((crop.width*scale, crop.height*scale), Image.Resampling.BICUBIC if bicubic else Image.Resampling.LANCZOS).save(out / (name+'_retry.png'))
    result = read_image(out / (name+'_retry.png'), language=language, psm=psm, tessdata=tessdata)
    return {'raw':result['text'], 'source_bbox_xyxy_px':box,
            'source_image':name+'_source.png', 'language':language, 'psm':psm, 'scale':scale, 'resampling':'BICUBIC' if bicubic else 'LANCZOS'}


def padded(box, margin=8):
    return [box[0]-margin, box[1]-margin, box[2]+margin, box[3]+margin]


def button_boundary(image, panel, below, out, tessdata):
    """OCR wide blue outlined controls that paragraph OCR skipped; never infer text."""
    pix = image.load()
    hits = []
    for y in range(int(below), image.height):
        count = sum(b > 150 and b > r+45 and b > g+10
                    for r,g,b in (pix[x,y] for x in range(panel[0],panel[2])))
        if count >= (panel[2]-panel[0])*.6:
            if not hits or y-hits[-1][-1] > 2:
                hits.append([])
            hits[-1].append(y)
    evidence = []
    # Limit retries even on unsupported images.
    for a,b in list(zip(hits,hits[1:]))[:4]:
        height = b[0]-a[-1]
        if not 12 <= height <= image.height*.15:
            continue
        rect = [panel[0]+2, a[-1]+2, panel[2]-2, b[0]-2]
        item = retry(image,rect,'boundary_%d'%len(evidence),out,tessdata)
        evidence.append(item)
        if re.search(r'옵션.*보기',compact(item['raw'])):
            return rect[1], evidence
    return None, evidence


def semantic_words(scan, row):
    return sorted([w for w in scan['words'] if w['line_key']==row['line_key']
                   and re.search(r'[0-9A-Za-z가-힣]',w['text'])],key=lambda w:w['bbox_px'][0])


def words_box(words, panel, margin=6):
    x=min(w['bbox_px'][0] for w in words);y=min(w['bbox_px'][1] for w in words)
    right=max(w['bbox_px'][0]+w['bbox_px'][2] for w in words)
    bottom=max(w['bbox_px'][1]+w['bbox_px'][3] for w in words)
    return [panel[0]+x/2-margin,y/2-margin,panel[0]+right/2+margin,bottom/2+margin]


def mass_words(words):
    # Ignore border/bullet tokens. Prefer a unit-bearing word even after grade labels.
    unit=[i for i,w in enumerate(words) if re.search(r'k[ge]|(?<![A-Za-z])g',w['text'],re.I)]
    if len(unit)==1:
        i=unit[0]
        if re.fullmatch(r'k?g',words[i]['text'],re.I) and i>0 and re.fullmatch(r'\d+(?:\.\d+)?',words[i-1]['text']):
            return words[i-1:i+1]
        return [words[i]]
    if not unit:
        return next(([w] for w in words if re.search(r'\d',w['text'])),[])
    return []


def parse_title(image, row, scan, panel, rid, out, tessdata):
    words=semantic_words(scan,row)
    focus=words_box(words,panel) if words else padded(row['source_bbox'])
    records = [retry(image,focus,rid+'_title',out,tessdata),
               retry(image,focus,rid+'_latin',out,tessdata,'eng')]
    texts = [row['text']] + [r['raw'] for r in records]
    weights = [mass(t) for t in texts]
    targets=mass_words(words)
    if targets:
        box=words_box(targets,panel)
        record=retry(image,box,rid+'_mass',out,tessdata,'eng',6,2,True)
        records.append(record);weights.append(mass(record['raw']))
    m = unique(weights)
    pack_values = [pack(t) for t in texts]
    if not any(v is not None for v in pack_values) and words:
        ordered = sorted(words,key=lambda w:w['bbox_px'][0])
        separators = [i for i,w in enumerate(ordered) if re.search(r'[x×]',w['text'],re.I)]
        if len(separators)==1:
            tail=ordered[separators[0]:]
            xs=[w['bbox_px'][0] for w in tail];ys=[w['bbox_px'][1] for w in tail]
            right=max(w['bbox_px'][0]+w['bbox_px'][2] for w in tail)
            bottom=max(w['bbox_px'][1]+w['bbox_px'][3] for w in tail)
            qb=[panel[0]+min(xs)/2-5,min(ys)/2-5,panel[0]+right/2+5,bottom/2+5]
            record=retry(image,qb,rid+'_pack',out,tessdata,'kor',6,2,True)
            records.append(record);pack_values.append(pack(record['raw']))
    q = unique(pack_values)
    ranges = {tuple(v) for t in texts if (v := fruit_range(t)) is not None}
    grades = {v for t in texts for v in re.findall(r'대\s*과|중\s*과|소\s*과', t)}
    grades = {compact(v) for v in grades}
    return {'weight_kg':m, 'pack_quantity':q[0] if q else None,
            'pack_unit':q[1] if q else None, 'box_quantity':q[0] if q and q[1]=='박스' else None,
            'total_weight_kg_derived':round(m*q[0],6) if m is not None and q else None,
            'fruit_count_range_displayed':list(next(iter(ranges))) if len(ranges)==1 else None,
            'grade_text':next(iter(grades)) if len(grades)==1 else None,
            'exact_apple_count':None, 'title_evidence':records, 'title_ocr_raw':row['text']}


def price_field(image, row, rid, out, tessdata):
    raw = row['text']
    # Unit-price figures must never become whole-option prices.
    if '당' in raw:
        return {'price_krw':None,'discount_label_displayed':None,'price_evidence':[],'currency_unit_ocr_confirmed':False}
    records = []
    amount = price(raw)
    currency = amount is not None
    if amount is None:
        record = retry(image,padded(row['source_bbox'],2),rid+'_price',out,tessdata,'kor',6,2)
        records.append(record)
        amount = price(record['raw'])
        currency = amount is not None
        if amount is None:
            # Comma-separated amount can be retained as a candidate, with currency unconfirmed.
            amount = amount_candidate(record['raw'])
    label = discount(' '.join([raw]+[r['raw'] for r in records]))
    return {'price_krw':amount,'discount_label_displayed':label,
            'price_evidence':[{'raw':raw,'source_bbox_xyxy_px':row['source_bbox']}]+records,
            'currency_unit_ocr_confirmed':currency}


def price_inversions(options):
    flags=[]
    for a in options:
        for b in options:
            if (a.get('weight_kg') is not None and b.get('weight_kg') is not None
                    and a.get('pack_quantity') is not None
                    and a.get('pack_quantity')==b.get('pack_quantity')
                    and a.get('pack_unit')==b.get('pack_unit')
                    and a.get('price_krw') is not None and b.get('price_krw') is not None
                    and a['weight_kg']<b['weight_kg'] and a['price_krw']>b['price_krw']):
                flags.append({'type':'HEAVIER_OPTION_HAS_LOWER_DISPLAYED_TOTAL_PRICE',
                    'lighter_option_id':a['id'],'heavier_option_id':b['id'],
                    'status':'CONDITION_DIFFERENCES_OR_SELLER_DISPLAY_REQUIRE_REVIEW',
                    'price_corrected':False})
    return flags


def write_result(source,image,panel,options,selected,layout,boundary,calls,out,extra=None):
    complete = all(o['weight_kg'] is not None and o['pack_quantity'] is not None and o['price_krw'] is not None for o in options)
    result = {'schema_version':'3.4','layout':layout,'source_name':source.name,
        'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),
        'source_size_px':list(image.size),'panel_bbox_xyxy_px':panel,'options':options,
        'selected_option_id':selected,'end_boundary_method':boundary,
        'status':('DISPLAYED_OFFER_CANDIDATE_REQUIRES_REVIEW' if layout=='COLLAPSED_DISPLAYED_SUMMARY' else 'LINKAGE_CANDIDATE_REQUIRES_REVIEW')
                 if complete and (selected or layout=='COLLAPSED_DISPLAYED_SUMMARY') and boundary.startswith('EXPLICIT_') else 'UNRESOLVED_REQUIRES_REVIEW',
        'API_CALLS':0,'ocr_recognition_calls':calls,'field_validation':'NOT_PERFORMED','human_review':'PENDING',
        'limits':['Screen OCR candidates only; no actual product facts or current purchase conditions verified.',
                  'Blue radio detection is heuristic. Collapsed control never proves hidden option coverage.',
                  'Pack count, displayed fruit range and cart quantity are distinct.',
                  'Discount eligibility, stock and checkout totals are not verified.']}
    result.update(extra or {})
    result['price_comparison_flags']=price_inversions(options)
    (out/'options.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    lines = ['# 구매 조건 OCR 후보','','| 옵션 | 개당 중량(kg) | 포장 수량 | 표시 가격(원) | 할인 표시 | 선택 후보 |',
             '| --- | --- | --- | --- | --- | --- |']
    for o in options:
        lines.append(f"| {o['id']} | {o['weight_kg']} | {o['pack_quantity']} {o['pack_unit']} | {o['price_krw']} | {o.get('discount_label_displayed')} | {o['selected']} |")
    for flag in result['price_comparison_flags']:
        lines.append('가격 조건 확인 필요: '+flag['lighter_option_id']+'보다 '+flag['heavier_option_id']+'가 더 무겁지만 표시 총가격은 낮습니다. 표기값을 변경하지 않았습니다.')
    if extra and extra.get('selected_variant_candidate'):
        lines.append('표시된 색상 선택 후보: '+extra['selected_variant_candidate']['label_compact'])
    lines += ['', '화면 표기 추출 후보입니다. 현재 가격·혜택 적용 자격·상품 사실은 미검증이며 사람의 원문 확인이 필요합니다.']
    (out/'options.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    # No single-image API bundle: price and title are separately located evidence.
    (out/'offer_evidence.json').write_text(json.dumps({'source_sha256':result['source_sha256'],
        'options':options,'api_review_status':'NOT_RUN_MULTI_IMAGE_REVIEW_NOT_WIRED','API_CALLS':0},ensure_ascii=False,indent=2),encoding='utf-8')
    return result


def collapsed(source,image,panel,rows,scan,anchor,out,tessdata):
    if anchor+1 >= len(rows) or not title_candidate(rows[anchor+1]['text']):
        return save_hold(out,source,image,panel,'COLLAPSED_SUMMARY_VALUE_UNRESOLVED')
    row = rows[anchor+1]
    # Value must be the adjacent line, not a later cart counter or unrelated section.
    head = rows[anchor]['source_bbox']; box = row['source_bbox']
    if not 0 <= box[1]-head[1] <= (head[3]-head[1])*2.5:
        return save_hold(out,source,image,panel,'COLLAPSED_SUMMARY_NOT_ADJACENT')
    option = parse_title(image,row,scan,panel,'D001',out,tessdata)
    bands = red_text_bands(image,int(head[0])-20,int(head[1]))
    prices = []
    for rect in bands[:3]:
        e = retry(image,rect,'D001_headline_'+str(len(prices)),out,tessdata)
        n,unit = leading_price(e['raw'])
        prices.append((n,unit,e))
    valid = [p for p in prices if p[0] is not None]
    amount,currency,evidence = valid[0] if len(valid)==1 else (None,False,None)
    option.update(id='D001',price_krw=amount,currency_unit_ocr_confirmed=currency,
        discount_label_displayed=discount(evidence['raw']) if evidence else None,
        price_evidence=[evidence] if evidence else [],selected=None,
        status='DISPLAYED_SUMMARY_REQUIRES_REVIEW',verified_product_fact=False,
        review_reasons=['collapsed_display_not_radio_selection','headline_price_to_displayed_summary_requires_review',
                        'cart_quantity_not_parsed','hidden_options_not_read'],
        source_bbox_xyxy_px=box)
    # A monetary amount was isolated by color, but discount text may extend to its right.
    if evidence:
        b=evidence['source_bbox_xyxy_px']
        same=[r['text'] for r in rows if abs(r['source_bbox'][1]-b[1]) < (b[3]-b[1])]
        option['discount_label_displayed']=discount(' '.join(same+[evidence['raw']]))
    if not currency:option['review_reasons'].append('currency_ocr_unconfirmed')
    return write_result(source,image,panel,[option],None,'COLLAPSED_DISPLAYED_SUMMARY',
        'EXPLICIT_ADJACENT_SUMMARY_FIELDS',1+len(option['title_evidence'])+len(prices),out,
        {'headline_price_linkage':'CANDIDATE_NOT_CHECKOUT_VERIFIED','cart_quantity':None})


def extract_offers(source,image,panel,rows,scan,out,tessdata=None):
    anchors=[i for i,r in enumerate(rows) if '중량' in compact(r.get('heading_sparse_raw',r['text'])) and '수량' in compact(r.get('heading_sparse_raw',r['text']))]
    if len(anchors)!=1:
        return save_hold(out,source,image,panel,'WEIGHT_QUANTITY_HEADING_UNRESOLVED')
    anchor=anchors[0]
    if '개당중량' in compact(rows[anchor]['text']):
        return collapsed(source,image,panel,rows,scan,anchor,out,tessdata)
    start=anchor+1
    stop,method=option_end(rows,start)
    boundary=[]
    if stop is None or not method.startswith('EXPLICIT_'):
        y,boundary=button_boundary(image,panel,rows[anchor]['source_bbox'][3],out,tessdata)
        if y is not None:
            stop=next((i for i in range(start,len(rows)) if rows[i]['source_bbox'][1]>=y),len(rows))
            method='EXPLICIT_OPTIONS_BUTTON_FOCUSED_OCR'
    if stop is None:
        stop=len(rows)
        method='IMAGE_BOTTOM_PARTIAL_REQUIRES_REVIEW'
    titles=[i for i in range(start,stop) if title_candidate(rows[i]['text'])]
    if not titles or len(titles)>8:
        return save_hold(out,source,image,panel,'OPTION_TITLES_UNRESOLVED')
    options=[];calls=1+len(boundary)
    for index,t in enumerate(titles):
        rid='O%03d'%(index+1);row=rows[t]
        end=titles[index+1] if index+1<len(titles) else stop
        following=rows[t+1:end]
        # Price must occupy the first numeric line beneath this title. Do not search through unit-price/sections.
        p_rows = []
        if following:
            first = following[0]
            title_box=row['source_bbox'];pb=first['source_bbox']
            if ('당' not in first['text'] and re.search(r'\d{3}',compact(first['text']))
                    and 0 <= pb[1]-title_box[1] <= (title_box[3]-title_box[1])*3):
                p_rows=[first]
        option=parse_title(image,row,scan,panel,rid,out,tessdata)
        calls+=len(option['title_evidence'])
        p=price_field(image,p_rows[0],rid,out,tessdata) if len(p_rows)==1 else {
            'price_krw':None,'currency_unit_ocr_confirmed':False,'discount_label_displayed':None,'price_evidence':[]}
        calls+=max(0,len(p['price_evidence'])-1)
        box=row['source_bbox'];rect=[panel[0],max(0,int(box[1])-12),panel[2],
            min(image.height,int(max(r['source_bbox'][3] for r in rows[t:end]))+10)]
        image.crop(rect).save(out/(rid+'_source.png'))
        dots=blue_dots(image,panel[0],rect[1],max(panel[0],int(box[0])-6),rect[3])
        reasons=['screen_claim_not_product_fact','selection_uses_blue_component_heuristic']
        if option['weight_kg'] is None:reasons.append('weight_unresolved_or_conflicting')
        if option['pack_quantity'] is None:reasons.append('pack_quantity_unresolved_or_conflicting')
        if len(p_rows)!=1:reasons.append('price_linkage_ambiguous')
        if p['price_krw'] is None:reasons.append('price_unresolved')
        if not p['currency_unit_ocr_confirmed']:reasons.append('currency_ocr_unconfirmed')
        if not method.startswith('EXPLICIT_'):reasons.append('end_boundary_unconfirmed')
        option.update(p)
        option.update(id=rid,source_bbox_xyxy_px=rect,source_image=rid+'_source.png',
            selection_blue_components=dots,review_reasons=reasons,status='CANDIDATE_REQUIRES_REVIEW',verified_product_fact=False)
        options.append(option)
    states=selection_states([len(o['selection_blue_components']) for o in options])
    for o,state in zip(options,states):o['selected']=state
    selected=[o['id'] for o in options if o['selected'] is True]
    return write_result(source,image,panel,options,selected[0] if len(selected)==1 else None,
        'VISIBLE_RADIO_OPTIONS',method,calls,out,{'boundary_evidence':boundary,
        'visible_option_candidate_count':len(titles),
        'row_discovery_rule':'MULTIPLICATION_WITH_DIGIT_OR_UNIT_BEFORE_VALUE_PARSING',
        'option_coverage':'VISIBLE_ROWS_ONLY_END_UNCONFIRMED' if method=='IMAGE_BOTTOM_PARTIAL_REQUIRES_REVIEW' else 'BOUNDED_VISIBLE_ROWS_NOT_ALL_HIDDEN_OPTIONS'})
