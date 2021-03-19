# This file is part of Flask-PluginEngine.
# Copyright (C) 2014-2021 CERN
#
# Flask-PluginEngine is free software; you can redistribute it
# and/or modify it under the terms of the Revised BSD License.

from .engine import PluginEngine
from .globals import current_plugin
from .mixins import (PluginBlueprintSetupState, PluginBlueprintSetupStateMixin, PluginBlueprint, PluginBlueprintMixin,
                     PluginFlask, PluginFlaskMixin)
from .plugin import Plugin, uses, depends, render_plugin_template, url_for_plugin
from .signals import plugins_loaded
from .templating import PluginPrefixLoader
from .util import with_plugin_context, wrap_in_plugin_context, trim_docstring, plugin_context

__version__ = '0.4'
__all__ = ('PluginEngine', 'current_plugin', 'PluginBlueprintSetupState', 'PluginBlueprintSetupStateMixin',
           'PluginBlueprint', 'PluginBlueprintMixin', 'PluginFlask', 'PluginFlaskMixin', 'Plugin', 'uses', 'depends',
           'render_plugin_template', 'url_for_plugin', 'plugins_loaded', 'PluginPrefixLoader', 'with_plugin_context',
           'wrap_in_plugin_context', 'trim_docstring', 'plugin_context')
