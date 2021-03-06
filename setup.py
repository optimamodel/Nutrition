#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from setuptools import setup, find_packages

with open("nutrition/version.py", "r") as f:
    version_file = {}
    exec(f.read(), version_file)
    version = version_file["version"]

try:
    from pypandoc import convert
except ImportError:
    import io
    def convert(filename, fmt):
        with io.open(filename, encoding='utf-8') as fd:
            return fd.read()

CLASSIFIERS = [
    'Environment :: Console',
    'Intended Audience :: Science/Research',
    'License :: OSI Approved :: GPLv3',
    'Operating System :: OS Independent',
    'Programming Language :: Python',
    'Topic :: Software Development :: Libraries :: Python Modules',
    'Development Status :: 3 - Alpha',
    'Programming Language :: Python :: 2.7',
]

setup(
    name='nutrition',
    version=version,
    author='Sam Hainsworth, Ruth Pearson, Madhura Killedar, Nick Scott',
    author_email='info@optimamodel.com',
    description='Optima Nutrition',
    url='http://github.com/optimamodel/nutrition',
    keywords=['optima','nutrition'],
    platforms=['OS Independent'],
    classifiers=CLASSIFIERS,
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        'matplotlib>=1.4.2',
        'numpy>=1.10.1',
        'scipy',
        'pandas>=0.17.1',
    ],
)
