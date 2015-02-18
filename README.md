
This repository contains the code for the Brocade Neutron LBaaS Device Driver.
Brocade Neutron LBaaS Device Driver package needs to be installed as a python package in openstack installation.

The inventory of Brocade load balancer devices are maintained in the database (same as neutron or user can define a separate databse). The device driver selects a Brocade load balancer device from the device inventory based on "subnet_id" specified in the request.

The device inventory can be updated either via the command line inventory client program (included in this package) and/or via the Brocade ADX Inventory Listener Service. The Brocade ADX Inventory Listener Service listens for nova notifications for the Brocade load balancer VM instances and automatically updates the device inventory database.

Install Instructions
====================

- Download and Install the Brocade Neutron LBaaS Device Driver Python Package

    - From a temporary location, run "https://github.com/brocade-vadx/adx-device-driver.git"

    - Change directory ("cd adx-device-driver")

    - Run "sudo python setup.py install"

- Edit device_inventory.ini file (in /etc/neutron/services/loadbalancer/brocade directory) and specify the database name for the device inventory DB tables. The database could be an existing database or a new database.


Brocade Device Inventory Client Usage
======================================

Brocade Device Inventory Client Command Line Utility (included as part of this package) can be used to manage the device inventory of the brocade load balancer devices.

User can also use the Brocade Nova Listener Service to automatically update the device inventory. Please refer to https://github.com/brocade-vadx/brocade_adx_inventory_listener for details on the Brocade Nova Listener.

brocade_inventory_client  -h

usage: brocade_inventory_client [-h]

    {create-device,delete-device,update-device,list-devices,add-port,delete-port,update-port,list-ports}

Command Line Arguments of Brocade Device Inventory Client

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

brocade_inventory_client create-device --management_ip 1.1.1.1 --user admin --password password

brocade_inventory_client delete-device --id 598b4db3-32d1-434c-a7d0-0e9f320ffaef

brocade_inventory_client list-devices

Add/Delete/List vADX/ADX Port
------------------------------

brocade_inventory_client add-port --subnet_id 54952d95-4b42-4d5b-93c1-3fff93b04eb1 --adx_lb_id 0277ff5d-4289-4d80-861b-c08c4ef214a4

brocade_inventory_client delete-port --id 9eb32e5f-311c-4db5-b1e0-e89180b32d01

brocade_inventory_client list-ports