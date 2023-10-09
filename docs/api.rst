===
API
===


.. automodule:: flask_pluginengine
    :members: uses, depends, render_plugin_template, url_for_plugin

PluginEngine
------------

.. autoclass:: PluginEngine
    :members:

Plugin
------

.. autoclass:: Plugin
    :members: init

    .. automethod:: plugin_context()
    .. classmethod:: instance

        The Plugin instance used by the current app

    .. classmethod:: title

        Plugin's title from the docstring

    .. classmethod:: description

        Plugin's description from the docstring