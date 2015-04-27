from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from abc import ABCMeta, abstractmethod, abstractproperty

from datetime import datetime, date, timedelta, time

from decimal import Decimal

from ripozo.exceptions import NotFoundException

from ripozo_tests.python2base import TestBase

from sqlalchemy.orm.exc import MultipleResultsFound
from sqlalchemy.orm.query import Query

import six

__author__ = 'Tim Martin'

@six.add_metaclass(ABCMeta)
class CommonTest(TestBase):
    @abstractproperty
    def field_dict(self):
        pass

    @abstractmethod
    def get_fake_values(self):
        pass

    @property
    def manager(self):
        return self._manager()

    def assertResponseEqualsModel(self, model, manager, response):
        try:
            for name, value in six.iteritems(response):
                model_value = getattr(model, name)
                if isinstance(model_value, Query):
                    model_value = model_value.all()
                elif isinstance(model_value, datetime):
                    model_value = model_value.strftime('%Y-%m-%d %H:%M:%S.%f')
                elif isinstance(model_value, (date, time,timedelta,)):
                    model_value = six.text_type(model_value)
                elif isinstance(model_value, Decimal):
                    model_value = float(model_value)
                self.assertEqual(model_value, response[name])
        except:
            raise

        for field in manager.fields:
            field = field.split('.')[0]
            self.assertIn(field, response)
        self.assertEqual(len(manager.fields), len(response))

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
            if isinstance(values[name], (datetime, date, timedelta, time,)):
                values[name] = six.text_type(values[name])
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
        self.session.refresh(model)
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

    def test_update_with_field_not_in_fields(self):
        values = self.get_fake_values()
        model = self.create(values=values)
        values['fake'] = 'nope'
        response = self.manager.update(dict(id=model.id), values)
        self.session.refresh(model)
        if 'fake' in response:
            assert False
        self.assertRaises(AttributeError, getattr, model, 'fake')

    def test_delete_multiple_fail(self):
        values = self.get_fake_values()
        self.create(values=values)
        self.create(values=values)
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
            filters = meta['links']['next']
            self.assertLessEqual(len(response), 3)
            for r in response:
                id = r['id']
                for model in models:
                    if model.id == id:
                        self.assertResponseEqualsModel(model, Manager(), r)
                        break