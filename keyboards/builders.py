from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder


def inline_builder(text: str | list[str],
                   callback_data: str | list[str],
                   sizes: int | list[int] = 2,
                   **kwargs):
    builder = InlineKeyboardBuilder()
    if isinstance(text, str):
        callback_data = [text]
    if isinstance(callback_data, str):
        callback_data = [callback_data]
    if isinstance(sizes, int):
        sizes = [sizes]

    [builder.button(text=txt, callback_data=cb) for txt, cb in zip(text, callback_data)]

    builder.adjust(*sizes)
    return builder.as_markup(**kwargs)
