from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from ripozo_sqlalchemy.session_handlers import ScopedSessionHandler, SessionHandler

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

import mock
import unittest2


class TestScopedSessionHandler(unittest2.TestCase):
    def test_get_session(self):
        engine = create_engine('sqlite:///:memory:')
        handler = ScopedSessionHandler(engine)
        session = handler.get_session()
        self.assertIsInstance(session, Session)

    def test_handle_session(self):
        engine = create_engine('sqlite:///:memory:')
        handler = ScopedSessionHandler(engine)
        session = mock.MagicMock()
        handler.handle_session(session)
        self.assertTrue(session.close.called)

    def test_handle_session_exception(self):
        session = mock.MagicMock()
        handler = ScopedSessionHandler(session)
        e = Exception()
        handler.handle_session(session, exc=e)
        self.assertTrue(session.rollback.called)


class TestSessionHandler(unittest2.TestCase):
    def test_get_session(self):
        session = mock.MagicMock()
        handler = SessionHandler(session)
        session_returned = handler.get_session()
        self.assertIs(session, session_returned)

    def test_handle_session(self):
        session = mock.MagicMock()
        handler = SessionHandler(session)
        self.assertIsNone(handler.handle_session(session))

    def test_handle_session_exception(self):
        session = mock.MagicMock()
        handler = SessionHandler(session)
        e = Exception()
        handler.handle_session(session, exc=e)
        self.assertTrue(session.rollback.called)

