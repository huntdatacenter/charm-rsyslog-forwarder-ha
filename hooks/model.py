#!/usr/bin/env python
# -*- coding: utf-8 -*-

__author__ = 'Jorge Niedbalski R. <jorge.niedbalski@canonical.com>'

from charmhelpers import fetch

try:
    import sqlalchemy
except ImportError:
    fetch.apt_install("python-sqlalchemy")

from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm.exc import NoResultFound

import os
import datetime


DEFAULT_SQLITE_PATH = os.path.expanduser("~/.rsyslog-servers.db")

Base = declarative_base()

engine = create_engine('sqlite:///%s' % DEFAULT_SQLITE_PATH)
Session = sessionmaker(bind=engine)
session = Session()


class Server(Base):
    __tablename__ = 'server'

    id = Column(Integer, primary_key=True)
    relation_id = Column(String(250), nullable=False)
    created = Column(DateTime, default=datetime.datetime.now)
    remote_unit = Column(String(250))
    private_address = Column(String(250))

    @classmethod
    def remove(cls, relation_id):
        try:
            server = session.query(Server).filter_by(
                relation_id=relation_id).one()
            session.delete(server)
            session.commit()
        except:
            session.rollback()

    @classmethod
    def has_relation(cls, relation_id):
        try:
            session.query(cls).filter_by(
                relation_id=relation_id).one()
        except NoResultFound:
            return False
        return True

    @classmethod
    def get_or_create(cls, **params):
        try:
            server = session.query(Server).filter_by(
                relation_id=params.get('relation_id')).one()
        except:
            server = cls(relation_id=params.get('relation_id'),
                         remote_unit=params.get('remote_unit'),
                         private_address=params.get('unit_private_ip'))
            try:
                session.add(server)
                session.commit()
            except:
                session.rollback()
        return server


def setup_local_database():
    Base.metadata.create_all(engine)

try:
    setup_local_database()
except:
    pass
