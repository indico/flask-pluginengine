# This file is part of Flask-PluginEngine.
# Copyright (C) 2014-2017 CERN
#
# Flask-PluginEngine is free software; you can redistribute it
# and/or modify it under the terms of the Revised BSD License.

import os

from flask import current_app
from flask.templating import Environment
from jinja2 import FileSystemLoader, PrefixLoader, TemplateNotFound, Template
from jinja2.compiler import dict_item_iter, CodeGenerator
from jinja2.runtime import Macro, Context
from jinja2.utils import internalcode

from ._compat import iteritems
from .util import (wrap_iterator_in_plugin_context, wrap_macro_in_plugin_context, get_state,
                   plugin_name_from_template_name)


class PrefixIgnoringFileSystemLoader(FileSystemLoader):
    """FileSystemLoader loader handling plugin prefixes properly

    The prefix is preserved in the template name but not when actually
    accessing the file system since the files there do not have prefixes.
    """

    def get_source(self, environment, template):
        name = template.split(':', 1)[1]
        source, filename, uptodate = super(PrefixIgnoringFileSystemLoader, self).get_source(environment, name)
        return source, filename, uptodate

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


class PluginJinjaContext(Context):
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


class PluginCodeGenerator(CodeGenerator):
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


class PluginEnvironmentMixin(object):
    code_generator_class = PluginCodeGenerator
    context_class = PluginJinjaContext
    template_class = PluginContextTemplate


class PluginEnvironment(PluginEnvironmentMixin, Environment):
    pass
