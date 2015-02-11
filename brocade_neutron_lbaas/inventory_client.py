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

import sys
from db.adx_lb_db_plugin import  AdxLoadBalancerDbPlugin
from db.context import Context
import argparse
import json
import ConfigParser
from db.db_base import configure_db
 

plugin = None
ctx = None

def create_device(device_args):
    print "Create Device - " + device_args["management_ip"]
    device = {"management_ip":device_args["management_ip"],
              "user":device_args["user"],
              "password":device_args["password"]}

    device["communication_type"] = device_args.get("communication_type", "HTTP")
    device["status"] = device_args.get("status", "active")
    device["name"] = device_args.get("name")
    device["version"] = device_args.get("version")
    device["status_description"] = device_args.get("status_description")
    device["ha_config_type"] = device_args.get("ha_config_type")
    device["tenant_id"] = device_args.get("tenant_id")
    device["nova_instance_id"] = device_args.get("nova_instance_id")
    print json.dumps(device, indent=4)
    
    try:
        device=plugin.create_adxloadbalancer(device,ctx)
        print "Device " + device["management_ip"] + " created successfully"
        print json.dumps(device, indent = 4)
    except Exception as e:
        print "Failed to create device - " + device["management_ip"]
        print e.message

def create_port(port_args):
    port={"subnet_id":port_args["subnet_id"],
          "adx_lb_id":port_args["adx_lb_id"]}
    port["mac"] = port_args.get("mac")
    port["ip_address"] = port_args.get("ip_address")
    port["network_id"] = port_args.get("network_id")
    print json.dumps(port, indent=4)
    try:
        port=plugin.create_port(port,ctx)
        print "Port " + port["id"] + " added successfully "
        print json.dumps(port,indent=4)
    except Exception as e:
        print "Failed to add port " + port["id"]
        print e.message

def delete_port(port_args):
    print "Delete Port - " + port_args['id']
    try:
        plugin.delete_port(port_args['id'],ctx)
    except Exception as e:
        print "Failed to delete port "
        print e.message
    print "Port " + port_args['id'] + " deleted successfully"


def update_device(device_args):
    device["id"] = device_args['id']
    device["user"] = device_args.get("user")
    device["password"] = device_args.get("password")
    device["communication_type"] = device_args.get("communication_type", "HTTP")
    device["name"] = device_args.get("name")
    device["version"] = device_args.get("version")
    device["status"] = device_args.get("status")
    device["status_description"] = device_args.get("status_description")
    device["ha_config_type"] = device_args.get("ha_config_type")
    device["tenant_id"] = device_args.get("tenant_id")
    device["nova_instance_id"] = device_args.get("nova_instance_id")
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
        print "Invalid Device - " + device_args['id']
    
    for device in devices:
        print json.dumps(device, indent = 4)
        plugin.delete_adxloadbalancer(device['id'],ctx)
        print "Device " + device['management_ip'] + " deleted successfully"


def list_devices(device_args):
    print "List Devices"
    devices = plugin.get_adxloadbalancer(ctx)
    print "Number of Devices - " + str(len(devices))
    for device in devices:
        print json.dumps(device, indent = 4)
        print ""
    
def list_ports(port_args):
    print "List Ports"
    ports = plugin.get_port(ctx)
    print "Number of Ports: "+ str(len(ports))
    for port in ports:
        print json.dumps(port,indent=4)
        print ""
        
def main(argv=sys.argv[1:]):
    global plugin, ctx

    devices_file_name = unicode('/etc/neutron/services/loadbalancer/brocade/device_inventory.ini')
    config=ConfigParser.ConfigParser()
    config.read(devices_file_name)
    dburl=config.get('DEFAULT','db_url')
    

    configure_db(dburl)
    ctx=Context()
    plugin = AdxLoadBalancerDbPlugin()

    parser = argparse.ArgumentParser(description='Command Line Arguments of Device Inventory Client')
    subparsers = parser.add_subparsers(description='Sub Commands', help='Sub Commands')
    
    device_parser_create = subparsers.add_parser('create-device', help='Create Device')
    device_parser_delete = subparsers.add_parser('delete-device', help='Delete Device')
    device_parser_update = subparsers.add_parser('update-device', help='Update Device')
    device_parser_list = subparsers.add_parser('list-devices', help='List Devices')

    port_parser_create = subparsers.add_parser('add-port', help='Add Port')
    port_parser_delete = subparsers.add_parser('delete-port', help='Delete Port')
    port_parser_update = subparsers.add_parser('update-port', help='Update Port')
    port_parser_list = subparsers.add_parser('list-ports', help='List Ports')


    device_parser_create.add_argument('--management_ip', dest='management_ip', required = True, help='Management IP Address of the device')
    device_parser_create.add_argument('--user', dest='user', required = True, help='User Name')
    device_parser_create.add_argument('--password', dest='password', required = True, help='Password')
    device_parser_create.add_argument('--communication_type', dest='communication_type', required = False, default="HTTP", help='HTTP/HTTPS. Default: HTTP')
    device_parser_create.add_argument('--name', dest='name', required = False, help='Device Name')
    device_parser_create.add_argument('--version', dest='version', required = False, help='running image version of the adx')
    device_parser_create.add_argument('--tenant_id', dest='tenant_id', required = False, help='id of the tenant owning the device')
    device_parser_create.add_argument('--nova_instance_id', dest='nova_instance_id', required = False, help='nova instance id of the adx (if deployed in openstack)')
    device_parser_create.add_argument('--status', dest='status', default="active", required = False, help='active, stopped, paused, suspended, error, inactive')
    device_parser_create.add_argument('--status_description', dest='status_description', required = False, help='status description')
    device_parser_create.add_argument('--ha_config_type', dest='ha_config_type', default="PRIMARY", required = False, help='PRIMARY, SECONDARY')
    device_parser_create.set_defaults(func=create_device)

    port_parser_create.add_argument('--subnet_id', dest='subnet_id',required=True, help='id of the subnet or ALL for default device')
    port_parser_create.add_argument('--adx_lb_id', dest='adx_lb_id',required=True, help='id of the load balancer to which the port belongs to')
    port_parser_create.add_argument('--ip_address',dest='ip_address',required=False, help="IP address of the port")
    port_parser_create.add_argument('--network_id',dest='network_id',required=False, help='The network id to which the port is connected')
    port_parser_create.add_argument('--mac',dest='mac',required=False, help='mac address of the port')
    port_parser_create.set_defaults(func=create_port)

    device_parser_update.add_argument('--id', dest='id', required = True, help='id of the device')
    device_parser_update.add_argument('--user', dest='user', required = False, help='User Name')
    device_parser_update.add_argument('--password', dest='password', required = False, help='Password')
    device_parser_update.add_argument('--communication_type', dest='communication_type', required = False, help='HTTP/HTTPS')
    device_parser_update.add_argument('--name', dest='name', required = False, help='Device Name')
    device_parser_update.add_argument('--version', dest='version', required = False, help='running image version of the adx')
    device_parser_update.add_argument('--tenant_id', dest='tenant_id', required = False, help='id of the tenant owning the device')
    device_parser_update.add_argument('--nova_instance_id', dest='nova_instance_id', required = False, help='nova instance id of the adx (if deployed in openstack)')
    device_parser_update.add_argument('--status', dest='status', required = False, help='active, stopped, paused, suspended, error, inactive')
    device_parser_update.add_argument('--status_description', dest='status_description', required = False, help='status description')
    device_parser_update.add_argument('--ha_config_type', dest='ha_config_type', required = False, help='Primary, Secondary')
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

if __name__ == '__main__':
    main()
