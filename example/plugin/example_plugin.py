# This file is part of Flask-PluginEngine.
# Copyright (C) 2014-2021 CERN
#
# Flask-PluginEngine is free software; you can redistribute it
# and/or modify it under the terms of the Revised BSD License.

from flask import render_template
from flask_pluginengine import Plugin, PluginBlueprint, current_plugin

plugin_blueprint = PluginBlueprint('example', __name__)


@plugin_blueprint.route('/plugin')
def hello_plugin():
    return render_template('example_plugin:index.html', plugin=current_plugin)


class ExamplePlugin(Plugin):
    """ExamplePlugin

    Just an example plugin
    """

    def get_blueprint(self):
        return plugin_blueprint
