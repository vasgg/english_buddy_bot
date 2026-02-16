import logging

from sqlalchemy import delete, select

from database.models.reminder_text_variant import ReminderTextVariant
from webapp.db import AsyncDBSession
from webapp.schemas.reminder_texts import ReminderTextVariantTableSchema

logger = logging.getLogger()


async def get_reminder_text_variants_table_content(session: AsyncDBSession) -> list[ReminderTextVariantTableSchema]:
    query = select(ReminderTextVariant).order_by(ReminderTextVariant.id.asc())
    result = await session.execute(query)
    results = result.scalars().all()
    variants: list[ReminderTextVariantTableSchema] = []
    for variant in results:
        variants.append(ReminderTextVariantTableSchema.model_validate(variant))
    logger.info("processed %s reminder text variants", len(variants))
    return variants


async def get_reminder_text_variant_by_id(variant_id: int, db_session: AsyncDBSession) -> ReminderTextVariant:
    query = select(ReminderTextVariant).filter(ReminderTextVariant.id == variant_id)
    result = await db_session.execute(query)
    return result.scalar()


async def delete_reminder_text_variant_by_id(variant_id: int, db_session: AsyncDBSession) -> None:
    query = delete(ReminderTextVariant).filter(ReminderTextVariant.id == variant_id)
    await db_session.execute(query)
