import re

_CJK_PATTERN = re.compile(
    r"[一-鿿㐀-䶿豈-﫿"
    r"\U00020000-\U0002a6df\U0002a700-\U0002ebef"
    r"　-〿＀-￯]"
)


def estimate_tokens(text: str) -> int:
    """Estimate token count for mixed CJK/English text.

    Heuristic based on typical BPE tokenizer behavior:
    - CJK characters: ~1.5 tokens each (many get split in BPE)
    - English words: ~1.3 tokens each (short words ~ 1, long words get split)
    - Punctuation/symbols: counted roughly via word splitting
    """
    if not text:
        return 0
    cjk_count = len(_CJK_PATTERN.findall(text))
    non_cjk = _CJK_PATTERN.sub(" ", text)
    ascii_tokens = [w for w in non_cjk.split() if w]
    ascii_word_count = len(ascii_tokens)
    return int(cjk_count * 1.5 + ascii_word_count * 1.3) + 1
