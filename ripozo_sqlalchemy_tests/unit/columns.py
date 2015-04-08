from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from datetime import datetime, date, timedelta, time

from ripozo.viewsets.fields.common import StringField, IntegerField, \
    FloatField, BooleanField, DateTimeField, BaseField

from ripozo_sqlalchemy.alcehmymanager import AlchemyManager

from ripozo_tests.python2base import TestBase

from sqlalchemy import Column, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.types import BigInteger, Boolean, Date, DateTime,\
    Enum, Float, Integer, Interval, LargeBinary, Numeric, PickleType,\
    SchemaType, SmallInteger, String, Text, Time, Unicode, UnicodeText

from ripozo_sqlalchemy_tests.unit.common import CommonTest

import logging
import random
import six
import string
import unittest

logger = logging.getLogger(__name__)


class TestColumnTypes(CommonTest, unittest.TestCase):
    def setUp(self):
        self.Base = declarative_base(create_engine('sqlite:///:memory:', echo=True))
        self.session = sessionmaker()()

        class MyModel(self.Base):
            __tablename__ = 'my_model'
            id = Column(Integer, primary_key=True)
            big_integer = Column(BigInteger)
            boolean = Column(Boolean)
            date = Column(Date)
            date_time = Column(DateTime)
            enum = Column(Enum('one', 'two' 'three'))
            float = Column(Float)
            integer = Column(Integer)
            interval = Column(Interval)
            large_binary = Column(LargeBinary)
            numeric = Column(Numeric)
            pickle_type = Column(PickleType)
            small_integer = Column(SmallInteger)
            string = Column(String)
            text = Column(Text)
            time = Column(Time)
            unicode = Column(Unicode)
            unicode_text = Column(UnicodeText)

        self.model = MyModel
        self.Base.metadata.create_all()

        class ModelManager(AlchemyManager):
            session = self.session
            model = self.model
            _fields = ['id', 'big_integer', 'boolean', 'date', 'date_time',
                       'enum', 'float', 'integer', 'interval', 'large_binary',
                       'numeric', 'pickle_type', 'small_integer',
                       'string', 'text', 'time', 'unicode', 'unicode_text']

        self._manager = ModelManager

    @property
    def field_dict(self):
        return dict(big_integer=IntegerField, boolean=BooleanField, date=DateTimeField,
                    enum=BaseField, float=FloatField, integer=IntegerField, interval=DateTimeField,
                    numeric=IntegerField, pickle_type=BaseField, small_integer=IntegerField,
                    string=StringField, text=StringField, time=DateTimeField, date_time=DateTimeField,
                    unicode=StringField, unicode_text=StringField, id=IntegerField, large_binary=StringField)

    def get_fake_values(self):
        return dict(
            big_integer=random.choice(range(0, 1000)),
            boolean=random.choice([True, False]),
            date=date(2010, 10, 1),
            enum=random.choice(('one', 'two' 'three',)),
            float=random.choice(range(0, 1000)) / 1000.0,
            integer=random.choice(range(0, 1000)),
            interval=timedelta(days=2),
            numeric=random.choice(range(0, 100)),
            pickle_type=dict(a=1, b=2),
            small_integer=random.choice(range(0, 100)),
            string=''.join(random.choice(string.ascii_letters) for _ in range(0, 100)).encode('utf-8'),
            text=''.join(random.choice(string.ascii_letters) for _ in range(0, 100)).encode('utf-8'),
            time=time(hour=10),
            date_time=datetime.now(),
            unicode=''.join(random.choice(string.ascii_letters) for _ in range(0, 100)),
            unicode_text=''.join(random.choice(string.ascii_letters) for _ in range(0, 100)),
            large_binary=''.join(random.choice(string.ascii_letters) for _ in range(0, 100)).encode('utf-8')
        )



