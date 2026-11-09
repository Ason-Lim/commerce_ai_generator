import hashlib
import json
import streamlit as st
from app.services.recipe_session.review_store import ReviewStore
from app.services.recipe_session.stock_clarify import build_stock,suggest_stock_inputs,preview_stock
from app.services.recipe_session.store import RevisionConflict
from app.ui.recipe_reference_compare_panel import render_reference_compare


def matches_saved(confirmation,note,capacity,remaining,approximate):
    if confirmation is None:return False
    try:return build_stock(note,capacity,remaining,approximate,True)==confirmation
    except ValueError:return False


def confirmation_widget_key(form_key,note,capacity,remaining,approximate):
    identity=json.dumps([note,capacity,remaining,approximate],ensure_ascii=False)
    return form_key+':confirmed:'+hashlib.sha256(identity.encode()).hexdigest()


def render_stock_clarify(item,sid,engine,saved,key,draft_id):
    confirmation=None if saved is None else saved['data'].get('stock_confirmation')
    if confirmation is not None:
        prefix='약 ' if confirmation['approximate'] else ''
        st.write('고객 확인에 따른 보유량: '+prefix+confirmation['available_ml']+'mL')
        st.success('저장 완료 · 검토 버전 '+str(saved['revision'])+' · '+prefix+confirmation['available_ml']+'mL')
        st.caption('근거: 포장 전체 '+confirmation['container_ml']+'mL × 남은 비율 '+confirmation['remaining_percent']+'%. 필요한 양과의 비교는 아래 ‘필요량과 참고 비교’에서 따로 확인해요.')
    render_reference_compare(item,sid,engine,saved,key,draft_id)
    if st.session_state[draft_id]['choice']!='보유량 확인':return
    with st.expander('보유량 메모의 의미 확인',expanded=True):
        st.caption('포장 용량과 남은 비율로 표현한 메모에만 사용합니다. 예: 200mL 포장에 절반이 남았다면 전체 200, 남은 비율 50을 입력합니다. 이미 남은 양 자체가 200mL라는 뜻이면 이 계산을 적용하지 마세요.')
        if saved is None or not saved['data']['notes']['stock_raw'].strip():
            st.info('보유량 메모를 먼저 저장해 주세요.');return
        if st.session_state[draft_id]['stock_raw']!=saved['data']['notes']['stock_raw']:
            st.info('보유량 메모 수정 중입니다. 위의 검토 기록 저장을 먼저 눌러 주세요.');return
        # Separate from note editors; changed notes/review revision reset the confirmation form.
        form_key=key+':clarify:'+str(saved['revision'])
        note=saved['data']['notes']['stock_raw']
        suggestion=suggest_stock_inputs(note) if confirmation is None else None
        defaults=confirmation if confirmation is not None else (suggestion or {})
        if suggestion is not None:
            st.caption('저장된 메모에서 용량과 비율을 미리 채웠습니다. 내용을 확인·수정한 뒤 저장해 주세요.')
        elif confirmation is None:
            st.caption('메모에서 전체 용량과 남은 비율을 명확히 읽지 못했습니다. 아래에 입력해 주세요.')
        capacity=st.text_input('포장 전체 용량(mL)',value=defaults.get('container_ml',''),key=form_key+':container',max_chars=32)
        remaining=st.text_input('남은 비율(%)',value=defaults.get('remaining_percent',''),key=form_key+':percent',max_chars=32)
        if capacity.strip() and remaining.strip():
            try:amount=preview_stock(capacity,remaining)
            except ValueError as exc:st.warning(str(exc))
            else:
                st.info('예상 보유량: 약 '+amount+'mL · 현재 입력 기준')
                st.caption('입력란 밖을 클릭하거나 Enter를 누르면 예상량이 갱신됩니다. 확인·저장 전에는 새 보유량으로 반영하지 않습니다.')
        approximate=st.checkbox('대략 가늠한 양입니다',value=True if confirmation is None else confirmation['approximate'],key=form_key+':approximate')
        note=saved['data']['notes']['stock_raw']
        unchanged=matches_saved(confirmation,note,capacity,remaining,approximate)
        confirmed=st.checkbox('입력한 용량은 포장 전체 용량이며, 남은 비율을 확인했습니다',
            value=unchanged,key=confirmation_widget_key(form_key,note,capacity,remaining,approximate))
        if unchanged:st.caption('현재 입력값은 이미 확인·저장한 값입니다. 다시 저장할 필요가 없습니다.')
        elif confirmation is not None:st.info('입력값이 저장된 값과 다릅니다. 변경한 용량·비율을 확인한 뒤 저장해 주세요.')
        st.caption('직접 입력한 값과 확인에 근거해 보유량만 계산합니다. 레시피의 컵 용량과 재료 상태는 참고 비교에서 별도로 확인해요.')
        if st.button('저장 완료 · 변경 사항 없음' if unchanged and confirmed else '확인한 보유량 계산·저장',key=form_key+':save',disabled=unchanged and confirmed):
            try:
                value=build_stock(saved['data']['notes']['stock_raw'],capacity,remaining,approximate,confirmed)
                if unchanged:
                    st.info('같은 보유량이 이미 저장되어 있습니다.');return
                with engine.begin() as conn:revision=ReviewStore(conn).save(sid,item,saved['data']['notes'],st.session_state[key+':version'],stock_confirmation=value)
            except RevisionConflict:
                st.warning('저장된 기록이 변경되어 반영하지 않았습니다. 새 탭에서 같은 레시피를 이어가 주세요.')
            except ValueError as exc:st.warning(str(exc))
            except Exception:st.error('보유량 확인을 저장하지 못했습니다. 저장 완료로 처리하지 않았습니다.')
            else:
                st.session_state[key+':version']=revision
                st.rerun()
