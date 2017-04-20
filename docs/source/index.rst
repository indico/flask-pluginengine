.. Flask-PluginEngine documentation master file, created by
   sphinx-quickstart on Tue Mar 28 14:14:23 2017.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Flask-PluginEngine
==================

Flask-PluginEngine allows you to define and use different plugins in your Flask application


==========
Quickstart
==========



Installation
------------

You can install Flask-PluginEngine with the following command::

    $ pip install Flask-PluginEngine


Creating a plugin
-----------------

Creating a plugin is simple. First of all you need to create a class for your plugin inheriting from Plugin::

    from flask_pluginengine import Plugin

    class ExamplePlugin(Plugin):
    """ExamplePlugin

    Just an example plugin
    """

Second, you need to create a setup file. It's important to define a proper entry point to plugin's class. For example::

    from setuptools import setup

    setup(
        name='Example-Plugin',
        version='0.0.1',
        py_modules=['example_plugin'],
        entry_points={'example': {'example_plugin = example_plugin:ExamplePlugin'}}
    )

Now you can install the plugin running in console::

    $ pip install -e .

Current plugin
--------------

Very useful feature of Flask-PluginEngine is a ``current_plugin`` global value. It's a proxy to currently active plugin.

Example plugin functionality
----------------------------

Now let's give our plugin some functionality to show how you can use the plugin. In this example we will render plugin's template from our application.

Let's create the templates folder with a simple Jinja template. For example displaying plugin's title and description::

    {% extends 'base.html' %}

    {% block content %}
        <h1>{{ plugin.title }}</h1>
        <div>{{ plugin.description }}</div>
    {% endblock %}

If you documented plugin's class now you can access it as a ``name`` and ``description`` class properties.
Notice that the template extends a base.html. We are going to use application's base template.

Let's create a blueprint in our plugin::

    plugin_blueprint = PluginBlueprint('example', __name__)

In order to create a blueprint of a plugin we need to create PluginBlueprint instance.

Then we can create a function rendering the template::

    @plugin_blueprint.route('/plugin')
    def hello_plugin():
    return render_template('example_plugin:index.html', plugin=current_plugin)

We can render any plugin template inside our application specifying name of the plugin before template name in ``render_template`` function, like above.
We are also passing a current_plugin object to the template.


Now in the plugin class we can create a method returning plugin's blueprint::

    def get_blueprint(self):
        return plugin_blueprint

So our plugin code should look like this::

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


To get more about information see `Plugin`_ API reference.

Minimal Application set up
--------------------------

To create Flask application using Flask-PluginEngine we need to define it as PluginFlask application::

    from flask_pluginengine import PluginFlask
    app = PluginFlask(__name__)

    @app.route("/")
    def hello():
        return "Hello world!"

    if __name__ == "__main__":
        app.run()

Now we need to set up the configuration: namespace of plugins we will be using with the application and plugins we want to use.
Let's use the ``example_plugin`` we created before. For example::

    app.config['PLUGINENGINE_NAMESPACE'] = 'example'
    app.config['PLUGINENGINE_PLUGINS'] = ['example_plugin']

Next we need to create an instance of PluginEngine for our app and load the plugins::

    plugin_engine = PluginEngine(app=app)
    plugin_engine.load_plugins(app)

Then we can access loaded plugins by calling :func:`get_active_plugins` method, it will return a dictionary.
If we want to check if all of the plugins were loaded correclty we can also call :func:`get_failed_plugins` method that will return a dictionary with plugins that failed to load::

    active_plugins = plugin_engine.get_active_plugins(app=app).values()


Example application functionality
---------------------------------

To understand the possibilities of Flask-PluginEngine we will create a Jinja template, where we will list all the plugins we are using.
Let's create two templates, the base one (base.html), for example::

    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <title>Title</title>
    </head>
    <body>
        {% block content %}
        {% endblock %}
    </body>
    </html>

And index.html, inheriting from the base one, for example::

    {% extends 'base.html' %}

    {% block content %}
        {% for plugin in plugins %}
            <div>{{ plugin.title }} - {{ plugin.description }}</div>
        {% endfor %}
    {% endblock %}

And let's pass the plugins, when rendering the template in our application::

    @app.route("/")
    def hello():
    return render_template('index.html', plugins=active_plugins)

Now what we also should do is register the blueprints of all our plugins, for instance::

    for plugin in active_plugins:
    with plugin.plugin_context():
        app.register_blueprint(plugin.get_blueprint())

So our application code looks like this::

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

Now when we will go to the index page of our application we will be able to access plugin's template.

You can find the application in the source code in example folder.

Configuring Flask-PluginEngine
------------------------------

The following configuration values exist for Flask-PluginEngine:

====================================== ===========================================
``PLUGINENGINE_NAMESPACE``             Specifies a namespace of the plugins
``PLUGINENGINE_PLUGINS``               List of plugins the application will be
                                       using
====================================== ===========================================


================
PluginEngine API
================


.. automodule:: flask_pluginengine
    :members:

PluginEngine
------------

.. autoclass:: PluginEngine
    :members:

Plugin
------

.. autoclass:: Plugin


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
