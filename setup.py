#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup, find_packages

from wotpy.__version__ import __version__

install_requires = [
    'tornado>=5.0,<6.0',
    'jsonschema>=2.0,<3.0',
    'six>=1.10.0,<2.0',
    'rx>=1.6.0,<2.0',
    'python-slugify>=1.2.4,<2.0'
]

setup(
    name='wotpy',
    version=__version__,
    description='Python implementation of the W3C WoT Scripting API',
    keywords='wot w3c ctic iot',
    author='Andres Garcia Mangas',
    author_email='andres.garcia@fundacionctic.org',
    url='https://bitbucket.org/fundacionctic/wot-py',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'Natural Language :: English',
        'Operating System :: Unix',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.6'
    ],
    packages=find_packages(),
    include_package_data=True,
    install_requires=install_requires,
    extras_require={
        'tests': [
            'pytest',
            'pytest-cov',
            'pytest-rerunfailures',
            'mock',
            'tox',
            'faker',
            'Sphinx',
            'sphinx-rtd-theme',
            'futures'
        ]
    }
)
