This repository contains the code for the Brocade Neutron LBaaS Device Driver.
Device driver will need to be installed as a python module in openstack installation.
The device driver manages the adx device inventory at the specified database location.
It also has client libraries to add, delete, update, and list devices along with its associated ports

- Download the code

- Install the device driver python module

    - Run "python setup.py install"

- Copy device_inventory.ini file to "/etc/neutron/services/loadbalancer/brocade" directory

- Modify the device_inventory.ini file to point to the database for the device inventory DB tables.


Client Library Usage
====================

Client Library/Program is needed to explictly add/delete vADX/ADX devices and
ports to the device inventory. The device driver selects the device from the 
device inventory based on "subnet_id" specified in the request.

Usage of Client Library is optional. User can run the Brocade ADX Inventory Listener
Service to automatically update the device inventory. 
Please refer to https://github.com/brocade-vadx/brocade_adx_inventory_listener for details
on the Brocade ADX Inventory Listener.

python brocade_lbaas_client.py -h
usage: brocade_lbaas_client.py [-h]
                               {create-device,delete-device,update-device,list-devices,add-port,delete-port,update-port,list-ports}
                               ...

Command Line Arguments of Device Inventory Client

optional arguments:
  -h, --help            show this help message and exit

subcommands:

  Sub Commands

  {create-device,delete-device,update-device,list-devices,add-port,delete-port,update-port,list-ports}

                        Sub Commands

    create-device       Create Device

    delete-device       Delete Device

    update-device       Update Device

    list-devices        List Devices

    add-port            Add Port

    delete-port         Delete Port

    update-port         Update Port

    list-ports          List Ports

Create/Delete/List vADX/ADX Device
----------------------------------

python brocade_lbaas_client.py create-device --management_ip 1.1.1.1 --user admin --password password

python brocade_lbaas_client.py delete-device --id 598b4db3-32d1-434c-a7d0-0e9f320ffaef

python brocade_lbaas_client.py list-devices

Add/Delete/List vADX/ADX Port
------------------------------

python brocade_lbaas_client.py add-port --subnet_id 54952d95-4b42-4d5b-93c1-3fff93b04eb1 --adx_lb_id 0277ff5d-4289-4d80-861b-c08c4ef214a4

python brocade_lbaas_client.py delete-port --id 9eb32e5f-311c-4db5-b1e0-e89180b32d01

python brocade_lbaas_client.py list-ports

