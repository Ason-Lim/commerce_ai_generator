# Streamlit Issues

## st.components.v1.html Deprecation

현재 Hero 카드와 스크롤 보정 스크립트에서 components.html을 사용한다.

Streamlit 경고:

st.components.v1.html will be removed after 2026-06-01.

## 현재 판단

Hero HTML 안정 렌더링과 anchor scroll 보정 때문에 즉시 변경하지 않는다.

## 향후 처리

Next.js 전환 전 다음 중 하나로 대체한다.

- st.iframe
- Streamlit native component
- Next.js Hero component
