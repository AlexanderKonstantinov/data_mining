from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from typing import List
from sqlalchemy import (
    Table,
    Column,
    ForeignKey,
    String,
    Integer,
    Date,
    Time
)


Base = declarative_base()

assoc_post_user = Table(
    'post_comment_user',
    Base.metadata,
    Column('post', Integer, ForeignKey('post.id')),
    Column('user', Integer, ForeignKey('user.id'))
)


assoc_tag_post = Table('tag_post', Base.metadata,
                       Column('post', Integer, ForeignKey('post.id')),
                       Column('tag', Integer, ForeignKey('tag.id')))


class BaseEntity(Base):
    __abstract__ = True

    id = Column(Integer, primary_key=True, autoincrement=True)

    def __init__(self, name: str, url: str):
        self.name = name
        self.url = url


class BaseNamedEntity(BaseEntity):
    __abstract__ = True

    name = Column(String, unique=False, nullable=False)
    url = Column(String, unique=True, nullable=False)

    def __init__(self, name: str, url: str):
        self.name = name
        self.url = url


class User(BaseNamedEntity):
    __tablename__ = 'user'

    posts = relationship('Post', backref='writer')
    comment = relationship('Comment', back_populates="writer")

    def __init__(self, name: str, url: str):
        super().__init__(name, url)


class Post(BaseNamedEntity):
    __tablename__ = 'post'

    comments_number = Column(Integer, unique=False, nullable=False)
    creation_date = Column(Date, unique=False, nullable=False)
    creation_time = Column(Time, unique=False, nullable=False)
    writer_id = Column(Integer, ForeignKey('user.id'))
    comments = relationship('Comment', back_populates='post')
    tags = relationship('Tag', secondary=assoc_tag_post, backref='post')

    def __init__(self, name: str, url: str, comments_number: int,
                 creation_date, creation_time,
                 writer: User, users: List[User]):
        super().__init__(name, url)
        self.comments_number = comments_number
        self.creation_date = creation_date
        self.creation_time = creation_time
        self.writer = writer
        if users:
            self.users.extend(users)


class Comment(BaseEntity):
    __tablename__ = 'comment'

    writer_id = Column(Integer, ForeignKey('user.id'))
    writer = relationship('User', back_populates="comments")
    post_id = Column(Integer, ForeignKey('post.id'))
    post = relationship('Post', back_populates="comments")

    def __init__(self, writer, post):
        self.writer = writer
        self.post = post


class Tag(BaseNamedEntity):
    __tablename__ = 'user'
    BaseNamedEntity.name = Column(String, unique=True, nullable=False)

    def __init__(self, name: str, url: str):
        super().__init__(name, url)