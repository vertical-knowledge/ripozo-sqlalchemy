from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from datetime import datetime

from ripozo_sqlalchemy.alcehmymanager import AlchemyManager
from ripozo_sqlalchemy.session_handlers import ScopedSessionHandler

from sqlalchemy import Column, Integer, String, Float, DateTime, create_engine, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import  relationship

import cProfile
import logging
import pstats
import unittest2


# Disable all logging since we don't care about its performance
logging.disable(logging.CRITICAL)

engine = create_engine('sqlite:///:memory:', echo=True)
Base = declarative_base(engine)
session_handler = ScopedSessionHandler(engine)


def profileit(func):
    """
    Decorator straight up stolen from stackoverflow
    """
    def wrapper(*args, **kwargs):
        datafn = func.__name__ + ".profile" # Name the data file sensibly
        prof = cProfile.Profile()
        prof.enable()
        retval = prof.runcall(func, *args, **kwargs)
        prof.disable()
        stats = pstats.Stats(prof)
        try:
            stats.sort_stats('cumtime').print_stats()
        except KeyError:
            pass  # breaks in python 2.6
        return retval

    return wrapper


class MyModel(Base):
    __tablename__ = 'my_model'
    id = Column(Integer, primary_key=True)
    name = Column(String)
    my_float = Column(Float)
    my_datetime = Column(DateTime)
    relateds = relationship("Related", lazy='dynamic')


class Related(Base):
    __tablename__ = 'other_model'
    id = Column(Integer, primary_key=True)
    my_model_id = Column(Integer, ForeignKey('my_model.id'))

Base.metadata.create_all()


class MyModelManager(AlchemyManager):
    model = MyModel
    fields = ('id', 'name', 'my_float', 'my_datetime', 'relateds.id')

create_dict = dict(name='sadofkfgnmsdkofgnsdf', my_float=1.000, my_datetime=datetime.now())


class TestProfiler(unittest2.TestCase):
    manager = MyModelManager(session_handler)

    @profileit
    def test_create_profile(self):
        for i in range(5000):
            self.manager.create(create_dict)

    def test_retrieve_a_shit_ton(self):
        for i in range(5):
            self.manager.create(create_dict)

        self.retrieve_list()

    @profileit
    def retrieve_list(self):
        self.manager.retrieve_list({})

