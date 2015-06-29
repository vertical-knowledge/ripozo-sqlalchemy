from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from ripozo import RequestContainer

from ripozo_sqlalchemy import create_resource, ScopedSessionHandler

from sqlalchemy import Column, Integer, String, create_engine
from sqlalchemy.ext.declarative import declarative_base

import unittest2

Base = declarative_base()


class MyModel(Base):
    __tablename__ = 'my_model'
    id = Column(Integer, primary_key=True)
    value = Column(String)


class TestEasyResource(unittest2.TestCase):
    def setUp(self):
        self.engine = create_engine('sqlite:///:memory:')
        self.session_handler = ScopedSessionHandler(self.engine)
        Base.metadata.create_all(self.engine)

    def tearDown(self):
        if self.engine:
            self.engine.dispose()
            self.engine = None

    def test_create_resource(self):
        resource = create_resource(MyModel, self.session_handler)
        req = RequestContainer(body_args=dict(value='blah'))
        resp = resource.create(req)
        self.assertEqual(resp.properties['value'], 'blah')
        id_ = resp.properties['id']
        session = self.session_handler.get_session()
        resp = session.query(MyModel).get(id_)
        self.assertIsNotNone(resp)
        self.assertEqual(resp.value, 'blah')

        retrieved = resource.retrieve(RequestContainer(url_params=dict(id=id_)))
        self.assertEqual(retrieved.properties['value'], 'blah')

        retrieved_list = resource.retrieve_list(RequestContainer())
        self.assertEqual(len(retrieved_list.related_resources), 1)
        relatec = retrieved_list.related_resources[0].resource
        self.assertEqual(len(relatec), 1)

        updated = resource.update(RequestContainer(url_params=dict(id=id_),
                                                   body_args=dict(value='new')))
        self.assertEqual(updated.properties['value'], 'new')
        session = self.session_handler.get_session()
        model = session.query(MyModel).get(id_)
        self.assertEqual(model.value, 'new')

        deleted = resource.delete(RequestContainer(url_params=dict(id=id_)))
        session = self.session_handler.get_session()
        model = session.query(MyModel).get(id_)
        self.assertIsNone(model)
