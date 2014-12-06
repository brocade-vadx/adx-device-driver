from distutils.core import setup

setup(name='brocade_neutron_lbaas',
      author='Pattabi Ayyasami',
      author_email='pattabi@brocade.com',
      description=" Brocade ADX Device Driver Library",
      long_description=" Brocade ADX Device Driver Library",
      version='1.0',
      url='http://www.brocade.com',
      packages=['brocade_neutron_lbaas','brocade_neutron_lbaas.db'],
      classifiers=[
      'License :: Apache',
      'Programming Language :: Python',
      ],
      )
