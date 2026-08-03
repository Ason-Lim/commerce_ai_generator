import html


def safe_html(value):
    """HTML 본문에 넣을 텍스트 이스케이프"""
    return html.escape(str(value or ""), quote=False)


def safe_attr(value):
    """HTML 속성값에 넣을 텍스트 이스케이프"""
    return html.escape(str(value or ""), quote=True)
