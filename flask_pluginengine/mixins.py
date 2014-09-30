# This file is part of Flask-PluginEngine.
# Copyright (C) 2014 CERN
#
# Flask-PluginEngine is free software; you can redistribute it
# and/or modify it under the terms of the Revised BSD License.

from __future__ import unicode_literals

import os

from flask import Blueprint, Flask
from flask.blueprints import BlueprintSetupState
from flask.helpers import locked_cached_property
from jinja2 import PrefixLoader, TemplateNotFound, FileSystemLoader, ChoiceLoader

from .globals import current_plugin
from .util import get_state, wrap_in_plugin_context


class PluginBlueprintSetupStateMixin(object):
    def add_url_rule(self, rule, endpoint=None, view_func=None, **options):
        func = view_func
        if view_func is not None:
            plugin = current_plugin._get_current_object()
            func = wrap_in_plugin_context(plugin, view_func)

        super(PluginBlueprintSetupStateMixin, self).add_url_rule(rule, endpoint, func, **options)


class PluginBlueprintMixin(object):
    def __init__(self, name, *args, **kwargs):
        if 'template_folder' in kwargs:
            raise ValueError('Template folder cannot be specified')
        kwargs.setdefault('static_folder', 'static')
        kwargs.setdefault('static_url_path', '/static/plugins/{}'.format(name))
        name = 'plugin_{}'.format(name)
        super(PluginBlueprintMixin, self).__init__(name, *args, **kwargs)

    def make_setup_state(self, app, options, first_registration=False):
        return PluginBlueprintSetupState(self, app, options, first_registration)

    @locked_cached_property
    def jinja_loader(self):
        return None


class PluginFlaskMixin(object):
    def create_global_jinja_loader(self):
        default_loader = super(PluginFlaskMixin, self).create_global_jinja_loader()
        return ChoiceLoader([PluginPrefixLoader(self), default_loader])


class PluginBlueprintSetupState(PluginBlueprintSetupStateMixin, BlueprintSetupState):
    pass


class PluginBlueprint(PluginBlueprintMixin, Blueprint):
    pass


class PluginFlask(PluginFlaskMixin, Flask):
    pass


class PluginPrefixLoader(PrefixLoader):
    """Prefix loader that uses plugin names"""
    def __init__(self, app):
        super(PluginPrefixLoader, self).__init__(None, ':')
        self.app = app

    def get_loader(self, template):
        try:
            plugin_name, name = template.split(self.delimiter, 1)
        except ValueError:
            raise TemplateNotFound(template)
        plugin = get_state(self.app).plugin_engine.get_plugin(plugin_name)
        if plugin is None:
            raise TemplateNotFound(template)
        loader = FileSystemLoader(os.path.join(plugin.root_path, 'templates'))
        return loader, name

    def list_templates(self):
        raise TypeError('this loader cannot iterate over all templates')
