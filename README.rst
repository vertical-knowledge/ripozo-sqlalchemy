ripozo-sqlalchemy
=================

.. image:: https://travis-ci.org/vertical-knowledge/ripozo-sqlalchemy.svg?branch=master
    :target: https://travis-ci.org/vertical-knowledge/ripozo-sqlalchemy
    :alt: Travis CI Status
    
.. image:: https://readthedocs.org/projects/ripozo-sqlalchemy/badge/?version=latest
    :target: https://ripozo-sqlalchemy.readthedocs.org/
    :alt: Documentation Status
    
This package is a ripozo extension that provides a Manager that integrate
SQLAlchemy with ripozo.  It provides convience functions for generating resources.
In particular, it focuses on creating shortcuts for CRUD type operations.  It fully
implements the BaseManager_ class that is provided in the
ripozo_ package.

Example
=======

This is a minimal example of creating ripozo managers
with ripozo-sqlalchemy and integrating them with a 
resource.

.. code-block:: python

    from ripozo.decorators import apimethod
    from ripozo.viewsets.resource_base import ResourceBase
    
    from ripozo_sqlalchemy import AlchemyManager

    from sqlalchemy import Column, Integer, String, create_engine
    from sqlalchemy.ext.declarative import declarative_base
    from sqlalchemy.orm import sessionmaker
    
    # Setup the database with sqlalchemy
    Base = declarative_base(create_engine('sqlite:///:memory:', echo=True))
    session = session_maker()()
    
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
        session = session
        model = Person
        fields = ('id', 'first_name', 'last_name')
        
        
    # This is the ripozo specific part.
    # This creates a resource class that can be given
    # to a dispatcher (e.g. the flask-ripozo package's FlaskDispatcher)
    class PersonResource(ResourceBase):
        _manager = PersonManager
        _pks = ['id']
        _namespace = '/api'
        
        # A retrieval method that will operate on the '/api/person' route
        # It retrieves the id, first_name, and last_name properties
        @apimethod(methods=['GET'])
        def get_person(cls, primary_keys, filters, values, *args, **kwargs):
            properties = self.manager.retrieve(primary_keys)
            return cls(properties=properties)
        
    
    

.. _BaseManager: https://ripozo.readthedocs.org/en/latest/API/ripozo.managers.html#ripozo.managers.base.BaseManager

.. _ripozo: https://ripozo.readthedocs.org/