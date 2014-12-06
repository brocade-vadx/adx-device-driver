'''
 Copyright 2013 by Brocade Communication Systems
 All rights reserved.

 This software is the confidential and proprietary information
 of Brocade Communication Systems, ("Confidential Information").
 You shall not disclose such Confidential Information and shall
 use it only in accordance with the terms of the license agreement
 you entered into with Brocade Communication Systems.
'''
from db.adx_lb_db_plugin import  AdxLoadBalancerDbPlugin
from db.context import Context
import argparse
import json
import configparser
from db.db_base import configure_db
import sys


        
def create_device(device_args):
    print 'Create Device - ' + device_args['name']

    device = {'name':device_args['name'],
              'management_ip':device_args['management_ip'],
              'user':device_args['user'],
              'password':device_args['password'],
              'status':device_args['status'],
              'communication_type':device_args['communication_type']
             }
    if 'additional_info' in device_args:
        device['additional_info']=device_args['additional_info']
    if 'ha_config_type' in device_args:
        device['ha_config_type']=device_args['ha_config_type']
    if 'tenant_id' in device_args:
        device['tenant_id']=device_args['tenant_id']
    if 'nova_instance_id' in device_args:
        device['nova_instance_id']=device_args['nova_instance_id']
    if 'status_description' in device_args:
        device['status_description']=device_args['status_description']
    if 'version' in device_args:
        device['version']=device_args['version']
    print json.dumps(device, indent=4)
    
    try:
        device=plugin.create_adxloadbalancer(device,ctx)
        print "Device " + device['name'] + " created successfully"
        print json.dumps(device, indent = 4)
    except Exception as e:
        print "Failed to create device - " + device['name']
        print e.message

def create_port(port_args):
    port={'subnet_id':port_args['subnet_id'],
          'adx_lb_id':port_args['adx_lb_id']}
    if port_args['status']:
        port['status']=port_args['status']
    if port_args['mac']:
        port['mac']=port_args['mac']
    if port_args['ip_address']:
        port['ip_address']=port_args['ip_address']
    if port_args['network_id']:
        port['network_id']=port_args['network_id']
    print json.dumps(port, indent=4)
    try:
        port=plugin.create_port(port,ctx)
        print "Port "+port['id']+" created successfully "
        print json.dumps(port,indent=4)
    except Exception as e:
        print "Failed to create port "
        print e.message


def delete_port(port_args):

    print "Delete Port - " + port_args['id']
    try:
        plugin.delete_port(port_args['id'],ctx)
    except Exception as e:
        print "Failed to delete port "
        print e.message
    print "Device " + port_args['id'] + " deleted successfully"


def update_device(device_args):
    device={'id':device_args['id']}
    if device_args['name']:
        device['name']=device_args['name']
    if device_args['user']:
        device['user']=device_args['user']
    if device_args['status']:
        device['status']=device_args['status']
    if device_args['communication_type']:
        device['communication_type']=device_args['communication_type']
    if device_args['password']:
        device['password']=device_args['password']
    if device_args['additional_info']:
        device['additional_info']=device_args['additional_info']
    if device_args['ha_config_type']:
        device['ha_config_type']=device_args['ha_config_type']
    if device_args['tenant_id']:
        device['tenant_id']=device_args['tenant_id']
    if device_args['nova_instance_id']:
        device['nova_instance_id']=device_args['nova_instance_id']
    if device_args['status_description']:
        device['status_description']=device_args['status_description']
    if device_args['version']:
        device['version']=device_args['version']
    print json.dumps(device, indent=4)
    try:
        device=plugin.update_adxloadbalancer(device,ctx)
        print json.dumps(device, indent = 4)
    except Exception as e:
        print "Failed to update device - " + device['id']
        print e.message


def delete_device(device_args):
    print "Delete Device - " + device_args['id']
    device_filter = {'id':device_args['id']}
    devices = plugin.get_adxloadbalancer(ctx, device_filter)
    
    if len(devices) == 0:
        print "Invalid Device - " + device_args['name']
    
    for device in devices:
        print json.dumps(device, indent = 4)
        plugin.delete_adxloadbalancer(device['id'],ctx)
        print "Device " + device['name'] + " deleted successfully"


def list_devices(device_args):
    print "List all devices"
    devices = plugin.get_adxloadbalancer(ctx)
    print "Number of Devices - " + str(len(devices))
    for device in devices:
        print json.dumps(device, indent = 4)
        print ""
    
def list_ports(port_args):
    print "List all devices"
    ports = plugin.get_port(ctx)
    print "Number of Ports -"+str(len(ports))
    for port in ports:
        print json.dumps(port,indent=4)
        print ""
        
if __name__ == '__main__':

    devices_file_name = unicode('/etc/neutron/services/loadbalancer/brocade/device_inventory.ini')
    config=configparser.ConfigParser()
    config.read(devices_file_name)
    dburl=config.get('DEFAULT','db_url')
    configure_db(dburl)
    ctx=Context()
    plugin = AdxLoadBalancerDbPlugin()
    
    parser = argparse.ArgumentParser(description='Command Line Arguments Parser')
    subparsers = parser.add_subparsers(description='Sub Commands', help='Sub Commands')
    
    parser_create = subparsers.add_parser('create', help='Create')
    parser_delete = subparsers.add_parser('delete', help='Delete')
    parser_update = subparsers.add_parser('update', help='Update')
    parser_list = subparsers.add_parser('list', help='List')
    
    subparsers_create = parser_create.add_subparsers(description='Create Resource', help='Resource')
    device_parser_create = subparsers_create.add_parser('device', help='Create ADX Device')
    port_parser_create = subparsers_create.add_parser('port', help="Create Port for ADX Device")

    subparsers_update = parser_update.add_subparsers(description='Update Resource', help='Resource')
    device_parser_update= subparsers_update.add_parser('device', help='Update ADX Device')

    subparsers_delete = parser_delete.add_subparsers(description='Delete Resource', help='Resource')
    device_parser_delete = subparsers_delete.add_parser('device', help='Delete Device')
    port_parser_delete = subparsers_delete.add_parser('port', help='Delete Port')

    subparsers_list = parser_list.add_subparsers(description='List Resource', help='Resource')
    device_parser_list = subparsers_list.add_parser('devices', help='List Devices')
    port_parser_list = subparsers_list.add_parser('ports', help='List Ports')



    
    device_parser_create.add_argument('--name', dest='name', required = True, help='Device Name')
    device_parser_create.add_argument('--management_ip', dest='management_ip', required = True, help='Device Management IP Address')
    device_parser_create.add_argument('--user', dest='user', required = True, help='User Name')
    device_parser_create.add_argument('--password', dest='password', required = True, help='Password')
    device_parser_create.add_argument('--status', dest='status', required = True, help='active, stopped, paused, suspended, error, inactive')
    device_parser_create.add_argument('--additional_info', dest='additional_info', required = False, help='A string to store additional informaton about the device/status etc')
    device_parser_create.add_argument('--ha_config_type', dest='ha_config_type', required = False, help='Primary, Secondary')
    device_parser_create.add_argument('--communication_type', dest='communication_type', required = True, help='HTTP/HTTPS')
    device_parser_create.add_argument('--tenant_id', dest='tenant_id', required = False, help='the id of the tenant that owns the device')
    device_parser_create.add_argument('--nova_instance_id', dest='nova_instance_id', required = False, help='the nova instance id of the adx (if deployed in openstack)')
    device_parser_create.add_argument('--status_description', dest='status_description', required = False, help='status description')
    device_parser_create.add_argument('--version', dest='version', required = False, help='running image version of the adx')


    device_parser_create.set_defaults(func=create_device)

    port_parser_create.add_argument('--subnet_id', dest='subnet_id',required=True, help='id of the subnet or ALL for default device')
    port_parser_create.add_argument('--adx_lb_id', dest='adx_lb_id',required=True, help='The id of the load balancer to which the port belongs to')
    port_parser_create.add_argument('--mac',dest='mac',required=False, help='the mac address of the port')
    port_parser_create.add_argument('--ip_address',dest='ip_address',required=False, help="Ip address of the port")
    port_parser_create.add_argument('--status',dest='status',required=False, help='status of the port Up,Down')
    port_parser_create.add_argument('--network_id',dest='network_id',required=False, help='The network id to which the port is connected')

    port_parser_create.set_defaults(func=create_port)

    device_parser_update.add_argument('--id', dest='id', required = True, help='Id of the device')
    device_parser_update.add_argument('--name', dest='name', required = False, help='Device Name')
    device_parser_update.add_argument('--user', dest='user', required = False, help='User Name')
    device_parser_update.add_argument('--password', dest='password', required = False, help='Password')
    device_parser_update.add_argument('--status', dest='status', required = False, help='active, stopped, paused, suspended, error, inactive')
    device_parser_update.add_argument('--additional_info', dest='additional_info', required = False, help='A string to store additional informaton about the device/status etc')
    device_parser_update.add_argument('--ha_config_type', dest='ha_config_type', required = False, help='Primary, Secondary')
    device_parser_update.add_argument('--communication_type', dest='communication_type', required = False, help='HTTP/HTTPS')
    device_parser_update.add_argument('--tenant_id', dest='tenant_id', required = False, help='the id of the tenant that owns the device')
    device_parser_update.add_argument('--nova_instance_id', dest='nova_instance_id', required = False, help='the nova instance id of the adx (if deployed in openstack)')
    device_parser_update.add_argument('--status_description', dest='status_description', required = False, help='status description')
    device_parser_update.add_argument('--version', dest='version', required = False, help='running image version of the adx')

    device_parser_update.set_defaults(func=update_device)

    device_parser_delete.add_argument('--id', dest='id', required=True, help='Device ID')
    device_parser_delete.set_defaults(func=delete_device)

    port_parser_delete.add_argument('--id',dest='id',required=True, help='id of the port')
    port_parser_delete.set_defaults(func=delete_port)

    device_parser_list.set_defaults(func=list_devices)
    port_parser_list.set_defaults(func=list_ports)

    args = parser.parse_args()
    args_dict = vars(args)
    args.func(args_dict)
