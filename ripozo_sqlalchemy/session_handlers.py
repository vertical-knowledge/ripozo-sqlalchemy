"""
Contains basic session handlers.
"""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from sqlalchemy.orm import sessionmaker, scoped_session


class ScopedSessionHandler(object):
    """
    A ScopedSessionHandler is injected into the AlchemyManager
    in order to get and handle sessions after a database
    access.

    There are two required methods for any session handler.
    It must have a
    """

    def __init__(self, engine):
        """
        Initializes the ScopedSessionHandler which is responsible
        for getting sessions and closing them after a database access.

        :param Engine engine: A SQLAlchemy engine.
        """
        self.engine = engine
        self.session_maker = scoped_session(sessionmaker(bind=self.engine))

    def get_session(self):
        """
        Gets an individual session.

        :return: The session object.
        :rtype: Session
        """
        return self.session_maker()

    @staticmethod
    def handle_session(session, exc=None):
        """
        Handles closing a session.

        :param Session session: The session to close.
        :param Exception exc: The exception raised,
            If an exception was raised, else None
        """
        if exc:
            session.rollback()
        session.close()


class SessionHandler(object):
    """
    The SessionHandler doesn't do anything.
    This is helpful in Flask-SQLAlchemy for example
    where all of the session handling is already under control
    """

    def __init__(self, session):
        """
        :param Session session: The session to pass
            to the Manager.  This is what will be directly
            used by the application
        :param Exception exc: The exception raised,
            If an exception was raised, else None
        """
        self.session = session

    def get_session(self):
        """
        Gets the session

        :return: The session for the manager.
        :rtype: Session
        """
        return self.session

    @staticmethod
    def handle_session(session, exc=None):
        """
        rolls back the session if appropriate.

        :param Session session: The session in use.
        :param Exception exc: The exception raised,
            If an exception was raised, else None
        """
        if exc:
            session.rollback()
