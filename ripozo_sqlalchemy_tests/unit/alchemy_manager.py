from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from ripozo_sqlalchemy.alchemymanager import AlchemyManager, NoResultFound, NotFoundException

import mock
import unittest2


class TestAlchemyManager(unittest2.TestCase):
    def test_set_values_on_model(self):
        manager = AlchemyManager(None)
        model = mock.MagicMock()
        m = manager._set_values_on_model(model, dict(first=1, second=2, third=3), fields=['first', 'second'])
        self.assertEqual(m.first, 1)
        self.assertEqual(m.second, 2)
        self.assertNotEqual(m.third, 3)

    def test_get_model_no_result_found(self):
        m = AlchemyManager(None)
        m.model = mock.Mock(__name__='blah')
        session = mock.MagicMock()
        session.query.side_effect = NoResultFound
        self.assertRaises(NotFoundException, m._get_model, {}, session)

    def test_serialize_model_helper_none(self):
        """
        Tests serializing None
        """
        m = AlchemyManager(None)
        self.assertIsNone(m._serialize_model_helper(None))

    def test_serialize_model_list(self):
        """
        Tests serializing a list/set
        """
        m = AlchemyManager(None)
        model = [None, None, None]
        resp = m._serialize_model_helper(model)
        for x in model:
            self.assertIsNone(x)
        self.assertEqual(len(model), 3)

    def test_serialize_model_recursion(self):
        """
        Tests a recursive serialization of a model.
        """
        m = AlchemyManager(None)
        field_dict = dict(first=None, second=dict(third=None))
        model = mock.Mock(first=1, second=mock.Mock(third=3))
        resp = m._serialize_model_helper(model, field_dict=field_dict)
        self.assertDictEqual(dict(first=1, second=dict(third=3)), resp)

    def test_queryset(self):
        m = AlchemyManager(None)
        session = mock.MagicMock()
        resp = m.queryset(session)
        self.assertTrue(session.query.called)
