ripozo-sqlalchemy
=================

.. image:: https://travis-ci.org/vertical-knowledge/ripozo-sqlalchemy.svg?branch=master&style=flat
    :target: https://travis-ci.org/vertical-knowledge/ripozo-sqlalchemy
    :alt: test status

.. image:: https://coveralls.io/repos/vertical-knowledge/ripozo-sqlalchemy/badge.svg?branch=master&style=flat
    :target: https://coveralls.io/r/vertical-knowledge/ripozo-sqlalchemy?branch=master
    :alt: test coverage

.. image:: https://readthedocs.org/projects/ripozo-sqlalchemy/badge/?version=latest&style=flat
    :target: https://ripozo-sqlalchemy.readthedocs.org/
    :alt: Documentation Status

..

    .. image:: https://pypip.in/version/ripozo-sqlalchemy/badge.svg?style=flat
        :target: https://pypi.python.org/pypi/ripozo-sqlalchemy/
        :alt: current version

    .. image:: https://pypip.in/d/ripozo-sqlalchemy/badge.png?style=flat
        :target: https://crate.io/packages/ripozo-sqlalchemy/
        :alt: Number of PyPI downloads

    .. image:: https://pypip.in/py_versions/ripozo-sqlalchemy/badge.svg?style=flat
        :target: https://pypi.python.org/pypi/ripozo-sqlalchemy/
        :alt: python versions
    
This package is a ripozo extension that provides a Manager that integrate
SQLAlchemy with ripozo.  It provides convience functions for generating resources.
In particular, it focuses on creating shortcuts for CRUD type operations.  It fully
implements the BaseManager_ class that is provided in the
ripozo_ package.

`Full Documentation <http://ripozo-sqlalchemy.readthedocs.org/en/latest/>`_

Example
=======

This is a minimal example of creating ripozo managers
with ripozo-sqlalchemy and integrating them with a 
resource.

.. code-block:: python

    from ripozo import apimethod, ResourceBase
    
    from ripozo_sqlalchemy import AlchemyManager, SessionHandler

    from sqlalchemy import Column, Integer, String, create_engine
    from sqlalchemy.ext.declarative import declarative_base
    from sqlalchemy.orm import Session
    
    # Setup the database with sqlalchemy
    engine = create_engine('sqlite:///:memory:', echo=True)
    Base = declarative_base()
    session = Session(engine)
    session_handler = SessionHandler(session)
    
    # Declare your ORM model
    class Person(Base):
        __tablename__ = 'person'
        id = Column(Integer, primary_key=True)
        first_name = Column(String)
        last_name = Column(String)
        
    # Sync the models wiht the database
    Base.metadata.create_all()
    
    # This is the code that is specific to ripozo-sqlalchemy
    # You give it the session, a SQLAlchemy Model, and the fields
    # You wish to serialize at a minimum.
    class PersonManager(AlchemyManager):
        model = Person
        fields = ('id', 'first_name', 'last_name')
        
        
    # This is the ripozo specific part.
    # This creates a resource class that can be given
    # to a dispatcher (e.g. the flask-ripozo package's FlaskDispatcher)
    class PersonResource(ResourceBase):
        manager = PersonManager
        pks = ['id']
        namespace = '/api'
        
        # A retrieval method that will operate on the '/api/person' route
        # It retrieves the id, first_name, and last_name properties
        @apimethod(methods=['GET'])
        def get_person(cls, primary_keys, filters, values, *args, **kwargs):
            properties = self.manager.retrieve(primary_keys)
            return cls(properties=properties)
        
    
    

.. _BaseManager: https://ripozo.readthedocs.org/en/latest/API/ripozo.managers.html#ripozo.managers.base.BaseManager

.. _ripozo: https://ripozo.readthedocs.org/