This repository contains the code for the Brocade Neutron LBaaS Device Driver.
Device driver will need to be installed as a python module in openstack installation.
The device driver manages the adx device inventory at the specified database location.
It has client libraries to add, delete, update, and list devices along with its associated ports

1.Download the code

2.run "python setup.py install

3.pip install configparser

4.copy the device_inventory.ini to /etc/neutron/services/loadbalancer/brocade

5.Modify the ini file to point to the database to which the device driver will connect to.


Client Library usage
==========================

python brocade_lbaas_client.py -h
usage: brocade_lbaas_client.py [-h] {create,list,update,delete} ...

Command Line Arguments Parser

optional arguments:
  -h, --help            show this help message and exit

subcommands:
  Sub Commands

  {create,list,update,delete}
                        Sub Commands
    create              Create
    delete              Delete
    update              Update
    list                List



python brocade_lbaas_client.py create -h

usage: brocade_lbaas_client.py create [-h] {device,port} ...

optional arguments:
  -h, --help     show this help message and exit

subcommands:
  Create Resource

  {device,port}  Resource
    device       Create ADX Device
    port         Create Port for ADX Device



python brocade_lbaas_client.py create device --name dummy --management_ip 1.1.1.1 --status active --communication_type http --user admin --password brocade

Create Device - dummy
{
    "status": "active",
    "ha_config_type": null,
    "name": "dummy",
    "communication_type": "http",
    "status_description": null,
    "management_ip": "1.1.1.1",
    "version": null,
    "user": "admin",
    "tenant_id": null,
    "nova_instance_id": null,
    "password": "brocade",
    "additional_info": null
}
Device dummy created successfully
{
    "status": "active",
    "ha_config_type": null,
    "deleted_at": null,
    "name": "dummy",
    "tenant_id": null,
    "status_description": null,
    "last_updated_time": null,
    "additional_info": null,
    "created_time": null,
    "management_ip": "1.1.1.1",
    "version": null,
    "user": "admin",
    "communication_type": "http",
    "nova_instance_id": null,
    "password": "brocade",
    "id": "e38e95d2-3871-40a0-9bde-cb59a0e184f4",
    "ports": []
}



python brocade_lbaas_client.py list devices

List all devices
Number of Devices - 3
{
    "status": "active",
    "ha_config_type": null,
    "deleted_at": null,
    "name": "asdfdsf",
    "tenant_id": "df912258ab2b4dfbaaa7427e77c88fbf",
    "status_description": null,
    "last_updated_time": null,
    "additional_info": {},
    "created_time": "\"2014-12-05 22:49:24\"",
    "management_ip": "1.1.1.83",
    "version": null,
    "user": "admin",
    "communication_type": "HTTP",
    "nova_instance_id": "17218fee-be7b-45cb-a92a-afe990d35e81",
    "password": "brocade",
    "id": "141eac66-b79d-4017-a1bd-598ac15cec59",
    "ports": [
        {
            "status": "DOWN",
            "subnet_id": "575e5549-2574-4b28-918d-b0ecc9a3d925",
            "adx_lb_id": "141eac66-b79d-4017-a1bd-598ac15cec59",
            "network_id": "99e910c2-8a2f-4e79-ace1-9702c0797361",
            "mac": "fa:16:3e:2e:9d:89",
            "ip_address": "1.1.1.83",
            "id": "4341a2c6-7304-48b8-b4a5-8d283d687d81"
        },
        {
            "status": "DOWN",
            "subnet_id": "4419b963-f9a7-4f53-9cba-789ee8d8e93e",
            "adx_lb_id": "141eac66-b79d-4017-a1bd-598ac15cec59",
            "network_id": "4c74e448-2571-48b0-9601-713c7cecb30e",
            "mac": "fa:16:3e:93:42:c5",
            "ip_address": "10.0.0.86",
            "id": "f4ffa69d-ce77-4430-aeee-f0e774b7293e"
        }
    ]
}

{
    "status": "active",
    "ha_config_type": null,
    "deleted_at": null,
    "name": "dummy",
    "tenant_id": null,
    "status_description": null,
    "last_updated_time": null,
    "additional_info": {},
    "created_time": null,
    "management_ip": "1.1.1.1",
    "version": null,
    "user": "admin",
    "communication_type": "HTTP",
    "nova_instance_id": null,
    "password": "brocade",
    "id": "5458934a-a4f5-4484-9e08-38fa2ae9260a",
    "ports": []
}

{
    "status": "active",
    "ha_config_type": null,
    "deleted_at": null,
    "name": "dummy",
    "tenant_id": null,
    "status_description": null,
    "last_updated_time": null,
    "additional_info": {},
    "created_time": null,
    "management_ip": "1.1.1.1",
    "version": null,
    "user": "admin",
    "communication_type": "HTTP",
    "nova_instance_id": null,
    "password": "brocade",
    "id": "e38e95d2-3871-40a0-9bde-cb59a0e184f4",
    "ports": []
}



python brocade_lbaas_client.py create port --subnet_id ALL --adx_lb_id e38e95d2-3871-40a0-9bde-cb59a0e184f4


{
    "subnet_id": "ALL",
    "adx_lb_id": "e38e95d2-3871-40a0-9bde-cb59a0e184f4"
}
Port 54952d95-4b42-4d5b-93c1-3fff93b04eb1 created successfully
{
    "status": null,
    "subnet_id": "ALL",
    "adx_lb_id": "e38e95d2-3871-40a0-9bde-cb59a0e184f4",
    "network_id": null,
    "mac": null,
    "ip_address": null,
    "id": "54952d95-4b42-4d5b-93c1-3fff93b04eb1"
}



python brocade_lbaas_client.py delete port --id 54952d95-4b42-4d5b-93c1-3fff93b04eb1

Delete Port - 54952d95-4b42-4d5b-93c1-3fff93b04eb1
Port 54952d95-4b42-4d5b-93c1-3fff93b04eb1 deleted successfully

