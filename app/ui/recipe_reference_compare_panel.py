import hashlib,json
import streamlit as st
from app.ui.recipe_pack_review_panel import render_pack_review
from app.services.recipe_session.reference_compare import build_comparison
from app.services.recipe_session.review_store import ReviewStore
from app.services.recipe_session.store import RevisionConflict


def render_reference_compare(item,sid,engine,saved,key,draft_id):
    if item['ingredient_id']!='EPIS:467:5145' or saved is None:return
    stock=saved['data'].get('stock_confirmation')
    if stock is None:return
    previous=saved['data'].get('reference_comparison')
    with st.expander('필요량과 참고 비교',expanded=True):
        st.caption('이 레시피에는 1컵이 몇 mL인지 안내되어 있지 않아요. 아래에서 정한 컵 용량으로 참고 계산할 수 있어요.')
        st.write('레시피에 적힌 필요량: '+item['requirement_raw'])
        st.write('고객 확인에 따른 보유량: '+('약 ' if stock['approximate'] else '')+stock['available_ml']+'mL')
        if previous is not None:
            st.success('참고 비교 저장 완료 · 검토 버전 '+str(saved['revision']))
            st.write(previous['display'])
            st.caption('직접 정한 컵 용량으로 계산한 참고 결과예요. 레시피에서 정한 정확한 컵 용량을 확인한 것은 아니에요.')
        if st.session_state[draft_id]['stock_raw']!=saved['data']['notes']['stock_raw']:
            st.info('보유량 메모 수정 중입니다. 메모 저장과 보유량 확인을 먼저 마쳐 주세요.');return
        form_key=key+':reference:'+str(saved['revision'])
        cup=st.text_input('이번 요리에 사용할 1컵 용량(mL)',value='' if previous is None else previous['selected_cup_ml'],key=form_key+':cup',max_chars=32)
        signature=hashlib.sha256(json.dumps([stock,cup],ensure_ascii=False,sort_keys=True).encode()).hexdigest()
        unchanged=previous is not None and cup==previous['selected_cup_ml'] and stock==previous['stock_confirmation']
        accepted=st.checkbox('위 설명을 확인했고, 입력한 컵 용량을 이번 요리의 참고 계산에 사용할게요.',value=unchanged,key=form_key+':accepted:'+signature)
        same=st.checkbox('입력한 보유량은 이번 요리에 쓸, 휘핑하지 않은 액체 생크림의 양이에요.',value=unchanged,key=form_key+':same_cream:'+signature)
        st.caption('휘핑한 크림이나 다른 재료는 같은 양으로 계산하지 않아요. 컵 용량이나 재료 상태를 모르겠다면 나중에 확인해도 돼요.')
        if previous is not None and not unchanged:st.info('입력한 가정이 저장된 비교와 다릅니다. 확인 후 저장하면 참고 비교가 갱신됩니다.')
        if st.button('참고 비교 저장 완료 · 변경 사항 없음' if unchanged and accepted and same else '가정 기준으로 참고 계산·저장',key=form_key+':save',disabled=unchanged and accepted and same):
            try:
                value=build_comparison(stock,item,cup,accepted,same)
                if previous==value:st.info('같은 참고 비교가 이미 저장되어 있습니다.');return
                with engine.begin() as conn:revision=ReviewStore(conn).save(sid,item,saved['data']['notes'],st.session_state[key+':version'],reference_comparison=value)
            except RevisionConflict:
                st.warning('저장된 기록이 변경되어 반영하지 않았습니다. 새 탭에서 같은 레시피를 이어가 주세요.')
            except ValueError as exc:st.warning(str(exc))
            except Exception:st.error('참고 비교를 저장하지 못했습니다. 저장 완료로 처리하지 않았습니다.')
            else:
                st.session_state[key+':version']=revision
                st.rerun()
        st.caption('이 참고 계산만으로 기존 답변이나 구매 여부가 바뀌지는 않아요.')
        if previous is not None and unchanged and accepted and same:
            render_pack_review(item,sid,engine,saved,key,previous)
        elif saved['data'].get('pack_review') is not None:
            st.info('컵 용량 확인이 저장된 내용과 달라 팩 수 검토를 숨겼어요. 참고 비교를 먼저 확인해 주세요.')
