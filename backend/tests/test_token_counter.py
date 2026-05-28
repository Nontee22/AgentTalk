from app.services.token_counter import estimate_tokens


def test_estimate_tokens_chinese():
    text = "你好世界"
    tokens = estimate_tokens(text)
    assert tokens >= 3


def test_estimate_tokens_english():
    text = "hello world this is a test"
    tokens = estimate_tokens(text)
    assert tokens >= 6


def test_estimate_tokens_mixed():
    text = "你好 hello 世界 world"
    tokens = estimate_tokens(text)
    assert tokens >= 4


def test_estimate_tokens_empty():
    assert estimate_tokens("") == 0
    assert estimate_tokens(None) == 0


def test_estimate_tokens_code():
    text = "def hello():\n    print('world')"
    tokens = estimate_tokens(text)
    assert tokens > 0
