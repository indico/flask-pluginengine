# This file is part of Flask-PluginEngine.
# Copyright (C) 2014-2017 CERN
#
# Flask-PluginEngine is free software; you can redistribute it
# and/or modify it under the terms of the Revised BSD License.

import ast
import re
import sys

from setuptools import setup


with open('flask_pluginengine/__init__.py', 'rb') as f:
    version_line = re.search(r'__version__\s+=\s+(.*)', f.read().decode('utf-8')).group(1)
    version = str(ast.literal_eval(version_line))


needs_pytest = {'pytest', 'test', 'ptr'}.intersection(sys.argv)
pytest_runner = ['pytest-runner'] if needs_pytest else []


setup(
    name='Flask-PluginEngine',
    version=version,
    url='https://github.com/indico/flask-pluginengine',
    license='BSD',
    author='Indico Team',
    author_email='indico-team@cern.ch',
    packages=['flask_pluginengine'],
    zip_safe=False,
    include_package_data=True,
    platforms='any',
    install_requires=[
        'Flask>=0.11',
        'Jinja2>=2.8,!=2.9.5',
        'blinker'
    ],
    setup_requires=pytest_runner,
    tests_require=['pytest', 'pytest-cov'],
    classifiers=[
        'License :: OSI Approved :: BSD License',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6'
    ],
)
