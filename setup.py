from distutils.core import setup

setup(name='brocade_neutron_lbaas',
      author='Pattabi Ayyasami',
      author_email='pattabi@brocade.com',
      description=" Brocade Loadbalancer Device Driver",
      long_description=" Brocade Loadbalancer Device Driver",
      version='1.0',
      url='http://www.brocade.com',
      packages=['brocade_neutron_lbaas',
                'brocade_neutron_lbaas.db'],
      scripts = ["scripts/brocade_inventory_client"],
      data_files = [("/etc/neutron/services/loadbalancer/brocade",
                    ["conf/device_inventory.ini"])],
      license = "Apache Software License",
      platforms = ["Linux"],
      classifiers = [
          "Intended Audience :: Information Technology",
          "Intended Audience :: System Administrators",
          "Environment :: OpenStack",
          "License :: OSI Approved :: Apache Software License"
          "Operating System :: POSIX :: Linux",
          "Programming Language :: Python",
          "Programming Language :: Python :: 2",
          "Programming Language :: Python :: 2.7" ])
