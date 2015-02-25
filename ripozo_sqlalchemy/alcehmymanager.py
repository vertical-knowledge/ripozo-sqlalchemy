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
        """
        Creates a new model of the type specified for the manager.
        The values of the model correspond to the dictionary values
        that maps the fields and values to set on the new model.
        Automatically commits the model.

        :param dict values: The values of the new model that is
            being created
        :return: The newly created SQLAlchemy Model serialized
            into a dictionary.  The dictionary keys will be the
            fields specified in the fields attribute on the class
            and the values will be the newly created models values.
        :rtype: dict
        """
        logger.info('Creating model')
        model = self.model()
        for name, value in six.iteritems(values):
            setattr(model, name, value)
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
        return self.serialize_model(self._get_model(lookup_keys))

    def retrieve_list(self, filters, *args, **kwargs):
        """
        Gets a list of models that match the filters provided.

        :param dict filters: A dictionary of values to match on
            in order to return a list of values.
        :return: A tuple, The first value is a list of the serialized models
            and a dictionary of metadata as the second value in the tuple.
        :rtype: tuple
        """
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
        """
        Updates a SQLAlchemy model and returns the update, serialized model

        :param dict lookup_keys: The keys for finding the model.  Typically this
            would be a dictionary of the primary key names and their associated values
        :param dict updates: a dictionary of the fields to update the values to set
            them as.
        :return: A serialized SQLAlchemy model that only returns the values
            on the model for the the fields attribute on the class
        :rtype:
        """
        model = self._get_model(lookup_keys)
        for name, value in six.iteritems(updates):
            setattr(model, name, value)
        self.session.commit()
        return self.serialize_model(model)

    def delete(self, lookup_keys, *args, **kwargs):
        """
        Deletes the model from the SQLAlchemy Model
        for the model found by the lookup_keys

        :param dict lookup_keys: The keys to find the model with
        """
        model = self._get_model(lookup_keys)
        self.session.delete(model)
        self.session.commit()

    @property
    def model_name(self):
        """
        Returns the name of the model.
        It is simply the class name for the SQLAlchemy Model
        """
        return self.model.__name__

    @property
    def queryset(self):
        """
        The queryset to use when looking for models.

        This is advantageous to override if you only
        want a subset of the model specified.
        """
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
