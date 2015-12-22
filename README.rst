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

First we need to setup our SQLAlchemy model.

.. code-block:: python

    from ripozo import apimethod, ResourceBase

    from sqlalchemy import Column, Integer, String, create_engine
    from sqlalchemy.ext.declarative import declarative_base
    
    # Setup the database with sqlalchemy
    engine = create_engine('sqlite:///:memory:', echo=True)
    Base = declarative_base()
    
    # Declare your ORM model
    class Person(Base):
        __tablename__ = 'person'
        id = Column(Integer, primary_key=True)
        first_name = Column(String)
        last_name = Column(String)
        
    # Sync the models wiht the database
    Base.metadata.create_all()

Now we can get to the ripozo-sqlalchemy part.

.. code-block:: python

    from ripozo_sqlalchemy import AlchemyManager, ScopedSessionHandler

    # A session handler if responsible for getting
    # And handling a session after either a successful or unsuccessful request
    session_handler = ScopedSessionHandler(engine)
    
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
        manager = PersonManager(session_handler)
        pks = ['id']
        namespace = '/api'
        
        # A retrieval method that will operate on the '/api/person/<id>' route
        # It retrieves the id, first_name, and last_name properties for the
        # resource as identified by the url parameter id.
        @apimethod(methods=['GET'])
        def get_person(cls, request):
            properties = cls.manager.retrieve(request.url_params)
            return cls(properties=properties)
            
Easy Resources
^^^^^^^^^^^^^^
        
Alternatively, we could use the create_resource method which
will automatically create a manager and resource that corresponds
to the manager.

.. code-block:: python

    from ripozo import restmixins
    from ripozo_sqlalchemy import ScopedSessionHandler, create_resource

    session_handler = ScopedSessionHandler(engine)
    PersonResource = create_resource(Person, session_handler)

By default create_resource will give you full CRUD+L (Create, Retrieve, Update, Delete, List).
Although there are many options that you can pass to create_resource to modify exactly how
the resource class is constructed.

After you create your resource class, you will need to load it into a dispatcher
corresponding to your framework.  For example, in flask-ripozo

.. code-block:: python

    from flask import Flask
    from flask_ripozo import FlaskDispatcher
    from ripozo.adapters import SirenAdapter, HalAdapter # These are the potential formats to return

    app = Flask(__name__)
    dispatcher = FlaskDispatcher(app)
    dispatcher.register_adapters(SirenAdapter, HalAdapter)
    dispatcher.register_resources(PersonResource)

    app.run()
    

.. _BaseManager: https://ripozo.readthedocs.org/en/latest/API/ripozo.managers.html#ripozo.managers.base.BaseManager

.. _ripozo: https://ripozo.readthedocs.org/
