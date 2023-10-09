===========
Application
===========

Minimal application setup
-------------------------

To create a Flask application using Flask-PluginEngine we need to define it as a ``PluginFlask`` application. It's a regular ``Flask`` application object that can handle plugins::

    from flask_pluginengine import PluginFlask
    app = PluginFlask(__name__)

    @app.route("/")
    def hello():
        return "Hello world!"

    if __name__ == "__main__":
        app.run()

Now we need to set up the configuration, specifically the namespace of the plugins and the plugins we want to use.
Let's use the ``example_plugin`` we created before. For example::

    app.config['PLUGINENGINE_NAMESPACE'] = 'example'
    app.config['PLUGINENGINE_PLUGINS'] = ['example_plugin']

Next we need to create an instance of PluginEngine for our app and load the plugins::

    plugin_engine = PluginEngine(app=app)
    plugin_engine.load_plugins(app)

Then, we can access the loaded plugins by calling the :func:`get_active_plugins` method, which will return a dictionary containing the active plugins.::

    active_plugins = plugin_engine.get_active_plugins(app=app).values()

To check if all of the plugins were loaded correctly we can also call the :func:`get_failed_plugins` method that will return a dictionary with plugins that failed to load.

Example application functionality
---------------------------------

To understand the possibilities of Flask-PluginEngine we will create a Jinja template where we will list all the plugins we are using.
Let's create two templates, ``base.html`` and ``index.html``.
Our files should be structured like below, where ``app.py`` is the file with the application code:

.. code-block:: text

    app
    ├── app.py
    └── templates
        ├── base.html
        └── index.html

base.html
::

    <!DOCTYPE html>
    <html lang="en">
        <head>
            <meta charset="UTF-8">
            <title>Flask-PluginEngine example</title>
        </head>
        <body>
            {% block content %}
            {% endblock %}
        </body>
    </html>

index.html
::

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

Now what we should also do is to register the blueprints of all our plugins, for instance::

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


    @app.route('/')
    def hello():
        return render_template('index.html', plugins=active_plugins)


    if __name__ == '__main__':
        app.run()

Now when we go to the index page of our application we can access the plugin's template.
We can also directly access it if we go to `/plugin`.

You can find the source code of the application in the `example folder <https://github.com/indico/flask-pluginengine/example/>`_.

Configuring Flask-PluginEngine
------------------------------

The following configuration values exist for Flask-PluginEngine:

====================================== ===========================================
``PLUGINENGINE_NAMESPACE``             Specifies a namespace of the plugins
``PLUGINENGINE_PLUGINS``               List of plugins the application will be
                                       using
====================================== ===========================================
