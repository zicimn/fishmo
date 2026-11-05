"""用户富文本消毒（nh3）。

评论允许少量排版标签，入库前统一清洗；文章正文是 Markdown，
不在此处消毒（前端渲染时用 DOMPurify）。
"""

import html
import re

import nh3

ALLOWED_TAGS = {
    "p", "br", "a", "strong", "b", "em", "i",
    "code", "pre", "blockquote", "ul", "ol", "li",
}
ALLOWED_ATTRIBUTES = {"a": {"href", "title"}}
ALLOWED_URL_SCHEMES = {"http", "https", "mailto"}

_TAG_ONLY = re.compile(r"<[^>]*>")


def sanitize_html(value: str) -> str:
    return nh3.clean(
        value or "",
        tags=ALLOWED_TAGS,
        attributes=ALLOWED_ATTRIBUTES,
        url_schemes=ALLOWED_URL_SCHEMES,
        link_rel="noopener noreferrer",
        strip_comments=True,
    )


def sanitize_comment(value: str) -> str:
    """把纯文本评论安全地转成 HTML 片段。

    前端可能上传纯文本或已经过 escape+``<br>`` 的 HTML：
    - 不含 ``<`` 视为纯文本：先转义，再保留换行；
    - 含 ``<`` 视为 HTML：交给 nh3 白名单清洗。
    """
    text = (value or "").strip()
    if not text:
        return ""
    if "<" not in text:
        text = html.escape(text).replace("\r\n", "\n").replace("\n", "<br>")
    return sanitize_html(text).strip()


def has_visible_text(value: str) -> bool:
    """清洗后的内容是否还有实际文字（过滤只发 ``<br>`` 的空评论）。"""
    return bool(_TAG_ONLY.sub("", value or "").replace("&nbsp;", " ").strip())