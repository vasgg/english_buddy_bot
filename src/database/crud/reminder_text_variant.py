from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.reminder_text_variant import ReminderTextVariant


async def get_all_reminder_text_variants(db_session: AsyncSession) -> list[str]:
    query = select(ReminderTextVariant.text).order_by(ReminderTextVariant.id.asc())
    result = await db_session.execute(query)
    return list(result.scalars().all())
