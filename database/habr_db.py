from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm.session import Session
from database.models import Base


class HabrDb:
    __session: Session

    def __init__(self, url: str, base=Base):
        engine = create_engine(url)
        base.metadata.create_all(engine)
        self.__session = sessionmaker(bind=engine)

    @property
    def session(self) -> Session:
        return self.__session
