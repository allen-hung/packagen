#!/usr/bin/python

import os
#from distutils.core import setup
from setuptools import setup, find_packages

ver = "1.0.3"

setup(name = "packagen",
      version = ver,
      description = "Auto build tool to build software into debian package",
      author = "Allen Hung",
      author_email = "allenhung8@gmail.com",
      packages = find_packages(),
      install_requires = [],
      scripts = ["scripts/packagen"],
     )
