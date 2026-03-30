"""
Тестирую работу разделителя на сообщения
который не режет по сепаратору "\n\n─────────────────────\n\n"
"""


def debug_split_text(text: str, max_length: int = 40):
    separator = "\n\n─────────────────────\n\n"

    print("ИСХОДНЫЙ ТЕКСТ:")
    print(repr(text))
    print("=" * 60)

    if len(text) <= max_length:
        print("Текст короткий, отправили бы целиком:")
        print(repr(text))
        return

    remaining_text = text
    part_number = 1

    while len(remaining_text) > max_length:
        print(f"\nШАГ {part_number}")
        print("remaining_text =", repr(remaining_text))

        split_pos = remaining_text.rfind(separator, 0, max_length)
        print("rfind(separator) =", split_pos)

        if split_pos == -1:
            split_pos = remaining_text.rfind("\n", 0, max_length)
            print("rfind('\\n') =", split_pos)

        if split_pos == -1:
            split_pos = max_length
            print("Ничего не нашли, режем по длине =", split_pos)

        chunk = remaining_text[:split_pos]
        print("chunk до проверки =", repr(chunk))

        if not chunk.strip():
            chunk = remaining_text[:max_length]
            split_pos = max_length
            print("chunk был пустышкой, режем по длине")
            print("новый chunk =", repr(chunk))
            print("новый split_pos =", split_pos)

        print(f"🔥 ОТПРАВИЛИ БЫ ЧАСТЬ {part_number}:")
        print(repr(chunk))
        print()

        remaining_text = remaining_text[split_pos:]
        print("remaining_text после среза =", repr(remaining_text))

        if remaining_text.startswith(separator):
            remaining_text = remaining_text[len(separator) :]
            print("Убрали separator в начале remaining_text")
        else:
            remaining_text = remaining_text.lstrip("\n")
            print("Убрали только \\n слева")

        print("remaining_text после очистки =", repr(remaining_text))

        part_number += 1

    if remaining_text.strip():
        print(f"\nОТПРАВИЛИ БЫ ФИНАЛЬНУЮ ЧАСТЬ {part_number}:")
        print(repr(remaining_text))


if __name__ == "__main__":
    separator = "\n\n─────────────────────\n\n"

    text = (
        "\n\n─────────────────────\n\n"
        "\n\n─────────────────────\n\n"
        "<i>📖 Бар | bar</i>\n\n"
        "\n\n─────────────────────\n\n"
        "<b>Описание: </b> Первый блок"
        "\n\n─────────────────────\n\n"
        "<i>📖 Бар | bar</i>\n\n"
        "<b>Описание: </b> Второй блок"
        "\n\n─────────────────────\n\n"
        "<i>📖 Бар | bar</i>\n\n"
        "<b>Описание: </b> Третий блок"
        "\n\n─────────────────────\n\n"
    )

    debug_split_text(text, max_length=80)
