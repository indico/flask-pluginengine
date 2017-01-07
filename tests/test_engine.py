# This file is part of Flask-PluginEngine.
# Copyright (C) 2014-2017 CERN
#
# Flask-PluginEngine is free software; you can redistribute it
# and/or modify it under the terms of the Revised BSD License.

import os
import re
from pkg_resources import EntryPoint, Distribution

import pytest
from jinja2 import TemplateNotFound
from flask import render_template, Flask

from flask_pluginengine import (PluginEngine, plugins_loaded, Plugin, render_plugin_template, current_plugin,
                                plugin_context, PluginFlask)
from flask_pluginengine.templating import PrefixIgnoringFileSystemLoader


class EspressoModule(Plugin):
    """EspressoModule

    Creamy espresso out of your Flask app
    """
    pass


class ImposterPlugin(object):
    """ImposterPlugin

    I am not really a plugin as I do not inherit from the Plugin class
    """
    pass


class OtherVersionPlugin(Plugin):
    """OtherVersionPlugin

    I am a plugin with a custom version
    """
    version = '2.0'


class NonDescriptivePlugin(Plugin):
    """NonDescriptivePlugin"""


class MockEntryPoint(EntryPoint):
    def load(self):
        if self.name == 'importfail':
            raise ImportError()
        elif self.name == 'imposter':
            return ImposterPlugin
        elif self.name == 'otherversion':
            return OtherVersionPlugin
        elif self.name == 'nondescriptive':
            return NonDescriptivePlugin
        else:
            return EspressoModule


@pytest.fixture
def flask_app():
    app = PluginFlask(__name__, template_folder='templates/core')
    app.config['TESTING'] = True
    app.config['PLUGINENGINE_NAMESPACE'] = 'test'
    app.config['PLUGINENGINE_PLUGINS'] = ['espresso']
    app.add_template_global(lambda: current_plugin.name if current_plugin else 'core', 'whereami')
    return app


@pytest.yield_fixture
def flask_app_ctx(flask_app):
    with flask_app.app_context():
        yield flask_app
        assert not current_plugin, 'leaked plugin context'


@pytest.fixture
def engine(flask_app):
    return PluginEngine(app=flask_app)


@pytest.fixture
def mock_entry_point(monkeypatch):
    from flask_pluginengine import engine as engine_mod

    def _mock_entry_points(_, name):
        return {
            'espresso': [MockEntryPoint('espresso', 'test.plugin')],
            'otherversion': [MockEntryPoint('otherversion', 'test.plugin')],
            'nondescriptive': [MockEntryPoint('nondescriptive', 'test.plugin')],
            'someotherstuff': [],
            'doubletrouble': [MockEntryPoint('double', 'double'), MockEntryPoint('double', 'double')],
            'importfail': [MockEntryPoint('importfail', 'test.importfail')],
            'imposter': [MockEntryPoint('imposter', 'test.imposter')]
        }[name]

    def _mock_distribution(name):
        return Distribution(version='1.2.3')

    monkeypatch.setattr(engine_mod, 'iter_entry_points', _mock_entry_points)
    monkeypatch.setattr(engine_mod, 'get_distribution', _mock_distribution)


@pytest.fixture
def loaded_engine(mock_entry_point, monkeypatch, flask_app, engine):
    engine.load_plugins(flask_app)

    def init_loader(self, *args, **kwargs):
        super(PrefixIgnoringFileSystemLoader, self).__init__(os.path.join(flask_app.root_path, 'templates/plugin'))

    monkeypatch.setattr('flask_pluginengine.templating.PrefixIgnoringFileSystemLoader.__init__', init_loader)
    return engine


def test_fail_pluginengine_namespace(flask_app):
    """
    Fail if PLUGINENGINE_NAMESPACE is not defined
    """
    del flask_app.config['PLUGINENGINE_NAMESPACE']
    with pytest.raises(Exception) as exc_info:
        PluginEngine(app=flask_app)
    assert 'PLUGINENGINE_NAMESPACE' in str(exc_info.value)


def test_load(mock_entry_point, flask_app, engine):
    """
    We can load a plugin
    """

    loaded = {'result': False}

    def _on_load(sender):
        loaded['result'] = True

    plugins_loaded.connect(_on_load, flask_app)
    engine.load_plugins(flask_app)

    assert loaded['result']

    with flask_app.app_context():
        assert len(engine.get_failed_plugins()) == 0
        assert list(engine.get_active_plugins()) == ['espresso']

        plugin = engine.get_active_plugins()['espresso']

        assert plugin.title == 'EspressoModule'
        assert plugin.description == 'Creamy espresso out of your Flask app'
        assert plugin.version == '1.2.3'
        assert plugin.package_version == '1.2.3'


def test_no_description(mock_entry_point, flask_app, engine):
    flask_app.config['PLUGINENGINE_PLUGINS'] = ['nondescriptive']
    engine.load_plugins(flask_app)
    with flask_app.app_context():
        plugin = engine.get_active_plugins()['nondescriptive']
        assert plugin.title == 'NonDescriptivePlugin'
        assert plugin.description == 'no description available'


def test_custom_version(mock_entry_point, flask_app, engine):
    flask_app.config['PLUGINENGINE_PLUGINS'] = ['otherversion']
    engine.load_plugins(flask_app)
    with flask_app.app_context():
        plugin = engine.get_active_plugins()['otherversion']
        assert plugin.package_version == '1.2.3'
        assert plugin.version == '2.0'


def test_fail_non_existing(mock_entry_point, flask_app, engine):
    """
    Fail if a plugin that is specified in the config does not exist
    """

    flask_app.config['PLUGINENGINE_PLUGINS'] = ['someotherstuff']

    engine.load_plugins(flask_app)

    with flask_app.app_context():
        assert len(engine.get_failed_plugins()) == 1
        assert len(engine.get_active_plugins()) == 0


def test_fail_noskip(mock_entry_point, flask_app, engine):
    """
    Fail immediately if no_skip=False
    """

    flask_app.config['PLUGINENGINE_PLUGINS'] = ['someotherstuff']

    assert engine.load_plugins(flask_app, skip_failed=False) is False


def test_fail_double(mock_entry_point, flask_app, engine):
    """
    Fail if the same plugin corresponds to two extension points
    """

    flask_app.config['PLUGINENGINE_PLUGINS'] = ['doubletrouble']

    engine.load_plugins(flask_app)

    with flask_app.app_context():
        assert len(engine.get_failed_plugins()) == 1
        assert len(engine.get_active_plugins()) == 0


def test_fail_import_error(mock_entry_point, flask_app, engine):
    """
    Fail if impossible to import Plugin
    """

    flask_app.config['PLUGINENGINE_PLUGINS'] = ['importfail']

    engine.load_plugins(flask_app)

    with flask_app.app_context():
        assert len(engine.get_failed_plugins()) == 1
        assert len(engine.get_active_plugins()) == 0


def test_fail_not_subclass(mock_entry_point, flask_app, engine):
    """
    Fail if the plugin is not a subclass of `Plugin`
    """

    flask_app.config['PLUGINENGINE_PLUGINS'] = ['imposter']

    engine.load_plugins(flask_app)

    with flask_app.app_context():
        assert len(engine.get_failed_plugins()) == 1
        assert len(engine.get_active_plugins()) == 0


def test_instance_not_loaded(mock_entry_point, flask_app, engine):
    """
    Fail when trying to get the instance for a plugin that's not loaded
    """

    other_app = Flask(__name__)
    other_app.config['TESTING'] = True
    other_app.config['PLUGINENGINE_NAMESPACE'] = 'test'
    other_app.config['PLUGINENGINE_PLUGINS'] = []
    engine.init_app(other_app)
    with other_app.app_context():
        with pytest.raises(RuntimeError):
            EspressoModule.instance


def test_instance(flask_app_ctx, loaded_engine):
    """
    Check if Plugin.instance points to the correct instance
    """

    assert EspressoModule.instance is loaded_engine.get_plugin(EspressoModule.name)


def test_double_load(flask_app, loaded_engine):
    """
    Fail if the engine tries to load the plugins a second time
    """

    with pytest.raises(RuntimeError) as exc_info:
        loaded_engine.load_plugins(flask_app)
    assert 'Plugins already loaded' in str(exc_info.value)


def test_has_plugin(flask_app, loaded_engine):
    """
    Test that has_plugin() returns the correct result
    """
    with flask_app.app_context():
        assert loaded_engine.has_plugin('espresso')
        assert not loaded_engine.has_plugin('someotherstuff')


def test_get_plugin(flask_app, loaded_engine):
    """
    Test that get_plugin() behaves consistently
    """
    with flask_app.app_context():
        plugin = loaded_engine.get_plugin('espresso')
        assert isinstance(plugin, EspressoModule)
        assert plugin.name == 'espresso'

        assert loaded_engine.get_plugin('someotherstuff') is None


def test_repr(loaded_engine):
    """
    Check that repr(PluginEngine(...)) is OK
    """
    assert repr(loaded_engine) == '<PluginEngine()>'


def test_repr_state(flask_app, loaded_engine):
    """
    Check that repr(PluginEngineState(...)) is OK
    """
    from flask_pluginengine.util import get_state
    assert repr(get_state(flask_app)) == ("<_PluginEngineState(<PluginEngine()>, <PluginFlask 'test_engine'>, "
                                          "{'espresso': <EspressoModule(espresso) bound to "
                                          "<PluginFlask 'test_engine'>>})>")


def test_render_template(flask_app, loaded_engine):
    """
    Check that app/plugin templates are separate
    """
    with flask_app.app_context():
        assert render_template('test.txt') == 'core test'
        assert render_template('espresso:test.txt') == 'plugin test'


def test_render_plugin_template(flask_app_ctx, loaded_engine):
    """
    Check that render_plugin_template works
    """
    plugin = loaded_engine.get_plugin('espresso')
    text = 'plugin test'
    with plugin.plugin_context():
        assert render_template('espresso:test.txt') == text
        assert render_plugin_template('test.txt') == text
        assert render_plugin_template('espresso:test.txt') == text
    # explicit plugin name works outside context
    assert render_plugin_template('espresso:test.txt') == text
    # implicit plucin name fails outside context
    with pytest.raises(RuntimeError):
        render_plugin_template('test.txt')


def _parse_template_data(data):
    items = [re.search(r'(\S+)=(.+)', item.strip()).groups() for item in data.strip().splitlines() if item.strip()]
    rv = dict(items)
    assert len(rv) == len(items)
    return rv


@pytest.mark.parametrize('in_plugin_ctx', (False, True))
def test_template_plugin_contexts_macros(flask_app_ctx, loaded_engine, in_plugin_ctx):
    """
    Check that the plugin context is handled properly in macros
    """
    plugin = loaded_engine.get_plugin('espresso')
    with plugin_context(plugin if in_plugin_ctx else None):
        assert _parse_template_data(render_template('simple_macro.txt')) == {
            'macro': 'core-imp-macro/core/undef',
            'macro_call': 'core-imp-macro/core/core'
        }
        assert _parse_template_data(render_template('espresso:simple_macro.txt')) == {
            'macro': 'core-imp-macro/core/undef',
            'macro_call': 'core-imp-macro/core/espresso'
        }


@pytest.mark.parametrize('in_plugin_ctx', (False, True))
def test_template_plugin_contexts_macros_extends(flask_app_ctx, loaded_engine, in_plugin_ctx):
    """
    Check that the plugin context is handled properly in macros with template inheritance
    """
    plugin = loaded_engine.get_plugin('espresso')
    with plugin_context(plugin if in_plugin_ctx else None):
        assert _parse_template_data(render_template('simple_macro_extends.txt')) == {
            'core_macro': 'core-macro/core/undef',
            'core_macro_call': 'core-macro/core/core',
        }
        assert _parse_template_data(render_template('espresso:simple_macro_extends.txt')) == {
            'plugin_macro': 'core-macro/core/undef',
            'plugin_macro_call': 'core-macro/core/espresso',
        }


@pytest.mark.parametrize('in_plugin_ctx', (False, True))
def test_template_plugin_contexts_macros_extends_base(flask_app_ctx, loaded_engine, in_plugin_ctx):
    """
    Check that the plugin context is handled properly in macros defined/called in the base tpl
    """
    plugin = loaded_engine.get_plugin('espresso')
    with plugin_context(plugin if in_plugin_ctx else None):
        assert _parse_template_data(render_template('simple_macro_extends_base.txt')) == {
            'core_macro': 'core-macro/core/undef',
            'core_macro_call': 'core-macro/core/core',
        }
        assert _parse_template_data(render_template('espresso:simple_macro_extends_base.txt')) == {
            'core_macro': 'core-macro/core/undef',
            'core_macro_call': 'core-macro/core/core',
        }


@pytest.mark.parametrize('in_plugin_ctx', (False, True))
def test_template_plugin_contexts_macros_nested_calls(flask_app_ctx, loaded_engine, in_plugin_ctx):
    """
    Check that the plugin context is handled properly when using nested call blocks
    """
    plugin = loaded_engine.get_plugin('espresso')
    with plugin_context(plugin if in_plugin_ctx else None):
        assert _parse_template_data(render_template('nested_calls.txt')) == {
            'outer': 'core-outer-macro/core/core',
            'inner': 'core-inner-macro/core/core',
        }
        assert _parse_template_data(render_template('espresso:nested_calls.txt')) == {
            'outer': 'core-outer-macro/core/espresso',
            'inner': 'core-inner-macro/core/espresso',
        }


@pytest.mark.parametrize('in_plugin_ctx', (False, True))
def test_template_plugin_contexts_super(flask_app_ctx, loaded_engine, in_plugin_ctx):
    """
    Check that the plugin context is handled properly when using `super()`
    """
    plugin = loaded_engine.get_plugin('espresso')
    with plugin_context(plugin if in_plugin_ctx else None):
        assert _parse_template_data(render_template('base.txt')) == {
            'block': 'core',
        }
        assert _parse_template_data(render_template('espresso:super.txt')) == {
            'block': 'core/espresso',
        }


@pytest.mark.parametrize('in_plugin_ctx', (False, True))
def test_template_plugin_contexts(flask_app_ctx, loaded_engine, in_plugin_ctx):
    """
    Check that the plugin contexts are correct in all cases
    """
    plugin = loaded_engine.get_plugin('espresso')
    with plugin_context(plugin if in_plugin_ctx else None):
        assert _parse_template_data(render_template('context.txt')) == {
            'core_main': 'core',
            'core_block_a': 'core-a/core',
            'core_block_b': 'core-b/core',
            'core_macro': 'core-macro/core/undef',
            'core_macro_call': 'core-macro/core/core',
            'core_macro_imp': 'core-imp-macro/core/undef',
            'core_macro_imp_call': 'core-imp-macro/core/core',
            'core_macro_plugin_imp': 'plugin-imp-macro/espresso/undef',
            'core_macro_plugin_imp_call': 'plugin-imp-macro/espresso/core',
            'core_inc_core': 'core test',
            'core_inc_plugin': 'plugin test',
        }
        assert _parse_template_data(render_template('espresso:context.txt')) == {
            'core_main': 'core',
            'core_block_a': 'plugin-a/espresso',
            'core_block_b': 'core-b/core',
            'core_macro': 'core-macro/core/undef',
            'core_macro_call': 'core-macro/core/core',
            'core_macro_in_plugin': 'core-macro/core/undef',
            'core_macro_in_plugin_call': 'core-macro/core/espresso',
            'core_macro_imp': 'core-imp-macro/core/undef',
            'core_macro_imp_call': 'core-imp-macro/core/core',
            'core_macro_plugin_imp': 'plugin-imp-macro/espresso/undef',
            'core_macro_plugin_imp_call': 'plugin-imp-macro/espresso/core',
            'plugin_macro': 'plugin-macro/espresso/undef',
            'plugin_macro_call': 'plugin-macro/espresso/espresso',
            'core_inc_core': 'core test',
            'core_inc_plugin': 'plugin test',
            'plugin_inc_core': 'core test',
            'plugin_inc_plugin': 'plugin test',
        }


def test_template_invalid(flask_app_ctx, loaded_engine):
    """
    Check that loading an invalid plugin template fails
    """
    with pytest.raises(TemplateNotFound):
        render_template('nosuchplugin:foobar.txt')
