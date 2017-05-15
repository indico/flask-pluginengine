======
Plugin
======

Creating a plugin
-----------------

Creating a plugin is simple. First of all, you need to create the necessary files: a file for your plugin code (in our case: ``example_plugin.py``), ``setup.py`` and
a ``templates`` folder, with a Jinja template inside.
It should be structured like below:

.. code-block:: text

    plugin
    ├── example_plugin.py
    ├── setup.py
    └── templates
        └── index.html

In ``example_plugin.py`` you need to create a class for your plugin inheriting from ``Plugin``::

    from flask_pluginengine import Plugin

    class ExamplePlugin(Plugin):
        """ExamplePlugin

        Just an example plugin
        """

Second, you need to fill the ``setup.py``. For example::

    from setuptools import setup

    setup(
        name='Example-Plugin',
        version='0.0.1',
        py_modules=['example_plugin'],
        entry_points={'example': {'example_plugin = example_plugin:ExamplePlugin'}}
    )

It's important to define a proper entry point to the plugin's class: ``'example'`` is the namespace we are going to use later in the application's configuration.

Now you can install the plugin running in console::

    $ pip install -e .

Current plugin
--------------

Very useful feature of Flask-PluginEngine is the ``current_plugin`` global value. It's a proxy to the currently active plugin.

Example plugin functionality
----------------------------

Now let's give our plugin some functionality to show how you can use it. In this example we will render the plugin's template from our application.

Let our ``index.html`` template display for example the plugin's title and description::

    {% extends 'base.html' %}

    {% block content %}
        <h1>{{ plugin.title }}</h1>
        <div>{{ plugin.description }}</div>
    {% endblock %}

Notice that the template extends a ``base.html``. We are going to use the application's base template.

Let's create a blueprint in ``example_plugin.py``::

    plugin_blueprint = PluginBlueprint('example', __name__)

In order to create a blueprint of a plugin we need to create a ``PluginBlueprint`` instance.

Then we can create a function rendering the template::

    @plugin_blueprint.route('/plugin')
    def hello_plugin():
        return render_template('example_plugin:index.html', plugin=current_plugin)

We can render any plugin template inside our application specifying the name of the plugin before the template name in the ``render_template`` function, like above.
We are also passing a ``current_plugin`` object to the template.


Now, in the plugin class we can create a method returning the plugin's blueprint::

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


To get more information see the `Plugin`_ API reference.
You can find the source code of the plugin in the `example folder <https://github.com/indico/flask-pluginengine/example/>`_.
