from __future__ import annotations

from app.ui.html_utils import (
    safe_attr,
    safe_html,
)


def build_cta_html(
    *,
    url: str,
    text: str,
    css_class: str = "product-link-button",
) -> str:
    """
    URL과 버튼 문구로 안전한 CTA HTML을 생성합니다.
    """

    url = str(
        url or ""
    ).strip()

    text = str(
        text or ""
    ).strip()

    if not url or not text:
        return ""

    return (
        f'<a href="{safe_attr(url)}" '
        'target="_blank" '
        'rel="noopener noreferrer" '
        f'class="{safe_attr(css_class)}">'
        f'{safe_html(text)}'
        '</a>'
    )


def render_cta_button(
    st,
    *,
    url: str = "",
    text: str = "",
    html: str = "",
    heading: str = "",
    css_class: str = "product-link-button",
):
    """
    Hero와 상품 카드가 공유하는 CTA 렌더러입니다.

    html이 있으면 해당 HTML을 우선 사용하고,
    없으면 url + text로 CTA HTML을 생성합니다.
    """

    cta_html = str(
        html or ""
    ).strip()

    if not cta_html:
        cta_html = build_cta_html(
            url=url,
            text=text,
            css_class=css_class,
        )

    if not cta_html:
        return

    if heading:
        st.markdown(
            heading
        )

    st.html(
        cta_html
    )