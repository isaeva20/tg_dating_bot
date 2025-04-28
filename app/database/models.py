from sqlalchemy import ForeignKey, CheckConstraint, BigInteger, Enum, Integer, Text, DateTime, TIMESTAMP, REAL, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.ext.asyncio import create_async_engine, AsyncAttrs, async_sessionmaker
from config import DB_URL

engine = create_async_engine(DB_URL)

async_session = async_sessionmaker(engine)

class Base(AsyncAttrs, DeclarativeBase):
    pass

class User(Base):
    __tablename__ = 'users'

    id: Mapped[int] = mapped_column(primary_key=True)
    tg_id = mapped_column(BigInteger)
    first_name: Mapped[str] = mapped_column(Text, nullable=False, default='Не указано')
    username: Mapped[str]
    age: Mapped[int] = mapped_column(Integer, nullable=False, default=18)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    gender = mapped_column(Enum('Мужской', 'Женский', name='gender_enum'), nullable=False, default='Мужской')
    city: Mapped[str] = mapped_column(Text, nullable=False, default='Не указано')
    profile_completion: Mapped[int] = mapped_column(Integer, default=0) 
    photos_count: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[DateTime] = mapped_column(TIMESTAMP, server_default=func.now())
    primary_rating: Mapped[float] = mapped_column(REAL, default=0.0)
    behavioral_rating: Mapped[float] = mapped_column(REAL, default=0.0)
    combined_rating: Mapped[float] = mapped_column(REAL, default=0.0)

    photos: Mapped[list['Photo']] = relationship(back_populates='user', cascade='all, delete-orphan')
    preferences: Mapped['UserPreferences'] = relationship(back_populates='user', uselist=False, cascade='all, delete-orphan')
    liked_by: Mapped[list['User']] = relationship(
        secondary='likes', 
        primaryjoin='User.id==Like.liked_id', 
        secondaryjoin='User.id==Like.liker_id',
        back_populates='liked_users'
    )
    liked_users: Mapped[list['User']] = relationship(
        secondary='likes',
        primaryjoin='User.id==Like.liker_id',
        secondaryjoin='User.id==Like.liked_id',
        back_populates='liked_by'
    )

    __table_args__ = (
        CheckConstraint('age >= 18 and age <= 100'),
    )

    async def calculate_primary_rating(self):
        profile_completion_weight = 0.5

        profile_completion = await self.calculate_profile_completion()

        self.primary_rating = (
            profile_completion * profile_completion_weight
        )


    async def calculate_profile_completion(self):
            fields_to_check = [
                self.first_name, self.age, self.description, self.gender, self.city
            ]

            filled_fields = sum(1 for field in fields_to_check if field not in [None, 'Не указано', 0] and field is not None)


            max_fields = len(fields_to_check)

            if max_fields == 0:
                return 0.0

            completion = filled_fields / max_fields
            return completion


    async def calculate_behavioral_rating(self, likes_received=0, matches_made=0):
        likes_weight = 0.5
        matches_weight = 0.5

        self.behavioral_rating = (
            likes_received * likes_weight +
            matches_made * matches_weight
        )

    async def calculate_combined_rating(self):
        primary_weight = 0.6
        behavioral_weight = 0.3
        self.combined_rating = (
            self.primary_rating * primary_weight +
            self.behavioral_rating * behavioral_weight
        )


class UserPreferences(Base):
    __tablename__ = 'user_preferences'

    user_id: Mapped[int] = mapped_column(Integer, ForeignKey('users.id'), primary_key=True)
    user: Mapped[User] = relationship(back_populates='preferences')
    preferred_gender: Mapped[str] = mapped_column(Enum('Мужской', 'Женский', name='gender_enum'))
    min_age: Mapped[int] = mapped_column(Integer)
    max_age: Mapped[int] = mapped_column(Integer)
    preferred_city: Mapped[str] = mapped_column(Text)

    __table_args__ = (
        CheckConstraint('min_age >= 18'),
        CheckConstraint('max_age <= 100'),
        CheckConstraint('min_age <= max_age'),
    )

class Photo(Base):
    __tablename__ = 'photos'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey('users.id'))
    user: Mapped[User] = relationship(back_populates='photos')
    photo_path: Mapped[str] = mapped_column(Text, nullable=False, default='Не указано')

class Like(Base):
    __tablename__ = 'likes'

    liker_id: Mapped[int] = mapped_column(Integer, ForeignKey('users.id'), primary_key=True)
    liked_id: Mapped[int] = mapped_column(Integer, ForeignKey('users.id'), primary_key=True)
    created_at: Mapped[DateTime] = mapped_column(TIMESTAMP, server_default=func.now())

class Match(Base):
    __tablename__ = 'matches'

    user1_id: Mapped[int] = mapped_column(Integer, ForeignKey('users.id'), primary_key=True)
    user2_id: Mapped[int] = mapped_column(Integer, ForeignKey('users.id'), primary_key=True)
    created_at: Mapped[DateTime] = mapped_column(TIMESTAMP, server_default=func.now())

async def async_main():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

