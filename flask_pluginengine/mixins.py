# This file is part of Flask-PluginEngine.
# Copyright (C) 2014-2017 CERN
#
# Flask-PluginEngine is free software; you can redistribute it
# and/or modify it under the terms of the Revised BSD License.

from __future__ import unicode_literals

from flask import Blueprint, Flask
from flask.blueprints import BlueprintSetupState
from flask.helpers import locked_cached_property
from jinja2 import ChoiceLoader

from .globals import current_plugin
from .templating import PluginPrefixLoader, PluginEnvironment
from .util import wrap_in_plugin_context


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
    plugin_jinja_loader = PluginPrefixLoader
    jinja_environment = PluginEnvironment

    def create_global_jinja_loader(self):
        default_loader = super(PluginFlaskMixin, self).create_global_jinja_loader()
        return ChoiceLoader([self.plugin_jinja_loader(self), default_loader])


class PluginBlueprintSetupState(PluginBlueprintSetupStateMixin, BlueprintSetupState):
    pass


class PluginBlueprint(PluginBlueprintMixin, Blueprint):
    pass


class PluginFlask(PluginFlaskMixin, Flask):
    pass
