"""Visible quantity rows under a color/quantity header; no invented weights."""
import json
import re
from .options import blue_dots, selection_states, save_hold, price
from .offer_rows import (compact, retry, padded, price_field, write_result,
                         button_boundary, semantic_words, words_box)


def quantity(text):
    matches=re.findall(r'(?<!\d)(\d+)\s*개',text)
    return int(matches[0]) if len(matches)==1 and int(matches[0])>0 else None


def color_frames(image, panel, top, bottom):
    """Bounded blue outline components, excluding small glyphs/solid thumbnail ink."""
    pix=image.load();points=set()
    for y in range(max(0,int(top)),min(image.height,int(bottom))):
        for x in range(panel[0],panel[2]):
            r,g,b=pix[x,y]
            if b>150 and b>r+45 and b>g+10:points.add((x,y))
    found=[]
    while points:
        start=points.pop();stack=[start];component=[start]
        while stack:
            x,y=stack.pop()
            for n in ((x-1,y),(x+1,y),(x,y-1),(x,y+1)):
                if n in points:points.remove(n);stack.append(n);component.append(n)
        xs,ys=zip(*component);w=max(xs)-min(xs)+1;h=max(ys)-min(ys)+1
        if 30<=w<(panel[2]-panel[0])*.5 and h>=40 and .3<=w/h<=2 and len(component)/(w*h)<.3:
            found.append([min(xs),min(ys),max(xs)+1,max(ys)+1])
    return found


def extract_quantity_variants(source,image,panel,rows,scan,anchor,out,tessdata=None):
    # Prices below the color chooser may share a line with quantity or sit above
    # it. Savings, points and unit prices are not option prices.
    candidates=[]
    for i in range(anchor+1,len(rows)):
        text=compact(rows[i]['text'])
        if any(v in text for v in ('절약','적립','당','배송','도착')):
            continue
        if re.search(r'\d{1,3}[,.]\d{3}',text):
            candidates.append(i)
    if not 1<=len(candidates)<=8:
        return save_hold(out,source,image,panel,'QUANTITY_PRICE_ROWS_UNRESOLVED')
    # Stop before the explicit options button; header/footer amounts cannot be rows.
    boundary_y,boundary=button_boundary(image,panel,rows[anchor]['source_bbox'][3],out,tessdata)
    if boundary_y is not None:
        candidates=[i for i in candidates if rows[i]['source_bbox'][1]<boundary_y]
    if not candidates:return save_hold(out,source,image,panel,'QUANTITY_PRICE_ROWS_UNRESOLVED')
    options=[];calls=1+len(boundary)
    for index,i in enumerate(candidates):
        row=rows[i];b=row['source_bbox'];rid='Q%03d'%(index+1)
        words=semantic_words(scan,row)
        price_words=[w for w in words if re.search(r'\d{1,3}[,.]\d{3}',w['text'])]
        if not price_words:
            continue
        px=panel[0]+min(w['bbox_px'][0] for w in price_words)/2
        # Determine the quantity column from the header's left edge and price x.
        # Include slight vertical misalignment without reading the later savings line.
        left=max(panel[0],int(rows[anchor]['source_bbox'][0])-3)
        qleft=min(int(px)-9,int(left+max(10,(b[3]-b[1])*.8)))
        qbox=[qleft,max(0,int(b[1])-4),max(left+1,int(px)-8),min(image.height,int(b[3])+8)]
        q=retry(image,qbox,rid+'_quantity',out,tessdata,'kor',7,3);calls+=1
        values={v for v in (quantity(row['text']),quantity(q['raw'])) if v is not None}
        fallback=None
        if not values:
            fallback=retry(image,qbox,rid+'_quantity_fallback',out,tessdata,'kor',7,4,True);calls+=1
            value=quantity(fallback['raw'])
            if value is not None:values.add(value)
        count=next(iter(values)) if len(values)==1 else None
        price_row=dict(row)
        price_row['source_bbox']=words_box(price_words,panel,2)
        p=price_field(image,price_row,rid,out,tessdata);calls+=max(0,len(p['price_evidence'])-1)
        rect=[left,max(0,int(b[1])-5),panel[2],min(image.height,int(b[3])+10)]
        image.crop(rect).save(out/(rid+'_source.png'))
        dots=blue_dots(image,left,rect[1],max(left,min(int(px)-40,int(left+image.width*.02))),rect[3])
        reasons=['quantity_is_offer_pack_count_not_weight','selection_uses_blue_component_heuristic',
                 'screen_claim_not_product_fact','savings_text_is_not_option_price']
        if count is None:reasons.append('quantity_unresolved_or_conflicting')
        if p['price_krw'] is None:reasons.append('price_unresolved')
        if not p['currency_unit_ocr_confirmed']:reasons.append('currency_ocr_unconfirmed')
        options.append({'id':rid,'weight_kg':None,'pack_quantity':count,'pack_unit':'개' if count else None,
            'box_quantity':None,'total_weight_kg_derived':None,'selected':None,**p,
            'quantity_evidence':q,'quantity_fallback_evidence':fallback,'title_ocr_raw':row['text'],'source_bbox_xyxy_px':rect,
            'source_image':rid+'_source.png','selection_blue_components':dots,
            'status':'CANDIDATE_REQUIRES_REVIEW','review_reasons':reasons,'verified_product_fact':False})
    states=selection_states([len(o['selection_blue_components']) for o in options])
    for o,state in zip(options,states):o['selected']=state
    selected=[o['id'] for o in options if o['selected'] is True]
    first_y=min(rows[i]['source_bbox'][1] for i in candidates)
    frames=color_frames(image,panel,rows[anchor]['source_bbox'][3],first_y-5)
    variant=None
    if len(frames)==1:
        f=frames[0];labelbox=[f[0]+3,int(f[1]+(f[3]-f[1])*.58),f[2]-3,f[3]-7]
        evidence=retry(image,labelbox,'V001_label',out,tessdata,'kor',7,3);calls+=1
        raw=evidence['raw'].strip()
        if raw and re.search(r'[가-힣]',raw):
            variant={'label_ocr_raw':raw,'label_compact':compact(raw),'frame_bbox_xyxy_px':f,
                     'evidence':evidence,'status':'BLUE_OUTLINE_SELECTION_CANDIDATE_REQUIRES_REVIEW'}
    result=write_result(source,image,panel,options,selected[0] if len(selected)==1 else None,
        'COLOR_VARIANT_WITH_QUANTITY_ROWS','EXPLICIT_OPTIONS_BUTTON_FOCUSED_OCR' if boundary_y else 'END_UNCONFIRMED',
        calls,out,{'selected_variant_candidate':variant,'variant_frame_candidates':frames,
                  'option_coverage':'VISIBLE_QUANTITIES_FOR_DISPLAYED_VARIANT_ONLY',
                  'visible_option_candidate_count':len(options),'boundary_evidence':boundary})
    # Weight is intentionally absent in this layout, not a failed required field.
    complete=bool(options) and all(o['pack_quantity'] is not None and o['price_krw'] is not None for o in options)
    result['status']='LINKAGE_CANDIDATE_REQUIRES_REVIEW' if complete and len(selected)==1 and boundary_y else 'UNRESOLVED_REQUIRES_REVIEW'
    result['limits'].append('Weight is not a required field here. Hidden color variants and their prices are not inferred.')
    (out/'options.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    return result
