from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from ripozo_sqlalchemy.alcehmymanager import AlchemyManager

from ripozo_tests.python2base import TestBase

from sqlalchemy import Column, String, Integer, create_engine, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship

import random
import string
import unittest


def random_string():
    return ''.join(random.choice(string.letters) for _ in range(20))


class TestOneToManyRelationship(TestBase, unittest.TestCase):
    def setUp(self):
        self.Base = declarative_base(create_engine('sqlite:///:memory:', echo=True))
        self.session = sessionmaker()()

        class One(self.Base):
            __tablename__ = 'one'
            id = Column(Integer, primary_key=True)
            value = Column(String(length=50))
            manies = relationship("Many", backref='one')

        class Many(self.Base):
            __tablename__ = 'many'
            id = Column(Integer, primary_key=True)
            many_value = Column(String(length=50))
            one_id = Column(Integer, ForeignKey('one.id'))

        self.One = One
        self.Many = Many
        self.Base.metadata.create_all()

    def create_one(self, value=None):
        value = value or random_string()
        one = self.One(value=value)
        self.session.add(one)
        self.session.commit()
        return one

    def create_many(self, many_value=None, one_id=None):
        many_value = many_value or random_string()
        many = self.Many(many_value=many_value)
        if one_id:
            many.one_id = one_id
        self.session.add(many)
        self.session.commit()
        return many

    def test_get_many_ids_from_one_manager(self):
        class OneManager(AlchemyManager):
            session = self.session
            model = self.One
            fields = ('id', 'value', 'manies.id')

        parent = self.create_one()
        child1 = self.create_many(one_id=parent.id)
        child2 = self.create_many(one_id=parent.id)

        parent_dict = OneManager().retrieve(dict(id=parent.id))
        self.assertIsInstance(parent_dict, dict)
        self.assertEqual(parent_dict['id'], parent.id)
        self.assertEqual(parent_dict['value'], parent.value)
        self.assertIsInstance(parent_dict['manies'], list)
        for child_dict in parent_dict['manies']:
            self.assertIsInstance(child_dict, dict)
            if child_dict['id'] == child1.id:
                child = child1
            elif child_dict['id'] == child2.id:
                child = child2
            else:
                assert False

    def test_get_many_values_from_one_manager(self):
        class OneManager(AlchemyManager):
            session = self.session
            model = self.One
            fields = ('id', 'value', 'manies.id', 'manies.many_value')

        parent = self.create_one()
        child1 = self.create_many(one_id=parent.id)
        child2 = self.create_many(one_id=parent.id)

        parent_dict = OneManager().retrieve(dict(id=parent.id))
        self.assertIsInstance(parent_dict, dict)
        self.assertEqual(parent_dict['id'], parent.id)
        self.assertEqual(parent_dict['value'], parent.value)
        self.assertIsInstance(parent_dict['manies'], list)
        for child_dict in parent_dict['manies']:
            self.assertIsInstance(child_dict, dict)
            if child_dict['id'] == child1.id:
                child = child1
            elif child_dict['id'] == child2.id:
                child = child2
            else:
                assert False
            self.assertEqual(child_dict['many_value'], child.many_value)

    def test_get_one_from_many_manager(self):
        class ManyManager(AlchemyManager):
            session = self.session
            model = self.Many
            _fields = ('id', 'many_value', 'one.id',)

        parent = self.create_one()
        child1 = self.create_many(one_id=parent.id)

        child1_dict = ManyManager().retrieve(dict(id=child1.id))
        self.assertIsInstance(child1_dict, dict)
        self.assertEqual(child1_dict['many_value'], child1.many_value)
        self.assertIsInstance(child1_dict['one'], dict)
        self.assertEqual(parent.id, child1_dict['one']['id'])

    def test_get_one_with_value_from_many_manager(self):
        class ManyManager(AlchemyManager):
            session = self.session
            model = self.Many
            _fields = ('id', 'many_value', 'one.id', 'one.value')

        parent = self.create_one()
        child1 = self.create_many(one_id=parent.id)

        child1_dict = ManyManager().retrieve(dict(id=child1.id))
        self.assertIsInstance(child1_dict, dict)
        self.assertEqual(child1_dict['many_value'], child1.many_value)
        self.assertIsInstance(child1_dict['one'], dict)
        self.assertEqual(parent.id, child1_dict['one']['id'])
        self.assertEqual(parent.value, child1_dict['one']['value'])

    def test_get_one_id_from_many_manager(self):
        class ManyManager(AlchemyManager):
            session = self.session
            model = self.Many
            _fields = ('id', 'many_value', 'one_id',)

        parent = self.create_one()
        child1 = self.create_many(one_id=parent.id)

        child1_dict = ManyManager().retrieve(dict(id=child1.id))
        self.assertIsInstance(child1_dict, dict)
        self.assertEqual(child1_dict['many_value'], child1.many_value)
        self.assertEqual(parent.id, child1_dict['one_id'])


class TestOneToManyRelationshipLazy(TestOneToManyRelationship):
    def setUp(self):
        self.Base = declarative_base(create_engine('sqlite:///:memory:', echo=True))
        self.session = sessionmaker()()

        class One(self.Base):
            __tablename__ = 'one'
            id = Column(Integer, primary_key=True)
            value = Column(String(length=50))
            manies = relationship("Many", lazy='dynamic', backref='one')

        class Many(self.Base):
            __tablename__ = 'many'
            id = Column(Integer, primary_key=True)
            many_value = Column(String(length=50))
            one_id = Column(Integer, ForeignKey('one.id'))

        self.One = One
        self.Many = Many
        self.Base.metadata.create_all()
