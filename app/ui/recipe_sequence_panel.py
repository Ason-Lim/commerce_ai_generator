import uuid
import hashlib
import streamlit as st
from app.services.recipe_session.sequence_467 import recipe,load_review,next_pending,apply,summary,LABELS
from app.services.recipe_session.store import RecipeSessionStore,RevisionConflict
from app.ui.recipe_shortage_panel import render_shortage_review
from app.services.recipe_session.resume_467 import list_saved, restore_review, session_tag

def render_recipe_followup_panel(engine_factory):
    source=recipe()
    st.header(source['basic']['RECIPE_NM_KO']+' · 재료 확인 시험')
    st.caption('공공데이터로 제공된 레시피 · '+source['basic']['QNT']+' · 직접 크림소스를 만드는 조리법')
    st.info('재료표 9개 외에 과정에서 바질·식용유가 확인됩니다. 바질은 분량이 없고 식용유는 과정에 약간으로 표기되어 있어 별도 확인 대상으로 표시합니다.')
    st.caption('레시피에 적힌 분량을 그대로 보여드려요. 컵 용량을 모르면 임의로 바꾸지 않아요. 현재는 2인분으로 확인할 수 있어요.')
    key='recipe_467_trial_session_id'
    if key not in st.session_state:st.session_state[key]='recipe:'+str(uuid.uuid4())
    if st.button('새 레시피 확인 시작',key='recipe_467_new'):
        st.session_state[key]='recipe:'+str(uuid.uuid4());st.rerun()
    st.caption('로컬 단일 사용자 시험용입니다. 저장된 확인을 선택하면 브라우저 재접속 후에도 이어갈 수 있습니다.')
    try:
        engine=engine_factory()
        with engine.connect() as conn:saved=list_saved(conn)
    except Exception:
        st.error('저장된 레시피 목록을 읽지 못했습니다. 기존 엔진 초기화 실행기를 확인해 주세요.');return
    with st.expander('저장된 레시피 확인 이어가기',expanded=True):
        if saved:
            by_sid={entry['session_id']:entry for entry in saved}
            options=list(by_sid)
            selected_sid=st.session_state.get('recipe_467_saved_sid',st.session_state[key])
            if selected_sid not in by_sid:selected_sid=options[0]
            labels_signature=hashlib.sha256(repr([(x['session_id'],x['label']) for x in saved]).encode()).hexdigest()[:16]
            choice=st.selectbox('저장된 확인 선택',options,index=options.index(selected_sid),
                format_func=lambda value:by_sid[value]['label'],key='recipe_467_saved_choice_v2:'+labels_signature)
            st.session_state['recipe_467_saved_sid']=choice
            if st.button('선택한 확인 이어가기',key='recipe_467_restore'):
                try:
                    with engine.connect() as conn:restore_review(conn,choice)
                    st.session_state[key]=choice
                    st.session_state.pop('recipe_467_review_index',None)
                except (ValueError,KeyError,TypeError):
                    st.error('저장된 원본 또는 상태가 현재 레시피와 일치하지 않아 복구하지 않았습니다.')
                except Exception:
                    st.error('저장된 확인을 복구하지 못했습니다. 기존 응답은 변경하지 않았습니다.')
                else:st.rerun()
        else:st.caption('아직 저장된 레시피 응답이 없습니다.')
    sid=st.session_state[key]
    st.caption('현재 확인: '+session_tag(sid)+' · 응답은 DB에 저장됩니다. 이어가기만으로는 응답이 변경되지 않습니다.')
    try:
        engine=engine_factory()
        cached_review=next((entry['review'] for entry in saved if entry['session_id']==sid),None)
        if cached_review is not None:review=cached_review
        else:
            with engine.connect() as conn:review=load_review(RecipeSessionStore(conn),sid)
    except Exception:
        st.error('레시피 저장소를 읽지 못했습니다. 기존 엔진 초기화 실행기를 사용하고 있는지 확인해 주세요.');return
    from app.ui.recipe_direct_chat_panel import render_direct_chat
    render_direct_chat(review,sid,engine)
    pending=next_pending(review)
    answered=sum(r['record']['state']['status'] not in ('ASK_PRESENCE','ASK_SUFFICIENCY') for r in review)
    st.progress(answered/len(review),text='재료 응답 완료 {}/{}'.format(answered,len(review)))
    if pending is not None:
        selected=pending
        st.caption('아직 응답하지 않은 재료를 순서대로 표시합니다.')
    else:
        st.success('모든 재료의 응답을 기록했습니다. 미확인·보류·출처 분량 미확인은 아래 표에서 확인해 주세요.')
        selected=None
    with st.expander('완료한 재료 다시 확인'):
        index=st.selectbox('재료 선택',range(len(review)),format_func=lambda i:review[i]['material']['name'],key='recipe_467_review_index')
        if st.button('선택한 재료 다시 질문',key='recipe_467_recheck'):
            row=review[index]
            if row['record']['state']['status'] in ('ASK_PRESENCE','ASK_SUFFICIENCY'):
                st.info('이미 확인할 질문이 남아 있습니다.')
            else:
                if _save(engine,sid,row,'recheck'):st.rerun()
    if selected is not None:
        row=review[selected];item=row['material'];state=row['record']['state']
        st.subheader(item['name'])
        st.write('원문 분량: '+item['quantity'])
        st.caption('원문 분류: '+item['source_role']+' · 필수/선택 여부를 뜻하지 않습니다.')
        if item['name']=='파스타':
            st.caption('원문은 파스타를 삶는 과정을 제시합니다. 200g의 계량 상태를 별도로 단정하거나 삶은 면 무게와 비교하지 않습니다.')
        if state['status']=='ASK_PRESENCE':
            st.write(item['name']+'이(가) 집에 있나요?')
            choices=[('have','있어요'),('none','없어요'),('unknown','잘 모르겠어요'),('skip','나중에 확인')]
        else:
            st.write('원문 분량 기준으로 준비할 수 있나요?')
            choices=[('enough','충분해요'),('short','부족해요'),('unknown','잘 모르겠어요'),('skip','나중에 확인')]
        for action,label in choices:
            if st.button(label,key='recipe467:{}:{}:{}'.format(selected,row['record']['revision'],action)):
                if _save(engine,sid,row,action):st.rerun()
    st.subheader('재료별 확인 요약')
    st.dataframe(summary(review),hide_index=True,use_container_width=True)
    st.caption('미보유·부족은 구매 검토 후보입니다. 선택 재료 여부·대체·수량·구매 동의는 아직 확인하지 않았습니다. 자동 구매 연결은 없습니다.')
    render_shortage_review(review,sid,engine)
    with st.expander('레시피 출처 보기'):
        st.write('제공기관: 농림수산식품교육문화정보원(EPIS)')
        st.write('레시피: 크림소스파스타 · 2인분')
        st.caption('출처에 적힌 재료와 분량을 사용합니다. 출처에 없는 컵 용량은 계산에 사용할 기준을 따로 확인해요.')
    with st.expander('원문 조리 과정 보기'):
        for step in source['steps']:st.write(step['COOKING_NO']+'. '+step['COOKING_DC'])

def _save(engine,sid,row,action):
    try:
        with engine.begin() as conn:apply(RecipeSessionStore(conn),sid,row['material'],action,row['record']['revision'])
        return True
    except RevisionConflict:
        st.warning('다른 응답이 먼저 저장되었습니다. 화면을 다시 불러와 주세요.')
    except Exception:
        st.error('저장하지 못했습니다. 응답 완료로 처리하지 않았습니다.')
    return False
