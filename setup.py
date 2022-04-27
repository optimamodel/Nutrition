#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from setuptools import setup, find_packages

import os

cwd = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(cwd, "nutrition", "version.py"), "r") as f:
    version = [x.split("=")[1].replace('"', "").strip() for x in f if x.startswith("version =")][0]

try:
    from pypandoc import convert
except ImportError:
    import io

    def convert(filename, fmt):
        with io.open(filename, encoding="utf-8") as fd:
            return fd.read()


CLASSIFIERS = [
    "Environment :: Console",
    "Intended Audience :: Science/Research",
    "License :: OSI Approved :: GPLv3",
    "Operating System :: OS Independent",
    "Programming Language :: Python",
    "Topic :: Software Development :: Libraries :: Python Modules",
    "Development Status :: 3 - Alpha",
    "Programming Language :: Python :: 2.7",
]

setup(
    name="nutrition",
    version=version,
    author="Sam Hainsworth, Ruth Pearson, Madhura Killedar, Nick Scott",
    author_email="info@optimamodel.com",
    description="Optima Nutrition",
    url="http://github.com/optimamodel/nutrition",
    keywords=["optima", "nutrition"],
    platforms=["OS Independent"],
    classifiers=CLASSIFIERS,
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "matplotlib>=1.4.2",
        "numpy>=1.10.1",
        "scipy",
        "pandas>=1.2.4",
        "babel",
        "openpyxl",
        "openpyexcel",
        "sciris",
        "seaborn",
    ],
)
