# This file is part of Flask-PluginEngine.
# Copyright (C) 2014-2021 CERN
#
# Flask-PluginEngine is free software; you can redistribute it
# and/or modify it under the terms of the Revised BSD License.

from setuptools import setup

setup(
    name='Example-Plugin',
    version='0.0.1',
    py_modules=['example_plugin'],
    entry_points={'example': {'example_plugin = example_plugin:ExamplePlugin'}}
)
