# This file is part of Flask-PluginEngine.
# Copyright (C) 2014 CERN
#
# Flask-PluginEngine is free software; you can redistribute it
# and/or modify it under the terms of the Revised BSD License.

from __future__ import unicode_literals
from contextlib import contextmanager

from flask import render_template

from .globals import _plugin_ctx_stack, current_plugin
from .util import wrap_in_plugin_context, trim_docstring


def depends(*plugins):
    """Adds dependencies for a plugin.

    This decorator adds the given dependencies to the plugin. Multiple
    dependencies can be specified using multiple arguments or by using
    the decorator multiple times.

    :param plugins: plugin names
    """

    def wrapper(cls):
        cls.required_plugins |= frozenset(plugins)
        return cls

    return wrapper


def uses(*plugins):
    """Adds soft dependencies for a plugin.

    This decorator adds the given soft dependencies to the plugin.
    Multiple soft dependencies can be specified using multiple arguments
    or by using the decorator multiple times.

    Unlike dependencies, the specified plugins will be loaded before the
    plugin if possible, but if they are not available, the plugin will be
    loaded anyway.

    :param plugins: plugin names
    """

    def wrapper(cls):
        cls.used_plugins |= frozenset(plugins)
        return cls

    return wrapper


def render_plugin_template(template, **context):
    """Renders a template from the plugin's template folder with the given context.

    :param template: the name of the template to be rendered
    :param context: the variables that should be available in the context of the template.
    """
    template = '{}:{}'.format(current_plugin.name, template)
    return render_template(template, **context)


class Plugin(object):
    package_name = None  # set to the containing package when the plugin is loaded
    name = None  # set to the entry point name when the plugin is loaded
    root_path = None  # set to the path of the module containing the class when the plugin is loaded
    required_plugins = frozenset()
    used_plugins = frozenset()

    def __init__(self, plugin_engine, app):
        self.plugin_engine = plugin_engine
        self.app = app
        with self.app.app_context():
            with self.plugin_context():
                self.init()

    def init(self):
        """Initializes the plugin at application startup.

        Should be overridden in your plugin if you need initialization.
        Runs inside an application context.
        """
        pass

    @property
    def title(self):
        parts = trim_docstring(self.__doc__).split('\n', 1)
        return parts[0].strip()

    @property
    def description(self):
        parts = trim_docstring(self.__doc__).split('\n', 1)
        try:
            return parts[1].strip()
        except IndexError:
            return 'no description available'

    @contextmanager
    def plugin_context(self):
        """Pushes the plugin on the plugin context stack."""
        _plugin_ctx_stack.push(self)
        yield
        assert _plugin_ctx_stack.pop() is self, 'Popped wrong plugin'

    def connect(self, signal, receiver, **connect_kwargs):
        connect_kwargs['weak'] = False
        signal.connect(wrap_in_plugin_context(self, receiver), **connect_kwargs)

    def __repr__(self):
        return '<{}({}) bound to {}>'.format(type(self).__name__, self.name, self.app)
