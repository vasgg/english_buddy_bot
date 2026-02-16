from datetime import datetime, timezone
import logging

import arrow
from sqlalchemy import select

from database.models.user import User
from enums import UserSubscriptionType
from webapp.controllers.misc import get_color_code_emoji
from webapp.db import AsyncDBSession
from webapp.schemas.user import UsersSchema

logger = logging.getLogger()


async def get_users_table_content(session: AsyncDBSession):
    query = select(User).order_by(User.created_at.desc())
    result = await session.execute(query)
    results = result.scalars().all()
    users = []
    for i, user in enumerate(results, start=1):
        reverse_number = len(results) - i + 1
        expired_at = " "
        if user.subscription_expired_at and user.subscription_expired_at > datetime.now(timezone.utc).date():
            arrow_expired_at = arrow.get(user.subscription_expired_at)
            expired_at = arrow_expired_at.humanize(locale="ru")
        if user.subscription_status == UserSubscriptionType.UNLIMITED_ACCESS:
            expired_at = "никогда"
        link = f"/users/edit/{user.id}/"
        user_data = {
            "id": user.id,
            "number": reverse_number,
            "fullname": user.fullname,
            "username": user.username if user.username else " ",
            "credentials": f"{user.fullname} | {user.username}" if user.username else user.fullname,
            "color_code": get_color_code_emoji(user.subscription_status),
            "icon": "👤",
            "link": link,
            "subscription_expired_at": expired_at,
            "comment": user.comment if user.comment else " ",
            "registration_date": arrow.get(user.created_at).humanize(locale="ru"),
        }
        valid_user = UsersSchema.model_validate(user_data)
        users.append(valid_user)
    logger.info(f"processed {len(users)} users")
    return users
