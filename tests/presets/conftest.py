import pytest


@pytest.fixture(autouse=True)
def preset_config_dir(tmp_path, monkeypatch):
    """Redirect all preset storage into an isolated temp dir and clear the
    module-global caches around every test.

    Both ``shared.presets.store`` and ``shared.presets.migration`` resolve the
    config directory through a late ``from ...known_paths import
    config_directory_path`` inside their functions, reading the attribute at
    call time. Patching it on the ``known_paths`` module therefore redirects
    both the JSON store (``{cfg}/presets/{game}/{id}.json``) and the legacy XML
    (``{cfg}/{id}_presets.xml``) at once.

    ``autouse`` so no test can accidentally read or migrate the developer's real
    Sollumz config. ``clear_all_caches`` runs before (defensive — the session
    start re-enables the addon, which seeds the cache) and after each test
    because ``store._cache`` is module-global and survives the whole session.
    """
    from ... import known_paths
    from ...shared.presets import store

    store.clear_all_caches()
    monkeypatch.setattr(known_paths, "config_directory_path", lambda: str(tmp_path))
    yield tmp_path
    store.clear_all_caches()


@pytest.fixture
def tmp_category():
    """An unregistered throwaway category. ``store``/``migration`` take a
    category object directly, so registering it (which would raise on a
    duplicate id) is unnecessary."""
    from ...shared.presets.core import PresetCategory

    return PresetCategory(id="testcat", label="Test", game="testgame")
