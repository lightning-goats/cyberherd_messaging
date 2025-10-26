import pytest
from types import SimpleNamespace

# Stubbing importlib.metadata.version early prevents import errors during
# test collection in developer environments where package metadata is not
# installed (PackageNotFoundError for 'lnbits'). This is a lightweight
# shim for unit tests that import parts of the lnbits package in-place.
import sys
import types
import importlib.util
from pathlib import Path

# Load the services.py module in isolation by creating lightweight package
# modules in sys.modules that point to the repository folders. This avoids
# importing the full `lnbits` package (and its many external deps) during
# unit tests.
repo_root = Path(__file__).resolve().parents[3] / "lnbits"
pkg_root = Path(__file__).resolve().parents[1]

lnbits_mod = types.ModuleType("lnbits")
lnbits_mod.__path__ = [str(repo_root)]
extensions_mod = types.ModuleType("lnbits.extensions")
extensions_mod.__path__ = [str(repo_root / "extensions")]
cyber_pkg = types.ModuleType("lnbits.extensions.cyberherd_messaging")
cyber_pkg.__path__ = [str(pkg_root)]

sys.modules["lnbits"] = lnbits_mod
sys.modules["lnbits.extensions"] = extensions_mod
sys.modules["lnbits.extensions.cyberherd_messaging"] = cyber_pkg

svc_path = str(pkg_root / "services.py")
spec = importlib.util.spec_from_file_location(
    "lnbits.extensions.cyberherd_messaging.services", svc_path
)
chm = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = chm
spec.loader.exec_module(chm)


def test_normalize_relay_hint():
    assert chm.normalize_relay_hint("wss://relay.example") == "wss://relay.example"
    assert chm.normalize_relay_hint("ws://relay.example") == "ws://relay.example"
    assert chm.normalize_relay_hint("https://relay.example/nostr") == "wss://relay.example/nostr"
    assert chm.normalize_relay_hint("http://relay.example/nostr") == "ws://relay.example/nostr"
    assert chm.normalize_relay_hint("ftp://bad") is None
    assert chm.normalize_relay_hint("") is None
    assert chm.normalize_relay_hint(None) is None


@pytest.mark.asyncio
async def test_render_from_json_template(monkeypatch):
    tpl = SimpleNamespace(content='{"content":"Hello {name}", "reply_relay":"https://r.example"}', reply_relay=None)

    async def fake_get_message_template(user_id, category, key):
        return tpl

    monkeypatch.setattr(chm, "crud", SimpleNamespace(get_message_template=fake_get_message_template))

    rendered, goats = await chm.render_and_publish_template(
        user_id="u",
        category="c",
        key="k",
        values={"name": "Alice"},
        return_websocket_message=True,
    )

    assert rendered == "Hello Alice"
    assert isinstance(goats, list) and len(goats) > 0


@pytest.mark.asyncio
async def test_render_from_python_literal_template(monkeypatch):
    tpl = SimpleNamespace(content="{'content': 'Hi {name}', 'reply_relay': 'http://r.example'}", reply_relay=None)

    async def fake_get_message_template(user_id, category, key):
        return tpl

    monkeypatch.setattr(chm, "crud", SimpleNamespace(get_message_template=fake_get_message_template))

    rendered, goats = await chm.render_and_publish_template(
        user_id="u",
        category="c",
        key="k",
        values={"name": "Bob"},
        return_websocket_message=True,
    )

    assert rendered == "Hi Bob"
    assert isinstance(goats, list) and len(goats) > 0


@pytest.mark.asyncio
async def test_render_from_messy_serialized_template(monkeypatch):
    # Missing consistent quoting but contains content key
    tpl = SimpleNamespace(content="{content:'Yo {name}', reply_relay:'https://r.example'}", reply_relay=None)

    async def fake_get_message_template(user_id, category, key):
        return tpl

    monkeypatch.setattr(chm, "crud", SimpleNamespace(get_message_template=fake_get_message_template))

    rendered, goats = await chm.render_and_publish_template(
        user_id="u",
        category="c",
        key="k",
        values={"name": "Carol"},
        return_websocket_message=True,
    )

    assert rendered == "Yo Carol"
    assert isinstance(goats, list) and len(goats) > 0


@pytest.mark.asyncio
async def test_discard_dict_like_template_without_content(monkeypatch):
    # No 'content' key -> should be discarded and produce empty rendered content
    tpl = SimpleNamespace(content="{'foo': 'bar', 'baz': 1}", reply_relay=None)

    async def fake_get_message_template(user_id, category, key):
        return tpl

    monkeypatch.setattr(chm, "crud", SimpleNamespace(get_message_template=fake_get_message_template))

    rendered, goats = await chm.render_and_publish_template(
        user_id="u",
        category="c",
        key="k",
        values={},
        return_websocket_message=True,
    )

    assert rendered == ""
    assert isinstance(goats, list) and len(goats) > 0
