"""Experimental labeled inline offer: weight x dispatch condition x box count."""
import hashlib
import json
from pathlib import Path
import re
from PIL import ImageOps
from .engine import read_image


def is_inline_heading(text):
    text=re.sub(r'\s+','',text)
    return re.search(r'개당중량[x×]출고[희회]망일[x×]총수량[:：]',text,re.I) is not None


def parse_inline(text):
    compact=re.sub(r'\s+','',text)
    header=re.search(r'개당중량[x×]출고[희회]망일[x×]총수량[:：]',compact,re.I)
    if not header:return None
    parts=re.split(r'[x×]',compact[header.end():],flags=re.I)
    if len(parts)!=3:return None
    w=re.fullmatch(r'(\d+(?:\.\d+)?)kg',parts[0],re.I)
    d=re.fullmatch(r'(\d+)(?:[~～〜-](\d+))?일소요',parts[1])
    q=re.fullmatch(r'(\d+)박스',parts[2])
    if not w or not d or not q:return None
    low,high=int(d[1]),int(d[2] or d[1])
    if float(w[1])<=0 or int(q[1])<=0 or low<0 or high<low:return None
    return {'weight_kg':float(w[1]),'box_quantity':int(q[1]),
            'dispatch_condition_raw':parts[1],'dispatch_days_range':[low,high],
            'dispatch_condition_label':'출고희망일','delivery_days_range':None,
            'header_ocr_alias_used':'회망일' in compact}


def red_text_bands(image,left,bottom):
    # Require a unique red price-like row in the text column, not the product photo.
    pix=image.convert('RGB').load()
    hits=[]
    for y in range(max(0,bottom)):
        xs=[]
        for x in range(max(0,left),image.width):
            r,g,b=pix[x,y]
            if r>150 and r>g*1.6 and r>b*1.6:xs.append(x)
        if len(xs)>=5:hits.append((y,min(xs),max(xs)))
    groups=[]
    for hit in hits:
        if not groups or hit[0]-groups[-1][-1][0]>10:groups.append([])
        groups[-1].append(hit)
    return [[max(0,min(v[1] for v in g)-8),max(0,g[0][0]-8),
             min(image.width,max(v[2] for v in g)+9),min(image.height,g[-1][0]+9)]
            for g in groups if g[-1][0]-g[0][0]>=5]


def leading_price(text):
    first=re.split(r'[（(]',text)[0]
    first=re.sub(r'\s+','',first)
    match=re.fullmatch(r'(\d{1,3}(?:[,.]\d{3})+)(원|H|2|7)?',first)
    if not match:return None,False
    return int(match[1].replace(',','').replace('.','')),match[2]=='원'


def extract_inline(source,image,panel,rows,heading,out,tessdata=None):
    box=heading['source_bbox']
    crop_box=[max(0,int(box[0])-8),max(0,int(box[1])-8),
              min(image.width,int(box[2])+8),min(image.height,int(box[3])+9)]
    image.crop(crop_box).save(out/'I001_summary_source.png')
    gray=ImageOps.grayscale(image.crop(crop_box))
    gray.resize((gray.width*3,gray.height*3)).save(out/'I001_summary_retry.png')
    kor=read_image(out/'I001_summary_retry.png',psm=7,tessdata=tessdata)
    eng=read_image(out/'I001_summary_retry.png',language='eng',psm=7,tessdata=tessdata)
    parsed=parse_inline(kor['text'])
    matches=re.findall(r'(?<![\d.])(\d+(?:\.\d+)?)\s*kg\b',eng['text'],re.I)
    eng_weight=float(matches[0]) if len(matches)==1 else None
    reasons=['offer_is_displayed_summary_not_radio_selection','dispatch_condition_is_not_arrival_guarantee',
             'grade_origin_actual_quality_unverified']
    if parsed is None:reasons.append('inline_fields_unresolved')
    weight=parsed['weight_kg'] if parsed else None
    if weight is not None and eng_weight is not None and weight!=eng_weight:
        weight=None;reasons.append('weight_retry_conflict')
    elif eng_weight is None:reasons.append('english_weight_retry_unresolved')
    red_boxes=red_text_bands(image,int(box[0]),int(box[1]))
    amount=None;currency=False;price_retry=None;price_box=None;calls=3
    if len(red_boxes)==1:
        price_box=red_boxes[0]
        image.crop(price_box).save(out/'I001_price_source.png')
        gray=ImageOps.grayscale(image.crop(price_box))
        gray.resize((gray.width*3,gray.height*3)).save(out/'I001_price_retry.png')
        price_retry=read_image(out/'I001_price_retry.png',psm=7,tessdata=tessdata);calls+=1
        amount,currency=leading_price(price_retry['text'])
    else:reasons.append('red_price_band_missing_or_multiple')
    if amount is None:reasons.append('price_unresolved')
    if not currency:reasons.append('currency_ocr_unconfirmed')
    option={'id':'I001','weight_kg':weight,'box_quantity':parsed['box_quantity'] if parsed else None,
        'exact_apple_count':None,'exact_cabbage_count':None,'price_krw':amount,'currency_unit_ocr_confirmed':currency,
        'selected':None,'status':'DISPLAYED_SUMMARY_REQUIRES_REVIEW','verified_product_fact':False,
        'dispatch_condition_raw':parsed['dispatch_condition_raw'] if parsed else None,
        'dispatch_days_range':parsed['dispatch_days_range'] if parsed else None,'delivery_days_range':None,
        'source_bbox_xyxy_px':crop_box,'price_source_bbox_xyxy_px':price_box,
        'summary_ocr_raw':heading['text'],'summary_retry_raw':kor['text'],'weight_retry_raw':eng['text'],
        'price_retry_raw':price_retry['text'] if price_retry else None,'review_reasons':reasons}
    observed=[]
    for row in rows:
        compact=re.sub(r'\s+','',row['text'])
        if '원산지' in compact or re.search(r'\d{1,2}/\d{1,2}.*도착',compact) or '무료배송' in compact:
            observed.append({'raw_ocr':row['text'],'source_bbox_xyxy_px':row['source_bbox'],
                             'status':'CAPTURED_TEXT_UNVERIFIED_NOT_CURRENT_CONDITION'})
    complete=parsed is not None and weight is not None and amount is not None and currency
    result={'schema_version':'3.2','layout':'INLINE_DISPLAYED_OFFER_SUMMARY',
        'source_name':source.name,'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),
        'source_size_px':list(image.size),'panel_bbox_xyxy_px':panel,'options':[option],
        'selected_option_id':None,'status':'DISPLAYED_OFFER_CANDIDATE_REQUIRES_REVIEW' if complete else 'UNRESOLVED_REQUIRES_REVIEW',
        'captured_context_ocr':observed,'API_CALLS':0,'ocr_recognition_calls':calls,
        'field_validation':'NOT_PERFORMED','human_review':'PENDING',
        'limits':['Only this labeled inline layout is supported; no general storefront coverage.',
                  'Shipping/arrival text is captured OCR, not a current promise.',
                  '1 box is not a cabbage-head count. Displayed summary is not a radio-selected option.',
                  'No real origin, quality, stock, checkout amount, coupon eligibility or purchase availability is verified.']}
    (out/'options.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    (out/'options.md').write_text('# 표시된 구매 조건 OCR 후보\n\n'
        '| 중량 | 박스 수량 | 가격 | 출고 조건 |\n| --- | --- | --- | --- |\n'
        f"| {weight} kg | {option['box_quantity']} | {amount}원 | {option['dispatch_condition_raw']} |\n\n"
        '화면 표기 후보이며 실제 품질·원산지·현재 배송 조건은 미검증입니다. 라디오 선택 상태는 판단하지 않았습니다.\n',encoding='utf-8')
    # A local review bundle includes the condition row and price as separate images.
    # Existing single-image review must not silently treat the row as price evidence.
    (out/'inline_evidence.json').write_text(json.dumps({'source_sha256':result['source_sha256'],
        'summary_image':'I001_summary_source.png','summary_bbox_xyxy_px':crop_box,
        'price_image':'I001_price_source.png' if price_box else None,'price_bbox_xyxy_px':price_box,
        'api_review_status':'NOT_RUN_TWO_IMAGE_REVIEW_NOT_WIRED','API_CALLS':0},ensure_ascii=False,indent=2),encoding='utf-8')
    return result
