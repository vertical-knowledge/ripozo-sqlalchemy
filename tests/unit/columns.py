from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from datetime import datetime, date, timedelta, time

from ripozo.exceptions import NotFoundException
from ripozo.viewsets.fields.common import StringField, IntegerField, \
    FloatField, BooleanField, DateTimeField, BaseField

from ripozo_sqlalchemy.alcehmymanager import AlchemyManager

from ripozo_tests.python2base import TestBase

from sqlalchemy import Column, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm.exc import NoResultFound, MultipleResultsFound
from sqlalchemy.types import BigInteger, Boolean, Date, DateTime,\
    Enum, Float, Integer, Interval, LargeBinary, Numeric, PickleType,\
    SchemaType, SmallInteger, String, Text, Time, Unicode, UnicodeText

import logging
import random
import six
import string
import unittest

logger = logging.getLogger(__name__)


class TestColumnTypes(TestBase, unittest.TestCase):
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

    def assertResponseEqualsModel(self, model, manager, response):
        try:
            for name, value in six.iteritems(response):
                self.assertEqual(getattr(model, name), response[name])
        except:
            raise

        for field in manager.fields:
            self.assertIn(field, response)
        self.assertEqual(len(manager.fields), len(response))

    @property
    def manager(self):
        return self._manager()

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
            string=''.join(random.choice(string.letters) for _ in range(0, 100)),
            text=''.join(random.choice(string.letters) for _ in range(0, 100)),
            time=time(hour=10),
            date_time=datetime.now(),
            unicode=''.join(random.choice(string.letters) for _ in range(0, 100)),
            unicode_text=''.join(random.choice(string.letters) for _ in range(0, 100)),
            large_binary=''.join(random.choice(string.letters) for _ in range(0, 100))
        )

    def create(self, values=None):
        values = values or self.get_fake_values()
        model = self.model(**values)
        self.session.add(model)
        self.session.commit()
        return model

    def get_model(self, id):
        return self.session.query(self.model).get(id)

    def test_get_fields(self):
        """
        Test getting all of the fields
        """
        for field in self.manager.fields:
            self.assertIsInstance(self.manager.get_field_type(field), self.field_dict[field],
                                  msg='{0} is not an instance of {1}'.format(field, self.field_dict[field]))

    def test_all_fields(self):
        """
        Tests to make sure that the all_fields class
        attribute correctly gets all of the fields.
        """
        class NoFieldsManager(self._manager):
            _fields = []

        # Make sure the fields are empty.
        self.assertEqual(NoFieldsManager.fields, [])
        self.assertEqual(len(NoFieldsManager.fields), 0)
        self.assertIsInstance(NoFieldsManager.fields, list)

        class AllFieldsManager(NoFieldsManager):
            all_fields = True

        for field in self._manager.fields:
            self.assertIn(field, AllFieldsManager.fields)
        self.assertEqual(len(self._manager.fields), len(AllFieldsManager.fields))

    def test_create(self):
        values = self.get_fake_values()
        response = self.manager.create(values)
        for name, value in six.iteritems(values):
            self.assertEqual(values[name], response[name])
        self.assertIn('id', response)

    def test_retrieve(self):
        model = self.create()
        response = self.manager.retrieve(dict(id=model.id))
        self.assertResponseEqualsModel(model, self.manager, response)

    def test_retrieve_list(self):
        models = []
        model_count = 10
        for i in range(model_count):
            models.append(self.create())
        response, meta = self.manager.retrieve_list({})
        for r in response:
            id = r['id']
            for model in models:
                if model.id == id:
                    self.assertResponseEqualsModel(model, self.manager, r)
                    break

    def test_update(self):
        original_values = self.get_fake_values()
        model = self.create(values=original_values)
        new_values = self.get_fake_values()
        response = self.manager.update(dict(id=model.id), new_values)
        self.assertResponseEqualsModel(model, self.manager, response)

        not_equal = False
        for key, value in six.iteritems(original_values):
            if not value == response[key]:
                not_equal = True
        self.assertTrue(not_equal)

    def test_delete(self):
        model = self.create()
        response = self.manager.delete(dict(id=model.id))
        assert not response
        model = self.get_model(id=model.id)
        self.assertIsNone(model)

    def test_update_multiple_fail(self):
        values = self.get_fake_values()
        self.create(values=values)
        self.create(values=values)
        new_values = self.get_fake_values()
        self.assertRaises(MultipleResultsFound, self.manager.update, values, new_values)

    def test_delete_multiple_fail(self):
        values = self.get_fake_values()
        self.create(values=values)
        self.create(values=values)
        new_values = self.get_fake_values()
        self.assertRaises(MultipleResultsFound, self.manager.delete, values)

    def test_none_found(self):
        self.assertRaises(NotFoundException, self.manager.retrieve, dict(id=1))
        self.assertRaises(NotFoundException, self.manager.retrieve, dict(id=1), self.get_fake_values())
        self.assertRaises(NotFoundException, self.manager.delete, dict(id=1))

    def test_retrieve_list_empty(self):
        response, meta = self.manager.retrieve_list({})
        self.assertEqual(response, [])

    def test_retrieve_list_paginate(self):
        class Manager(self._manager):
            paginate_by = 3
        models = []
        model_count = 10
        for i in range(model_count):
            models.append(self.create())

        filters = {}
        for i in range(4):
            response, meta = Manager().retrieve_list(filters)
            filters = meta['next']
            self.assertLessEqual(len(response), 3)
            for r in response:
                id = r['id']
                for model in models:
                    if model.id == id:
                        self.assertResponseEqualsModel(model, Manager(), r)
                        break