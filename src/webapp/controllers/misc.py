import asyncio
import io
import logging
from pathlib import Path

from PIL import Image
import aiofiles
import aiohttp
from aiohttp import FormData
import fastapi

from config import Settings
from database.models.slide import Slide
from enums import SlideType, UserSubscriptionType
from webapp.schemas.slide import EditImageSlideData

logger = logging.getLogger()


def get_slide_emoji(slide_type: SlideType) -> str:
    slide_type_to_emoji = {
        SlideType.TEXT: '🖋',
        SlideType.IMAGE: '🖼',
        SlideType.PIN_DICT: '📎',
        SlideType.SMALL_STICKER: '🧨',
        SlideType.BIG_STICKER: '💣',
        SlideType.QUIZ_OPTIONS: '🧩',
        SlideType.QUIZ_INPUT_WORD: '🗨',
        SlideType.QUIZ_INPUT_PHRASE: '💬',
    }
    return slide_type_to_emoji.get(slide_type)


def get_slide_type_text(slide_type: SlideType) -> str:
    slide_type_to_text = {
        SlideType.TEXT: 'text',
        SlideType.IMAGE: 'image',
        SlideType.PIN_DICT: 'dict',
        SlideType.SMALL_STICKER: 'sticker',
        SlideType.BIG_STICKER: 'sticker',
        SlideType.QUIZ_OPTIONS: 'quiz_option',
        SlideType.QUIZ_INPUT_WORD: 'quiz_input_word',
        SlideType.QUIZ_INPUT_PHRASE: 'quiz_input_phrase',
    }
    return slide_type_to_text.get(slide_type)


def get_color_code_emoji(subscription_type: UserSubscriptionType) -> str:
    subscription_type_to_emoji = {
        UserSubscriptionType.NO_ACCESS: '⬜',
        UserSubscriptionType.UNLIMITED_ACCESS: '⭐',
        UserSubscriptionType.LIMITED_ACCESS: '🟩',
        UserSubscriptionType.ACCESS_EXPIRED: '🟥',
        UserSubscriptionType.ACCESS_INFO_REQUESTED: '🟨',
    }
    return subscription_type_to_emoji.get(subscription_type)


def get_slide_details(slide: Slide) -> str:
    slide_type_to_str = {
        SlideType.TEXT: slide.keyboard_type if slide.keyboard_type else ' ',
        SlideType.IMAGE: slide.keyboard_type if slide.keyboard_type else ' ',
        SlideType.PIN_DICT: ' ',
        SlideType.SMALL_STICKER: ' ',
        SlideType.BIG_STICKER: ' ',
        SlideType.QUIZ_OPTIONS: f'{slide.right_answers}|{slide.keyboard}',
        SlideType.QUIZ_INPUT_WORD: slide.right_answers,
        SlideType.QUIZ_INPUT_PHRASE: slide.right_answers,
    }
    return slide_type_to_str.get(slide.slide_type, ' ')


async def extract_img_from_form(request: fastapi.Request):
    async with request.form() as form_data:
        data = None
        if form_data.get('upload_new_picture') is not None:
            image_obj = form_data.get('upload_new_picture')
            data = await image_obj.read()
        return data


async def send_newsletter(bot_token: str, user_id: int, message: str, image_path: Path = None) -> None:
    async with aiohttp.ClientSession() as session:
        if image_path is not None:
            url = f"https://api.telegram.org/bot{bot_token}/sendPhoto"
            data = FormData()
            data.add_field('chat_id', str(user_id))
            data.add_field('caption', message)
            data.add_field('disable_notification', True)
            data.add_field('parse_mode', 'HTML')
            async with aiofiles.open(image_path, 'rb') as photo:
                photo_data = await photo.read()
                data.add_field('photo', photo_data, filename=image_path.name)

            text_ok = f'Сообщение с рассылкой "{message}" и файлом {image_path.name} было отправлено пользователю {user_id}.'
            text_error = (
                f'Произошла ошибка при отправке рассылки "{message}" и файлом {image_path.name} пользователю {user_id}: '
                + '{}. {}'
            )
        else:
            url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
            data = {
                'chat_id': str(user_id),
                'text': message,
                'disable_notification': True,
                'parse_mode': 'HTML',
            }
            text_ok = f'Сообщение с рассылкой "{message}" было отправлено пользователю {user_id}.'
            text_error = f'Произошла ошибка при отправке рассылки "{message}" пользователю {user_id}: ' + '{}. {}'

        async with session.post(url, data=data) as response:
            if response.status == 200:
                logger.info(text_ok)
            else:
                error_text = await response.text()
                logger.info(text_error.format(response.status, error_text))


async def send_newsletter_to_users(bot_token: str, users: list[int], message: str, image_path: Path = None) -> None:
    for user in users:
        await send_newsletter(bot_token, user, message, image_path)
        await asyncio.sleep(1)


def image_upload(image_file: bytes, form: EditImageSlideData, lesson_id: int, settings: Settings):
    if form.upload_new_picture.filename.rsplit('.', 1)[1].lower() in settings.allowed_image_formats:
        optimal_width = 800
        directory = Path(f"src/webapp/static/lessons_images/{lesson_id}")
        directory.mkdir(parents=True, exist_ok=True)
        image = Image.open(io.BytesIO(image_file))
        if image.width > optimal_width:
            new_height = int((optimal_width / image.width) * image.height)
            image = image.resize((optimal_width, new_height), Image.Resampling.LANCZOS)
        file_path = directory / form.upload_new_picture.filename
        with open(file_path, "wb") as buffer:
            image_format = form.upload_new_picture.content_type
            image.save(buffer, format=image_format.split("/")[1])


def trim_non_alpha(string: str) -> str:
    start = 0
    while start < len(string) and not string[start].isalpha():
        start += 1
    if start == len(string):
        return ""
    end = len(string) - 1
    while end >= 0 and not string[end].isalpha():
        end -= 1
    # fmt: off
    return string[start:end + 1]
    # fmt: on


def normalize_apostrophes(text):
    return text.replace("‘", "'").replace("’", "'").replace("`", "'")
