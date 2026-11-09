import streamlit as st
from app.services.recipe_session.shortage_review import candidates,draft_key
from app.services.recipe_session.review_store import ReviewStore,CHOICES
from app.services.recipe_session.store import RevisionConflict
from app.ui.recipe_stock_clarify_panel import render_stock_clarify

def _capture_editor(draft_id,field,widget_key):
    # This key is not owned by a widget, so hiding an editor cannot delete it.
    st.session_state[draft_id][field]=st.session_state[widget_key]


def _editor(key,draft_id,field,label,placeholder,epoch):
    widget_key=key+':editor:'+str(epoch)+':'+field
    value=st.text_input(label,value=st.session_state[draft_id][field],
        placeholder=placeholder,key=widget_key,max_chars=300,
        on_change=_capture_editor,args=(draft_id,field,widget_key))
    st.session_state[draft_id][field]=value


def render_shortage_review(review,sid,engine):
    st.subheader('부족 재료 검토')
    st.caption('검토 기록은 별도로 저장합니다. 기존 재료 응답·필요량·구매 동의는 변경하지 않습니다.')
    items=candidates(review)
    if not items:
        st.info('현재 미보유·부족으로 표시된 재료가 없습니다. 미확인·보류 재료는 위 요약에서 확인해 주세요.');return
    for item in items:
        key=draft_key(sid,item)+':editor_fix_v1'
        try:
            with engine.connect() as conn:
                store=ReviewStore(conn)
                saved=store.load(sid,item)
                previous=store.load_previous(sid,item)
        except Exception:
            st.error('검토 저장소를 읽지 못했습니다. 패키지의 setup_db.py 실행 결과를 확인해 주세요. 기존 재료 응답은 변경하지 않았습니다.');return
        if key+':version' not in st.session_state:
            st.session_state[key+':version']=0 if saved is None else saved['revision']
        notes=dict(choice=CHOICES[0],stock_raw='',substitute_raw='') if saved is None else saved['data']['notes']
        draft_id=key+':draft'
        if draft_id not in st.session_state:
            st.session_state[draft_id]=dict(notes)
        if key+':choice' not in st.session_state:
            st.session_state[key+':choice']=st.session_state[draft_id]['choice']
        with st.expander(item['name']+' · '+item['judgement'],expanded=True):
            st.write('원문 필요량: '+item['requirement_raw'])
            st.write('현재 확인: '+item['judgement'])
            st.write('레시피의 정확한 컵 기준: 확인 안 됨 · 팩 수는 아래 검토 기록에서 확인해요.')
            if saved is None:st.caption('현재 재료 응답 버전에 저장된 검토 기록이 없습니다. 이전 임시 메모는 자동 이전되지 않습니다.')
            else:
                st.caption('저장된 검토 버전: {} · 수정 시각: {}'.format(saved['revision'],saved['updated_at']))
                st.write('저장된 검토 선택: '+saved['data']['notes']['choice'])
                st.text('저장된 보유량 메모: '+(saved['data']['notes']['stock_raw'] or '(없음)'))
                st.text('저장된 대체 메모: '+(saved['data']['notes']['substitute_raw'] or '(없음)'))
            if previous is not None:
                with st.expander('이전 검토 기록 · 재확인 필요',expanded=True):
                    st.warning('이전 재료 응답의 기록입니다. 현재 보유량이나 구매 수량으로 확정하지 않았습니다.')
                    st.caption('이전 재료 응답 버전 {} · 검토 버전 {} · {}'.format(previous['answer_revision'],previous['revision'],previous['updated_at']))
                    old_notes=previous['data']['notes']
                    st.text('이전 보유량 메모: '+(old_notes['stock_raw'] or '(없음)'))
                    st.text('이전 대체 메모: '+(old_notes['substitute_raw'] or '(없음)'))
                    old_comparison=previous['data'].get('reference_comparison')
                    if old_comparison:st.text('이전 참고 비교: '+old_comparison['display'])
                    old_pack=previous['data'].get('pack_review')
                    if old_pack:
                        st.text('이전 팩 수: {}mL × {}팩 · 잔량 약 {}mL'.format(old_pack['pack_ml'],old_pack['pack_count'],old_pack['reference_remainder_ml']))
                    memo_kind=st.radio('가져올 이전 메모',['보유량 메모','대체 메모'],key=key+':import_kind_v2')
                    field='stock_raw' if memo_kind=='보유량 메모' else 'substitute_raw'
                    st.text('가져올 내용: '+(old_notes[field] or '(빈 메모)'))
                    consent=st.checkbox('선택한 메모의 현재 편집 내용을 이전 메모로 바꿀게요. 아직 저장되지는 않아요.',key=key+':import_consent_v2:'+field)
                    if st.button('선택한 이전 메모 가져오기',key=key+':import_notes_v2',disabled=not consent):
                        draft=dict(st.session_state[draft_id])
                        draft[field]=old_notes[field]
                        draft['choice']='보유량 확인' if field=='stock_raw' else '대체 재료 검토'
                        st.session_state[draft_id]=draft
                        st.session_state[key+':choice']=draft['choice']
                        st.session_state[key+':epoch']=st.session_state.get(key+':epoch',0)+1
                        st.session_state[key+':imported_v2']=memo_kind
                        st.rerun()
                imported=st.session_state.get(key+':imported_v2')
                if imported:
                    field='stock_raw' if imported=='보유량 메모' else 'substitute_raw'
                    if saved is not None and saved['data']['notes'][field]==st.session_state[draft_id][field]:
                        st.caption('가져온 '+imported+'가 현재 검토 기록에 저장되어 있습니다.')
                    else:
                        st.info('이전 '+imported+'를 편집란으로 가져왔습니다. 아직 저장하지 않았습니다. ‘검토 기록 저장’을 눌러 주세요.')
            st.caption('아래 입력은 ‘검토 기록 저장’을 눌러야 저장됩니다. 재접속 후 같은 레시피 확인을 이어가면 저장한 메모를 불러옵니다.')
            choice=st.radio('다음 검토',CHOICES,key=key+':choice')
            if st.session_state.get(key+':last_choice')!=choice:
                st.session_state[key+':epoch']=st.session_state.get(key+':epoch',0)+1
                st.session_state[key+':last_choice']=choice
            st.session_state[draft_id]['choice']=choice
            epoch=st.session_state[key+':epoch']
            if choice=='보유량 확인':
                _editor(key,draft_id,'stock_raw','보유량 메모','예: 생크림 200mL 절반 정도',epoch)
                st.caption('이번 저장은 보유량 메모에만 반영됩니다. 기존에 저장한 대체 메모는 유지됩니다.')
            elif choice=='대체 재료 검토':
                _editor(key,draft_id,'substitute_raw','대체 검토 메모','대신 쓰고 싶은 재료와 보유량',epoch)
                st.caption('이번 저장은 대체 검토 메모에만 반영됩니다. 기존에 저장한 보유량 메모는 유지됩니다.')
            else:
                st.caption('추가 메모 입력 없이 검토 선택만 저장합니다. 기존에 저장한 메모는 유지됩니다.')
            st.caption('항목을 바꿔도 현재 접속 중인 편집 내용은 유지됩니다. 재접속 시에는 저장한 메모를 불러옵니다.')
            st.caption('입력한 내용은 메모로 보관해요. 보유량 계산과 필요한 양의 비교는 아래에서 따로 확인해요. 다른 재료로 바꿔 쓸 수 있는지는 아직 확인하지 않았어요.')
            if st.button('검토 기록 저장',key=key+':save'):
                notes=dict(st.session_state[draft_id])
                try:
                    with engine.begin() as conn:version=ReviewStore(conn).save(sid,item,notes,st.session_state[key+':version'])
                except RevisionConflict:
                    st.warning('재료 응답 또는 검토 기록이 변경되어 저장하지 않았습니다. 저장된 레시피를 새 탭에서 다시 이어간 뒤 확인해 주세요.')
                except Exception:
                    st.error('검토 기록을 저장하지 못했습니다. 저장 완료로 처리하지 않았습니다.')
                else:
                    st.session_state[key+':version']=version
                    st.rerun()
            render_stock_clarify(item,sid,engine,saved,key,draft_id)
            st.caption('나중에 확인을 저장해도 기존 부족·미보유 판단과 구매 검토 후보는 유지됩니다. 상품 검색·장바구니·구매 실행은 연결하지 않았습니다.')
