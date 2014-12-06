# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright 2013 Brocade Communications Systems, Inc.  All rights reserved.
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
# @author: Pattabi Ayyasami, Brocade Communications Systems,Inc.
#

from neutron.common import log
from neutron.context import get_admin_context
from neutron.openstack.common import log as logging
from neutron.services.loadbalancer import constants

import adx_device_driver_impl_v1 as driver_impl
import adx_device_inventory as device_inventory

LOG = logging.getLogger(__name__)

class BrocadeAdxDeviceDriverV1():
    def __init__(self, plugin):
        self.plugin = plugin
        self.device_inv_mgr = (device_inventory
                               .BrocadeAdxDeviceInventoryManager(self))

    def _get_pool(self, pool_id):
        return self.plugin.get_pool(get_admin_context(), pool_id)

    def _get_vip(self, vip_id):
        return self.plugin.get_vip(get_admin_context(), vip_id)

    def _get_pool_members(self, pool_id):
        pool = self._get_pool(pool_id)
        return ([self.plugin.get_member(get_admin_context(), member_id)
                for member_id in pool['members']])

    def _get_health_monitors(self, pool_id):
        pool = self.plugin.get_pool(get_admin_context(), pool_id)
        return ([self.plugin.get_health_monitor(get_admin_context(), monitor_id)
                for monitor_id in pool['health_monitors']])

    def _get_device(self, subnet_id):
        devices = self.device_inv_mgr.get_device(subnet_id)
        if len(devices) == 0:
            raise device_inventory.NoValidDevice()

        # filter by subnet_id
        filtered = [device for device in devices
                   if 'active' in device['status'] ]

        if not filtered:
            LOG.error(_('No active device was found for subnet: %s'), subnet_id)
            raise device_inventory.NoValidDevice()

        device =filtered[0]
        return device

    def _fetch_device(self, pool_id):
        pool = self._get_pool(pool_id)
        subnet_id = pool['subnet_id']
        #self.device_inv_mgr.load_devices()
        device = self._get_device(subnet_id)
        return device

    @log.log
    def create_vip(self, obj):
        device = self._fetch_device(obj['pool_id'])
        impl = driver_impl.BrocadeAdxDeviceDriverImplV1(self.plugin, device)
        impl.create_vip(obj)

        pool_id = obj['pool_id']
        # Retrieve the Pool Members for the specified pool_id
        # Bind the Members to VIP
        members = self._get_pool_members(pool_id)
        for member in members:
            impl.bind_member_to_vip(member, obj)

        # Retrieve the lb_method from the pool and set it on vip
        pool = self._get_pool(pool_id)
        lb_method = pool['lb_method']
        impl.set_predictor_on_virtual_server(obj, lb_method)

    @log.log
    def update_vip(self, obj, old_obj):
        device = self._fetch_device(obj['pool_id'])
        impl = driver_impl.BrocadeAdxDeviceDriverImplV1(self.plugin, device)
        impl.update_vip(obj, old_obj)


        # Retrieve the lb_method from the pool and set it on vip
        old_pool_id = old_obj['pool_id']
        new_pool_id = obj['pool_id']
        if old_pool_id != new_pool_id:
            # Pool has been updated
            pool = self._get_pool(new_pool_id)
            lb_method = pool['lb_method']
            impl.set_predictor_on_virtual_server(obj, lb_method)

            # Retrieve the pool members of old_pool_id
            # Unbind the members from vip
            members = self._get_pool_members(old_pool_id)
            for member in members:
                impl.unbind_member_from_vip(member, obj)

            # Retrieve the members of new_pool_id
            # Bind the members to vip
            members = self._get_pool_members(new_pool_id)
            for member in members:
                impl.bind_member_to_vip(member, obj)

    @log.log
    def delete_vip(self, obj):
        device = self._fetch_device(obj['pool_id'])
        impl = driver_impl.BrocadeAdxDeviceDriverImplV1(self.plugin, device)
        impl.delete_vip(obj)

    @log.log
    def create_pool(self, obj):
        pass
        #device = self._fetch_device(obj['id'])
        #impl = driver_impl.BrocadeAdxDeviceDriverImplV1(self.plugin, device)
        #impl.create_pool(obj)

    @log.log
    def update_pool(self, obj, old_obj):
        device = self._fetch_device(obj['id'])
        impl = driver_impl.BrocadeAdxDeviceDriverImplV1(self.plugin, device)

        new_lb_method = obj.get('lb_method')
        old_lb_method = old_obj.get('lb_method')
        vip_id = obj.get('vip_id')

        if new_lb_method == old_lb_method:
            return

        if vip_id and new_lb_method:
            vip = self._get_vip(vip_id)
            impl.set_predictor_on_virtual_server(vip, new_lb_method)

    @log.log
    def delete_pool(self, obj):
        device = self._fetch_device(obj['id'])
        impl = driver_impl.BrocadeAdxDeviceDriverImplV1(self.plugin, device)
        #impl.delete_pool(obj)

        pool_id = obj['id']

        # Retrieve health monitors
        # Delete health monitors
        hms = self._get_health_monitors(pool_id)
        for hm in hms:
            impl.delete_health_monitor(hm, pool_id)

        # Retrieve pool members
        # Delete members
        members = self._get_pool_members(pool_id)
        for member in members:
            impl.delete_member(member)


    @log.log
    def create_member(self, obj):
        device = self._fetch_device(obj['pool_id'])
        impl = driver_impl.BrocadeAdxDeviceDriverImplV1(self.plugin, device)
        impl.create_member(obj)

        pool_id = obj['pool_id']

        # bind member to vip
        pool = self._get_pool(pool_id)
        vip_id = pool['vip_id']
        if vip_id:
            vip = self._get_vip(vip_id)
            impl.bind_member_to_vip(obj, vip)

        # bind the monitor to member
        hms = self._get_health_monitors(pool_id)
        for hm in hms:
            impl.bind_monitor_to_member(hm, obj)


    @log.log
    def update_member(self, obj, old_obj):
        device = self._fetch_device(obj['pool_id'])
        impl = driver_impl.BrocadeAdxDeviceDriverImplV1(self.plugin, device)
        impl.update_member(obj, old_obj)

        new_pool_id = obj['pool_id']
        old_pool_id = old_obj['pool_id']
        if new_pool_id != old_pool_id:

            # Retrieve the monitors bound to old pool and unbind
            old_hms = self._get_health_monitors(old_pool_id)
            for old_hm in old_hms:
                impl.unbind_monitor_from_member(old_hm, obj)

            # Retrieve the monitors bound to the new pool and bind
            hms = self._get_health_monitors(new_pool_id)
            for hm in hms:
                impl.bind_monitor_to_member(hm, obj)

            # Retrieve the vip from the old pool
            # If pool bound to a vip, unbind the Members from vip
            old_pool = self._get_pool(old_pool_id)
            old_vip_id = old_pool['vip_id']
            if old_vip_id:
                old_vip = self._get_vip(old_vip_id)
                impl.unbind_member_from_vip(obj, old_vip)

            # Retrieve the vip from the new_pool_id
            # UnBind the Members from vip
            new_pool = self._get_pool(new_pool_id)
            new_vip_id = new_pool['vip_id']
            if new_vip_id:
                new_vip = self._get_vip(new_vip_id)
                impl.bind_member_to_vip(obj, new_vip)

    @log.log
    def delete_member(self, obj):
        device = self._fetch_device(obj['pool_id'])
        impl = driver_impl.BrocadeAdxDeviceDriverImplV1(self.plugin, device)
        impl.delete_member(obj)

    @log.log
    def create_health_monitor(self, obj, pool_id):
        device = self._fetch_device(pool_id)
        impl = driver_impl.BrocadeAdxDeviceDriverImplV1(self.plugin, device)
        impl.create_health_monitor(obj, pool_id)

        monitor_type = obj['type']
        if monitor_type in [constants.HEALTH_MONITOR_HTTP,
                            constants.HEALTH_MONITOR_HTTPS,
                            constants.HEALTH_MONITOR_TCP]:
            members = self._get_pool_members(pool_id)
            for member in members:
                impl.bind_monitor_to_member(obj, member)

    @log.log
    def delete_health_monitor(self, obj, pool_id):
        device = self._fetch_device(pool_id)
        impl = driver_impl.BrocadeAdxDeviceDriverImplV1(self.plugin, device)

        # Retrieve the members of the pool from pool_id
        # Unbind health monitor from the members
        members = self._get_pool_members(pool_id)
        for member in members:
            impl.unbind_monitor_from_member(obj, member)

        impl.delete_health_monitor(obj, pool_id)

    @log.log
    def update_health_monitor(self, obj, old_obj, pool_id):
        device = self._fetch_device(pool_id)
        impl = driver_impl.BrocadeAdxDeviceDriverImplV1(self.plugin, device)
        impl.update_health_monitor(obj, old_obj, pool_id)

    @log.log
    def get_pool_stats(self, pool_id):
        device = self._fetch_device(pool_id)
        impl = driver_impl.BrocadeAdxDeviceDriverImplV1(self.plugin, device)
        return impl.get_pool_stats(pool_id)
