from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from datetime import datetime, date, time, timedelta
from decimal import Decimal

from ripozo.decorators import classproperty
from ripozo.exceptions import NotFoundException
from ripozo.managers.base import BaseManager
from ripozo.viewsets.fields.base import BaseField
from ripozo.viewsets.fields.common import StringField, IntegerField, FloatField, DateTimeField, BooleanField
from ripozo.utilities import make_json_safe

from sqlalchemy.orm import class_mapper
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.orm.query import Query
from sqlalchemy.orm.relationships import RelationshipProperty

import logging
import six

logger = logging.getLogger(__name__)


class AlchemyManager(BaseManager):
    """
    This is the Manager that interops between ripozo
    and sqlalchemy.  It provides a series of convience
    functions primarily for basic CRUD.  This class can
    be extended as necessary and it is recommended that direct
    database access should be performed in a manager.

    :param session: The sqlalchemy session needs to be set on an
        subclass of AlchemyManager.
    """
    session = None  # the database object needs to be given to the class
    pagination_pk_query_arg = 'page'
    all_fields = False

    def __init__(self, *args, **kwargs):
        super(AlchemyManager, self).__init__(*args, **kwargs)
        self._field_dict = None

    @classproperty
    def fields(cls):
        """
        :return: Returns the _fields attribute if it is available.  If it
            is not and the cls.all_fields attribute is set to True,
            then it will return all of the columns names on the model.
            Otherwise it will return an empty list
        :rtype: list
        """
        if not cls._fields and cls.all_fields is True:
            fields = []
            for name in cls.model._sa_class_manager:
                prop = getattr(cls.model, name)
                if isinstance(prop.property, RelationshipProperty):
                    for pk in class_mapper(prop.class_).primary_key:
                        fields.append('{0}.{1}'.format(name, pk.name))
                else:
                    fields.append(name)
            cls._fields = fields
        return cls._fields or []

    @staticmethod
    def _get_field_python_type(model, name):
        try:
            return getattr(model, name).property.columns[0].type.python_type
        except AttributeError:  # It's a relationship
            parts = name.split('.')
            try:
                model = getattr(model, parts.pop(0)).comparator.mapper.class_
                return AlchemyManager._get_field_python_type(model, '.'.join(parts))
            except AttributeError:
                return object  # TODO Fuck it
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
        t = cls._get_field_python_type(cls.model, name)
        if t in (six.text_type, six.binary_type):
            return StringField(name)
        elif t is int:
            return IntegerField(name)
        elif t in (float, Decimal,):
            return FloatField(name)
        elif t in (datetime, date, timedelta, time):
            return DateTimeField(name)
        elif t is bool:
            return BooleanField(name)
        else:
            return BaseField(name)

    def create(self, values, *args, **kwargs):
        model = self._set_values_on_model(self.model(), values)
        self.session.add(model)
        self.session.commit()
        return self.serialize_model(model)

    def retrieve(self, lookup_keys, *args, **kwargs):
        """
        Retrieves a model using the lookup keys provided.
        Only one model should be returned by the lookup_keys
        or else the manager will fail.

        :param dict lookup_keys: A dictionary mapping the fields
            and their expected values
        :return: The dictionary of keys and values for the retrieved
            model.  The only values returned will be those specified by
            fields attrbute on the class
        :rtype: dict
        """
        model = self._get_model(lookup_keys)
        return self.serialize_model(model)

    def retrieve_list(self, filters, *args, **kwargs):
        q = self.queryset
        pagination_count = filters.pop(self.pagination_count_query_arg, self.paginate_by)
        pagination_pk = filters.pop(self.pagination_pk_query_arg, 1)
        pagination_pk -= 1  # logic works zero based. Pagination shouldn't be though

        q = q.filter_by(**filters)

        if pagination_pk:
            q = q.offset(pagination_pk * pagination_count)
        if pagination_count:
            q = q.limit(pagination_count + 1)

        count = q.count()
        next = None
        previous = None
        if count > pagination_count:
            next = {self.pagination_pk_query_arg: pagination_pk + 2,
                    self.pagination_count_query_arg: pagination_count}
        if pagination_pk > 0:
            previous = {self.pagination_pk_query_arg: pagination_pk,
                        self.pagination_count_query_arg: pagination_count}

        props = self.serialize_model(q[:pagination_count], field_dict=self.dot_field_list_to_dict(self.list_fields))
        return props, dict(links=dict(next=next, prev=previous))

    def update(self, lookup_keys, updates, *args, **kwargs):
        model = self._get_model(lookup_keys)
        model = self._set_values_on_model(model, updates)
        self.session.commit()
        return self.serialize_model(model)

    def delete(self, lookup_keys, *args, **kwargs):
        model = self._get_model(lookup_keys)
        self.session.delete(model)
        self.session.commit()
        return {}

    @property
    def queryset(self):
        """
        The queryset to use when looking for models.

        This is advantageous to override if you only
        want a subset of the model specified.
        """
        # attrs, joins = self._get_model_attributes()
        # q = self.session.query(*attrs)
        # for j in joins:
        #     q = q.outerjoin(j)
        # return q
        return self.session.query(self.model)

    def serialize_model(self, model, field_dict=None):
        response = self._serialize_model_helper(model, field_dict=field_dict)
        return make_json_safe(response)

    def _serialize_model_helper(self, model, field_dict=None):
        field_dict = field_dict or self.dot_field_list_to_dict()
        if model is None:
            return None

        if isinstance(model, Query):
            model = model.all()

        if isinstance(model, (list, set)):
            model_list = []
            for m in model:
                model_list.append(self.serialize_model(m, field_dict=field_dict))
            return model_list

        model_dict = {}
        for name, sub in six.iteritems(field_dict):
            value = getattr(model, name)
            if sub:
                value = self.serialize_model(value, field_dict=sub)
            model_dict[name] = value
        return model_dict

    def _get_model(self, lookup_keys):
        try:
            return self.queryset.filter_by(**lookup_keys).one()
        except NoResultFound:
            raise NotFoundException('No model of type {0} was found using '
                                    'lookup_keys {1}'.format(self.model.__name__, lookup_keys))

    def _set_values_on_model(self, model, values):
        for name, val in six.iteritems(values):
            if name not in self.fields:
                continue
            setattr(model, name, val)
        return model
