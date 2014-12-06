This repository contains the code for the Brocade Neutron LBaaS Device Driver.
Device driver will need to be installed as a python module in openstack installation.
The device driver manages the adx device inventory at the specified database location.
It has client libraries to add, delete, update, and list devices along with its associated ports

Download the code
run "python setup.py install
pip install configparser
copy the device_inventory.ini to /etc/neutron/services/loadbalancer/brocade
Modify the ini file to point to the database to which the device driver will connect to