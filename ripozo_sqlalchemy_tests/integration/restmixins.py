from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from ripozo.viewsets.fields.common import IntegerField, StringField
from ripozo.viewsets.relationships import ListRelationship, Relationship
from ripozo.viewsets.restmixins import RetrieveUpdateDelete, CreateRetrieveList
from ripozo.viewsets.resource_base import ResourceBase

from ripozo_sqlalchemy.alcehmymanager import AlchemyManager

from sqlalchemy import Column, String, Integer, create_engine, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship

from ripozo_sqlalchemy_tests.unit.common import CommonTest

import random
import string
import unittest


class TestRestMixins(CommonTest, unittest.TestCase):
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

        class DefaultManager(AlchemyManager):
            session = self.session
            model = One
            _fields = ['id', 'value', 'manies.id']

        class OneResource(ResourceBase):
            _pks = ['id']
            _relationships = [ListRelationship('manies', relation='ManyResource')]

        class ManyResource(ResourceBase):
            _pks = ['id']
            _relationships = [Relationship('one', relation='OneResource')]

        self.model = One
        self._manager = DefaultManager

        self.One = One
        self.Many = Many
        self.Base.metadata.create_all()
