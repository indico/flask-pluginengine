# This file is part of Flask-PluginEngine.
# Copyright (C) 2014 CERN
#
# Flask-PluginEngine is free software; you can redistribute it
# and/or modify it under the terms of the Revised BSD License.

import sys

from setuptools import setup
from setuptools.command.test import test as TestCommand


class PyTest(TestCommand):
    user_options = [('pytest-args=', 'a', "Arguments to pass to py.test")]

    def initialize_options(self):
        TestCommand.initialize_options(self)
        self.pytest_args = []

    def finalize_options(self):
        TestCommand.finalize_options(self)
        self.test_args = []
        self.test_suite = True

    def run_tests(self):
        import pytest
        errno = pytest.main(self.pytest_args)
        sys.exit(errno)


setup(
    name='Flask-PluginEngine',
    version='0.1',
    url='https://github.com/indico/flask-pluginengine',
    license='BSD',
    author='Indico Team',
    author_email='indico-team@cern.ch',
    packages=['flask_pluginengine'],
    zip_safe=False,
    include_package_data=True,
    platforms='any',
    install_requires=[
        'Flask>=0.7',
        'Jinja2>=2.8',
        'blinker'
    ],
    tests_require=['pytest', 'pytest-cov'],
    cmdclass={'test': PyTest},
    classifiers=[
        'License :: OSI Approved :: BSD License',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4'
    ],
)
