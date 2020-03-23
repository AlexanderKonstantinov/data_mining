from sqlalchemy import (
    Table,
    Column,
    ForeignKey,
    String,
    Integer,
    Date,
    Time
)
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from typing import List


Base = declarative_base()

assoc_post_user = Table(
    'post_comment_user',
    Base.metadata,
    Column('post', Integer, ForeignKey('post.id')),
    Column('user', Integer, ForeignKey('user.id'))
)


class BaseEntity(Base):
    __abstract__ = True

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, unique=False, nullable=False)
    url = Column(String, unique=True, nullable=False)

    def __init__(self, name: str, url: str):
        self.name = name
        self.url = url


class User(BaseEntity):
    __tablename__ = 'user'

    def __init__(self, name: str, url: str):
        super(User, self).__init__(name, url)


class Post(BaseEntity):
    __tablename__ = 'post'

    comments_number = Column(Integer, unique=False, nullable=False)
    creation_date = Column(Date, unique=False, nullable=False)
    creation_time = Column(Time, unique=False, nullable=False)
    writer_id = Column(Integer, ForeignKey('user.id'))
    writer = relationship('User', backref='posts')
    users = relationship('User', secondary=assoc_post_user, backref='commented_posts')

    def __init__(self, name: str, url: str, comments_number: int,
                 creation_date, creation_time,
                 writer: User, users: List[User]):
        super(Post, self).__init__(name, url)
        self.comments_number = comments_number
        self.creation_date = creation_date
        self.creation_time = creation_time
        self.writer = writer
        if users:
            self.users.extend(users)
