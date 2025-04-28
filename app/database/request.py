from app.database.models import async_session
from app.database.models import User, Photo, UserPreferences, Like, Match
from sqlalchemy import select, update, or_, and_, func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

async def set_user(tg_id, username):
    async with async_session() as session:
        user = await session.scalar(select(User).where(User.tg_id == tg_id))

        if not user:
            session.add(User(tg_id=tg_id, username=username))
            await session.commit()

async def get_user_by_id(tg_id):
    async with async_session() as session:
        return await session.scalar(select(User).where(User.tg_id == tg_id))
    
async def calculate_and_update_rating(user: User, session: AsyncSession):
    await user.calculate_primary_rating(session)
    await user.calculate_combined_rating(session)
    session.add(user)
    await session.commit()

async def register_user(tg_id, first_name, username, age, description, gender, city, photo_url):
    async with async_session() as session:
        async with session.begin():
            try:
                user = await session.scalar(select(User).where(User.tg_id == tg_id))
                if user:
                    user.first_name = first_name
                    user.username = username
                    user.age = age
                    user.description = description
                    user.gender = gender
                    user.city = city
                    session.add(Photo(user_id=user.id, photo_path=photo_url))
                else:
                    user = User(
                        tg_id=tg_id,
                        first_name=first_name,
                        username=username,
                        age=age,
                        description=description,
                        gender=gender,
                        city=city
                    )
                    session.add(user)
                    await session.flush()
                    session.add(Photo(user_id=user.id, photo_path=photo_url))
                await user.calculate_primary_rating()
                await user.calculate_combined_rating()
                return True, 'Регистрация успешна завершена!'
            except IntegrityError as e:
                await session.rollback()
                return False, f'Ошибка регистрации: {e}'
            except Exception as e:
                await session.rollback()
                return False, f'Непредвиденная ошибка: {e}'

async def get_user_profile(tg_id):
    async with async_session() as session:
        user = await session.scalar(select(User).where(User.tg_id == tg_id))
        if user:
            photo = await session.scalar(select(Photo).where(Photo.user_id == user.id))
            photo_url = photo.photo_path if photo else None
            return user, photo_url
        return None, None

async def update_user_profile(tg_id, field_name, new_value):
    async with async_session() as session:
        async with session.begin():
            user = await session.scalar(select(User).where(User.tg_id == tg_id))
            if not user:
                return False, 'Пользователь не найден'
            if field_name == 'photo_path':
                photo = await session.scalar(select(Photo).where(Photo.user_id == user.id))
                if photo:
                    photo.photo_path = new_value
                else:
                    session.add(Photo(photo_path=new_value, user_id=user.id))
                await session.commit()
                return True, 'Фото успешно обновлено!'
            else:
                setattr(user, field_name, new_value)
                if field_name in ['first_name', 'age', 'description', 'gender', 'city']:
                    await user.calculate_primary_rating()
                    await user.calculate_combined_rating()
                return True, 'Ваш профиль обновлен!'
    
async def delete_user_profile(tg_id):
    async with async_session() as session:
        user = await session.scalar(select(User).where(User.tg_id == tg_id))
        if user:
            await session.delete(user)
            await session.commit()
            return True, 'Профиль успешно удален'
        else:
            return False, 'Пользователь не найден'
        
async def specify_parametrs(tg_id, preferred_gender, min_age, max_age, preferred_city):
    async with async_session() as session:
        user = await session.scalar(select(User).where(User.tg_id == tg_id))
        preferences = await session.scalar(
            select(UserPreferences).where(UserPreferences.user_id == user.id))
        if preferences:
            await session.execute(
                update(UserPreferences)
                .where(UserPreferences.user_id == user.id)
                .values(
                    user_id=user.id,
                    preferred_gender=preferred_gender,
                    min_age=min_age,
                    max_age=max_age,
                    preferred_city=preferred_city
                )
            )
        else:
            preferences = UserPreferences(
                user_id=user.id,
                preferred_gender=preferred_gender,
                min_age=min_age,
                max_age=max_age,
                preferred_city=preferred_city,
            )
            session.add(preferences)
        try:
            await session.commit()
            return True, 'Отлично! Основываясь на ваших предпотениях, мы сможем найти вам подходящего партнера!'
        except IntegrityError as e:
            await session.rollback()
            return False, f'Ошибка регистрации: {e}'
        except Exception as e:
            await session.rollback()
            return False, f'Непредвиденная ошибка: {e}'
        
async def get_user_preferences(tg_id):
    async with async_session() as session:
        user = await session.scalar(select(User).where(User.tg_id == tg_id))
        if not user:
            return None
        preferences = await session.scalar(
            select(UserPreferences).where(UserPreferences.user_id == user.id)
        )
        if preferences:
            return {
                "gender": preferences.preferred_gender,
                "min_age": preferences.min_age,
                "max_age": preferences.max_age,
                "city": preferences.preferred_city,
            }
        else:
            return None
        
async def get_matching_profiles(tg_id):
    async with async_session() as session:
        preferences = await get_user_preferences(tg_id)
        if not preferences:
            return None
        query = (
            select(User)
            .join(Photo, User.id == Photo.user_id)
            .where(User.tg_id != tg_id)
        )

        if preferences.get("gender"):
            query = query.where(User.gender == preferences["gender"])

        if preferences.get("min_age"):
            query = query.where(User.age >= preferences["min_age"])

        if preferences.get("max_age"):
            query = query.where(User.age <= preferences["max_age"])

        if preferences.get("city"):
            query = query.where(User.city == preferences["city"])

        query = query.options(selectinload(User.photos))

        result = await session.execute(query)
        profiles = result.fetchall()

        return [{
            "id": profile.User.id,
            "first_name": profile.User.first_name,
            "age": profile.User.age,
            "description": profile.User.description,
            "city": profile.User.city,
            "photo_path": profile.User.photos[0].photo_path if profile.User.photos else None
        } for profile in profiles]
    
async def count_likes_received(user_id, session: AsyncSession):
    count = await session.scalar(
        select(func.count()).select_from(Like).where(Like.liked_id == user_id)
    )
    return count or 0

async def count_matches_made(user_id, session: AsyncSession):
    count = await session.scalar(
        select(func.count()).select_from(Match).where(
            or_(Match.user1_id == user_id, Match.user2_id == user_id)
        )
    )
    return count or 0
    
async def update_behavioral_rating(user: User, session: AsyncSession):
    likes_received = await count_likes_received(user.id, session)
    matches_made = await count_matches_made(user.id, session)
    await user.calculate_behavioral_rating(likes_received, matches_made)
    await user.calculate_combined_rating()
    session.add(user)
    await session.flush()

async def like_user(liker_id, liked_id, session: AsyncSession):
    liker = await session.scalar(
        select(User)
        .where(User.id == liker_id)
        .options(selectinload(User.liked_users))
    )
    liked = await session.scalar(select(User).where(User.id == liked_id))

    if liked not in liker.liked_users:
        liker.liked_users.append(liked)
        await update_behavioral_rating(liked, session)
        await update_behavioral_rating(liker, session)

async def check_match(user1_id, user2_id, session: AsyncSession):
    user1 = await session.scalar(
        select(User)
        .where(User.id == user1_id)
        .options(selectinload(User.liked_users))
    )
    user2 = await session.scalar(
        select(User)
        .where(User.id == user2_id)
        .options(selectinload(User.liked_users))
    )

    if not user1 or not user2:
        return False, None, None

    if user2 in user1.liked_users and user1 in user2.liked_users:
        existing_match = await session.scalar(
            select(Match).where(
                or_(
                    and_(Match.user1_id == user1_id, Match.user2_id == user2_id),
                    and_(Match.user1_id == user2_id, Match.user2_id == user1_id)
                )
            )
        )
        
        if not existing_match:
            new_match = Match(user1_id=user1_id, user2_id=user2_id)
            session.add(new_match)
            await update_behavioral_rating(user1, session)
            await update_behavioral_rating(user2, session)
            return True, user1, user2
    
    return False, None, None