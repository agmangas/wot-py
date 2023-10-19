#!/usr/bin/env python
# -*- coding: utf-8 -*-

from os import path

from setuptools import find_packages, setup

from wotpy.__version__ import __version__
from wotpy.support import is_coap_supported, is_dnssd_supported, is_mqtt_supported

install_requires = [
    "tornado>=6.1,<7.0",
    "jsonschema>=2.0,<3.0",
    "rx>=1.6.0,<2.0",
    "python-slugify>=1.2.4,<2.0",
]

test_requires = [
    "pytest>=6.2.5",
    "pytest-asyncio==0.21.1",
    "pytest-cov>=2.5.1,<2.6.0",
    "pytest-rerunfailures>=10.2,<11.0",
    "mock>=2.0,<3.0",
    "tox>=3.0,<4.0",
    "faker>=13.14.0,<14.0.0",
    "Sphinx>=1.7.5,<2.0.0",
    "sphinx-rtd-theme>=0.4.0,<0.5.0",
    "pyOpenSSL>=18.0.0,<19.0.0",
    "coveralls>=1.0,<2.0",
    "coverage>=5.0,<6.0",
    "cryptography==3.4.8",
    "autopep8>=1.4,<2.0",
    "rope>=0.14.0,<1.0",
    "bump2version>=1.0,<2.0",
    "coloredlogs",
]

if is_coap_supported():
    install_requires.append("aiocoap[all]==0.4.7")

if is_mqtt_supported():
    install_requires.append("hbmqtt>=0.9.4,<1.0")
    install_requires.append("websockets>=8.0,<9.0")

if is_dnssd_supported():
    install_requires.append("zeroconf>=0.30.0,<0.37.0")
    test_requires.append("aiozeroconf==0.1.8")

this_dir = path.abspath(path.dirname(__file__))

with open(path.join(this_dir, "README.md")) as fh:
    long_description = fh.read()

setup(
    name="wotpy",
    version=__version__,
    description="Python implementation of a W3C WoT Runtime and the WoT Scripting API",
    long_description=long_description,
    long_description_content_type="text/markdown",
    keywords="wot iot gateway fog w3c",
    author="Andres Garcia Mangas",
    author_email="andres.garcia@fundacionctic.org",
    url="https://github.com/agmangas/wot-py",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Natural Language :: English",
        "Operating System :: OS Independent",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
    ],
    packages=find_packages(),
    include_package_data=True,
    install_requires=install_requires,
    extras_require={
        "tests": test_requires,
        "uvloop": ["uvloop>=0.12.2,<0.13.0"],
    },
)
