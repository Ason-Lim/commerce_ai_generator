import streamlit as st
from app.services.recipe_session.direct_stock_chat import interpret,save_direct
from app.services.recipe_session.store import RecipeSessionStore,RevisionConflict


def render_direct_chat(review,sid,engine):
    st.subheader('말로 보유량 입력하기')
    st.caption('예: 생크림 100mL 남았어요 · 재료 하나씩 입력해 주세요. 조리 질문·인분 변경·추가량 합산은 다음 연결 단계입니다.')
    key='direct_stock_chat:'+sid
    pending_key=key+':pending'
    message=st.text_input('어떤 재료가 얼마나 남아 있나요?',key=key+':message',max_chars=300)
    if st.button('입력 내용 확인',key=key+':parse',disabled=not message.strip()):
        st.session_state.pop(pending_key,None)
        try:
            with st.spinner('입력 내용을 확인하고 있어요…'):
                proposal=interpret(message,[r['material'] for r in review])
            row=next(r for r in review if r['material']['context']['ingredient_id']==proposal['ingredient_id'])
            st.session_state[pending_key]=dict(proposal=proposal,context=row['material']['context'],revision=row['record']['revision'])
        except ValueError as exc: st.warning(str(exc))
        except Exception: st.error('입력을 처리하지 못했어요. 보유량은 변경하지 않았습니다.')
    pending=st.session_state.get(pending_key)
    if pending and message==pending['proposal']['message']:
        p=pending['proposal']
        st.info(p['name']+'의 현재 전체 보유량을 '+p['amount']+p['unit']+'로 저장합니다. 이전 직접 보유량이 있으면 교체합니다.')
        if st.button('이 내용으로 저장',key=key+':save'):
            try:
                row=next(r for r in review if r['material']['context']==pending['context'])
                with engine.begin() as conn:
                    save_direct(RecipeSessionStore(conn),sid,row['material'],p,pending['revision'])
            except (RevisionConflict,StopIteration):
                st.warning('재료 기록이 변경됐어요. 새로고침 후 다시 입력해 주세요.')
            except Exception: st.error('저장하지 못했습니다. 저장 완료로 처리하지 않았습니다.')
            else:
                st.session_state.pop(pending_key,None)
                st.session_state[key+':notice']='보유량을 저장했어요.'
                st.rerun()
    if st.session_state.pop(key+':notice',None): st.success('보유량을 저장했어요.')
    rows=[]
    for row in review:
        stock=row['record']['state'].get('direct_stock')
        if stock:
            rows.append({'재료':row['material']['name'],'원문 필요량':row['material']['quantity'],
                         '직접 입력한 보유량':stock['amount']+stock['unit'],'부족량':'비교 기준 확인 필요'})
    if rows: st.dataframe(rows,hide_index=True)
    st.caption('직접 보유량은 기존 충분·부족 응답과 별도로 저장합니다. 기존 응답에 연결된 참고 비교·팩 수 기록은 이전 버전이 되므로 다시 확인해야 합니다. 컵 용량이나 재료 상태를 임의 환산하지 않습니다.')
