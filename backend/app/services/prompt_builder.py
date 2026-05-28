from app.models.character import Character
from app.models.message import Message
from app.models.world import WorldBook


def build_system_prompt(world: WorldBook, character: Character) -> str:
    sections = []

    if world.setting:
        sections.append(f"【世界观】\n你所处的世界是「{world.name}」。\n{world.setting}")

    if world.rules:
        sections.append(f"【世界规则】\n{world.rules}")

    if world.factions:
        factions_text = "、".join(world.factions)
        sections.append(f"【势力与阵营】\n{factions_text}")

    if world.lore:
        sections.append(f"【历史与传说】\n{world.lore}")

    sections.append(f"【你的身份】\n你是{character.name}，{character.identity or ''}。")

    if character.personality:
        sections.append(f"【你的性格】\n{character.personality}")

    if character.background:
        sections.append(f"【你的经历】\n{character.background}")

    if character.relationships:
        sections.append(f"【你的人际关系】\n{character.relationships}")

    if character.language_style:
        sections.append(f"【说话风格】\n{character.language_style}")

    if character.knowledge:
        sections.append(f"【你知道的事情】\n{character.knowledge}")

    sections.append(
        "【行为准则】\n"
        f"- 始终以{character.name}的身份回应，不要跳出角色\n"
        "- 所有回答必须符合世界观设定，不能出现超出世界观的知识\n"
        "- 保持角色的说话风格和性格特征\n"
        "- 如果用户问的内容超出角色认知范围，以角色的方式表达困惑或不知"
    )

    return "\n\n".join(sections)


def build_messages(
    system_prompt: str,
    history: list[Message],
    user_input: str,
    max_history: int = 20,
) -> list[dict[str, str]]:
    messages: list[dict[str, str]] = [{"role": "system", "content": system_prompt}]

    recent = history[-max_history:]
    for msg in recent:
        messages.append({"role": msg.role, "content": msg.content})

    messages.append({"role": "user", "content": user_input})
    return messages
