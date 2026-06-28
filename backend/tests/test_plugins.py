"""Sprint 12: Plugin loader tests."""

from plugins.loader import PluginLoader


def test_plugin_loader_blueprints():
    loader = PluginLoader()
    loader.load_all()
    assert "saas" in loader.blueprints
    assert "ecommerce" in loader.blueprints


def test_plugin_integrations():
    loader = PluginLoader()
    loader.load_all()
    assert "nextjs" in loader.integrations
    assert "wordpress" in loader.integrations


def test_integration_snippet():
    loader = PluginLoader()
    loader.load_all()
    snippet = loader.get_integration_snippet("nextjs", "GTM-TEST")
    assert snippet is not None
    assert "GTM-TEST" in snippet
