# This file is part of Flask-PluginEngine.
# Copyright (C) 2014 CERN
#
# Flask-PluginEngine is free software; you can redistribute it
# and/or modify it under the terms of the Revised BSD License.

from __future__ import unicode_literals

import sys
from contextlib import contextmanager
from functools import wraps, update_wrapper

from ._compat import iteritems
from .globals import _plugin_ctx_stack


def get_state(app):
    """Gets the application-specific plugine engine data."""
    assert 'pluginengine' in app.extensions, \
        'The pluginengine extension was not registered to the current application. ' \
        'Please make sure to call init_app() first.'
    return app.extensions['pluginengine']


def resolve_dependencies(plugins):
    """Resolves dependencies between plugins and sorts them accordingly.

    This function guarantees that a plugin is never loaded before any
    plugin it depends on. If multiple plugins are ready to be loaded,
    the order in which they are loaded is undefined and should not be
    relied upon. If you want a certain order, add a (soft) dependency!

    :param plugins: dict mapping plugin names to plugin classes
    """
    plugins_deps = {name: (cls.required_plugins, cls.used_plugins) for name, cls in iteritems(plugins)}
    resolved_deps = set()
    while plugins_deps:
        # Get plugins with both hard and soft dependencies being met
        ready = {cls for cls, deps in iteritems(plugins_deps) if all(d <= resolved_deps for d in deps)}
        if not ready:
            # Otherwise check for plugins with all hard dependencies being met
            ready = {cls for cls, deps in iteritems(plugins_deps) if deps[0] <= resolved_deps}
        if not ready:
            # Either a circular dependency or a dependency that's not loaded
            raise Exception('Could not resolve dependencies between plugins')
        resolved_deps |= ready
        for name in ready:
            yield name, plugins[name]
            del plugins_deps[name]


@contextmanager
def plugin_context(plugin):
    """Enters a plugin context if a plugin is provided, otherwise clears it

    Useful for code which sometimes needs a plugin context, e.g.
    because it may be used in both the core and in a plugin.
    """
    if plugin is None:
        # Explicitly push a None plugin to disable an existing plugin context
        _plugin_ctx_stack.push(None)
        yield
        assert _plugin_ctx_stack.pop() is None
    else:
        with plugin.instance.plugin_context():
            yield


def wrap_iterator_in_plugin_context(plugin, gen_or_func):
    """Runs an iterator inside a plugin context"""
    # Heavily based on Flask's stream_with_context
    try:
        gen = iter(gen_or_func)
    except TypeError:
        def decorator(*args, **kwargs):
            return wrap_iterator_in_plugin_context(plugin, gen_or_func(*args, **kwargs))

        return update_wrapper(decorator, gen_or_func)

    def generator():
        with plugin_context(plugin):
            # Dummy sentinel.  Has to be inside the context block or we're
            # not actually keeping the context around.
            yield None

            for item in gen:
                yield item

    # The trick is to start the generator.  Then the code execution runs until
    # the first dummy None is yielded at which point the context was already
    # pushed.  This item is discarded.  Then when the iteration continues the
    # real generator is executed.
    wrapped_g = generator()
    next(wrapped_g)
    return wrapped_g


def wrap_macro_in_plugin_context(plugin, macro):
    """Wraps a macro inside a plugin context"""
    func = macro._func

    def decorator(*args, **kwargs):
        with plugin_context(plugin):
            return func(*args, **kwargs)

    macro._func = update_wrapper(decorator, func)


class classproperty(property):
    def __get__(self, obj, type=None):
        return self.fget.__get__(None, type)()


def make_hashable(obj):
    """Makes an object containing dicts and lists hashable."""
    if isinstance(obj, list):
        return tuple(obj)
    elif isinstance(obj, dict):
        return frozenset((k, make_hashable(v)) for k, v in iteritems(obj))
    return obj


# http://wiki.python.org/moin/PythonDecoratorLibrary#Alternate_memoize_as_nested_functions
def memoize(obj):
    cache = {}

    @wraps(obj)
    def memoizer(*args, **kwargs):
        key = (make_hashable(args), make_hashable(kwargs))
        if key not in cache:
            cache[key] = obj(*args, **kwargs)
        return cache[key]

    return memoizer


@memoize
def wrap_in_plugin_context(plugin, func):
    assert plugin is not None

    @wraps(func)
    def wrapped(*args, **kwargs):
        with plugin.plugin_context():
            return func(*args, **kwargs)

    return wrapped


def with_plugin_context(plugin):
    """Decorator to ensure a function is always called in the given plugin context.

    :param plugin: Plugin instance
    """
    def decorator(f):
        return wrap_in_plugin_context(plugin, f)

    return decorator


def trim_docstring(docstring):
    """Trims a docstring based on the algorithm in PEP 257

    http://legacy.python.org/dev/peps/pep-0257/#handling-docstring-indentation
    """
    if not docstring:
        return ''
    # Convert tabs to spaces (following the normal Python rules)
    # and split into a list of lines:
    lines = docstring.expandtabs().splitlines()
    # Determine minimum indentation (first line doesn't count):
    indent = sys.maxsize
    for line in lines[1:]:
        stripped = line.lstrip()
        if stripped:
            indent = min(indent, len(line) - len(stripped))
    # Remove indentation (first line is special):
    trimmed = [lines[0].strip()]
    if indent < sys.maxsize:
        for line in lines[1:]:
            trimmed.append(line[indent:].rstrip())
    # Strip off trailing and leading blank lines:
    while trimmed and not trimmed[-1]:
        trimmed.pop()
    while trimmed and not trimmed[0]:
        trimmed.pop(0)
    # Return a single string:
    return '\n'.join(trimmed)
