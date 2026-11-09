import hashlib,json
import streamlit as st
from app.services.recipe_session.pack_review import build_pack
from app.services.recipe_session.review_store import ReviewStore
from app.services.recipe_session.store import RevisionConflict

def render_pack_review(item,sid,engine,saved,key,comparison):
    previous=saved['data'].get('pack_review')
    with st.expander('구매할 팩 수 검토',expanded=True):
        st.caption('저장된 컵 용량 가정과 보유량을 기준으로 계산해요. 살펴보는 상품 한 팩의 용량을 입력해 주세요.')
        st.write(comparison['display'])
        form=key+':pack:'+str(saved['revision'])
        volume=st.text_input('상품 한 팩의 용량(mL)',value='' if previous is None else previous['pack_ml'],key=form+':volume',max_chars=32)
        unchanged=previous is not None and volume==previous['pack_ml'] and previous['comparison']==comparison
        signature=hashlib.sha256(json.dumps([comparison,volume],sort_keys=True).encode()).hexdigest()
        confirmed=st.checkbox('상품에 표시된 한 팩의 용량이며, 이번 요리에 사용할 휘핑하지 않은 액체 생크림이에요.',value=unchanged,key=form+':confirmed:'+signature)
        if previous is not None:
            if unchanged and confirmed:
                st.success('팩 수 검토 저장 완료 · 검토 버전 '+str(saved['revision']))
            else:
                if not unchanged:
                    st.warning('한 팩 용량 또는 계산 근거가 변경되었습니다. 현재 입력은 아직 저장되지 않았습니다.')
                else:
                    st.warning('상품 용량과 재료 상태를 다시 확인해 주세요. 기존 저장 결과는 유지됩니다.')
                st.caption('이전 저장 결과 · 검토 버전 '+str(saved['revision'])+' · 현재 입력의 계산 결과가 아닙니다.')
            st.write('한 팩 '+previous['pack_ml']+'mL × '+str(previous['pack_count'])+'팩 = '+previous['total_ml']+'mL')
            st.write('참고 부족량을 채우고 남는 양: 약 '+previous['reference_remainder_ml']+'mL')
        st.caption('여러 팩 묶음의 전체 용량이나 g 표시는 여기에 입력하지 마세요. 이 단계에서는 한 팩의 mL 용량을 사용해요.')
        if st.button('팩 수 검토 저장 완료 · 변경 사항 없음' if unchanged and confirmed else '팩 수 계산·검토 저장',key=form+':save',disabled=unchanged and confirmed):
            try:
                value=build_pack(comparison,volume,confirmed)
                with engine.begin() as conn:
                    revision=ReviewStore(conn).save(sid,item,saved['data']['notes'],st.session_state[key+':version'],pack_review=value)
            except RevisionConflict:st.warning('저장된 근거가 변경됐습니다. 같은 레시피 확인을 다시 이어가 주세요.')
            except ValueError as exc:st.warning(str(exc))
            except Exception:st.error('팩 수 검토를 저장하지 못했습니다. 저장 완료로 처리하지 않았습니다.')
            else:
                st.session_state[key+':version']=revision
                st.rerun()
        st.caption('참고 구매 수량을 검토한 기록이에요. 주문이나 구매 동의를 뜻하지 않아요. 보유량이나 컵 용량을 바꾸면 다시 검토해야 해요.')
