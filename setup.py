#!/usr/bin/env python2
from setuptools import setup, find_packages

requirements = [x.strip() for x in open("requirements.txt", "r").readlines()]

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(
    name = "voiptests",
    version = "1.0.1",
    packages = ['voiptests', 'voiptests.lib', 'voiptests.test_cases'],
    package_dir = {'voiptests': '.'},

    install_requires = requirements,

    test_suite = 'tests',

    entry_points = {
        'console_scripts': [
            'alice_ua = voiptests.alice_main:main_func',
            'bob_ua = voiptests.bob_main:main_func',
            ],
        },

    long_description = long_description,
    long_description_content_type = "text/markdown",

    # meta-data for upload to PyPi
    author = "Sippy Software, Inc.",
    author_email = "sobomax@sippysoft.com",
    description = "VoIP Integrated Tests Suite",
    license = "BSD",
    keywords = "ci,sip,b2bua,voip,rfc3261,sippy",
    url = "https://github.com/sippy/voiptests/",
    classifiers = [
        'License :: OSI Approved :: BSD License',
        'Operating System :: POSIX',
        'Programming Language :: Python'
    ],
)
