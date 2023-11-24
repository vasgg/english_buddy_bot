from sqlalchemy import Result, select

from core.database.models.user import User


async def create_user_in_db(event, session) -> User:
    new_user = User(
        telegram_id=event.from_user.id,
        first_name=event.from_user.first_name,
        last_name=event.from_user.last_name,
        username=event.from_user.username,
    )
    session.add(new_user)
    await session.flush()
    return new_user


async def get_user_from_db(event, session) -> User:
    query = select(User).filter(User.telegram_id == event.from_user.id)
    result: Result = await session.execute(query)
    user = result.scalar()
    if not user:
        user = await create_user_in_db(event, session)
    return user
