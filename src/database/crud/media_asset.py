from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.media_asset import MediaAsset


async def get_media_asset_by_file_id(file_id: str, db_session: AsyncSession) -> MediaAsset | None:
    query = select(MediaAsset).filter(MediaAsset.file_id == file_id)
    result = await db_session.execute(query)
    return result.scalar_one_or_none()


async def get_media_asset_by_id(media_asset_id: int, db_session: AsyncSession) -> MediaAsset | None:
    return await db_session.get(MediaAsset, media_asset_id)


async def get_media_assets_by_ids(media_asset_ids: list[int], db_session: AsyncSession) -> dict[int, MediaAsset]:
    if not media_asset_ids:
        return {}
    query = select(MediaAsset).where(MediaAsset.id.in_(media_asset_ids))
    result = await db_session.execute(query)
    assets = result.scalars().all()
    return {asset.id: asset for asset in assets}


async def upsert_media_asset(
    *,
    file_id: str,
    media_type: str,
    file_name: str | None,
    file_extension: str | None,
    mime_type: str | None,
    file_unique_id: str | None,
    db_session: AsyncSession,
    comment: str | None = None,
) -> MediaAsset:
    media_asset = await get_media_asset_by_file_id(file_id, db_session)
    if media_asset is None:
        media_asset = MediaAsset(
            file_id=file_id,
            media_type=media_type,
            file_name=file_name,
            file_extension=file_extension,
            mime_type=mime_type,
            file_unique_id=file_unique_id,
            comment=comment,
        )
        db_session.add(media_asset)
        await db_session.flush()
        return media_asset

    media_asset.media_type = media_type
    media_asset.file_name = file_name
    media_asset.file_extension = file_extension
    media_asset.mime_type = mime_type
    media_asset.file_unique_id = file_unique_id
    if comment is not None:
        media_asset.comment = comment
    await db_session.flush()
    return media_asset


async def update_media_comment_by_file_id(
    *,
    file_id: str,
    comment: str,
    db_session: AsyncSession,
) -> MediaAsset | None:
    media_asset = await get_media_asset_by_file_id(file_id, db_session)
    if media_asset is None:
        return None
    media_asset.comment = comment
    await db_session.flush()
    return media_asset
