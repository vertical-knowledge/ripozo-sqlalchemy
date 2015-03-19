from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from datetime import datetime, date, time, timedelta
from decimal import Decimal

from ripozo.viewsets.fields.common import StringField, IntegerField
from ripozo.exceptions import NotFoundException

from ripozo_sqlalchemy.alcehmymanager import AlchemyManager, sql_to_json_encoder

from ripozo_tests.bases.manager import TestManagerMixin
from ripozo_tests.python2base import TestBase

from sqlalchemy import Column, Integer, String, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

import six
import unittest


Base = declarative_base(create_engine('sqlite:///:memory:', echo=True))
session = sessionmaker()()


class Person(Base):
    __tablename__ = 'person'
    id = Column(Integer, primary_key=True)
    first_name = Column(String)
    last_name = Column(String)

Base.metadata.create_all()


class PersonManager(AlchemyManager):
    session = session
    model = Person
    paginate_by = 10
    fields = ('id', 'first_name', 'last_name')


class TestAlchemyManager(TestManagerMixin, TestBase, unittest.TestCase):
    @property
    def manager(self):
        return PersonManager()

    @property
    def all_person_models(self):
        return session.query(Person).all()

    def get_person_model_by_id(self, person_id):
        to_return = session.query(Person).get(person_id)
        if to_return is None:
            raise NotFoundException
        return to_return

    @property
    def does_not_exist_exception(self):
        return NotFoundException

    def test_get_field_type(self):
        manager = self.manager
        self.assertIsInstance(manager.get_field_type('first_name'), StringField)
        self.assertIsInstance(manager.get_field_type('last_name'), StringField)
        self.assertIsInstance(manager.get_field_type('id'), IntegerField)

    def test_retrieve_many_pagination_arbitrary_count(self):
        pass # arbitrary count doesn't really make sense

    def test_sql_to_json_encoder(self):
        dt = datetime.now()
        dt = sql_to_json_encoder(dt)
        self.assertIsInstance(dt, six.text_type)

        t = time()
        t = sql_to_json_encoder(t)
        self.assertIsInstance(t, six.text_type)

        d = date(2015, 3, 17)
        d = sql_to_json_encoder(d)
        self.assertIsInstance(d, six.text_type)

        td = datetime.now() - datetime(2015, 2, 10)
        td = sql_to_json_encoder(td)
        self.assertIsInstance(td, six.text_type)

        dec = Decimal('2.0')
        dec = sql_to_json_encoder(dec)
        self.assertIsInstance(dec, float)

        string = 'somestring'
        same_string = sql_to_json_encoder(string)
        self.assertEqual(string, same_string)

        dictionary = dict(dt=datetime.now(), d=Decimal("2.0"), string='somestring')
        dictionary = sql_to_json_encoder(dictionary)
        self.assertIsInstance(dictionary['dt'], six.text_type)
        self.assertIsInstance(dictionary['d'], float)
        self.assertEqual('somestring', dictionary['string'])
