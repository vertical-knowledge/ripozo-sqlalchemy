from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from ripozo_sqlalchemy.alcehmymanager import AlchemyManager, NoResultFound, NotFoundException

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
