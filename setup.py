#!/usr/bin/env python
from distutils.core import setup

setup(name='brocade_neutron_lbaas',
      author='Pattabi Ayyasami',
      author_email='pattabi@brocade.com',
      description=" Brocade Loadbalancer Device Driver",
      long_description=open('README.md').read(),
      version='1.0',
      url='http://www.brocade.com',

      # packages=find_packages()
      packages=['brocade_neutron_lbaas',
                  'brocade_neutron_lbaas.db'],

      scripts=["scripts/brocade_inventory_client"],

      data_files=[("/etc/neutron/services/loadbalancer/brocade",
                  ["conf/device_inventory.ini"])],

      license="Apache Software License",
      platforms=["Linux"],
      classifiers=[
          "Intended Audience :: Information Technology",
          "Intended Audience :: System Administrators",
          "Environment :: OpenStack",
          "License :: OSI Approved :: Apache Software License"
          "Operating System :: POSIX :: Linux",
          "Programming Language :: Python",
          "Programming Language :: Python :: 2",
          "Programming Language :: Python :: 2.7"],


      install_requires=["suds>=0.4"])
