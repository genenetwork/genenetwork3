#!/usr/bin/env python
"""Basic setup script for gn3"""
from setuptools import setup, find_packages  # type: ignore
from setup_commands import RunTests

def long_description():
    """Retrieve long description from the README file."""
    with open('README.md', encoding="utf-8") as readme:
        return readme.read()

setup(author='Bonface M. K.',
      author_email='me@bonfacemunyoki.com',
      description=('GeneNetwork3 REST API for data '
                   'science and machine learning'),
      install_requires=[
          "click",
          "Flask>=1.1.2",
          "mypy>=0.790",
          "mypy-extensions>=0.4.3",
          "mysqlclient>=2.0.1",
          "numpy>=1.20.1",
          "pylint>=2.5.3",
          "pymonad",
          "redis>=3.5.3",
          "requests>=2.25.1",
          "scipy>=1.6.0",
          "plotly>=4.14.3",
          "pyld",
          "flask-cors", # with the `>=3.0.9` specification, it breaks the build
          # "xapian-bindings" # this line breaks `guix shell …` for some reason
      ],
      include_package_data=True,
      scripts=["scripts/index-genenetwork"],
      license='GPLV3',
      long_description=long_description(),
      long_description_content_type='text/markdown',
      name='gn3',
      packages=find_packages(),
      url='https://github.com/genenetwork/genenetwork3',
      version='3.12',
      tests_require=[
          "pytest",
          "hypothesis",
          "pytest-mock"
      ],
      cmdclass={
          "run_tests": RunTests ## testing
      })
