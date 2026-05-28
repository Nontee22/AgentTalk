import re

_CJK_PATTERN = re.compile(
    r"[一-鿿㐀-䶿豈-﫿"
    r"\U00020000-\U0002a6df\U0002a700-\U0002ebef"
    r"　-〿＀-￯]"
)


def estimate_tokens(text: str) -> int:
    if not text:
        return 0
    cjk_count = len(_CJK_PATTERN.findall(text))
    non_cjk = _CJK_PATTERN.sub("", text)
    ascii_words = len(non_cjk.split())
    return int(cjk_count * 0.75 + ascii_words * 1.3) + 1
