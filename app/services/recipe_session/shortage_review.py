"""Read-only projection. Customer judgement does not establish numeric shortage."""
import hashlib


def candidates(review):
    result=[]
    for row in review:
        m=row['material'];record=row['record'];s=record['state']
        if s['status'] not in ('CUSTOMER_REPORTED_SHORT','CUSTOMER_REPORTED_ABSENT'):continue
        if s.get('purchase_candidate') is not True:continue
        result.append(dict(ingredient_id=m['context']['ingredient_id'],name=m['name'],
            requirement_raw=m['quantity'],status=s['status'],revision=record['revision'],
            context=m['context'],judgement='고객 판단: 부족' if s['status']=='CUSTOMER_REPORTED_SHORT' else '고객 응답: 미보유',
            numeric_shortage=None,shopping_consent=None))
    return result


def draft_key(sid,item):
    # Changes to source or answer revision invalidate earlier review drafts.
    import json
    identity=json.dumps([sid,item['context'],item['revision']],sort_keys=True,ensure_ascii=False)
    return 'recipe_shortage:'+hashlib.sha256(identity.encode()).hexdigest()
