from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from ripozo import Relationship, ListRelationship, restmixins
from ripozo.resources.constructor import ResourceMetaClass

from ripozo_sqlalchemy.easy_resource import _get_pks, _get_fields_for_model, \
    _get_relationships, create_resource

from sqlalchemy import Column, Integer, String, ForeignKey, Table
from sqlalchemy.orm import relationship, backref
from sqlalchemy.ext.declarative import declarative_base

import unittest2


class TestEasyResource(unittest2.TestCase):
    def assertAllIn(self, first, second):
        self.assertEqual(len(first), len(second))
        for val in first:
            self.assertIn(val, second)

    def assertIsNotInstance(self, obj, types):
        self.assertFalse(isinstance(obj, types))

    def test_get_pks_single(self):
        Base = declarative_base()

        class MyModel(Base):
            __tablename__ = 'blah'
            id = Column(Integer, primary_key=True)
            value = Column(String)

        resp = _get_pks(MyModel)
        self.assertAllIn(('id',), resp)

    def test_get_pks_multiple(self):
        Base = declarative_base()

        class MyModel(Base):
            __tablename__ = 'blah'
            id = Column(Integer, primary_key=True)
            pk = Column(String, primary_key=True)
            value = Column(String)

        self.assertAllIn(_get_pks(MyModel), ('id', 'pk',))

    def test_get_fields_for_model(self):
        """
        Tests a simple get_field_for_model
        """
        Base = declarative_base()

        class MyModel(Base):
            __tablename__ = 'blah'
            id = Column(Integer, primary_key=True)
            value = Column(String)

        resp = _get_fields_for_model(MyModel)
        self.assertAllIn(('id', 'value',), resp)

    def test_get_fields_for_model_one_to_many(self):
        """
        Tests getting the fields for a one_to_many
        """
        Base = declarative_base()

        class Parent(Base):
            __tablename__ = 'parent'
            id = Column(Integer, primary_key=True)
            children = relationship("Child", backref="parent")

        class Child(Base):
            __tablename__ = 'child'
            id = Column(Integer, primary_key=True)
            parent_id = Column(Integer, ForeignKey('parent.id'))

        resp = _get_fields_for_model(Parent)
        self.assertAllIn(resp, ('id', 'children.id',))
        resp = _get_fields_for_model(Child)
        self.assertAllIn(resp, ('id', 'parent_id', 'parent.id'))

    def test_get_fields_for_model_many_to_one(self):
        """
        Tests getting the fields for a many_to_one
        """
        Base = declarative_base()

        class Parent(Base):
            __tablename__ = 'parent'
            id = Column(Integer, primary_key=True)
            child_id = Column(Integer, ForeignKey('child.id'))
            child = relationship("Child", backref="parents")

        class Child(Base):
            __tablename__ = 'child'
            id = Column(Integer, primary_key=True)

        resp = _get_fields_for_model(Parent)
        self.assertAllIn(resp, ('id', 'child.id', 'child_id'))
        resp = _get_fields_for_model(Child)
        self.assertAllIn(resp, ('id', 'parents.id',))

    def test_get_fields_one_to_one(self):
        """
        Tests getting the fields for a one-to-one
        """
        Base = declarative_base()

        class Parent(Base):
            __tablename__ = 'parent'
            id = Column(Integer, primary_key=True)
            child_id = Column(Integer, ForeignKey('child.id'))
            child = relationship("Child", backref=backref("parent", uselist=False))

        class Child(Base):
            __tablename__ = 'child'
            id = Column(Integer, primary_key=True)

        resp = _get_fields_for_model(Parent)
        self.assertAllIn(resp, ('id', 'child.id', 'child_id'))
        resp = _get_fields_for_model(Child)
        self.assertAllIn(resp, ('id', 'parent.id',))

    def test_get_fields_many_to_many(self):
        """
        Tests getting the fields for a many-to-many
        """
        Base = declarative_base()

        association_table = Table(
            'association', Base.metadata,
            Column('left_id', Integer, ForeignKey('left.id')),
            Column('right_id', Integer, ForeignKey('right.id'))
        )

        class Parent(Base):
            __tablename__ = 'left'
            id = Column(Integer, primary_key=True)
            children = relationship("Child", secondary=association_table, backref='parents')

        class Child(Base):
            __tablename__ = 'right'
            id = Column(Integer, primary_key=True)

        resp = _get_fields_for_model(Parent)
        self.assertAllIn(resp, ('id', 'children.id',))
        resp = _get_fields_for_model(Child)
        self.assertAllIn(resp, ('id', 'parents.id',))

    def test_get_relationships_for_model(self):
        """
        Tests a simple get_field_for_model
        """
        Base = declarative_base()

        class MyModel(Base):
            __tablename__ = 'blah'
            id = Column(Integer, primary_key=True)
            value = Column(String)

        resp = _get_relationships(MyModel)
        self.assertTupleEqual(tuple(), resp)

    def test_get_relationships_for_model_one_to_many(self):
        """
        Tests getting the fields for a one_to_many
        """
        Base = declarative_base()

        class Parent(Base):
            __tablename__ = 'parent'
            id = Column(Integer, primary_key=True)
            children = relationship("Child", backref="parent")

        class Child(Base):
            __tablename__ = 'child'
            id = Column(Integer, primary_key=True)
            parent_id = Column(Integer, ForeignKey('parent.id'))

        resp = _get_relationships(Parent)
        self.assertEqual(len(resp), 1)
        rel = resp[0]
        self.assertIsInstance(rel, ListRelationship)
        self.assertEqual(rel.name, 'children')
        self.assertEqual(rel._relation, 'Child')

        resp = _get_relationships(Child)
        self.assertEqual(len(resp), 1)
        rel = resp[0]
        self.assertIsInstance(rel, Relationship)
        self.assertIsNotInstance(rel, ListRelationship)
        self.assertEqual(rel.name, 'parent')
        self.assertEqual(rel._relation, 'Parent')

    def test_get_relationships_for_model_many_to_one(self):
        """
        Tests getting the fields for a many_to_one
        """
        Base = declarative_base()

        class Parent(Base):
            __tablename__ = 'parent'
            id = Column(Integer, primary_key=True)
            child_id = Column(Integer, ForeignKey('child.id'))
            child = relationship("Child", backref="parents")

        class Child(Base):
            __tablename__ = 'child'
            id = Column(Integer, primary_key=True)

        resp = _get_relationships(Parent)
        self.assertEqual(len(resp), 1)
        rel = resp[0]
        self.assertIsInstance(rel, Relationship)
        self.assertIsNotInstance(rel, ListRelationship)
        self.assertEqual(rel.name, 'child')
        self.assertEqual(rel._relation, 'Child')

        resp = _get_relationships(Child)
        self.assertEqual(len(resp), 1)
        rel = resp[0]
        self.assertIsInstance(rel, ListRelationship)
        self.assertEqual(rel.name, 'parents')
        self.assertEqual(rel._relation, 'Parent')

    def test_get_relationships_one_to_one(self):
        """
        Tests getting the fields for a one-to-one
        """
        Base = declarative_base()

        class Parent(Base):
            __tablename__ = 'parent'
            id = Column(Integer, primary_key=True)
            child_id = Column(Integer, ForeignKey('child.id'))
            child = relationship("Child", backref=backref("parent", uselist=False))

        class Child(Base):
            __tablename__ = 'child'
            id = Column(Integer, primary_key=True)

        resp = _get_relationships(Parent)
        self.assertEqual(len(resp), 1)
        rel = resp[0]
        self.assertIsInstance(rel, Relationship)
        self.assertIsNotInstance(rel, ListRelationship)
        self.assertEqual(rel.name, 'child')
        self.assertEqual(rel._relation, 'Child')

        resp = _get_relationships(Child)
        self.assertEqual(len(resp), 1)
        rel = resp[0]
        self.assertIsInstance(rel, Relationship)
        self.assertIsNotInstance(rel, ListRelationship)
        self.assertEqual(rel.name, 'parent')
        self.assertEqual(rel._relation, 'Parent')

    def test_get_relationships_many_to_many(self):
        """
        Tests getting the fields for a many-to-many
        """
        Base = declarative_base()

        association_table = Table(
            'association', Base.metadata,
            Column('left_id', Integer, ForeignKey('left.id')),
            Column('right_id', Integer, ForeignKey('right.id'))
        )

        class Parent(Base):
            __tablename__ = 'left'
            id = Column(Integer, primary_key=True)
            children = relationship("Child", secondary=association_table, backref='parents')

        class Child(Base):
            __tablename__ = 'right'
            id = Column(Integer, primary_key=True)

        resp = _get_relationships(Parent)
        self.assertEqual(len(resp), 1)
        rel = resp[0]
        self.assertIsInstance(rel, ListRelationship)
        self.assertEqual(rel.name, 'children')
        self.assertEqual(rel._relation, 'Child')

        resp = _get_relationships(Child)
        self.assertEqual(len(resp), 1)
        rel = resp[0]
        self.assertIsInstance(rel, ListRelationship)
        self.assertEqual(rel.name, 'parents')
        self.assertEqual(rel._relation, 'Parent')

    def test_create_resource(self):
        """
        Tests the create_resource method minimal application
        """
        Base = declarative_base()

        class MyModel(Base):
            __tablename__ = 'base'
            id = Column(Integer, primary_key=True)
            value = Column(String)

        resp = create_resource(MyModel, None)
        self.assertIsInstance(resp, ResourceMetaClass)
        self.assertEqual(resp.__name__, 'MyModel')
        self.assertIn(resp, ResourceMetaClass.registered_resource_classes)
        self.assertIn(resp.__name__, ResourceMetaClass.registered_names_map)
        res = resp()
        self.assertIsInstance(res, restmixins.CRUDL)
        self.assertEqual(res.resource_name, 'my_model')
