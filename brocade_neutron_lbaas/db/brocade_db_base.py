'''
 Copyright 2013 by Brocade Communication Systems
 All rights reserved.

 This software is the confidential and proprietary information
 of Brocade Communication Systems, ("Confidential Information").
 You shall not disclose such Confidential Information and shall
 use it only in accordance with the terms of the license agreement
 you entered into with Brocade Communication Systems.
'''
from sqlalchemy import orm
from sqlalchemy import types

from sqlalchemy.ext import declarative
from sqlalchemy.orm import object_mapper
import sqlalchemy as sa
from sqlalchemy.types import TypeDecorator

from brocade_neutron_lbaas.db import uuidutils
import jsonutils


class ModelBase(object):
    """Base class for models."""
    #__table_initialized__ = False

   
    def __setitem__(self, key, value):
        setattr(self, key, value)

    def __getitem__(self, key):
        return getattr(self, key)

    def get(self, key, default=None):
        return getattr(self, key, default)

    def __iter__(self):
        columns = dict(object_mapper(self).columns).keys()
        # NOTE(russellb): Allow models to specify other keys that can be looked
        # up, beyond the actual db columns.  An example would be the 'name'
        # property for an Instance.
        if hasattr(self, '_extra_keys'):
            columns.extend(self._extra_keys())
        self._i = iter(columns)
        return self

    def next(self):
        n = self._i.next()
        return n, getattr(self, n)

    def update(self, values):
        """Make the model object behave like a dict."""
        for k, v in values.iteritems():
            setattr(self, k, v)

    def iteritems(self):
        """Make the model object behave like a dict.

        Includes attributes from joins.
        """
        local = dict(self)
        joined = dict([(k, v) for k, v in self.__dict__.iteritems()
                      if not k[0] == '_'])
        local.update(joined)
        return local.iteritems()

class BrocadeBase(ModelBase):
    """Base class for Neutron Models."""

    __table_args__ = {'mysql_engine': 'InnoDB'}

    def __iter__(self):
        self._i = iter(orm.object_mapper(self).columns)
        return self

    def next(self):
        n = self._i.next().name
        return n, getattr(self, n)

    def __repr__(self):
        """sqlalchemy based automatic __repr__ method."""
        items = ['%s=%r' % (col.name, getattr(self, col.name))
                 for col in self.__table__.columns]
        return "<%s.%s[object at %x] {%s}>" % (self.__class__.__module__,
                                               self.__class__.__name__,
                                               id(self), ', '.join(items))


class BrocadeBaseV2(BrocadeBase):

    @declarative.declared_attr
    def __tablename__(cls):  # @NoSelf
        # NOTE(jkoelker) use the pluralized name of the class as the table
        t_name = cls.__name__.lower()
        if(t_name.endswith('y')):
            return t_name.rstrip('y')+'ies'
        return t_name + 's'

BASEV2 = declarative.declarative_base(cls=BrocadeBaseV2)

# HasId
class HasId(object):
    id = sa.Column(sa.String(36),primary_key=True,default=uuidutils.generate_uuid)

class HasTenant(object):
    """Tenant mixin, add to subclasses that have a tenant."""

    # NOTE(jkoelker) tenant_id is just a free form string ;(
    tenant_id = sa.Column(sa.String(255))

class JsonType(TypeDecorator):
    impl = types.String

    def process_bind_param(self, value, engine):
        if value is not None:
            return jsonutils.dumps(value)
        return jsonutils.dumps({})

    def process_result_value(self, value, engine):
        if value is not None:
            return jsonutils.loads(value)
        return {}


class BrocadeAdxGroup(BASEV2,HasId):
    name = sa.Column(sa.String(256),nullable=False)
    devices=orm.relationship("BrocadeAdxLoadBalancer",backref="brocadeadxgroups",cascade="all")


class BrocadeAdxLoadBalancer(BASEV2, HasId, HasTenant):
    """ Represents Brocade ADX loadbalancer device
    """
    name = sa.Column(sa.String(36))
    version = sa.Column(sa.String(36))
    management_ip = sa.Column(sa.String(36))
    nova_instance_id=sa.Column(sa.String(36),unique=True)
    user = sa.Column(sa.String(36), nullable=False)
    password = sa.Column(sa.String(36), nullable=False)
    status=sa.Column(sa.String(36))
    ha_config_type=sa.Column(sa.Enum("PRIMARY","SECONDARY",name="ha_config_type"))
    communication_type=sa.Column(sa.Enum("HTTP","HTTPS",name="communication_type"))
    status_description = sa.Column(sa.String(36), nullable=True)
    additional_info = sa.Column(JsonType(255), nullable=True)
    created_time = sa.Column(sa.DateTime)
    last_updated_time = sa.Column(sa.DateTime)
    deleted_at=sa.Column(sa.DateTime)
    ports = orm.relationship(
        "BrocadeAdxPort", backref="brocadeadxloadbalancers",
        cascade="all, delete-orphan"
    )
    adx_group_id=sa.Column(sa.String(36),sa.ForeignKey("brocadeadxgroups.id"))

class BrocadeAdxPort(BASEV2,HasId):

    subnet_id = sa.Column(sa.String(36), nullable=False)
    adx_lb_id = sa.Column(sa.String(36), sa.ForeignKey("brocadeadxloadbalancers.id"), nullable=False)
    mac=sa.Column(sa.String(36))
    ip_address=sa.Column(sa.String(36))
    network_id=sa.Column(sa.String(36))

