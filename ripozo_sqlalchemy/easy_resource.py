from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from ripozo import Relationship, ListRelationship
from ripozo.resources.constructor import ResourceMetaClass
from ripozo.resources.restmixins import CRUDL

from ripozo_sqlalchemy import AlchemyManager

from sqlalchemy.inspection import inspect
from sqlalchemy.orm import class_mapper, RelationshipProperty


def _get_fields_for_model(model):
    fields = []
    for name in model._sa_class_manager:
        prop = getattr(model, name)
        if isinstance(prop.property, RelationshipProperty):
            for pk in class_mapper(prop.class_).primary_key:
                fields.append('{0}.{1}'.format(name, pk.name))
        else:
            fields.append(name)
    return tuple(fields)


def _get_pks(model):
    return tuple([key.name for key in inspect(model).primary_key])


def _get_relationships(model):
    relationships = []
    for name in model._sa_class_manager:
        prop = getattr(model, name)
        if isinstance(prop.property, RelationshipProperty):
            if prop._supports_population:
                class_ = inspect(model).relationships._data[name].mapper.class_
                rel = ListRelationship(name, relation=class_.__name__)
            else:
                rel = Relationship(name, relation=prop.class_.__name__)
            relationships.append(rel)
    return tuple(relationships)


def create_resource(model, session_handler, resource_bases=(CRUDL,),
                    relationships=None, links=None, preprocessors=None,
                    postprocessors=None, fields=None, paginate_by=100,
                    auto_relationships=True, pks=None):
        """

        :param sqlalchemy.Model model:
        :param tuple resource_bases:
        :param tuple relationships:
        :param tuple links:
        :param tuple preprocessors:
        :param tuple postprocessors:
        :param ripozo_sqlalchemy.SessionHandler session_handler:
        :param tuple fields:
        :param bool auto_relationships:
        :return: A ResourceBase subclass and AlchemyManager subclass
        :rtype: ResourceMetaClass, type
        """
        relationships = relationships or tuple()
        if auto_relationships:
            relationships += _get_relationships(model)
        links = links or tuple()
        preprocessors = preprocessors or tuple()
        postprocessors = postprocessors or tuple()
        pks = pks or _get_pks(model)
        fields = fields or _get_fields_for_model(model)

        manager_cls_attrs = dict(paginate_by=paginate_by, fields=fields, model=model)
        manager_class = type(str(model.__name__), (AlchemyManager,), manager_cls_attrs)
        manager = manager_class(session_handler)

        resource_cls_attrs = dict(preprocessors=preprocessors,
                                  postprocessors=postprocessors,
                                  _relationships=relationships, _links=links,
                                  pks=pks, manager=manager)
        res_class = ResourceMetaClass(str(model.__name__), resource_bases, resource_cls_attrs)
        return res_class
