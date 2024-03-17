import asyncio
import logging
from pathlib import Path

import aiofiles
import aiohttp
from aiohttp import FormData
import fastapi

from config import settings
from database.models.slide import Slide
from enums import SlideType

logger = logging.getLogger()


def get_slide_emoji(slide_type: SlideType) -> str:
    slide_type_to_emoji = {
        'text': '🖋',
        'image': '🖼',
        'pin_dict': '📎',
        'small_sticker': '🧨',
        'big_sticker': '💣',
        'quiz_options': '🧩',
        'quiz_input_word': '🗨',
        'quiz_input_phrase': '💬',
        'final_slide': '🎉',
    }
    return slide_type_to_emoji.get(slide_type.value, '')


def get_slide_details(slide: Slide) -> str:
    slide_type_to_str = {
        'text': slide.keyboard_type if slide.keyboard_type else ' ',
        'image': slide.keyboard_type if slide.keyboard_type else ' ',
        'pin_dict': ' ',
        'small_sticker': ' ',
        'big_sticker': ' ',
        'quiz_options': slide.keyboard,
        'quiz_input_word': slide.right_answers,
        'quiz_input_phrase': slide.right_answers,
        'final_slide': ' ',
    }
    return slide_type_to_str.get(slide.slide_type.value, ' ')


def get_lesson_details(is_paid: bool) -> str:
    lesson_is_paid_to_str = {
        True: '☑️',
        False: ' ',
    }
    return lesson_is_paid_to_str.get(is_paid, ' ')


async def extract_img_from_form(request: fastapi.Request):
    async with request.form() as form_data:
        data = None
        if form_data.get('upload_new_picture') is not None:
            image_obj = form_data.get('upload_new_picture')
            data = await image_obj.read()
        return data


async def send_newsletter(user_id: int, message: str, image_path: Path = None) -> None:
    async with aiohttp.ClientSession() as session:
        if image_path is not None:
            url = f"https://api.telegram.org/bot{settings.BOT_TOKEN.get_secret_value()}/sendPhoto"
            data = FormData()
            data.add_field('chat_id', str(user_id))
            data.add_field('caption', message)
            async with aiofiles.open(image_path, 'rb') as photo:
                photo_data = await photo.read()
                data.add_field('photo', photo_data, filename=image_path.name)

            text_ok = (
                f'Сообщение с рассылкой "{message}" и файлом {image_path.name} было отправлено пользователю {user_id}.'
            )
            text_error = (
                f'Произошла ошибка при отправке рассылки "{message}" и файлом {image_path.name} пользователю {user_id}: '
                + '{}. {}'
            )
        else:
            url = f"https://api.telegram.org/bot{settings.BOT_TOKEN.get_secret_value()}/sendMessage"
            data = {
                'chat_id': str(user_id),
                'text': message,
            }
            text_ok = f'Сообщение с рассылкой "{message}" было отправлено пользователю {user_id}.'
            text_error = f'Произошла ошибка при отправке рассылки "{message}" пользователю {user_id}: ' + '{}. {}'

        async with session.post(url, data=data) as response:
            if response.status == 200:
                logger.info(text_ok)
            else:
                error_text = await response.text()
                logger.info(text_error.format(response.status, error_text))


async def send_newsletter_to_users(users: list[int], message: str, image_path: Path = None) -> None:
    for user in users:
        await send_newsletter(user, message, image_path)
        await asyncio.sleep(1)
