from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from ripozo_sqlalchemy import AlchemyManager, ScopedSessionHandler
from ripozo import restmixins, RequestContainer

from sqlalchemy import create_engine, Column
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.types import Integer, String

import random
import string
import unittest2


class TestPagination(unittest2.TestCase):
    def setUp(self):
        self.engine = create_engine('sqlite:///:memory:', echo=True)
        self.Base = declarative_base(self.engine)
        self.session_handler = ScopedSessionHandler(self.engine)

        class MyModel(self.Base):
            __tablename__ = 'my_model'
            id = Column(Integer, primary_key=True)
            value = Column(String(length=63))

        self.model = MyModel
        self.Base.metadata.create_all()

        class MyManager(AlchemyManager):
            model = self.model
            fields = ('id', 'value',)
            paginate_by = 10

        self.manager = MyManager(self.session_handler)

        class MyResource(restmixins.RetrieveList):
            manager = self.manager
            pks = ('id',)
            resource_name = 'my_resource'

        self.resource = MyResource

    def tearDown(self):
        self.engine.dispose()

    def create_models(self, count=5):
        session = self.session_handler.get_session()
        for i in range(count):
            m = self.model(value=''.join(random.choice(string.ascii_letters) for _ in range(63)))
            session.add(m)
        session.commit()
        session.close()

    def get_linked_resource(self, resource, name):
        for linked in resource.linked_resources:
            if linked.name == name:
                return linked.resource
        return None

    def test_empty(self):
        """
        Tests for when no models have been created
        """
        req = RequestContainer()
        resource = self.resource.retrieve_list(req)
        self.assertEqual(len(resource.linked_resources), 0)
        self.assertEqual(len(resource.properties['my_resource']), 0)

    def test_not_enough_for_pagination(self):
        """
        Tests that no pagination links are available when
        there are less than or equal the paginate_by count
        of records.
        """
        self.create_models(count=10)
        req = RequestContainer()
        resource = self.resource.retrieve_list(req)
        self.assertEqual(len(resource.linked_resources), 0)
        self.assertEqual(len(resource.properties['my_resource']), 10)

    def test_next_pagination(self):
        """
        Tests basic forward pagination end on
        a multiple of the paginate_by
        """
        self.create_models(count=100)
        req = RequestContainer()
        resource = self.resource.retrieve_list(req)
        self.assertEqual(len(resource.properties['my_resource']), 10)
        count = 1
        while self.get_linked_resource(resource, 'next'):
            next_link = self.get_linked_resource(resource, 'next')
            req = RequestContainer(query_args=next_link.get_query_arg_dict())
            resource = self.resource.retrieve_list(req)
            self.assertEqual(len(resource.properties['my_resource']), 10)
            count += 1
        self.assertEqual(10, count)

    def test_next_pagination_partial_end(self):
        """
        Tests forward pagination that ends with a
        partial page (i.e. less than the paginate_by)
        """
        self.create_models(count=101)
        req = RequestContainer()
        resource = self.resource.retrieve_list(req)
        count = 1
        while self.get_linked_resource(resource, 'next'):
            self.assertEqual(len(resource.properties['my_resource']), 10)
            next_link = self.get_linked_resource(resource, 'next')
            req = RequestContainer(query_args=next_link.get_query_arg_dict())
            resource = self.resource.retrieve_list(req)
            count += 1
        self.assertEqual(len(resource.properties['my_resource']), 1)
        self.assertEqual(11, count)

    def test_prev_pagintation(self):
        """
        Tests prev pagination with the total count
        of models as a multiple of the paginate_by
        """
        self.create_models(count=100)
        req = RequestContainer(query_args=dict(page=10))
        resource = self.resource.retrieve_list(req)
        self.assertEqual(len(resource.properties['my_resource']), 10)
        count = 1
        while self.get_linked_resource(resource, 'previous'):
            previous = self.get_linked_resource(resource, 'previous')
            req = RequestContainer(query_args=previous.get_query_arg_dict())
            resource = self.resource.retrieve_list(req)
            self.assertEqual(len(resource.properties['my_resource']), 10)
            count += 1
        self.assertEqual(10, count)

    def test_prev_pagination_uneven_total(self):
        """
        Tests previous pagination with the total count
        of models not as a multiple of the paginate_by.
        """
        self.create_models(count=101)
        req = RequestContainer(query_args=dict(page=11))
        resource = self.resource.retrieve_list(req)
        self.assertEqual(len(resource.properties['my_resource']), 1)
        count = 1
        while self.get_linked_resource(resource, 'previous'):
            previous = self.get_linked_resource(resource, 'previous')
            req = RequestContainer(query_args=previous.get_query_arg_dict())
            resource = self.resource.retrieve_list(req)
            self.assertEqual(len(resource.properties['my_resource']), 10)
            count += 1
        self.assertEqual(11, count)
