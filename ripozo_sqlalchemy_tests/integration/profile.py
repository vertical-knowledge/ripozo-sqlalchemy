from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from datetime import datetime

from ripozo.viewsets.restmixins import Create, RetrieveUpdateDelete

from ripozo_sqlalchemy.alcehmymanager import AlchemyManager

from ripozo_tests.python2base import TestBase

from sqlalchemy import Column, Integer, String, Float, DateTime, create_engine, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship

import cProfile
import logging
import pstats
import unittest


# Disable all logging since we don't care about its performance
logging.disable(logging.CRITICAL)


Base = declarative_base(create_engine('sqlite:///:memory:', echo=True))
session = sessionmaker()()


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
    session = session
    model = MyModel
    fields = ('id', 'name', 'my_float', 'my_datetime', 'relateds.id')

create_dict = dict(name='sadofkfgnmsdkofgnsdf', my_float=1.000, my_datetime=datetime.now())


class TestProfiler(TestBase, unittest.TestCase):

    @profileit
    def test_create_profile(self):
        for i in range(5000):
            MyModelManager().create(create_dict)

    def test_retrieve_a_shit_ton(self):
        for i in range(5):
            MyModelManager().create(create_dict)
        session.commit()

        self.retrieve_list()

    @profileit
    def retrieve_list(self):
        MyModelManager().retrieve_list({})

