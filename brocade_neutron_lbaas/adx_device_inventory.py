# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright 2014 Brocade Communications Systems, Inc.
# All Rights Reserved.
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
# @author: Pattabi Ayyasami, Brocade Communication Systems, Inc.
#
import json
from oslo.config import cfg

from neutron.openstack.common import log as logging
from neutron.common import exceptions as q_exc
import adx_service
import ConfigParser
from db.db_base import configure_db
from db.adx_lb_db_plugin import AdxLoadBalancerDbPlugin
from neutron.openstack.common import log as logging
from db.context import Context
import adx_exception as adx_exception
LOG = logging.getLogger(__name__)



brocade_device_driver_opts = [
    cfg.StrOpt('devices_file_name',
               default='/etc/neutron/services/loadbalancer/'
                       'brocade/device_inventory.ini',
               help=_('file containing the brocade device database url'))]
cfg.CONF.register_opts(brocade_device_driver_opts, "brocade")


class AdxLoadBalancerManager(object):
    def __init__(self, device_driver):
        self.device_driver = device_driver
        self.devices_file_name = cfg.CONF.brocade.devices_file_name
        config=ConfigParser.ConfigParser()
        config.read(self.devices_file_name)
        self.dburl=config.get('DEFAULT','db_url')
        if self.dburl==None:
            LOG.error("Database url not configured for brocade device inventory")
            raise adx_exception.StartupError(msg="DbUrl Not configured")
        self.context=Context()
        configure_db(self.dburl)
        self.db_plugin= AdxLoadBalancerDbPlugin()

    def get_device(self,subnet_id):
        filters={'BrocadeAdxPort.subnet_id':subnet_id}
        adx= self.db_plugin.get_adxloadbalancer(self.context,filters)
        if len(adx)==0:
            filters={'BrocadeAdxPort.subnet_id':'ALL'}
            adx=self.db_plugin.get_adxloadbalancer(self.context,filters)
        return adx

    def add_device(self,device_dict):
        adx=self.db_plugin.create_adxloadbalancer(device_dict,self.context)
        return adx

    def add_port(self,port_dict,adx_lb_id):
        port=self.db_plugin.create_port(port_dict,self.context,adx_lb_id)
        return port


    def delete_port(self,port_id):
        port= self.db_plugin.delete_port(port_id,self.context)
        return port


    def update_device(self,device_dict):
        device=self.db_plugin.update_adxloadbalancer(device_dict, self.context)
        adx_service.ClientCache.delete_adx_service_client(device)
        adx_service.ClientCache.add_adx_service_client(device)


    def delete_device(self,device_id):
        device=self.db_plugin.delete_adxloadbalancer(device_id,self.context)
        adx_service.ClientCache.delete_adx_service_client(device)

