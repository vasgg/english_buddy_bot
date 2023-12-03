from random import choice


def get_random_sticker_id(collection: tuple[str]) -> str:
    random_sticker_id = choice(collection)
    return random_sticker_id
