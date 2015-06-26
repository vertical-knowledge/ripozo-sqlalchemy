ripozo-sqlalchemy example
=========================

.. testsetup:: *
    :hide:

    import logging
    logging.disable(logging.ERROR)

.. testsetup:: basic

    from sqlalchemy import Column, Integer, String, create_engine
    from sqlalchemy.ext.declarative import declarative_base
    from sqlalchemy.orm import Session

    # Setup the database with sqlalchemy
    engine = create_engine('sqlite:///:memory:', echo=True)
    Base = declarative_base(engine)
    session = Session(engine)

    # Declare your ORM model
    class Person(Base):
        __tablename__ = 'person'
        id = Column(Integer, primary_key=True)
        first_name = Column(String)
        last_name = Column(String)
        secret = Column(String)

    Base.metadata.create_all()

Creatings your manager
^^^^^^^^^^^^^^^^^^^^^^

.. testsetup:: basic

    from ripozo_sqlalchemy import AlchemyManager, SessionHandler

    class PersonManager(AlchemyManager):
        fields = ['id', 'first_name', 'last_name']
        model = Person
        paginate_by = 10

    session_handler = SessionHandler(session)


And the resource...
^^^^^^^^^^^^^^^^^^^

.. testsetup:: basic

    from ripozo import restmixins

    class PersonResource(restmixins.CRUDL):
        resource_name = 'people'
        manager = PersonManager(session_handler)
        namespace = '/api'
        pks = ['id']

Creating a person
^^^^^^^^^^^^^^^^^

.. doctest:: basic

    >>> from ripozo import RequestContainer
    >>> req = RequestContainer(body_args=dict(first_name='Hey', last_name='there'))
    >>> person = PersonResource.create(req)
    >>> print(person.properties['first_name'])
    Hey
    >>> print(person.properties['last_name'])
    there
    >>> print(person.url)
    /api/people/1

Retrieving a person
^^^^^^^^^^^^^^^^^^^

.. doctest:: basic

    >>> person_id = person.properties['id']
    >>> req = RequestContainer(url_params=dict(id=person_id))
    >>> retrieved = PersonResource.retrieve(req)
    >>> print(person.properties['first_name'])
    Hey
    >>> print(person.properties['last_name'])
    there

Updating a person
^^^^^^^^^^^^^^^^^

.. doctest:: basic

    >>> req = RequestContainer(url_params=dict(id=person_id), body_args=dict(first_name='Bob'))
    >>> person = PersonResource.update(req)
    >>> print(person.properties['first_name'])
    Bob
    >>> print(person.properties['last_name'])
    there
    >>> req = RequestContainer(url_params=dict(id=person_id))
    >>> retrieved = PersonResource.retrieve(req)
    >>> print(person.properties['first_name'])
    Bob
    >>> print(person.properties['last_name'])
    there

Retrieving many
^^^^^^^^^^^^^^^

.. doctest:: basic

    >>> for i in range(10):
    ...     req = RequestContainer(body_args=dict(first_name='John', last_name=i))
    ...     res = PersonResource.create(req)
    >>> req = RequestContainer()
    >>> resource_list = PersonResource.retrieve_list(req)
    >>> assert len(resource_list.related_resources[0].resource) == 10 # only ten because paginate_by=10
    >>> print(resource_list.url)
    /api/people
