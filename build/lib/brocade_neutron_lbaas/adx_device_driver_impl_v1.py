# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright 2014 Brocade Communication Systems, Inc.  All rights reserved.
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

import suds as suds

from neutron.common import log
from neutron.context import get_admin_context
from neutron.openstack.common import log as logging
from neutron.services.loadbalancer import constants
import adx_exception
import adx_service


LOG = logging.getLogger(__name__)

ADX_STANDARD_PORTS = [21, 22, 23, 25, 53, 69, 80, 109, 110, 119, 123, 143, 161,
                      389, 443, 554, 636, 993, 995, 1645, 1755, 1812,
                      3389, 5060, 5061, 7070]

ADX_PREDICTOR_MAP = {
    constants.LB_METHOD_ROUND_ROBIN: 'ROUND_ROBIN',
    constants.LB_METHOD_LEAST_CONNECTIONS: 'LEAST_CONN'
}

ADX_PROTOCOL_MAP = {
    constants.PROTOCOL_TCP: 'TCP',
    constants.PROTOCOL_HTTP: 'HTTP',
    constants.PROTOCOL_HTTPS: 'SSL'
}


class BrocadeAdxDeviceDriverImplV1():
    def __init__(self, plugin, device):
        self.plugin = plugin
        service_clients = (adx_service.ClientCache
                           .get_adx_service_client(device))
        self.slb_factory = service_clients[0].factory
        self.slb_service = service_clients[0].service

        self.sys_factory = service_clients[1].factory
        self.sys_service = service_clients[1].service

        self.net_factory = service_clients[2].factory
        self.net_service = service_clients[2].service


    def _get_pool(self, pool_id):
        return self.plugin.get_pool(get_admin_context(), pool_id)

    def _get_pool_members(self, pool_id):
        pool = self._get_pool(pool_id)
        ctx = get_admin_context()
        return ([self.plugin.get_member(ctx, member_id)
                for member_id in pool['members']])

    def _get_health_monitors(self, pool_id):
        ctx = get_admin_context()
        pool = self.plugin.get_pool(ctx, pool_id)
        return ([self.plugin.get_health_monitor(ctx, monitor_id)
                for monitor_id in pool['health_monitors']])

    def _adx_server(self, address, name=None):
        server = self.slb_factory.create("Server")
        server.IP = address
        if name:
            server.Name = name
        return server

    def _adx_server_port(self, address, protocol_port, name=None):
        # Create Server
        server = self._adx_server(address, name)

        # Create L4Port
        l4_port = self.slb_factory.create('L4Port')
        l4_port.NameOrNumber = protocol_port

        # Create ServerPort
        server_port = self.slb_factory.create('ServerPort')
        server_port.srvr = server
        server_port.port = l4_port
        return server_port

    def _update_real_server_port_properties(self, new_member, old_member):
        try:
            address = new_member['address']
            protocol_port = new_member['protocol_port']
            new_admin_state_up = new_member.get('admin_state_up')
            old_admin_state_up = old_member.get('admin_state_up')

            if new_admin_state_up == old_admin_state_up:
                return

            rsServerPort = self._adx_server_port(address, protocol_port)
            reply = (self.slb_service
                     .getRealServerPortConfiguration(rsServerPort))
            rsPortConfSeq = (self.slb_factory.create
                             ('ArrayOfRealServerPortConfigurationSequence'))
            reply.rsPortConfig.serverPort = rsServerPort
            rsPortAdminState = 'ENABLED'
            if not new_admin_state_up:
                rsPortAdminState = 'DISABLED'
            reply.rsPortConfig.adminState = rsPortAdminState

            rsPortConfList = [reply.rsPortConfig]
            rsPortConfSeq.RealServerPortConfigurationSequence = rsPortConfList

            (self.slb_service
             .setRealServersPortConfiguration(rsPortConfSeq))
        except suds.WebFault as e:
            raise adx_exception.ConfigError(msg=e.message)

    def _update_real_server_properties(self, new_member, old_member):
        try:
            address = new_member['address']
            new_weight = new_member.get('weight')
            old_weight = old_member.get('weight')

            if new_weight == old_weight:
                return

            rsServer = self._adx_server(address)
            reply = (self.slb_service
                     .getRealServerConfiguration(rsServer))

            rsConfSeq = (self.slb_factory.create
                         ("ArrayOfRealServerConfigurationSequence"))
            if new_weight:
                reply.rsConfig.leastConnectionWeight = new_weight

            rsConfList = []
            rsConfList.append(reply.rsConfig)
            rsConfSeq.RealServerConfigurationSequence = rsConfList

            (self.slb_service
             .setRealServersConfiguration(rsConfSeq))
        except suds.WebFault as e:
            raise adx_exception.ConfigError(msg=e.message)

    def _get_server_port_count(self, ip_address, is_virtual):
        server = self._adx_server(ip_address)
        startIndex = 1
        numRetrieved = 5
        api_call = (self.slb_service
                    .getAllVirtualServerPortsSummary if is_virtual
                    else self.slb_service.getAllRealServerPortsSummary)
        try:
            reply = api_call(server, startIndex, numRetrieved)
            return reply.genericInfo.totalEntriesAvailable
        except suds.WebFault:
            return 0

    def bind_member_to_vip(self, member, vip):
        rsIpAddress = member['address']
        rsName = rsIpAddress
        if member.get('name'):
            rsName = member['name']
        rsPort = member['protocol_port']

        vsIpAddress = vip['address']
        vsPort = vip['protocol_port']
        vsName = vip['name']

        try:
            vsServerPort = self._adx_server_port(vsIpAddress, vsPort, vsName)
            rsServerPort = self._adx_server_port(rsIpAddress, rsPort, rsName)

            (self.slb_service
             .bindRealServerPortToVipPort(vsServerPort, rsServerPort))
        except suds.WebFault as e:
            raise adx_exception.ConfigError(msg=e.message)

    def unbind_member_from_vip(self, member, vip):
        rsIpAddress = member['address']
        rsName = rsIpAddress
        if member.get('name'):
            rsName = member['name']
        rsPort = member['protocol_port']

        vsIpAddress = vip['address']
        vsPort = vip['protocol_port']
        vsName = vip['name']

        try:
            vsServerPort = self._adx_server_port(vsIpAddress, vsPort, vsName)
            rsServerPort = self._adx_server_port(rsIpAddress, rsPort, rsName)

            (self.slb_service
             .unbindRealServerPortFromVipPort(vsServerPort, rsServerPort))
        except suds.WebFault as e:
            raise adx_exception.ConfigError(msg=e.message)

    def bind_monitor_to_member(self, healthmonitor, member):
        healthmonitor_name = healthmonitor['id']
        rsIpAddress = member['address']
        rsName = rsIpAddress
        if member.get('name'):
            rsName = member['name']
        rsPort = member['protocol_port']
        rsAdminState = 'ENABLED' if member['admin_state_up'] else 'DISABLED'
        rsRunTimeStatus = 'UNDEFINED'

        try:
            rsServerPort = self._adx_server_port(rsIpAddress, rsPort, rsName)

            realServerPortConfig = (self.slb_factory
                                    .create('RealServerPortConfiguration'))
            realServerPortConfig.serverPort = rsServerPort
            realServerPortConfig.adminState = rsAdminState
            realServerPortConfig.runTimeStatus = rsRunTimeStatus
            realServerPortConfig.portPolicyName = healthmonitor_name
            realServerPortConfig.enablePeriodicHealthCheck = True

            rsPortSeq = (self.slb_factory
                         .create('ArrayOfRealServerPortConfigurationSequence'))
            (rsPortSeq.RealServerPortConfigurationSequence
             .append(realServerPortConfig))
            self.slb_service.setRealServersPortConfiguration(rsPortSeq)
        except suds.WebFault as e:
            raise adx_exception.ConfigError(msg=e.message)

    def unbind_monitor_from_member(self, healthmonitor, member):

        rsIpAddress = member['address']
        rsName = rsIpAddress
        if member.get('name'):
            rsName = member['name']
        rsPort = member['protocol_port']
        rsAdminState = 'ENABLED' if member['admin_state_up'] else 'DISABLED'
        rsRunTimeStatus = 'UNDEFINED'

        try:
            rsServerPort = self._adx_server_port(rsIpAddress, rsPort, rsName)

            realServerPortConfig = (self.slb_factory
                                    .create('RealServerPortConfiguration'))
            realServerPortConfig.serverPort = rsServerPort
            realServerPortConfig.adminState = rsAdminState
            realServerPortConfig.runTimeStatus = rsRunTimeStatus
            realServerPortConfig.portPolicyName = ''
            realServerPortConfig.enablePeriodicHealthCheck = False

            rsPortSeq = (self.slb_factory
                         .create('ArrayOfRealServerPortConfigurationSequence'))
            (rsPortSeq.RealServerPortConfigurationSequence
             .append(realServerPortConfig))
            self.slb_service.setRealServersPortConfiguration(rsPortSeq)
        except suds.WebFault as e:
            raise adx_exception.ConfigError(msg=e.message)

    @log.log
    def set_predictor_on_virtual_server(self, vip, lb_method):
        try:
            server = self._adx_server(vip['address'], vip['name'])

            predictorMethodConfiguration = (self.slb_factory.create
                                            ('PredictorMethodConfiguration'))
            predictor = ADX_PREDICTOR_MAP.get(lb_method)
            if predictor:
                predictorMethodConfiguration.predictor = predictor
            else:
                error_message = (_('Load Balancing Method/Predictor %s '
                                   'not supported')) % (lb_method)
                LOG.error(error_message)
                raise adx_exception.UnsupportedFeature(msg=error_message)

            (self.slb_service
             .setPredictorOnVirtualServer(server,
                                          predictorMethodConfiguration))
        except suds.WebFault as e:
            raise adx_exception.ConfigError(msg=e.message)

    def create_virtual_server(self, vip):
        vsName = vip['name']
        vsIpAddress = vip['address']
        vsPort = vip['protocol_port']
        description = vip['description']

        serverPort = self._adx_server_port(vsIpAddress, vsPort, vsName)

        try:
            vsSeq = (self.slb_factory
                     .create('ArrayOfVirtualServerConfigurationSequence'))
            vsConfig = (self.slb_factory
                        .create('VirtualServerConfiguration'))

            vsConfig.virtualServer = serverPort.srvr
            vsConfig.adminState = True
            vsConfig.description = description

            # Work Around to define a value for Enumeration Type
            vsConfig.predictor = 'ROUND_ROBIN'
            vsConfig.trackingMode = 'NONE'
            vsConfig.haMode = 'NOT_CONFIGURED'

            (vsSeq.VirtualServerConfigurationSequence
             .append(vsConfig))
            (self.slb_service.
             createVirtualServerWithConfiguration(vsSeq))
        except suds.WebFault as e:
            LOG.error(_("Exception in create_virtual_server "
                        "in device driver : %s"), e.message)
            raise adx_exception.ConfigError(msg=e.message)

    @log.log
    def create_virtual_server_port(self, vip):
        vsName = vip['name']
        vsIpAddress = vip['address']
        vsPort = vip['protocol_port']
        admin_state_up = vip.get('admin_state_up', True)

        try:
            serverPort = self._adx_server_port(vsIpAddress, vsPort, vsName)
            vsPortSeq = (self.slb_factory.create
                         ('ArrayOfVirtualServerPortConfigurationSequence'))
            vsPortConfig = (self.slb_factory
                            .create('VirtualServerPortConfiguration'))

            vsPortConfig.virtualServer = serverPort.srvr
            vsPortConfig.port = serverPort.port
            vsPortAdminState = 'ENABLED' if admin_state_up else 'DISABLED'
            vsPortConfig.adminState = vsPortAdminState

            session_persistence = vip.get('session_persistence')
            if session_persistence:
                sp_type = session_persistence['type']
                if sp_type == constants.SESSION_PERSISTENCE_SOURCE_IP:
                    vsPortConfig.enableSticky = True
                else:
                    error_message = (_('Session Persistence of type %s '
                                       'not supported')) % (sp_type)
                    LOG.error(error_message)
                    raise adx_exception.UnsupportedFeature(msg=error_message)

            (vsPortSeq.VirtualServerPortConfigurationSequence
             .append(vsPortConfig))
            (self.slb_service
             .createVirtualServerPortWithConfiguration(vsPortSeq))
        except suds.WebFault as e:
            raise adx_exception.ConfigError(msg=e.message)

    @log.log
    def create_vip(self, vip):
        self.create_virtual_server(vip)
        self.create_virtual_server_port(vip)

    @log.log
    def delete_vip(self, vip):
        address = vip['address']
        port = vip['protocol_port']

        vsServerPort = self._adx_server_port(address, port)
        vipPortCount = self._get_server_port_count(address, True)

        try:
            self.slb_service.deleteVirtualServerPort(vsServerPort)
        except suds.WebFault:
            pass

        try:
            if vipPortCount <= 2:
                self.slb_service.deleteVirtualServer(vsServerPort.srvr)
        except suds.WebFault as e:
            raise adx_exception.ConfigError(msg=e.message)

    @log.log
    def update_vip(self, new_vip, old_vip):
        vsIpAddress = new_vip['address']
        vsPort = new_vip['protocol_port']
        vsName = new_vip['name']
        vsServerPort = self._adx_server_port(vsIpAddress, vsPort, vsName)

        old_admin_state_up = old_vip.get('admin_state_up')
        new_admin_state_up = new_vip.get('admin_state_up')
        if new_admin_state_up != old_admin_state_up:
            try:
                if new_admin_state_up:
                    (self.slb_service
                     .enableVirtualServerPort(vsServerPort))
                else:
                    (self.slb_service
                     .disableVirtualServerPort(vsServerPort))
            except suds.WebFault as e:
                raise adx_exception.ConfigError(msg=e.message)

        old_session_persistence = old_vip.get('session_persistence')
        new_session_persistence = new_vip.get('session_persistence')
        if new_session_persistence != old_session_persistence:
            LOG.debug(_('Update Session Persistence'))
            if new_session_persistence is None:
                try:
                    (self.slb_service
                     .disableStickyOnVirtualServerPort(vsServerPort))
                except suds.WebFault as e:
                    raise adx_exception.ConfigError(msg=e.message)
            else:
                type = new_vip['session_persistence']['type']
                if type == constants.SESSION_PERSISTENCE_SOURCE_IP:
                    try:
                        (self.slb_service
                         .enableStickyOnVirtualServerPort(vsServerPort))
                    except suds.WebFault as e:
                        raise adx_exception.ConfigError(msg=e.message)
                else:
                    error_message = (_('Session Persistence of type %s '
                                     'not supported')) % (type)
                    LOG.error(error_message)
                    raise adx_exception.UnsupportedFeature(msg=error_message)

    @log.log
    def _is_port_policy_in_use(self, healthmonitor_name):
        startIndex = 1
        numRetrieved = 15
        portPolicySummaryFilter = (self.slb_factory
                                   .create('PortPolicySummaryFilter'))
        simpleFilter = (self.slb_factory
                        .create('PortPolicySummarySimpleFilter'))
        simpleFilter.field = 'POLICY_NAME'
        simpleFilter.operator = 'EQUAL_TO'
        simpleFilter.value = healthmonitor_name

        portPolicySummaryFilter.simpleFilter = simpleFilter

        try:
            reply = (self.slb_service
                     .getAllPortPolicies(startIndex,
                                         numRetrieved,
                                         portPolicySummaryFilter))
            if reply and reply.policyList:
                policyList = reply.policyList.PortPoliciesSummarySequence
                return any(policy.inUse for policy in policyList)
            else:
                # Check if Port Policy is bound to a Real Server Port
                #inUse = reply.policy.inUse
                return False
        except suds.WebFault:
            return False

    def _does_port_policy_exist(self, healthmonitor):
        name = healthmonitor['id']
        try:
            reply = self.slb_service.getPortPolicy(name)
            if reply:
                return True
        except suds.WebFault:
            return False
        return False

    @log.log
    def _validate_delay(self, monitor_type, delay):
        if monitor_type == constants.HEALTH_MONITOR_HTTP:
            if delay < 1 or delay > 120:
                raise adx_exception.UnsupportedOption(value=delay,
                                                      name="delay")
        elif monitor_type == constants.HEALTH_MONITOR_HTTPS:
            if delay < 5 or delay > 120:
                raise adx_exception.UnsupportedOption(value=delay,
                                                      name="delay")

    @log.log
    def _validate_max_retries(self, max_retries):
        if max_retries < 1 or max_retries > 5:
            raise adx_exception.UnsupportedOption(value=max_retries,
                                                  name="max_retries")

    @log.log
    def _create_update_port_policy(self, healthmonitor, is_create=True):

        name = healthmonitor['id']
        monitor_type = healthmonitor['type']
        delay = healthmonitor['delay']
        self._validate_delay(monitor_type, delay)
        max_retries = healthmonitor['max_retries']
        self._validate_max_retries(max_retries)

        if monitor_type in [constants.HEALTH_MONITOR_HTTP,
                            constants.HEALTH_MONITOR_HTTPS,
                            constants.HEALTH_MONITOR_TCP]:
            portPolicy = self.slb_factory.create('PortPolicy')
            l4Port = self.slb_factory.create('L4Port')

            if monitor_type == constants.HEALTH_MONITOR_HTTP:
                portPolicy.name = name
                l4Port.NameOrNumber = (ADX_PROTOCOL_MAP
                                       .get(constants.PROTOCOL_HTTP))
                portPolicy.port = l4Port
                portPolicy.protocol = (ADX_PROTOCOL_MAP
                                       .get(constants.PROTOCOL_HTTP))
                portPolicy.l4Check = False
            elif monitor_type == constants.HEALTH_MONITOR_HTTPS:
                portPolicy.name = name
                l4Port.NameOrNumber = (ADX_PROTOCOL_MAP
                                       .get(constants.PROTOCOL_HTTPS))
                portPolicy.port = l4Port
                portPolicy.protocol = (ADX_PROTOCOL_MAP
                                       .get(constants.PROTOCOL_HTTPS))
                portPolicy.l4Check = False
            elif monitor_type == constants.HEALTH_MONITOR_TCP:
                # TCP Monitor
                portPolicy.name = name
                portPolicy.l4Check = True

                # Setting Protocol and Port to HTTP
                # so that this can be bound to a Real Server Port
                l4Port.NameOrNumber = (ADX_PROTOCOL_MAP
                                       .get(constants.PROTOCOL_HTTP))
                portPolicy.port = l4Port
                portPolicy.protocol = (ADX_PROTOCOL_MAP
                                       .get(constants.PROTOCOL_HTTP))

            portPolicy.keepAliveInterval = delay
            portPolicy.numRetries = max_retries

            http_method = 'GET'
            url_path = '/'
            expected_codes = '200'
            if 'http_method' in healthmonitor:
                http_method = healthmonitor['http_method']
            if 'url_path' in healthmonitor:
                url_path = healthmonitor['url_path']

            start_status_codes = []
            end_status_codes = []
            if 'expected_codes' in healthmonitor:
                expected_codes = healthmonitor['expected_codes']
                # parse the expected codes.
                # Format:"200, 201, 300-400, 400-410"
                for code in map(lambda x: x.strip(' '),
                                expected_codes.split(',')):
                    if '-' in code:
                        codeRange = map(lambda x: x.strip(' '),
                                        code.split('-'))
                        start_status_codes.append(int(codeRange[0]))
                        end_status_codes.append(int(codeRange[1]))
                    else:
                        start_status_codes.append(int(code))
                        end_status_codes.append(int(code))

            if monitor_type == constants.HEALTH_MONITOR_HTTP:
                httpPortPolicy = (self.slb_factory
                                  .create('HttpPortPolicy'))
                urlHealthCheck = (self.slb_factory
                                  .create('URLHealthCheck'))
                startCodes = (self.slb_factory
                              .create('ArrayOfunsignedIntSequence'))
                endCodes = (self.slb_factory
                            .create('ArrayOfunsignedIntSequence'))

                startCodes.unsignedIntSequence = start_status_codes
                endCodes.unsignedIntSequence = end_status_codes
                urlHealthCheck.url = http_method + ' ' + url_path
                urlHealthCheck.statusCodeRangeStart = startCodes
                urlHealthCheck.statusCodeRangeEnd = endCodes
                httpPortPolicy.urlStatusCodeInfo = urlHealthCheck
                httpPortPolicy.healthCheckType = 'SIMPLE'

                portPolicy.httpPolInfo = httpPortPolicy

            elif monitor_type == constants.HEALTH_MONITOR_TCP:
                httpPortPolicy = (self.slb_factory
                                  .create('HttpPortPolicy'))
                urlHealthCheck = (self.slb_factory
                                  .create('URLHealthCheck'))
                urlHealthCheck.url = 'HEAD /'
                httpPortPolicy.urlStatusCodeInfo = urlHealthCheck
                httpPortPolicy.healthCheckType = 'SIMPLE'

                portPolicy.httpPolInfo = httpPortPolicy

            elif monitor_type == constants.HEALTH_MONITOR_HTTPS:
                sslPortPolicy = (self.slb_factory
                                 .create('HttpPortPolicy'))
                urlHealthCheck = (self.slb_factory
                                  .create('URLHealthCheck'))
                startCodes = (self.slb_factory
                              .create('ArrayOfunsignedIntSequence'))
                endCodes = (self.slb_factory
                            .create('ArrayOfunsignedIntSequence'))

                urlHealthCheck.url = http_method + ' ' + url_path
                urlHealthCheck.statusCodeRangeStart = startCodes
                urlHealthCheck.statusCodeRangeEnd = endCodes

                sslPortPolicy.urlStatusCodeInfo = urlHealthCheck
                sslPortPolicy.healthCheckType = 'SIMPLE'

                portPolicy.sslPolInfo = sslPortPolicy

            try:
                if is_create:
                    self.slb_service.createPortPolicy(portPolicy)
                else:
                    self.slb_service.updatePortPolicy(portPolicy)
            except suds.WebFault as e:
                LOG.error(_('Error in create/update port policy %s'), e)
                raise adx_exception.ConfigError(msg=e.message)

    @log.log
    def create_health_monitor(self, healthmonitor, pool_id):

        # Limit to 1 Health Monitor per Pool
        healthmonitors = self._get_health_monitors(pool_id)
        if len(healthmonitors) > 1:
            m = _('Only one health monitor can be associated with the pool')
            LOG.error(m)
            raise adx_exception.UnsupportedFeature(msg=m)

        name = healthmonitor['id']
        monitor_type = healthmonitor['type']

        # Create Port Policy
        # if the Monitor Type is TCP / HTTP / HTTPS
        if monitor_type in [constants.HEALTH_MONITOR_HTTP,
                            constants.HEALTH_MONITOR_HTTPS,
                            constants.HEALTH_MONITOR_TCP]:
            if not self._does_port_policy_exist(healthmonitor):
                self._create_update_port_policy(healthmonitor)
            else:
                LOG.debug(_('Port Policy %s already exists on the device'),
                          name)
        elif monitor_type == constants.HEALTH_MONITOR_PING:
            m = _('Health Monitor of type PING not supported')
            LOG.error(m)
            raise adx_exception.UnsupportedFeature(msg=m)

    @log.log
    def delete_health_monitor(self, healthmonitor, pool_id):
        name = healthmonitor['id']
        monitor_type = healthmonitor['type']

        if monitor_type in [constants.HEALTH_MONITOR_HTTP,
                            constants.HEALTH_MONITOR_HTTPS,
                            constants.HEALTH_MONITOR_TCP]:
            if not self._does_port_policy_exist(healthmonitor):
                LOG.debug(_('Health Monitor %s does not '
                          'exist on the device'), name)
                return

            if not self._is_port_policy_in_use(name):
                try:
                    (self.slb_service
                     .deletePortPolicy(name))
                except suds.WebFault as e:
                    raise adx_exception.ConfigError(msg=e.message)
        elif monitor_type == constants.HEALTH_MONITOR_PING:
            m = _('Delete of PING Monitor not supported')
            LOG.error(m)
            raise adx_exception.UnsupportedFeature(msg=m)

    @log.log
    def update_health_monitor(self, new_hm, old_hm, pool_id):
        monitor_type = new_hm['type']

        # Create Port Policy
        # if the Monitor Type is TCP / HTTP / HTTPS
        if monitor_type in [constants.HEALTH_MONITOR_HTTP,
                            constants.HEALTH_MONITOR_HTTPS,
                            constants.HEALTH_MONITOR_TCP]:
            self._create_update_port_policy(new_hm, False)
        elif monitor_type == constants.HEALTH_MONITOR_PING:
            m = _('Health Monitor of type PING not supported')
            LOG.error(m)
            raise adx_exception.UnsupportedFeature(msg=m)

    def _create_real_server(self, member):
        address = member['address']
        weight = member['weight']
        name = address
        if member.get('name'):
            name = member['name']
        is_remote = member.get('is_remote', False)

        try:
            rs = self._adx_server(address, name)
            rsConfigSequence = (self.slb_factory.create
                                ('ArrayOfRealServerConfigurationSequence'))
            rsConfig = (self.slb_factory
                        .create('RealServerConfiguration'))

            rsConfig.realServer = rs
            rsConfig.isRemoteServer = is_remote
            rsConfig.adminState = 'ENABLED'
            rsConfig.leastConnectionWeight = weight
            rsConfig.hcTrackingMode = 'NONE'

            rsConfigSequence.RealServerConfigurationSequence.append(rsConfig)
            (self.slb_service
             .createRealServerWithConfiguration(rsConfigSequence))
        except suds.WebFault as e:
            LOG.debug(_('Error in creating Real Server %s'), e)
            pass

    def _create_real_server_port(self, member):
        address = member['address']
        port = member['protocol_port']
        admin_state_up = member['admin_state_up']
        name = address
        if member.get('name'):
            name = member['name']
        is_backup = member.get('is_backup', False)

        try:
            # Create Port Profile if it is not a standard port
            if port not in ADX_STANDARD_PORTS:
                port_profile = dict()
                port_profile['protocol_port'] = port
                self._create_port_profile(port_profile)

            rsServerPort = self._adx_server_port(address, port, name)
            rsPortSeq = (self.slb_factory
                         .create('ArrayOfRealServerPortConfigurationSequence'))
            rsPortConfig = (self.slb_factory
                            .create('RealServerPortConfiguration'))

            rsPortConfig.serverPort = rsServerPort
            rsAdminState = 'ENABLED' if admin_state_up else 'DISABLED'
            rsPortConfig.adminState = rsAdminState
            if 'max_connections' in member:
                rsPortConfig.maxConnection = member['max_connections']
            rsPortConfig.isBackup = is_backup

            # Work Around to define a value for Enumeration Type
            rsPortConfig.runTimeStatus = 'UNDEFINED'

            (rsPortSeq.RealServerPortConfigurationSequence
             .append(rsPortConfig))

            self.slb_service.createRealServerPortWithConfiguration(rsPortSeq)
        except suds.WebFault as e:
            raise adx_exception.ConfigError(msg=e.message)

    @log.log
    def create_member(self, member):
        self._create_real_server(member)
        self._create_real_server_port(member)

    @log.log
    def delete_member(self, member):
        rsPortCount = self._get_server_port_count(member['address'], False)
        try:
            rsServerPort = self._adx_server_port(member['address'],
                                                 member['protocol_port'])
            self.slb_service.deleteRealServerPort(rsServerPort)

            # Delete the Real Server
            # if this is the only port other than default port
            if rsPortCount <= 2:
                self.slb_service.deleteRealServer(rsServerPort.srvr)
        except suds.WebFault as e:
            raise adx_exception.ConfigError(msg=e.message)

    @log.log
    def update_member(self, new_member, old_member):

        self._update_real_server_properties(new_member, old_member)
        self._update_real_server_port_properties(new_member, old_member)

    @log.log
    def write_mem(self):
        try:
            self.sys_service.writeConfig()
        except Exception as e:
            raise adx_exception.ConfigError(msg=e.message)


    @log.log
    def get_version(self):
        try:
            return self.sys_service.getVersion()
        except Exception as e:
            return None

    @log.log
    def create_pool(self, pool):
        pool_name = pool['name']

        try:
            serverGroupList = (self.slb_factory.create
                               ('ArrayOfRealServerGroupSequence'))
            realServerGroup = (self.slb_factory
                               .create('RealServerGroup'))
            realServerGroup.groupName = pool_name
            serverGroupList.RealServerGroupSequence.append(realServerGroup)

            (self.slb_service
             .createRealServerGroups(serverGroupList))
        except suds.WebFault as e:
            raise adx_exception.ConfigError(msg=e.message)

    @log.log
    def update_pool(self, new_pool, old_pool):
        pass

    @log.log
    def delete_pool(self, pool):
        pool_name = pool['name']
        try:
            serverGroupList = (self.slb_factory
                               .create('ArrayOfStringSequence'))
            serverGroupList.StringSequence.append(pool_name)

            (self.slb_service
             .deleteRealServerGroups(pool_name))
        except suds.WebFault as e:
            raise adx_exception.ConfigError(msg=e.message)

    @log.log
    def get_pool_stats(self, pool_id):
        bytesIn = 0
        bytesOut = 0
        activeConnections = 0
        totalConnections = 0

        poolMembers = self._get_pool_members(pool_id)
        for poolMember in poolMembers:
            try:
                rsIpAddress = poolMember['address']
                rsName = poolMember['address']
                rsPort = poolMember['protocol_port']
                rsServerPort = self._adx_server_port(rsIpAddress,
                                                     rsPort, rsName)
                reply = (self.slb_service
                         .getRealServerPortMonitoringDetails(rsServerPort))

                statistics = reply.statistics.statistics
                bytesIn = bytesIn + statistics.rxBytes
                bytesOut = bytesOut + statistics.txBytes
                activeConnections = activeConnections + statistics.currentConn
                totalConnections = totalConnections + statistics.totalConn

            except suds.WebFault:
                pass

        return {constants.STATS_IN_BYTES: bytesIn,
                constants.STATS_OUT_BYTES: bytesOut,
                constants.STATS_ACTIVE_CONNECTIONS: activeConnections,
                constants.STATS_TOTAL_CONNECTIONS: totalConnections}

    @log.log
    def _create_port_profile(self, port_profile):
        protocol_port = port_profile['protocol_port']
        try:
            portProfile = self.slb_factory.create('PortProfile')
            l4Port = self.slb_factory.create('L4Port')
            l4Port.NameOrNumber = protocol_port
            portProfile.port = l4Port
            portProfile.portType = 'TCP'
            portProfile.status = True

            self.slb_service.createPortProfile(portProfile)
        except suds.WebFault as e:
            LOG.debug(_('Exception in create port profile %s'), e)

    @log.log
    def _delete_port_profile(self, port_profile):
        protocol_port = port_profile['protocol_port']
        try:
            l4Port = self.slb_factory.create('L4Port')
            l4Port.NameOrNumber = protocol_port
            self.slb_service.deletePortProfile(l4Port)
        except suds.WebFault as e:
            LOG.debug(_('Exception in Delete Port Profile %s'), e)

    @log.log
    def ifconfig_e1(self, ip_address, cidr):
        # Configure route only on e1
        try:

            (network,mask) = cidr.split('/')

            ifconfig = self.net_factory.create('InterfaceConfig')
            ifconfig.id.interfaceType = "ETHERNET"
            ifconfig.id.portString = "1"
            ifconfig.isRouteOnly = True

            interfaceConfigSeq = self.net_factory.create(
                'ArrayOfInterfaceConfigSequence')
            interfaceConfigSeq.InterfaceConfigSequence.append(ifconfig)

            self.net_service.setInterfaceConfig(interfaceConfigSeq)

            # Configure ip address on e1
            ifid = self.net_factory.create('InterfaceID')
            ipaddrSeq = self.net_factory.create('ArrayOfInterfaceIPAddressSequence')
            ipaddr = self.net_factory.create('InterfaceIPAddress')

            ifid.portString = "1"
            ifid.interfaceType = "ETHERNET"
            ipaddr.ip = ip_address
            ipaddr.subnetMaskLength = mask

            ipaddrSeq.InterfaceIPAddressSequence.append(ipaddr)

            # Sending operations to the vLb
            self.net_service.setInterfaceConfig(interfaceConfigSeq)
            self.net_service.addIPsToInterface(ifid,ipaddrSeq)
        except suds.WebFault as e:
            LOG.debug(_('Exception configuring e1 %s'), e)
            raise adx_exception.ConfigError(msg=e.message)

    @log.log
    def create_static_route(self, destIPAddress, networkMask, nexthopIPAddress):
        try:
            staticRoute = self.net_factory.create('StaticRoute')
            staticRouteSeq = self.net_factory.create('ArrayOfStaticRouteSequence')

            staticRoute.staticRouteType = 'STANDARD'
            staticRoute.ipVersion = 'IPV4'
            staticRoute.destIPAddress = destIPAddress
            staticRoute.networkMaskBits = networkMask
            staticRoute.nexthopIPAddress = nexthopIPAddress

            staticRouteSeq.StaticRouteSequence.append(staticRoute)

            self.net_service.createStaticRoute(staticRouteSeq)
        except suds.WebFault as e:
            LOG.debug(_('Exception configuring static route %s'), e)
            raise adx_exception.ConfigError(msg=e.message)

    @log.log
    def enable_source_nat(self):
        try:
            globalConfig = self.slb_factory.create('GlobalSlbConfiguration')
            globalConfig.enableSourceNat = True
            self.slb_service.updateSlbGlobalConfiguration(globalConfig)
        except suds.WebFault as e:
            LOG.debug(_('Exception enabling source nat %s'), e)
            raise adx_exception.ConfigError(msg=e.message)
