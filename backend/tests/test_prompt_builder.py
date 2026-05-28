from unittest.mock import MagicMock

from app.services.prompt_builder import build_messages, build_system_prompt


def _make_message(role: str, content: str, token_count: int | None = None):
    msg = MagicMock()
    msg.role = role
    msg.content = content
    msg.token_count = token_count
    return msg


def _make_world(**kwargs):
    defaults = {
        "name": "Test World",
        "setting": "A test world setting",
        "rules": "Rule 1\nRule 2",
        "lore": "Ancient history",
        "factions": ["Faction A", "Faction B"],
    }
    defaults.update(kwargs)
    world = MagicMock()
    for k, v in defaults.items():
        setattr(world, k, v)
    return world


def _make_character(**kwargs):
    defaults = {
        "name": "Test Char",
        "identity": "A test character",
        "personality": "Brave",
        "background": "Born in test",
        "relationships": "Friend of Test2",
        "language_style": "Formal",
        "knowledge": "Knows everything",
    }
    defaults.update(kwargs)
    char = MagicMock()
    for k, v in defaults.items():
        setattr(char, k, v)
    return char


def test_build_system_prompt_includes_world():
    world = _make_world()
    char = _make_character()
    prompt = build_system_prompt(world, char)
    assert "Test World" in prompt
    assert "A test world setting" in prompt
    assert "Rule 1" in prompt
    assert "Ancient history" in prompt
    assert "Faction A" in prompt


def test_build_system_prompt_includes_character():
    world = _make_world()
    char = _make_character()
    prompt = build_system_prompt(world, char)
    assert "Test Char" in prompt
    assert "Brave" in prompt
    assert "Formal" in prompt
    assert "行为准则" in prompt


def test_build_system_prompt_skips_none_fields():
    world = _make_world(rules=None, lore=None, factions=None)
    char = _make_character(background=None, relationships=None)
    prompt = build_system_prompt(world, char)
    assert "世界规则" not in prompt
    assert "历史与传说" not in prompt
    assert "你的经历" not in prompt


def test_build_messages_fits_in_budget():
    system = "System prompt"
    history = [_make_message("user", "msg " * 50, 100) for _ in range(10)]
    messages = build_messages(system, history, "hello", max_context_tokens=500)
    assert messages[0]["role"] == "system"
    assert messages[-1]["role"] == "user"
    assert messages[-1]["content"] == "hello"
    history_count = len(messages) - 2
    assert history_count < 10


def test_build_messages_all_fit():
    system = "Short prompt"
    history = [_make_message("user", "hi", 5) for _ in range(3)]
    messages = build_messages(system, history, "hello", max_context_tokens=6000)
    assert len(messages) == 5


def test_build_messages_empty_history():
    system = "System"
    messages = build_messages(system, [], "hello")
    assert len(messages) == 2
    assert messages[0]["role"] == "system"
    assert messages[1]["role"] == "user"


def test_build_messages_respects_max_history():
    system = "S"
    history = [_make_message("user", "x", 1) for _ in range(50)]
    messages = build_messages(system, history, "y", max_history=5, max_context_tokens=100000)
    history_count = len(messages) - 2
    assert history_count <= 5
