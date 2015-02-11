# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright 2014 Brocade Communications Systems, Inc.  All rights reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.
#

from brocade_neutron_lbaas.db import db_utils as utils
from brocade_neutron_lbaas.db.brocade_db_base import BrocadeAdxLoadBalancer
from brocade_neutron_lbaas.db.brocade_db_base import BrocadeAdxPort
import json
import uuid

def _format_date_time(date):
    if(date!=None):
        return json.dumps(date.strftime("%Y-%m-%d %H:%M:%S"))
    else:
        return None

class AdxLoadBalancerDbPlugin():
    def _make_device_dict(self, device, fields=None):
        res = {'id': device['id'],
               'tenant_id': device['tenant_id'],
               'name': device['name'],
               'version': device['version'],
               'management_ip': device['management_ip'],
               'user': device['user'],
               'password': device['password'],
               'status': device['status'],
               'ha_config_type':device['ha_config_type'],
               'communication_type':device['communication_type'],
               'nova_instance_id':device['nova_instance_id'],
               'created_time' :_format_date_time(device['created_time']),
               'last_updated_time':_format_date_time(device['last_updated_time']),
               'deleted_at':_format_date_time(device['deleted_at']),
               'status_description': device.get('status_descritpion')}
        port_objs=device.ports
        ports=[]
        if port_objs:
            for port in port_objs:
                ports.append(self._make_port_dict(port))
        res['ports']=ports
        return utils._fields(res, fields)

    def _make_port_dict(self,port,fields=None):
        res={'id':port['id'],
            'subnet_id':port['subnet_id'],
            'adx_lb_id':port['adx_lb_id'],
            'mac':port['mac'],
            'ip_address':port['ip_address'],
            'network_id':port['network_id']}
        return utils._fields(res,fields)

    def set_obj_attr(self,obj,obj_dict):
        for k,v in obj_dict.iteritems():
            setattr(obj,k,v)
        return obj

    def create_adxloadbalancer(self, d, context):
        with context.session.begin(subtransactions=True):
            device_db=None
            try:
                device_db = BrocadeAdxLoadBalancer(id=str(uuid.uuid4())
                self.set_obj_attr(device_db,d)
                context.session.add(device_db)
                context.session.flush()
            except Exception as e:
                raise e
        device_info = self._make_device_dict(device_db)
        return device_info

    def create_port(self,d,context):
        with context.session.begin(subtransactions=True):
            port_db = BrocadeAdxPort(id=str(uuid.uuid4())
            self.set_obj_attr(port_db,d)
            context.session.add(port_db)
            context.session.flush()

        port_info =self._make_port_dict(port_db)
        return port_info

    def delete_port(self,port_id,context):
        with context.session.begin(subtransactions=True):
            port_db=utils._get_resource(context,
                                        BrocadeAdxPort,
                                        port_id)
            context.session.delete(port_db)
        port_info =self._make_port_dict(port_db)
        return port_info


    def update_adxloadbalancer(self, d,context):
        with context.session.begin(subtransactions=True):
            device_db = utils._get_resource(context,
                                            BrocadeAdxLoadBalancer,d['id'])
            self.set_obj_attr(device_db,d)
            context.session.merge(device_db)
            context.session.flush()
        device_info=self._make_device_dict(device_db)
        return device_info


    def delete_adxloadbalancer(self, device_id,context):
        device_info = None
        with context.session.begin(subtransactions=True):
            device_db = utils._get_resource(context,
                                            BrocadeAdxLoadBalancer,
                                            device_id)
            device_info =  self._make_device_dict(device_db)
            context.session.delete(device_db)
        device_info=self._make_device_dict(device_db)
        return device_info


    def get_port(self,context,filters=None,fields=None):
        return utils._get_collection(context,
                                     BrocadeAdxPort,
                                     self._make_port_dict,
                                     filters=filters,
                                     fields=fields,
                                     limit=None,
                                     offset=0,
                                     joins=None)


    def get_adxloadbalancer(self,context, filters=None, fields=None):
        joins=[BrocadeAdxPort]
        return utils._get_collection(context,
                                     BrocadeAdxLoadBalancer,
                                     self._make_device_dict,
                                     filters=filters,
                                     fields=fields,
                                     limit=None,
                                     offset=0,joins=joins)
