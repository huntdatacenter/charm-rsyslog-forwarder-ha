#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""Define SQLalchemy model for rsyslog-servers database."""

import datetime
import os

from sqlalchemy import Column, DateTime, Integer, String
from sqlalchemy import create_engine
from sqlalchemy.exc import DatabaseError, SQLAlchemyError
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm.exc import NoResultFound


DEFAULT_SQLITE_PATH = os.path.expanduser("~/.rsyslog-servers.db")

Base = declarative_base()

engine = create_engine("sqlite:///%s" % DEFAULT_SQLITE_PATH)
Session = sessionmaker(bind=engine)
session = Session()


PORT_COLUMN_CREATION = "ALTER TABLE server ADD COLUMN port INT"


class Server(Base):
    """Define Server model for database."""

    __tablename__ = "server"

    id = Column(Integer, primary_key=True)
    relation_id = Column(String(250), nullable=False)
    created = Column(DateTime, default=datetime.datetime.now)
    remote_unit = Column(String(250))
    private_address = Column(String(250))
    port = Column(Integer)

    @classmethod
    def remove(cls, relation_id):
        try:
            server = session.query(Server).filter_by(relation_id=relation_id).one()
            session.delete(server)
            session.commit()
        except SQLAlchemyError:
            session.rollback()

    @classmethod
    def has_relation(cls, relation_id):
        try:
            session.query(cls).filter_by(relation_id=relation_id).one()
        except NoResultFound:
            return False
        return True

    @classmethod
    def get_or_create(cls, **params):
        try:
            server = (
                session.query(Server)
                .filter_by(relation_id=params.get("relation_id"))
                .one()
            )
        except SQLAlchemyError:
            server = cls(
                relation_id=params.get("relation_id"),
                remote_unit=params.get("remote_unit"),
                private_address=params.get("unit_private_ip"),
            )
            try:
                session.add(server)
                session.commit()
            except SQLAlchemyError:
                session.rollback()
        return server


def setup_local_database():
    Base.metadata.create_all(engine)
    with engine.connect() as conn:
        conn.execute(PORT_COLUMN_CREATION)


try:
    setup_local_database()
except (DatabaseError, SQLAlchemyError):
    pass
