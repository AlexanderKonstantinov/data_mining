from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, session
from database.models import Base


class HabrDb:
    __session: session

    def __init__(self, url, base=Base):
        engine = create_engine(url)
        base.metadata.create_all(engine)
        session_db = sessionmaker(bind=engine)
        self.__session = session_db()

    @property
    def session(self):
        return self.__session
