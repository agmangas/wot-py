#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
from setuptools import setup, find_packages

install_requires = [
    'tornado>=4.0,<5.0',
    'jsonschema>=2.0,<3.0',
    'six>=1.10.0,<2.0',
    'rx>=1.6.0,<2.0'
]

# concurrent.futures is a built-in in Python 3 but needs a backport in Python 2

if sys.version_info[0] == 2:
    install_requires.append('futures>=3.0,<4.0')

setup(
    name='wotpy',
    version='0.0.1',
    description='Python implementation of the W3C WoT standards',
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
            'mock',
            'tox'
        ]
    }
)
