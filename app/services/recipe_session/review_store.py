"""Caller-owned transactions; review notes separate from ingredient answers."""
import json
from .store import RecipeSessionStore, RevisionConflict, context_key

from .stock_clarify import validate_stock
from .reference_compare import validate_comparison
from .pack_review import validate_pack

_UNCHANGED=object()

CHOICES=['아직 선택하지 않음','보유량 확인','대체 재료 검토','나중에 확인']

def validate_notes(notes):
    if not isinstance(notes,dict) or set(notes)!={'choice','stock_raw','substitute_raw'}:raise ValueError('Invalid notes')
    if notes['choice'] not in CHOICES:raise ValueError('Invalid choice')
    for k in ('stock_raw','substitute_raw'):
        if not isinstance(notes[k],str) or len(notes[k])>300:raise ValueError('Invalid memo')

def selected_notes(choice,stock_raw,substitute_raw,previous=None):
    result=dict(choice=choice,stock_raw='',substitute_raw='') if previous is None else dict(previous)
    result['choice']=choice
    if choice=='보유량 확인':result['stock_raw']=stock_raw
    elif choice=='대체 재료 검토':result['substitute_raw']=substitute_raw
    validate_notes(result)
    return result

class ReviewStore:
    def __init__(self,conn,statement_factory=None):
        if statement_factory is None:
            from sqlalchemy import text
            statement_factory=text
        self.conn=conn;self.sql=statement_factory

    def identity(self,sid,item):
        if type(item['revision']) is not int or item['revision']<1:raise ValueError('Unsaved answer')
        return dict(session_id=sid,ingredient_id=item['ingredient_id'],answer_revision=item['revision'],context_key=context_key(item['context']))

    def load(self,sid,item):
        params=self.identity(sid,item)
        row=self.conn.execute(self.sql('''SELECT review_json,revision,updated_at FROM public.recipe_material_review
            WHERE session_id=:session_id AND ingredient_id=:ingredient_id
            AND answer_revision=:answer_revision AND context_key=:context_key'''),params).mappings().first()
        if row is None:return None
        data=json.loads(row['review_json']);validate_notes(data['notes'])
        if data.get('stock_confirmation') is not None:validate_stock(data['stock_confirmation'],data['notes']['stock_raw'])
        if data.get('reference_comparison') is not None:validate_comparison(data['reference_comparison'],data.get('stock_confirmation'),item)
        if data.get('pack_review') is not None:validate_pack(data['pack_review'],data.get('reference_comparison'))
        if len(data['history'])!=row['revision']:raise ValueError('Review history mismatch')
        return dict(data=data,revision=row['revision'],updated_at=str(row['updated_at']))

    def load_previous(self,sid,item):
        """Read only: same session, ingredient and context; older answer only."""
        params=self.identity(sid,item)
        row=self.conn.execute(self.sql('''SELECT answer_revision FROM public.recipe_material_review
            WHERE session_id=:session_id AND ingredient_id=:ingredient_id
            AND context_key=:context_key AND answer_revision<:answer_revision
            ORDER BY answer_revision DESC LIMIT 1'''),params).mappings().first()
        if row is None:return None
        older=dict(item,revision=int(row['answer_revision']))
        result=self.load(sid,older)
        if result is not None:result['answer_revision']=older['revision']
        return result

    def save(self,sid,item,notes,expected_revision,stock_confirmation=_UNCHANGED,reference_comparison=_UNCHANGED,pack_review=_UNCHANGED):
        validate_notes(notes)
        if type(expected_revision) is not int or expected_revision<0:raise ValueError('Invalid revision')
        params=self.identity(sid,item)
        # Serializes review saving with answer updates; SQLite tests omit this PG clause.
        locked=self.conn.execute(self.sql('''SELECT revision FROM public.recipe_followup_state
            WHERE session_id=:session_id AND ingredient_id=:ingredient_id FOR UPDATE'''),params).mappings().first()
        if locked is None:raise RevisionConflict('Answer missing')
        original=RecipeSessionStore(self.conn,self.sql).load(sid,item['ingredient_id'])
        if original['revision']!=item['revision'] or original['state']['context']!=item['context']:
            raise RevisionConflict('Answer changed')
        if original['state']['status'] not in ('CUSTOMER_REPORTED_SHORT','CUSTOMER_REPORTED_ABSENT') or original['state']['purchase_candidate'] is not True:
            raise RevisionConflict('No longer a candidate')
        old=self.load(sid,item)
        if (0 if old is None else old['revision'])!=expected_revision:raise RevisionConflict('Review changed')
        notes=selected_notes(notes['choice'],notes['stock_raw'],notes['substitute_raw'],None if old is None else old['data']['notes'])
        history=[] if old is None else list(old['data']['history'])
        previous=None if old is None else old['data'].get('stock_confirmation')
        if stock_confirmation is _UNCHANGED:
            confirmation=previous if previous is not None and previous.get('stock_note')==notes['stock_raw'] else None
        else:
            validate_stock(stock_confirmation,notes['stock_raw'])
            confirmation=stock_confirmation
        old_comparison=None if old is None else old['data'].get('reference_comparison')
        if reference_comparison is _UNCHANGED:
            comparison=old_comparison if confirmation is not None and confirmation==previous else None
        else:
            validate_comparison(reference_comparison,confirmation,item)
            comparison=reference_comparison
        old_pack=None if old is None else old['data'].get('pack_review')
        if pack_review is _UNCHANGED:
            pack=old_pack if comparison is not None and comparison==old_comparison else None
        else:
            validate_pack(pack_review,comparison)
            pack=pack_review
        history.append(dict(notes=dict(notes),stock_confirmation=confirmation,reference_comparison=comparison,pack_review=pack))
        data=dict(notes=dict(notes),history=history,stock_confirmation=confirmation,reference_comparison=comparison,pack_review=pack)
        params.update(review_json=json.dumps(data,ensure_ascii=False,allow_nan=False),expected_revision=expected_revision)
        if expected_revision==0:
            query='''INSERT INTO public.recipe_material_review
                (session_id,ingredient_id,answer_revision,context_key,review_json,revision)
                VALUES (:session_id,:ingredient_id,:answer_revision,:context_key,:review_json,1)
                ON CONFLICT (session_id,ingredient_id,answer_revision,context_key) DO NOTHING'''
        else:
            query='''UPDATE public.recipe_material_review SET review_json=:review_json,revision=revision+1,
                updated_at=CURRENT_TIMESTAMP WHERE session_id=:session_id AND ingredient_id=:ingredient_id
                AND answer_revision=:answer_revision AND context_key=:context_key AND revision=:expected_revision'''
        if self.conn.execute(self.sql(query),params).rowcount!=1:raise RevisionConflict('Review changed')
        return expected_revision+1
