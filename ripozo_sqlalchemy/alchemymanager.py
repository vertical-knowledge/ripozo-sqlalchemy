"""
Core pieces of the AlchemyManager
"""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from datetime import datetime, date, time, timedelta
from decimal import Decimal
from functools import wraps

from ripozo.exceptions import NotFoundException
from ripozo.manager_base import BaseManager
from ripozo.resources.fields.base import BaseField
from ripozo.resources.fields.common import StringField, IntegerField,\
    FloatField, DateTimeField, BooleanField
from ripozo.utilities import make_json_safe

from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.orm.query import Query

import logging
import six

_logger = logging.getLogger(__name__)

_COLUMN_FIELD_MAP = {
    six.text_type: StringField,
    six.binary_type: StringField,
    int: IntegerField,
    float: FloatField,
    Decimal: FloatField,
    datetime: DateTimeField,
    date: DateTimeField,
    timedelta: DateTimeField,
    time: DateTimeField,
    bool: BooleanField,
}


def db_access_point(func):
    """
    Wraps a function that actually accesses the database.
    It injects a session into the method and attempts to handle
    it after the function has run.

    :param method func: The method that is interacting with the database.
    """
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        """
        Wrapper responsible for handling
        sessions
        """
        session = self.session_handler.get_session()
        try:
            resp = func(self, session, *args, **kwargs)
        except Exception as exc:
            self.session_handler.handle_session(session, exc=exc)
            raise exc
        else:
            self.session_handler.handle_session(session)
            return resp
    return wrapper


class AlchemyManager(BaseManager):
    """
    This is the Manager that interops between ripozo
    and sqlalchemy.  It provides a series of convience
    functions primarily for basic CRUD.  This class can
    be extended as necessary and it is recommended that direct
    database access should be performed in a manager.

    :param bool all_fields:  If this is true, then all fields on
        the model will be used.  The model will be inspected to
        get the fields.
    """
    pagination_pk_query_arg = 'page'
    all_fields = False
    fields = tuple()

    def __init__(self, session_handler, *args, **kwargs):
        super(AlchemyManager, self).__init__(*args, **kwargs)
        self._field_dict = None
        self.session_handler = session_handler

    @staticmethod
    def _get_field_python_type(model, name):
        """
        Gets the python type for the attribute on the model
        with the name provided.

        :param Model model: The SqlAlchemy model class.
        :param unicode name: The column name on the model
            that you are attempting to get the python type.
        :return: The python type of the column
        :rtype: type
        """
        try:
            return getattr(model, name).property.columns[0].type.python_type
        except AttributeError:  # It's a relationship
            parts = name.split('.')
            model = getattr(model, parts.pop(0)).comparator.mapper.class_
            return AlchemyManager._get_field_python_type(model, '.'.join(parts))
        except NotImplementedError:
            # This is for pickle type columns.
            return object

    @classmethod
    def get_field_type(cls, name):
        """
        Takes a field name and gets an appropriate BaseField instance
        for that column.  It inspects the Model that is set on the manager
        to determine what the BaseField subclass should be.

        :param unicode name:
        :return: A BaseField subclass that is appropriate for
            translating a string input into the appropriate format.
        :rtype: ripozo.viewsets.fields.base.BaseField
        """
        python_type = cls._get_field_python_type(cls.model, name)
        if python_type in _COLUMN_FIELD_MAP:
            field_class = _COLUMN_FIELD_MAP[python_type]
            return field_class(name)
        return BaseField(name)

    @db_access_point
    def create(self, session, values, *args, **kwargs):
        """
        Creates a new instance of the self.model
        and persists it to the database.

        :param dict values: The dictionary of values to
            set on the model.  The key is the column name
            and the value is what it will be set to.  If
            the cls._create_fields is defined then it will
            use those fields.  Otherwise, it will use the
            fields defined in cls.fields
        :param Session session: The sqlalchemy session
        :return: The serialized model.  It will use the self.fields
            attribute for this.
        :rtype: dict
        """
        model = self.model()
        model = self._set_values_on_model(model, values, fields=self.create_fields)
        session.add(model)
        session.commit()
        return self.serialize_model(model)

    @db_access_point
    def retrieve(self, session, lookup_keys, *args, **kwargs):
        """
        Retrieves a model using the lookup keys provided.
        Only one model should be returned by the lookup_keys
        or else the manager will fail.

        :param Session session: The SQLAlchemy session to use
        :param dict lookup_keys: A dictionary mapping the fields
            and their expected values
        :return: The dictionary of keys and values for the retrieved
            model.  The only values returned will be those specified by
            fields attrbute on the class
        :rtype: dict
        :raises: NotFoundException
        """
        model = self._get_model(lookup_keys, session)
        return self.serialize_model(model)

    @db_access_point
    def retrieve_list(self, session, filters, *args, **kwargs):
        """
        Retrieves a list of the model for this manager.
        It is restricted by the filters provided.

        :param Session session: The SQLAlchemy session to use
        :param dict filters: The filters to restrict the returned
            models on
        :return: A tuple of the list of dictionary representation
            of the models and the dictionary of meta data
        :rtype: list, dict
        """
        query = self.queryset(session)
        pagination_count = filters.pop(self.pagination_count_query_arg, self.paginate_by)
        pagination_pk = filters.pop(self.pagination_pk_query_arg, 1)
        pagination_pk -= 1  # logic works zero based. Pagination shouldn't be though

        query = query.filter_by(**filters)

        if pagination_pk:
            query = query.offset(pagination_pk * pagination_count)
        if pagination_count:
            query = query.limit(pagination_count + 1)

        count = query.count()
        next_link = None
        previous_link = None
        if count > pagination_count:
            next_link = {self.pagination_pk_query_arg: pagination_pk + 2,
                         self.pagination_count_query_arg: pagination_count}
        if pagination_pk > 0:
            previous_link = {self.pagination_pk_query_arg: pagination_pk,
                             self.pagination_count_query_arg: pagination_count}

        field_dict = self.dot_field_list_to_dict(self.list_fields)
        props = self.serialize_model(query[:pagination_count], field_dict=field_dict)
        meta = dict(links=dict(next=next_link, previous=previous_link))
        return props, meta

    @db_access_point
    def update(self, session, lookup_keys, updates, *args, **kwargs):
        """
        Updates the model with the specified lookup_keys and returns
        the dictified object.

        :param Session session: The SQLAlchemy session to use
        :param dict lookup_keys: A dictionary mapping the fields
            and their expected values
        :param dict updates: The columns and the values to update
            them to.
        :return: The dictionary of keys and values for the retrieved
            model.  The only values returned will be those specified by
            fields attrbute on the class
        :rtype: dict
        :raises: NotFoundException
        """
        model = self._get_model(lookup_keys, session)
        model = self._set_values_on_model(model, updates, fields=self.update_fields)
        session.commit()
        return self.serialize_model(model)

    @db_access_point
    def delete(self, session, lookup_keys, *args, **kwargs):
        """
        Deletes the model found using the lookup_keys

        :param Session session: The SQLAlchemy session to use
        :param dict lookup_keys: A dictionary mapping the fields
            and their expected values
        :return: An empty dictionary
        :rtype: dict
        :raises: NotFoundException
        """
        model = self._get_model(lookup_keys, session)
        session.delete(model)
        session.commit()
        return {}

    def queryset(self, session):
        """
        The queryset to use when looking for models.

        This is advantageous to override if you only
        want a subset of the model specified.
        """
        return session.query(self.model)

    def serialize_model(self, model, field_dict=None):
        """
        Takes a model and serializes the fields provided into
        a dictionary.

        :param Model model: The Sqlalchemy model instance to serialize
        :param dict field_dict: The dictionary of fields to return.
        :return: The serialized model.
        :rtype: dict
        """
        response = self._serialize_model_helper(model, field_dict=field_dict)
        return make_json_safe(response)

    def _serialize_model_helper(self, model, field_dict=None):
        """
        A recursive function for serializing a model
        into a json ready format.
        """
        field_dict = field_dict or self.dot_field_list_to_dict()
        if model is None:
            return None

        if isinstance(model, Query):
            model = model.all()

        if isinstance(model, (list, set)):
            return [self.serialize_model(m, field_dict=field_dict) for m in model]

        model_dict = {}
        for name, sub in six.iteritems(field_dict):
            value = getattr(model, name)
            if sub:
                value = self.serialize_model(value, field_dict=sub)
            model_dict[name] = value
        return model_dict

    def _get_model(self, lookup_keys, session):
        """
        Gets the sqlalchemy Model instance associated with
        the lookup keys.

        :param dict lookup_keys: A dictionary of the keys
            and their associated values.
        :param Session session: The sqlalchemy session
        :return: The sqlalchemy orm model instance.
        """
        try:
            return self.queryset(session).filter_by(**lookup_keys).one()
        except NoResultFound:
            raise NotFoundException('No model of type {0} was found using '
                                    'lookup_keys {1}'.format(self.model.__name__, lookup_keys))

    def _set_values_on_model(self, model, values, fields=None):
        """
        Updates the values with the specified values.

        :param Model model: The sqlalchemy model instance
        :param dict values: The dictionary of attributes and
            the values to set.
        :param list fields: A list of strings indicating
            the valid fields. Defaults to self.fields.
        :return: The model with the updated
        :rtype: Model
        """
        fields = fields or self.fields
        for name, val in six.iteritems(values):
            if name not in fields:
                continue
            setattr(model, name, val)
        return model
