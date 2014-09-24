# This file is part of Flask-PluginEngine.
# Copyright (C) 2014 CERN
#
# Flask-PluginEngine is free software; you can redistribute it
# and/or modify it under the terms of the Revised BSD License.

from setuptools import setup


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
        'blinker'
    ],
)
