from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from datetime import datetime
from ripozo.exceptions import NotFoundException
from ripozo.managers.base import BaseManager
from ripozo.viewsets.fields.base import BaseField
from ripozo.viewsets.fields.common import StringField, IntegerField, FloatField, DateTimeField, BooleanField
from ripozo.utilities import serialize_fields

import logging
import six

logger = logging.getLogger(__name__)


class AlchemyManager(BaseManager):
    session = None  # the database object needs to be given to the class
    pagination_pk_query_arg = 'page'

    @classmethod
    def get_field_type(cls, name):
        # TODO need to look at the columns for defaults and such
        t = cls.model.metadata.tables[cls.model.__tablename__].columns._data[name].type.python_type
        if t in (six.text_type, six.binary_type):
            return StringField(name)
        elif t is int:
            return IntegerField(name)
        elif t is float:
            return FloatField(name)
        elif t is datetime:
            return DateTimeField(name)
        elif t is bool:
            return BooleanField(name)
        else:
            return BaseField(name)

    def create(self, values, *args, **kwargs):
        logger.info('Creating model')
        model = self.model()
        for name, value in six.iteritems(values):
            setattr(model, name, value)
        self.session.add(model)
        self.session.commit()
        return self.serialize_model(model)

    def retrieve(self, lookup_keys, *args, **kwargs):
        return self.serialize_model(self._get_model(lookup_keys))

    def retrieve_list(self, filters, *args, **kwargs):
        pagination_count, filters = self.get_pagination_count(filters)
        pagination_pk, filters = self.get_pagination_pks(filters)
        if isinstance(pagination_pk, (list, tuple)):
            if len(pagination_pk) == 0:
                pagination_pk = None
            else:
                pagination_pk = pagination_pk[0]

        if pagination_pk is None:
            pagination_pk = 0
        q = self.queryset.filter_by(**filters)
        if self.order_by:
            q = q.order_by(self.order_by)
        q = q.limit(pagination_count).offset(pagination_pk * pagination_count)
        model_list = []
        for m in q.all():
            model_list.append(self.serialize_model(m))
        next_page = pagination_pk + 1
        query_args = '{0}={1}&{2}={3}'.format(self.pagination_pk_query_arg, next_page,
                                              self.pagination_count_query_arg, pagination_count)
        return model_list, {self.pagination_pk_query_arg: next_page,
                            self.pagination_count_query_arg: pagination_count,
                            self.pagination_next: query_args}

    def update(self, lookup_keys, updates, *args, **kwargs):
        model = self._get_model(lookup_keys)
        for name, value in six.iteritems(updates):
            setattr(model, name, value)
        self.session.commit()
        return self.serialize_model(model)

    def delete(self, lookup_keys, *args, **kwargs):
        model = self._get_model(lookup_keys)
        self.session.delete(model)
        self.session.commit()

    @property
    def model_name(self):
        return self.model.__name__

    @property
    def queryset(self):
        return self.session.query(self.model)

    def _get_model(self, lookup_keys):
        """
        Gets the model specified by the lookupkeys

        :param lookup_keys: A dictionary of fields and values on the model to filter by
        :type lookup_keys: dict
        """
        pks = six.itervalues(lookup_keys)
        row = self.queryset.get(list(pks))
        if row is None:
            raise NotFoundException('The model {0} could not be found. '
                                    'lookup_keys: {1}'.format(self.model_name, lookup_keys))
        return row

    def serialize_model(self, obj):
        values = []
        for f in self.fields:
            values.append(getattr(obj, f))
        return serialize_fields(self.fields, values)