# This file is part of Flask-PluginEngine.
# Copyright (C) 2015 CERN
#
# Flask-PluginEngine is free software; you can redistribute it
# and/or modify it under the terms of the Revised BSD License.

import os

from flask import current_app
from jinja2 import FileSystemLoader, PrefixLoader, TemplateNotFound, Template
from jinja2.runtime import Macro
from jinja2.utils import internalcode

from ._compat import iteritems
from .util import get_state, wrap_iterator_in_plugin_context, wrap_macro_in_plugin_context


class PrefixIgnoringFileSystemLoader(FileSystemLoader):
    """FileSystemLoader loader handling plugin prefixes properly

    The prefix is preserved in the template name but not when actually
    accessing the file system since the files there do not have prefixes.
    """
    def get_source(self, environment, template):
        name = template.split(':', 1)[1]
        contents, _, uptodate = super(PrefixIgnoringFileSystemLoader, self).get_source(environment, name)
        return contents, template, uptodate

    def list_templates(self):  # pragma: no cover
        raise TypeError('this loader cannot iterate over all templates')


class PluginPrefixLoader(PrefixLoader):
    """Prefix loader that uses plugin names to select the load path"""
    def __init__(self, app):
        super(PluginPrefixLoader, self).__init__(None, ':')
        self.app = app

    def get_loader(self, template):
        try:
            plugin_name, _ = template.split(self.delimiter, 1)
        except ValueError:
            raise TemplateNotFound(template)
        plugin = get_state(self.app).plugin_engine.get_plugin(plugin_name)
        if plugin is None:
            raise TemplateNotFound(template)
        loader = PrefixIgnoringFileSystemLoader(os.path.join(plugin.root_path, 'templates'))
        return loader, template

    def list_templates(self):  # pragma: no cover
        raise TypeError('this loader cannot iterate over all templates')

    @internalcode
    def load(self, environment, name, globals=None):
        loader = self.get_loader(name)[0]
        tpl = loader.load(environment, name, globals)
        plugin_name = name.split(':', 1)[0]
        plugin = get_state(current_app).plugin_engine.get_plugin(plugin_name)
        if plugin is None:  # pragma: no cover
            # that should never happen
            raise RuntimeError('Plugin template {} has no plugin'.format(name))
        # Keep a reference to the plugin so we don't have to get it from the name later
        tpl.plugin = plugin
        return tpl


class PluginContextTemplate(Template):
    plugin = None  # overridden on the instance level if a template is in a plugin

    @property
    def root_render_func(self):
        # Wraps the root render function in the plugin context.
        # That way we get the correct context when inheritance/includes are used
        return wrap_iterator_in_plugin_context(self.plugin, self._root_render_func)

    @root_render_func.setter
    def root_render_func(self, value):
        self._root_render_func = value

    def make_module(self, vars=None, shared=False, locals=None):
        # When creating a template module we need to wrap all macros in the plugin context
        # of the containing template in case they are called from another context
        module = super(PluginContextTemplate, self).make_module(vars, shared, locals)
        for attr, macro in iteritems(module.__dict__):
            if not isinstance(macro, Macro):
                continue
            wrap_macro_in_plugin_context(self.plugin, macro)
        return module
