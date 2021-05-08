#!/usr/bin/env python
from setuptools import setup


setup(author='Bonface M. K.',
      author_email='me@bonfacemunyoki.com',
      description=('GeneNetwork3 REST API for data '
                   'science and machine learning'),
      install_requires=[
          "bcrypt>=3.1.7"
          "Flask==1.1.2"
          "ipfshttpclient==0.7.0"
          "mypy==0.790"
          "mypy-extensions==0.4.3"
          "mysqlclient==2.0.1"
          "numpy==1.20.1"
          "pylint==2.5.3"
          "redis==3.5.3"
          "requests==2.25.1"
          "scipy==1.6.0"
          "sqlalchemy-stubs==0.4"
      ],
      license='GPLV3',
      long_description=open('README.md').read(),
      long_description_content_type='text/markdown',
      name='gn3',
      packages=[
          'gn3',
          'gn3.computations',
          'gn3.db',
          'gn3.utility'
      ],
      url='https://github.com/genenetwork/genenetwork3',
      version='0.1')
