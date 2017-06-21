#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup, find_packages

setup(
    name='wotpy',
    version='0.0.1',
    description='Python implementation of the W3C WoT standards',
    keywords='wot w3c ctic iot',
    author='Andres Garcia Mangas',
    author_email='andres.garcia@fundacionctic.org',
    url='https://bitbucket.org/fundacionctic/wot-py',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Natural Language :: English',
        'Operating System :: Unix',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.6'
    ],
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
    ],
    extras_require={
        'tests': [
            'pytest',
            'pytest-cov',
            'mock',
            'tox'
        ]
    }
)
