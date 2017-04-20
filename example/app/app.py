# This file is part of Flask-PluginEngine.
# Copyright (C) 2014-2017 CERN
#
# Flask-PluginEngine is free software; you can redistribute it
# and/or modify it under the terms of the Revised BSD License.

from flask import render_template
from flask_pluginengine import PluginFlask, PluginEngine

app = PluginFlask(__name__)

app.config['PLUGINENGINE_NAMESPACE'] = 'example'
app.config['PLUGINENGINE_PLUGINS'] = ['example_plugin']

plugin_engine = PluginEngine(app=app)
plugin_engine.load_plugins(app)
active_plugins = plugin_engine.get_active_plugins(app=app).values()

for plugin in active_plugins:
    with plugin.plugin_context():
        app.register_blueprint(plugin.get_blueprint())


@app.route("/")
def hello():
    return render_template('index.html', plugins=active_plugins)


if __name__ == "__main__":
    app.run()
