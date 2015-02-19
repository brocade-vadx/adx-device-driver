
This repository contains the code for the Brocade Neutron LBaaS Device Driver.
Brocade Neutron LBaaS Device Driver package needs to be installed as a python package in openstack installation.

The inventory of Brocade load balancer devices are maintained in the database (same as neutron or user can define a separate databse). The device driver selects a Brocade load balancer device from the device inventory based on "subnet_id" specified in the request.

The device inventory can be updated either via the command line inventory client program (included in this package) and/or via the Brocade ADX Inventory Listener Service. The Brocade ADX Inventory Listener Service listens for nova notifications for the Brocade load balancer VM instances and automatically updates the device inventory database.

Install Instructions
--------------------

- Download and Install the Brocade Neutron LBaaS Device Driver Python Package

    - From a temporary location, run "https://github.com/brocade-vadx/adx-device-driver.git"

    - Change directory ("cd adx-device-driver")

    - Run "sudo python setup.py install"

- Edit device_inventory.ini file (in /etc/neutron/services/loadbalancer/brocade directory)

    - Specify the database name (existing database or a new database) for the device inventory DB tables.


Brocade Device Inventory Client Usage
-------------------------------------

Brocade Device Inventory Client Command Line Utility (included as part of this package) can be used to manage the device inventory of the brocade load balancer devices.

User can also use the Brocade Nova Listener Service to automatically update the device inventory. Please refer to https://github.com/brocade-vadx/brocade_adx_inventory_listener for details on the Brocade Nova Listener.

Command Line Arguments of Brocade Device Inventory Client

Usage: brocade_inventory_client [-h or --help]

    {create-device,delete-device,update-device,list-devices,
     add-port,delete-port,list-ports}

    Sub Commands:

    create-device       Create load balancer device

    delete-device       Delete load balancer device

    update-device       Update load balancer device

    list-devices        List all load balancer devices

    add-port            Add port to load balancer device

    delete-port         Delete port from load balancer device

    list-ports          List all ports

Create/Delete/Update/List Load Balancer Device
----------------------------------------------

brocade_inventory_client create-device --management-ip 1.1.1.1 --user admin --password password

brocade_inventory_client delete-device --id 598b4db3-32d1-434c-a7d0-0e9f320ffaef

brocade_inventory_client update-device --id "11af24c2-ae73-4bb1-a5e0-23dee3f27571" --version 4.0 --status-description "status description"

brocade_inventory_client list-devices

Add/Delete/List Load Balancer Port
----------------------------------

brocade_inventory_client add-port --subnet-id 54952d95-4b42-4d5b-93c1-3fff93b04eb1 --adx-lb-id 0277ff5d-4289-4d80-861b-c08c4ef214a4

brocade_inventory_client delete-port --id 9eb32e5f-311c-4db5-b1e0-e89180b32d01

brocade_inventory_client list-ports
