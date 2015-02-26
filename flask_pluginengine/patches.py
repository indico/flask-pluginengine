# This file is part of Flask-PluginEngine.
# Copyright (C) 2014 CERN
#
# Flask-PluginEngine is free software; you can redistribute it
# and/or modify it under the terms of the Revised BSD License.

from __future__ import unicode_literals

import jinja2.compiler
import jinja2.runtime
from flask import current_app
from jinja2.compiler import dict_item_iter
from jinja2.utils import internalcode

from .util import wrap_macro_in_plugin_context, get_state, plugin_name_from_template_name


class PluginJinjaContext(jinja2.runtime.Context):
    @internalcode
    def call(__self, __obj, *args, **kwargs):
        # A caller must run in the containing template's context instead of the
        # one containing the macro. This is achieved by storing the plugin name
        # on the anonymous caller macro.
        if 'caller' in kwargs:
            caller = kwargs['caller']
            plugin = None
            if caller._plugin_name:
                plugin = get_state(current_app).plugin_engine.get_plugin(caller._plugin_name)
            wrap_macro_in_plugin_context(plugin, caller)
        return super(PluginJinjaContext, __self).call(__obj, *args, **kwargs)


class PluginCodeGenerator(jinja2.compiler.CodeGenerator):
    def __init__(self, *args, **kwargs):
        super(PluginCodeGenerator, self).__init__(*args, **kwargs)
        self.inside_call_blocks = []

    def visit_Template(self, node, frame=None):
        super(PluginCodeGenerator, self).visit_Template(node, frame)
        plugin_name = plugin_name_from_template_name(self.name)
        # Execute all blocks inside the plugin context
        self.writeline('from flask_pluginengine.util import wrap_iterator_in_plugin_context')
        self.writeline('blocks = {name: wrap_iterator_in_plugin_context(%r, func) for name, func in blocks.%s()}' %
                       (plugin_name, dict_item_iter))

    def visit_CallBlock(self, *args, **kwargs):
        sentinel = object()
        self.inside_call_blocks.append(sentinel)
        # ths parent's function ends up calling `macro_def` to create the macro function
        super(PluginCodeGenerator, self).visit_CallBlock(*args, **kwargs)
        assert self.inside_call_blocks.pop() is sentinel

    def macro_def(self, *args, **kwargs):
        super(PluginCodeGenerator, self).macro_def(*args, **kwargs)
        if self.inside_call_blocks:
            # we don't have access to the actual Template object here, but we do have
            # access to its name which gives us the plugin name.
            plugin_name = plugin_name_from_template_name(self.name)
            self.writeline('caller._plugin_name = {!r}'.format(plugin_name))


def patch():
    """Applies monkey-patches to Jinja"""
    jinja2.runtime.Context = PluginJinjaContext
    jinja2.compiler.CodeGenerator = PluginCodeGenerator
