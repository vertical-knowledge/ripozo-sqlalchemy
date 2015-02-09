from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from sqlalchemy import Column, Integer, String, create_engine
import unittest

from ripozo.exceptions import NotFoundException
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from tests.unit.managers.test_manager_common import TestManagerMixin

from ripozo_sqlalchemy.alcehmymanager import AlchemyManager


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


class TestAlchemyManager(TestManagerMixin, unittest.TestCase):
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
        self.assertEqual(manager.get_field_type('first_name'), str)
        self.assertEqual(manager.get_field_type('last_name'), str)
        self.assertEqual(manager.get_field_type('id'), int)

    def test_retrieve_many_pagination_arbitrary_count(self):
        pass # arbitrary count doesn't really make sense